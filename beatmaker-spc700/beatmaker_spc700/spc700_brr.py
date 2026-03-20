"""BRR encoder and WAV loader for the SPC700 DSP.

Encodes PCM audio into BRR (Bit Rate Reduction) format used by the SNES S-DSP.
Each BRR block is 9 bytes (1 header + 8 data) encoding 16 four-bit samples.

The filter prediction coefficients match the reference DSP decoder exactly.
"""

from __future__ import annotations

import struct
import warnings
import wave
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BRR_BLOCK_SAMPLES = 16
BRR_BLOCK_BYTES = 9
DSP_SAMPLE_RATE = 32000


# ---------------------------------------------------------------------------
# WAV loading
# ---------------------------------------------------------------------------

def load_wav(path: str | Path) -> tuple[list[int], int]:
    """Load a WAV file and return (mono_samples_int16, sample_rate).

    Handles stereo→mono mixdown, 8/16/24/32-bit sample widths.
    Returns a list of ints in [-32768, 32767].
    """
    path = Path(path)
    with wave.open(str(path), "r") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    # Unpack raw bytes to per-channel samples
    samples_per_ch: list[list[int]] = [[] for _ in range(nch)]

    if sw == 1:
        # 8-bit unsigned
        for i in range(nframes):
            for ch in range(nch):
                val = raw[i * nch + ch]
                samples_per_ch[ch].append((val - 128) << 8)
    elif sw == 2:
        # 16-bit signed little-endian
        fmt = f"<{nframes * nch}h"
        vals = struct.unpack(fmt, raw)
        for i in range(nframes):
            for ch in range(nch):
                samples_per_ch[ch].append(vals[i * nch + ch])
    elif sw == 3:
        # 24-bit signed little-endian → truncate to 16-bit
        for i in range(nframes):
            for ch in range(nch):
                off = (i * nch + ch) * 3
                val = raw[off] | (raw[off + 1] << 8) | (raw[off + 2] << 16)
                if val >= 0x800000:
                    val -= 0x1000000
                samples_per_ch[ch].append(max(-32768, min(32767, val >> 8)))
    elif sw == 4:
        # 32-bit signed little-endian → truncate to 16-bit
        fmt = f"<{nframes * nch}i"
        vals = struct.unpack(fmt, raw)
        for i in range(nframes):
            for ch in range(nch):
                samples_per_ch[ch].append(
                    max(-32768, min(32767, vals[i * nch + ch] >> 16)))
    else:
        raise ValueError(f"Unsupported sample width: {sw} bytes")

    # Mix to mono
    if nch == 1:
        mono = samples_per_ch[0]
    else:
        mono = []
        for i in range(nframes):
            total = sum(samples_per_ch[ch][i] for ch in range(nch))
            mono.append(max(-32768, min(32767, total // nch)))

    return mono, sr


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------

def resample(samples: list[int], src_rate: int, dst_rate: int) -> list[int]:
    """Resample PCM using linear interpolation.

    Args:
        samples: Input samples (int16 range).
        src_rate: Source sample rate.
        dst_rate: Target sample rate.

    Returns:
        Resampled list of int16 values.
    """
    if src_rate == dst_rate or len(samples) < 2:
        return list(samples)

    ratio = src_rate / dst_rate
    out_len = int(len(samples) / ratio)
    result = []
    for i in range(out_len):
        pos = i * ratio
        idx = int(pos)
        frac = pos - idx
        if idx + 1 < len(samples):
            val = samples[idx] * (1.0 - frac) + samples[idx + 1] * frac
        else:
            val = samples[min(idx, len(samples) - 1)]
        result.append(max(-32768, min(32767, int(round(val)))))
    return result


# ---------------------------------------------------------------------------
# BRR filter prediction — exact reference coefficients
# ---------------------------------------------------------------------------

def _brr_predict(filt: int, old: int, older: int) -> int:
    """Compute filter prediction matching the DSP decoder exactly.

    These are the reference C coefficients from spc700_dsp.py:219-224.
    Python >> on negative ints is arithmetic shift (correct).
    """
    if filt == 0:
        return 0
    if filt == 1:
        return old + (-old >> 4)
    if filt == 2:
        return (old << 1) + ((-3 * old) >> 5) - older + (older >> 4)
    # filt == 3
    return (old << 1) + ((-13 * old) >> 6) - older + ((3 * older) >> 4)


def _clamp16(s: int) -> int:
    if s > 32767:
        return 32767
    if s < -32768:
        return -32768
    return s


def _clamp15(s: int) -> int:
    """Clamp to 16-bit then clip to 15-bit, matching DSP hardware."""
    s = _clamp16(s)
    # (int16_t)(s << 1) >> 1 — clear bit 15, signed 15-bit
    s = ((s << 1) & 0xFFFF)
    if s >= 0x8000:
        s -= 0x10000
    return s >> 1


def _decode_nibble(nibble: int, shift: int, filt: int,
                   old: int, older: int) -> int:
    """Simulate DSP decoding of a single nibble. Returns decoded sample."""
    # Sign-extend from 4 bits
    if nibble >= 8:
        nibble -= 16

    # Apply range shift
    if shift <= 12:
        s = (nibble << shift) >> 1
    else:
        s = -2048 if nibble < 0 else 0

    # Apply filter
    s += _brr_predict(filt, old, older)

    # Clamp + 15-bit clip
    return _clamp15(s)


# ---------------------------------------------------------------------------
# BRR block encoder
# ---------------------------------------------------------------------------

def _find_best_nibble(target: int, shift: int, filt: int,
                      old: int, older: int) -> tuple[int, int, int]:
    """Find the 4-bit nibble (-8..+7) that minimizes error.

    Exhaustively tries all 16 nibble values (0x0-0xF).
    Returns: (best_nibble_unsigned, decoded_sample, squared_error)
    """
    best_nib = 0
    best_err = 2**60
    best_dec = 0

    for nib in range(16):
        decoded = _decode_nibble(nib, shift, filt, old, older)
        err = (target - decoded) ** 2
        if err < best_err:
            best_err = err
            best_nib = nib
            best_dec = decoded

    return best_nib & 0x0F, best_dec, best_err


def _encode_brr_block(
    pcm: list[int],
    old: int,
    older: int,
    is_end: bool = False,
    is_loop: bool = False,
) -> tuple[bytes, int, int, float]:
    """Encode 16 PCM samples into one 9-byte BRR block.

    Tries all 4 filters × 13 shifts, picks minimum total squared error.

    Returns: (brr_bytes_9, new_old, new_older, total_error)
    """
    assert len(pcm) == BRR_BLOCK_SAMPLES

    best_block = None
    best_error = float('inf')
    best_old = old
    best_older = older

    for filt in range(4):
        for shift in range(13):  # 0-12
            cur_old = old
            cur_older = older
            block_error = 0.0
            nibbles = []

            for i in range(BRR_BLOCK_SAMPLES):
                nib, decoded, err = _find_best_nibble(
                    pcm[i], shift, filt, cur_old, cur_older)
                nibbles.append(nib)
                block_error += err
                cur_older = cur_old
                cur_old = decoded

            if block_error < best_error:
                best_error = block_error
                # Build the 9-byte block
                header = (shift << 4) | (filt << 2)
                if is_loop:
                    header |= 0x02
                if is_end:
                    header |= 0x01
                data = bytearray(9)
                data[0] = header
                for i in range(8):
                    hi = nibbles[i * 2] & 0x0F
                    lo = nibbles[i * 2 + 1] & 0x0F
                    data[1 + i] = (hi << 4) | lo
                best_block = bytes(data)
                best_old = cur_old
                best_older = cur_older

    return best_block, best_old, best_older, best_error


# ---------------------------------------------------------------------------
# Full sample encoder
# ---------------------------------------------------------------------------

def encode_brr(
    pcm_samples: list[int],
    loop_start: int | None = None,
) -> tuple[bytes, int | None]:
    """Encode a complete PCM sample into BRR format.

    Args:
        pcm_samples: Mono 16-bit PCM samples.
        loop_start: Sample index where loop begins (None = no loop).
                    Rounded down to nearest 16-sample boundary.

    Returns:
        (brr_data, loop_block_byte_offset)
        loop_block_byte_offset is the byte offset within brr_data
        where the loop block starts, or None if no loop.
    """
    if not pcm_samples:
        return b'', None

    # Pad to multiple of 16
    n = len(pcm_samples)
    remainder = n % BRR_BLOCK_SAMPLES
    if remainder:
        pcm_samples = list(pcm_samples) + [0] * (BRR_BLOCK_SAMPLES - remainder)

    num_blocks = len(pcm_samples) // BRR_BLOCK_SAMPLES

    # Handle loop point
    loop_block: int | None = None
    loop_byte_offset: int | None = None
    if loop_start is not None:
        if loop_start >= n:
            warnings.warn(f"loop_start ({loop_start}) >= sample length ({n}), "
                          "ignoring loop")
        else:
            loop_block = loop_start // BRR_BLOCK_SAMPLES
            if loop_start % BRR_BLOCK_SAMPLES != 0:
                warnings.warn(
                    f"loop_start ({loop_start}) not on 16-sample boundary, "
                    f"rounded down to {loop_block * BRR_BLOCK_SAMPLES}")
            loop_byte_offset = loop_block * BRR_BLOCK_BYTES

    # Encode blocks
    old = 0
    older = 0
    blocks = []

    for b in range(num_blocks):
        start = b * BRR_BLOCK_SAMPLES
        block_pcm = pcm_samples[start:start + BRR_BLOCK_SAMPLES]
        is_end = (b == num_blocks - 1)
        is_loop = loop_block is not None

        block_bytes, old, older, _ = _encode_brr_block(
            block_pcm, old, older, is_end=is_end, is_loop=is_loop)
        blocks.append(block_bytes)

    return b''.join(blocks), loop_byte_offset


# ---------------------------------------------------------------------------
# High-level convenience
# ---------------------------------------------------------------------------

def load_and_encode(
    wav_path: str | Path,
    target_rate: int = DSP_SAMPLE_RATE,
    loop_start: int | None = None,
    trim_silence: bool = True,
    silence_threshold: int = 64,
) -> tuple[bytes, int, int | None]:
    """Load a WAV, resample, optionally trim silence, encode to BRR.

    Args:
        wav_path: Path to WAV file.
        target_rate: Sample rate for BRR encoding.
        loop_start: Loop point in source samples (auto-scaled to target rate).
        trim_silence: Remove trailing near-zero samples.
        silence_threshold: Amplitude below which samples are silent.

    Returns:
        (brr_data, native_freq, loop_block_byte_offset)
        native_freq: The rate the BRR was encoded at (for pitch calculation).
    """
    pcm, src_rate = load_wav(wav_path)

    # Resample
    if src_rate != target_rate:
        # Scale loop point
        if loop_start is not None:
            loop_start = int(loop_start * target_rate / src_rate)
        pcm = resample(pcm, src_rate, target_rate)

    # Trim trailing silence
    if trim_silence:
        end = len(pcm)
        while end > 0 and abs(pcm[end - 1]) <= silence_threshold:
            end -= 1
        if end < len(pcm):
            pcm = pcm[:max(end, BRR_BLOCK_SAMPLES)]

    brr_data, loop_offset = encode_brr(pcm, loop_start)
    return brr_data, target_rate, loop_offset
