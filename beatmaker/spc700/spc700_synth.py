"""SPC700 composition API — drive the DSP directly for maximum expressiveness.

Bypasses the SPC700 CPU entirely, writing DSP registers from Python with
sample-accurate timing. This gives unlimited "CPU budget" and direct control
over every parameter: pitch slides, volume fades, vibrato, echo sweeps, etc.

Usage:
    from spc700_synth import Song, Instrument, ADSR, EchoConfig

    kick = Instrument.drum("kick.wav")
    song = Song(bpm=120)
    t = song.add_track(kick)
    t.note(duration=1.0).rest(1.0).note(duration=1.0).rest(1.0)
    song.render("output.wav")
"""

from __future__ import annotations

import math
import struct
import warnings
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from .spc700_brr import load_and_encode, encode_brr, load_wav, resample
from .spc700_dsp import DSP


# ===========================================================================
# Constants
# ===========================================================================

SAMPLE_RATE = 32000
MAX_VOICES = 8
RAM_SIZE = 0x10000  # 64KB

# Automation resolution: DSP samples between continuous parameter updates
AUTOMATION_STEP = 32  # ~1ms at 32kHz


# ===========================================================================
# Pitch utilities
# ===========================================================================

# Semitone offsets from C
_NOTE_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi_to_freq(note: int) -> float:
    """Convert MIDI note number to frequency in Hz. A4 (69) = 440 Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def note_to_midi(name: str) -> int:
    """Parse note name to MIDI number.

    Accepts: 'C4' (60), 'C#4' (61), 'Db4' (61), 'A4' (69), etc.
    Octave range: -1 to 9.
    """
    name = name.strip()
    if not name:
        raise ValueError("Empty note name")

    # Parse letter
    letter = name[0].upper()
    if letter not in _NOTE_BASE:
        raise ValueError(f"Invalid note letter: {letter}")

    pos = 1
    # Parse accidental
    accidental = 0
    if pos < len(name) and name[pos] == '#':
        accidental = 1
        pos += 1
    elif pos < len(name) and name[pos] == 'b':
        accidental = -1
        pos += 1

    # Parse octave
    octave_str = name[pos:]
    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"Invalid octave in note name: {name!r}")

    return (octave + 1) * 12 + _NOTE_BASE[letter] + accidental


def freq_to_pitch(target_freq: float, sample_native_freq: float) -> int:
    """Convert target frequency to 14-bit DSP pitch register value.

    pitch = (target_freq / sample_native_freq) * 4096
    Clamped to [0, 0x3FFF].
    """
    pitch = int(round((target_freq / sample_native_freq) * 4096.0))
    return max(0, min(0x3FFF, pitch))


# A Pitch can be specified as:
#   int   -> MIDI note number
#   float -> frequency in Hz
#   str   -> note name ('C4', 'F#3')
#   None  -> play at sample's native rate
Pitch = Union[int, float, str, None]


def resolve_pitch(pitch: Pitch) -> float:
    """Resolve any Pitch to frequency in Hz."""
    if isinstance(pitch, str):
        return midi_to_freq(note_to_midi(pitch))
    if isinstance(pitch, int):
        return midi_to_freq(pitch)
    if isinstance(pitch, float):
        return pitch
    raise ValueError("Cannot resolve pitch: None (use sample native rate)")


# ===========================================================================
# Envelope types
# ===========================================================================

@dataclass
class ADSR:
    """ADSR envelope. Maps directly to DSP ADSR1/ADSR2 registers.

    attack:        0-15 (higher = faster, 15 ≈ 1ms)
    decay:         0-7  (higher = faster)
    sustain_level: 0-7  (sustain threshold = (level+1)/8 of max)
    sustain_rate:  0-31 (0 = no decrease, 31 = fastest)
    """
    attack: int = 15
    decay: int = 7
    sustain_level: int = 7
    sustain_rate: int = 0

    def to_adsr1(self) -> int:
        return 0x80 | ((self.decay & 7) << 4) | (self.attack & 0x0F)

    def to_adsr2(self) -> int:
        return ((self.sustain_level & 7) << 5) | (self.sustain_rate & 0x1F)


@dataclass
class Gain:
    """GAIN envelope (alternative to ADSR).

    mode: 'direct', 'linear_dec', 'exp_dec', 'linear_inc', 'bent_inc'
    value: level (0-127) for direct, rate (0-31) for variable modes
    """
    mode: str = 'direct'
    value: int = 127

    _MODE_MAP = {
        'direct': -1,
        'linear_dec': 0,
        'exp_dec': 1,
        'linear_inc': 2,
        'bent_inc': 3,
    }

    def to_gain_reg(self) -> int:
        if self.mode == 'direct':
            return self.value & 0x7F
        code = self._MODE_MAP.get(self.mode, 0)
        return 0x80 | ((code & 3) << 5) | (self.value & 0x1F)

    @classmethod
    def direct(cls, level: int = 127) -> Gain:
        return cls('direct', level)

    @classmethod
    def linear_dec(cls, rate: int = 16) -> Gain:
        return cls('linear_dec', rate)

    @classmethod
    def exp_dec(cls, rate: int = 16) -> Gain:
        return cls('exp_dec', rate)

    @classmethod
    def linear_inc(cls, rate: int = 16) -> Gain:
        return cls('linear_inc', rate)

    @classmethod
    def bent_inc(cls, rate: int = 16) -> Gain:
        return cls('bent_inc', rate)


Envelope = Union[ADSR, Gain]


# ===========================================================================
# Sample & Instrument
# ===========================================================================

@dataclass
class Sample:
    """A BRR-encoded sample ready for the DSP."""
    name: str
    brr_data: bytes
    native_freq: float        # Hz — the rate it was encoded at
    loop_offset: Optional[int] = None  # byte offset of loop block in brr_data

    @classmethod
    def from_wav(
        cls,
        path: str | Path,
        name: str | None = None,
        target_rate: int = SAMPLE_RATE,
        loop_start: int | None = None,
        trim_silence: bool = True,
    ) -> Sample:
        """Load a WAV file and encode to BRR."""
        path = Path(path)
        if name is None:
            name = path.stem
        brr, native, loop_off = load_and_encode(
            path, target_rate=target_rate, loop_start=loop_start,
            trim_silence=trim_silence)
        return cls(name=name, brr_data=brr, native_freq=native,
                   loop_offset=loop_off)

    @classmethod
    def from_pcm(
        cls,
        pcm: list[int],
        sample_rate: int,
        name: str = "pcm",
        loop_start: int | None = None,
    ) -> Sample:
        """Create from raw mono int16 PCM data."""
        brr, loop_off = encode_brr(pcm, loop_start)
        return cls(name=name, brr_data=brr, native_freq=sample_rate,
                   loop_offset=loop_off)

    @classmethod
    def from_single_cycle(
        cls,
        path: str | Path,
        name: str | None = None,
        target_rate: int = SAMPLE_RATE,
    ) -> Sample:
        """Load a single-cycle waveform (e.g. AKWF) and set up for looped playback.

        Single-cycle waveforms contain exactly one period of a wave.
        The fundamental frequency is derived from: sample_rate / num_frames.
        The entire waveform is set to loop from the start.

        Args:
            path: Path to a single-cycle WAV file.
            name: Display name (defaults to filename stem).
            target_rate: BRR encoding rate. 32000 gives best quality.
        """
        path = Path(path)
        if name is None:
            name = path.stem

        pcm, src_rate = load_wav(str(path))
        fundamental = src_rate / len(pcm)

        brr, native, loop_off = load_and_encode(
            path, target_rate=target_rate, loop_start=0,
            trim_silence=False)

        return cls(name=name, brr_data=brr, native_freq=fundamental,
                   loop_offset=loop_off)

    @property
    def num_blocks(self) -> int:
        return len(self.brr_data) // 9

    @property
    def duration(self) -> float:
        """Duration in seconds at native playback rate."""
        return (self.num_blocks * 16) / self.native_freq

    @property
    def memory_bytes(self) -> int:
        return len(self.brr_data)


@dataclass
class Instrument:
    """A playable instrument: sample + envelope + volume defaults."""
    name: str
    sample: Sample
    envelope: Envelope = field(default_factory=ADSR)
    default_volume: tuple[int, int] = (127, 127)  # (left, right)

    @classmethod
    def from_wav(
        cls,
        path: str | Path,
        name: str | None = None,
        envelope: Envelope | None = None,
        volume: tuple[int, int] = (127, 127),
        target_rate: int = SAMPLE_RATE,
        loop_start: int | None = None,
    ) -> Instrument:
        """Load WAV, create Sample, wrap in Instrument."""
        sample = Sample.from_wav(path, name=name, target_rate=target_rate,
                                 loop_start=loop_start)
        if name is None:
            name = sample.name
        if envelope is None:
            envelope = ADSR()
        return cls(name=name, sample=sample, envelope=envelope, volume=volume)

    @classmethod
    def drum(cls, path: str | Path, name: str | None = None,
             target_rate: int = SAMPLE_RATE) -> Instrument:
        """Drum preset: fast attack, natural decay, no sustain, no loop."""
        sample = Sample.from_wav(path, name=name, target_rate=target_rate)
        if name is None:
            name = sample.name
        return cls(
            name=name, sample=sample,
            envelope=ADSR(attack=15, decay=5, sustain_level=0, sustain_rate=31),
            default_volume=(127, 127),
        )

    @classmethod
    def pad(cls, path: str | Path, name: str | None = None,
            loop_start: int | None = None,
            target_rate: int = SAMPLE_RATE) -> Instrument:
        """Pad preset: full sustain, with loop."""
        sample = Sample.from_wav(path, name=name, target_rate=target_rate,
                                 loop_start=loop_start)
        if name is None:
            name = sample.name
        return cls(
            name=name, sample=sample,
            envelope=ADSR(attack=12, decay=7, sustain_level=7, sustain_rate=0),
            default_volume=(100, 100),
        )

    @classmethod
    def synth(
        cls,
        path: str | Path,
        name: str | None = None,
        preset: str = 'pad',
        volume: tuple[int, int] = (100, 100),
        target_rate: int = SAMPLE_RATE,
    ) -> Instrument:
        """Create an instrument from a single-cycle waveform (e.g. AKWF).

        These tiny waveforms (~600 samples) loop perfectly and can be
        pitched to any note. The preset controls the envelope shape.

        Args:
            path: Path to a single-cycle WAV file.
            name: Display name (defaults to filename stem).
            preset: Envelope preset name:
                'pad'    — slow attack, full sustain (lush pads)
                'lead'   — medium attack, high sustain (melodic leads)
                'pluck'  — fast attack, quick decay (pizzicato / keys)
                'bass'   — fast attack, medium decay, some sustain
                'organ'  — instant attack, full sustain, no decay
                'string' — slow attack, full sustain (orchestral strings)
                'bell'   — fast attack, long exponential decay
            volume: Default (left, right) volume.
            target_rate: BRR encoding rate.
        """
        sample = Sample.from_single_cycle(path, name=name,
                                          target_rate=target_rate)
        if name is None:
            name = sample.name

        presets: dict[str, ADSR] = {
            'pad':    ADSR(attack=10, decay=7, sustain_level=6, sustain_rate=0),
            'lead':   ADSR(attack=13, decay=6, sustain_level=5, sustain_rate=5),
            'pluck':  ADSR(attack=15, decay=4, sustain_level=0, sustain_rate=20),
            'bass':   ADSR(attack=15, decay=5, sustain_level=3, sustain_rate=8),
            'organ':  ADSR(attack=15, decay=7, sustain_level=7, sustain_rate=0),
            'string': ADSR(attack=8,  decay=7, sustain_level=6, sustain_rate=0),
            'bell':   ADSR(attack=15, decay=3, sustain_level=0, sustain_rate=10),
        }
        envelope = presets.get(preset)
        if envelope is None:
            valid = ', '.join(sorted(presets))
            raise ValueError(f"Unknown preset {preset!r}. Choose from: {valid}")

        return cls(name=name, sample=sample, envelope=envelope,
                   default_volume=volume)


# ===========================================================================
# Folder loaders
# ===========================================================================

def load_sample_folder(
    folder: str | Path,
    target_rate: int = SAMPLE_RATE,
    single_cycle: bool = False,
    loop_start: int | None = None,
    trim_silence: bool = True,
) -> dict[str, Sample]:
    """Load all WAV files from a folder into a dict of Samples.

    Args:
        folder: Path to directory containing .wav files.
        target_rate: BRR encoding rate for all samples.
        single_cycle: If True, treat files as single-cycle waveforms
                      (loop from start, native_freq = fundamental).
        loop_start: Loop point for non-single-cycle samples (None = no loop).
        trim_silence: Trim trailing silence (ignored if single_cycle).

    Returns:
        Dict mapping filename stem (e.g. 'AKWF_piano_0001') to Sample.
    """
    folder = Path(folder)
    samples: dict[str, Sample] = {}
    for wav_path in sorted(folder.glob("*.wav")):
        if single_cycle:
            sample = Sample.from_single_cycle(wav_path, target_rate=target_rate)
        else:
            sample = Sample.from_wav(wav_path, target_rate=target_rate,
                                     loop_start=loop_start,
                                     trim_silence=trim_silence)
        samples[sample.name] = sample
    return samples


def load_drum_kit(
    folder: str | Path,
    target_rate: int = SAMPLE_RATE,
    envelope: Envelope | None = None,
    volume: tuple[int, int] = (127, 127),
) -> dict[str, Instrument]:
    """Load all WAV files from a folder as drum instruments.

    Args:
        folder: Path to directory containing .wav files.
        target_rate: BRR encoding rate.
        envelope: Envelope for all drums (default: punchy drum preset).
        volume: Default stereo volume.

    Returns:
        Dict mapping filename stem to Instrument.
    """
    if envelope is None:
        envelope = ADSR(attack=15, decay=5, sustain_level=0, sustain_rate=31)
    folder = Path(folder)
    kit: dict[str, Instrument] = {}
    for wav_path in sorted(folder.glob("*.wav")):
        sample = Sample.from_wav(wav_path, target_rate=target_rate)
        kit[sample.name] = Instrument(
            name=sample.name, sample=sample,
            envelope=envelope, default_volume=volume,
        )
    return kit


def load_synth_bank(
    folder: str | Path,
    preset: str = 'pad',
    target_rate: int = SAMPLE_RATE,
    volume: tuple[int, int] = (100, 100),
) -> dict[str, Instrument]:
    """Load all single-cycle WAVs from a folder as synth instruments.

    Each file becomes an Instrument with the given preset envelope.
    Useful for AKWF waveform collections.

    Args:
        folder: Path to directory containing single-cycle .wav files.
        preset: Envelope preset (see Instrument.synth() for options).
        target_rate: BRR encoding rate.
        volume: Default stereo volume.

    Returns:
        Dict mapping filename stem to Instrument.
    """
    folder = Path(folder)
    bank: dict[str, Instrument] = {}
    for wav_path in sorted(folder.glob("*.wav")):
        inst = Instrument.synth(wav_path, preset=preset,
                                target_rate=target_rate, volume=volume)
        bank[inst.name] = inst
    return bank


# ===========================================================================
# Track Events
# ===========================================================================

@dataclass
class Note:
    """Play a note."""
    pitch: Pitch = None       # None = native sample rate
    duration: float = 1.0     # beats
    velocity: float = 1.0     # 0.0-1.0
    pan: float | None = None  # -1.0=left, 0.0=center, 1.0=right


@dataclass
class Rest:
    """Silence for a duration."""
    duration: float = 1.0     # beats


@dataclass
class PitchBend:
    """Smooth pitch slide over a duration."""
    target: Pitch
    duration: float = 0.25    # beats
    curve: str = 'linear'     # 'linear' or 'exponential'


@dataclass
class VolumeSlide:
    """Smooth volume change."""
    target_velocity: float    # 0.0-1.0
    duration: float = 0.25    # beats
    target_pan: float | None = None


@dataclass
class Vibrato:
    """Pitch vibrato on the current note."""
    depth: float = 0.5        # semitones
    rate: float = 6.0         # Hz
    duration: float = 1.0     # beats
    delay: float = 0.0        # beats before vibrato starts


@dataclass
class Tremolo:
    """Volume tremolo on the current note."""
    depth: float = 0.3        # 0.0-1.0 fraction of volume
    rate: float = 6.0         # Hz
    duration: float = 1.0     # beats
    delay: float = 0.0        # beats before tremolo starts


@dataclass
class SetEnvelope:
    """Change envelope for subsequent notes."""
    envelope: Envelope


@dataclass
class SetInstrument:
    """Change instrument for subsequent notes."""
    instrument: Instrument


@dataclass
class RawRegWrite:
    """Direct DSP register write at this point in the timeline."""
    register: int
    value: int


Event = Union[Note, Rest, PitchBend, VolumeSlide, Vibrato, Tremolo,
              SetEnvelope, SetInstrument, RawRegWrite]


# ===========================================================================
# Echo Configuration
# ===========================================================================

@dataclass
class EchoConfig:
    """Echo/reverb effect configuration."""
    enabled: bool = False
    delay: int = 4              # EDL (0-15), each unit = 16ms
    feedback: int = 60          # EFB (signed 8-bit, -128..127)
    volume_left: int = 40       # EVOL_L (signed 8-bit)
    volume_right: int = 40      # EVOL_R (signed 8-bit)
    voices: int = 0x00          # EON bitmask
    fir: tuple[int, ...] = (127, 0, 0, 0, 0, 0, 0, 0)

    @property
    def buffer_bytes(self) -> int:
        return self.delay * 2048 if self.delay > 0 else 4

    @classmethod
    def reverb(cls, delay: int = 6, feedback: int = 80,
               volume: int = 50, voices: int = 0xFF) -> EchoConfig:
        return cls(enabled=True, delay=delay, feedback=feedback,
                   volume_left=volume, volume_right=volume, voices=voices,
                   fir=(127, 0, 0, 0, 0, 0, 0, 0))

    @classmethod
    def slapback(cls, voices: int = 0xFF) -> EchoConfig:
        return cls(enabled=True, delay=2, feedback=40,
                   volume_left=60, volume_right=60, voices=voices,
                   fir=(127, 0, 0, 0, 0, 0, 0, 0))

    @classmethod
    def lowpass_echo(cls, delay: int = 4, feedback: int = 90,
                     volume: int = 50, voices: int = 0xFF) -> EchoConfig:
        return cls(enabled=True, delay=delay, feedback=feedback,
                   volume_left=volume, volume_right=volume, voices=voices,
                   fir=(64, 64, 32, 16, 8, 4, 2, 1))


# ===========================================================================
# Track
# ===========================================================================

class Track:
    """A sequence of musical events assigned to a DSP voice."""

    def __init__(self, instrument: Instrument,
                 voice: int | None = None) -> None:
        self.instrument = instrument
        self.voice = voice
        self.events: list[Event] = []

    # Fluent API
    def note(self, pitch: Pitch = None, duration: float = 1.0,
             velocity: float = 1.0, pan: float | None = None) -> Track:
        self.events.append(Note(pitch, duration, velocity, pan))
        return self

    def rest(self, duration: float = 1.0) -> Track:
        self.events.append(Rest(duration))
        return self

    def bend(self, target: Pitch, duration: float = 0.25,
             curve: str = 'linear') -> Track:
        self.events.append(PitchBend(target, duration, curve))
        return self

    def slide(self, target_velocity: float, duration: float = 0.25,
              target_pan: float | None = None) -> Track:
        self.events.append(VolumeSlide(target_velocity, duration, target_pan))
        return self

    def vibrato(self, depth: float = 0.5, rate: float = 6.0,
                duration: float = 1.0, delay: float = 0.0) -> Track:
        self.events.append(Vibrato(depth, rate, duration, delay))
        return self

    def tremolo(self, depth: float = 0.3, rate: float = 6.0,
                duration: float = 1.0, delay: float = 0.0) -> Track:
        self.events.append(Tremolo(depth, rate, duration, delay))
        return self

    def set_envelope(self, envelope: Envelope) -> Track:
        self.events.append(SetEnvelope(envelope))
        return self

    def set_instrument(self, instrument: Instrument) -> Track:
        self.events.append(SetInstrument(instrument))
        return self

    def raw(self, register: int, value: int) -> Track:
        self.events.append(RawRegWrite(register, value))
        return self

    def repeat(self, times: int) -> Track:
        """Repeat all events so far N additional times."""
        original = list(self.events)
        for _ in range(times):
            self.events.extend(original)
        return self

    def pattern(self, events: list[Event], times: int = 1) -> Track:
        """Append a pattern of events one or more times."""
        for _ in range(times):
            self.events.extend(events)
        return self


# ===========================================================================
# Song
# ===========================================================================

class Song:
    """Top-level composition container."""

    def __init__(self, bpm: float = 120.0) -> None:
        self.bpm = bpm
        self.tracks: list[Track] = []
        self.echo = EchoConfig()
        self.master_volume: tuple[int, int] = (127, 127)
        self.noise_clock: int = 0   # FLG bits 0-4
        self.pmon: int = 0x00       # pitch modulation bitmask

    @property
    def samples_per_beat(self) -> float:
        return (60.0 / self.bpm) * SAMPLE_RATE

    def beats_to_samples(self, beats: float) -> int:
        return int(round(beats * self.samples_per_beat))

    def add_track(self, instrument: Instrument,
                  voice: int | None = None) -> Track:
        """Add a track. Returns the Track for fluent event building."""
        if len(self.tracks) >= MAX_VOICES:
            raise ValueError(f"Maximum {MAX_VOICES} tracks")
        track = Track(instrument, voice)
        self.tracks.append(track)
        return track

    def compile(self) -> _CompiledSong:
        """Compile into RAM image + register write timeline."""
        return _SongCompiler(self).compile()

    def render(self, output_path: str | Path,
               duration: float | None = None,
               tail: float = 2.0,
               progress: bool = True) -> None:
        """Compile and render to WAV."""
        compiled = self.compile()
        compiled.render(output_path, duration=duration, tail=tail,
                        progress=progress)


# ===========================================================================
# Register write event
# ===========================================================================

@dataclass
class _RegWrite:
    """A DSP register write at a specific sample position."""
    pos: int       # absolute sample position
    reg: int       # DSP register (0x00-0x7F)
    val: int       # value (0x00-0xFF)


# ===========================================================================
# Compiled Song
# ===========================================================================

class _CompiledSong:
    """Compiled song: RAM image + sorted timeline of register writes."""

    def __init__(self, ram: bytearray, timeline: list[_RegWrite],
                 duration_samples: int) -> None:
        self.ram = ram
        self.timeline = timeline
        self.duration_samples = duration_samples

    def render(self, output_path: str | Path,
               duration: float | None = None,
               tail: float = 2.0,
               progress: bool = True) -> None:
        """Render to WAV via the DSP emulator."""
        dsp = DSP(bytearray(self.ram))  # copy RAM so DSP can write echo

        total_samples = self.duration_samples + int(tail * SAMPLE_RATE)
        if duration is not None:
            total_samples = int(duration * SAMPLE_RATE)

        # Sort by position, then by register (KON last so voice regs are set first)
        timeline = sorted(self.timeline,
                          key=lambda w: (w.pos, 0 if w.reg != 0x4C else 1))
        # Merge KON and KOFF writes at the same position
        timeline = _merge_kon_koff(timeline)

        ti = 0
        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)

            buf = bytearray()
            for si in range(total_samples):
                while ti < len(timeline) and timeline[ti].pos <= si:
                    dsp.dsp_write(timeline[ti].reg, timeline[ti].val)
                    ti += 1
                left, right = dsp.generate_sample()
                buf += struct.pack("<hh", left, right)

                if len(buf) >= SAMPLE_RATE * 4:
                    wf.writeframes(buf)
                    buf = bytearray()
                    if progress:
                        el = (si + 1) / SAMPLE_RATE
                        tot = total_samples / SAMPLE_RATE
                        pct = (si + 1) / total_samples * 100
                        print(f"\r  Rendering: {el:.1f}s / {tot:.1f}s "
                              f"({pct:.0f}%)", end="", flush=True)
            if buf:
                wf.writeframes(buf)

        if progress:
            tot = total_samples / SAMPLE_RATE
            print(f"\r  Rendering: {tot:.1f}s / {tot:.1f}s (100%)")
            print(f"Wrote {output_path}")

    def render_to_buffer(self, duration: float | None = None,
                         tail: float = 2.0,
                         progress: bool = False) -> tuple[bytes, int]:
        """Render to raw stereo 16-bit PCM buffer (in memory).

        Same DSP pipeline as render(), but returns bytes instead of writing
        to a WAV file. Useful for integration with other audio frameworks.

        Args:
            duration: Total render duration in seconds. If None, uses the
                      song duration plus tail.
            tail:     Extra seconds after the last note for echo decay.
            progress: Print progress to stdout.

        Returns:
            (pcm_bytes, total_samples) where pcm_bytes is packed little-endian
            signed 16-bit stereo (4 bytes per sample frame: LLRR).
        """
        dsp = DSP(bytearray(self.ram))

        total_samples = self.duration_samples + int(tail * SAMPLE_RATE)
        if duration is not None:
            total_samples = int(duration * SAMPLE_RATE)

        timeline = sorted(self.timeline,
                          key=lambda w: (w.pos, 0 if w.reg != 0x4C else 1))
        timeline = _merge_kon_koff(timeline)

        ti = 0
        buf = bytearray()
        for si in range(total_samples):
            while ti < len(timeline) and timeline[ti].pos <= si:
                dsp.dsp_write(timeline[ti].reg, timeline[ti].val)
                ti += 1
            left, right = dsp.generate_sample()
            buf += struct.pack("<hh", left, right)

            if progress and (si + 1) % SAMPLE_RATE == 0:
                el = (si + 1) / SAMPLE_RATE
                tot = total_samples / SAMPLE_RATE
                pct = (si + 1) / total_samples * 100
                print(f"\r  Rendering: {el:.1f}s / {tot:.1f}s "
                      f"({pct:.0f}%)", end="", flush=True)

        if progress:
            tot = total_samples / SAMPLE_RATE
            print(f"\r  Rendering: {tot:.1f}s / {tot:.1f}s (100%)")

        return bytes(buf), total_samples


def _merge_kon_koff(timeline: list[_RegWrite]) -> list[_RegWrite]:
    """Merge KON (0x4C) and KOFF (0x5C) writes at the same sample position.

    The DSP processes all bits in a single KON/KOFF write at once.
    Multiple voice key-ons at the same time must be OR'd together.
    """
    result: list[_RegWrite] = []
    i = 0
    while i < len(timeline):
        w = timeline[i]
        if w.reg in (0x4C, 0x5C):
            # Collect all KON or KOFF at this position
            combined = w.val
            j = i + 1
            while (j < len(timeline) and timeline[j].pos == w.pos
                   and timeline[j].reg == w.reg):
                combined |= timeline[j].val
                j += 1
            result.append(_RegWrite(w.pos, w.reg, combined & 0xFF))
            i = j
        else:
            result.append(w)
            i += 1
    return result


# ===========================================================================
# Panning helper
# ===========================================================================

def _pan_to_volumes(base_l: int, base_r: int, pan: float | None,
                    velocity: float) -> tuple[int, int]:
    """Compute stereo volumes from pan and velocity.

    Equal-power panning: constant perceived loudness across the field.
    pan: -1.0 = full left, 0.0 = center, 1.0 = full right
    """
    if pan is None:
        pan = 0.0
    pan = max(-1.0, min(1.0, pan))
    angle = (pan + 1.0) / 2.0 * (math.pi / 2.0)
    l_scale = math.cos(angle) * velocity
    r_scale = math.sin(angle) * velocity
    vol_l = max(-128, min(127, int(round(base_l * l_scale))))
    vol_r = max(-128, min(127, int(round(base_r * r_scale))))
    return vol_l, vol_r


# ===========================================================================
# Song Compiler
# ===========================================================================

class _SongCompiler:
    """Compiles a Song into a _CompiledSong."""

    def __init__(self, song: Song) -> None:
        self.song = song
        self.ram = bytearray(RAM_SIZE)
        self.timeline: list[_RegWrite] = []
        self._samples: list[Sample] = []
        self._sample_to_srcn: dict[int, int] = {}  # id(sample) -> SRCN
        self._sample_addrs: dict[int, tuple[int, int]] = {}  # SRCN -> (start, loop)
        self._dir_page = 0x02  # Directory at $0200

    def compile(self) -> _CompiledSong:
        self._assign_voices()
        self._collect_samples()
        self._plan_and_write_ram()
        self._emit_global_init()
        self._compile_tracks()
        duration = max((w.pos for w in self.timeline), default=0)
        return _CompiledSong(self.ram, self.timeline, duration)

    def _assign_voices(self) -> None:
        used: set[int] = set()
        # Explicit assignments first
        for track in self.song.tracks:
            if track.voice is not None:
                if track.voice in used:
                    raise ValueError(f"Voice {track.voice} assigned to multiple tracks")
                if not 0 <= track.voice < MAX_VOICES:
                    raise ValueError(f"Voice must be 0-7, got {track.voice}")
                used.add(track.voice)
        # Auto-assign the rest
        auto_idx = 0
        for track in self.song.tracks:
            if track.voice is None:
                while auto_idx in used:
                    auto_idx += 1
                track.voice = auto_idx
                used.add(auto_idx)
                auto_idx += 1

    def _collect_samples(self) -> None:
        seen: dict[int, int] = {}  # id(Sample) -> SRCN
        samples: list[Sample] = []

        for track in self.song.tracks:
            # Collect from initial instrument and any SetInstrument events
            instruments = [track.instrument]
            for evt in track.events:
                if isinstance(evt, SetInstrument):
                    instruments.append(evt.instrument)
            for inst in instruments:
                sid = id(inst.sample)
                if sid not in seen:
                    srcn = len(samples)
                    seen[sid] = srcn
                    samples.append(inst.sample)

        self._samples = samples
        self._sample_to_srcn = seen

    def _plan_and_write_ram(self) -> None:
        dir_base = self._dir_page * 0x100
        num_samples = len(self._samples)
        dir_size = num_samples * 4
        brr_start = dir_base + dir_size

        # Calculate echo buffer placement (at top of RAM)
        echo_size = self.song.echo.buffer_bytes if self.song.echo.enabled else 0
        if echo_size > 0:
            echo_base = (RAM_SIZE - echo_size) & 0xFF00  # align to page
        else:
            echo_base = RAM_SIZE  # no echo = full RAM available

        # Pack BRR data
        cursor = brr_start
        for srcn, sample in enumerate(self._samples):
            start_addr = cursor
            loop_addr = start_addr  # default: loop to start
            if sample.loop_offset is not None:
                loop_addr = start_addr + sample.loop_offset

            # Check fit
            end_addr = cursor + len(sample.brr_data)
            if end_addr > echo_base:
                self._memory_error(srcn, cursor, echo_base, echo_size)

            # Write BRR data
            self.ram[cursor:cursor + len(sample.brr_data)] = sample.brr_data
            cursor += len(sample.brr_data)

            # Write directory entry
            entry_addr = dir_base + srcn * 4
            self.ram[entry_addr] = start_addr & 0xFF
            self.ram[entry_addr + 1] = (start_addr >> 8) & 0xFF
            self.ram[entry_addr + 2] = loop_addr & 0xFF
            self.ram[entry_addr + 3] = (loop_addr >> 8) & 0xFF

            self._sample_addrs[srcn] = (start_addr, loop_addr)

        # Store echo base for init
        self._echo_page = echo_base >> 8 if echo_size else 0

        used = cursor - 0x200
        avail = echo_base - 0x200
        print(f"RAM: {num_samples} samples, {used} bytes used / "
              f"{avail} available ({echo_size} echo)")

    def _memory_error(self, srcn: int, cursor: int, echo_base: int,
                      echo_size: int) -> None:
        lines = ["Sample data exceeds available RAM!\n",
                 "Sample sizes:"]
        for i, s in enumerate(self._samples):
            marker = " <-- overflow" if i == srcn else ""
            lines.append(f"  [{i}] {s.name}: {s.memory_bytes} bytes{marker}")
        total = sum(s.memory_bytes for s in self._samples)
        avail = echo_base - (self._dir_page * 0x100 + len(self._samples) * 4)
        lines.append(f"\nTotal BRR: {total} bytes")
        lines.append(f"Echo buffer: {echo_size} bytes")
        lines.append(f"Available: {avail} bytes")
        lines.append("\nTip: reduce target_rate to save memory (e.g. 16000)")
        raise MemoryError("\n".join(lines))

    def _emit(self, pos: int, reg: int, val: int) -> None:
        self.timeline.append(_RegWrite(pos, reg & 0x7F, val & 0xFF))

    def _emit_global_init(self) -> None:
        """Emit register writes at sample 0 for global setup."""
        # DIR
        self._emit(0, 0x5D, self._dir_page)
        # Master volume
        ml, mr = self.song.master_volume
        self._emit(0, 0x0C, ml & 0xFF)
        self._emit(0, 0x1C, mr & 0xFF)
        # FLG: echo write disable if no echo, noise clock
        flg = self.song.noise_clock & 0x1F
        if not self.song.echo.enabled:
            flg |= 0x20  # echo write disable
        self._emit(0, 0x6C, flg)
        # PMON
        self._emit(0, 0x2D, self.song.pmon & 0xFF)
        # NON (no noise voices by default)
        self._emit(0, 0x3D, 0x00)
        # Echo
        if self.song.echo.enabled:
            echo = self.song.echo
            self._emit(0, 0x6D, self._echo_page)
            self._emit(0, 0x7D, echo.delay & 0x0F)
            self._emit(0, 0x0D, echo.feedback & 0xFF)
            self._emit(0, 0x2C, echo.volume_left & 0xFF)
            self._emit(0, 0x3C, echo.volume_right & 0xFF)
            self._emit(0, 0x4D, echo.voices & 0xFF)
            # FIR coefficients
            fir = echo.fir
            for t in range(8):
                coef = fir[t] if t < len(fir) else 0
                self._emit(0, t * 0x10 + 0x0F, coef & 0xFF)

    def _compile_tracks(self) -> None:
        for track in self.song.tracks:
            self._compile_track(track)

    def _compile_track(self, track: Track) -> None:
        voice = track.voice
        v = voice << 4
        pos = 0  # current sample position
        cur_inst = track.instrument
        cur_env = cur_inst.envelope
        cur_freq: float | None = None   # current pitch in Hz
        cur_pitch: int = 0              # current 14-bit pitch register value
        cur_vel: float = 1.0
        cur_pan: float | None = None

        to_samples = self.song.beats_to_samples

        for evt in track.events:
            if isinstance(evt, Note):
                # Resolve pitch
                if evt.pitch is None:
                    freq = cur_inst.sample.native_freq
                else:
                    freq = resolve_pitch(evt.pitch)
                cur_freq = freq
                cur_pitch = freq_to_pitch(freq, cur_inst.sample.native_freq)
                cur_vel = evt.velocity
                if evt.pan is not None:
                    cur_pan = evt.pan

                srcn = self._sample_to_srcn[id(cur_inst.sample)]
                vol_l, vol_r = _pan_to_volumes(
                    *cur_inst.default_volume, cur_pan, cur_vel)

                # Set voice registers
                self._emit(pos, v | 0x04, srcn)  # SRCN
                if isinstance(cur_env, ADSR):
                    self._emit(pos, v | 0x05, cur_env.to_adsr1())
                    self._emit(pos, v | 0x06, cur_env.to_adsr2())
                else:
                    self._emit(pos, v | 0x05, 0x00)  # ADSR disabled
                    self._emit(pos, v | 0x07, cur_env.to_gain_reg())
                self._emit(pos, v | 0x02, cur_pitch & 0xFF)
                self._emit(pos, v | 0x03, (cur_pitch >> 8) & 0x3F)
                self._emit(pos, v | 0x00, vol_l & 0xFF)
                self._emit(pos, v | 0x01, vol_r & 0xFF)
                # KON
                self._emit(pos, 0x4C, 1 << voice)

                # Schedule KOFF at end of note
                dur_samples = to_samples(evt.duration)
                koff_pos = pos + dur_samples
                self._emit(koff_pos, 0x5C, 1 << voice)

                pos += dur_samples

            elif isinstance(evt, Rest):
                pos += to_samples(evt.duration)

            elif isinstance(evt, PitchBend):
                if cur_freq is None:
                    continue
                target_freq = resolve_pitch(evt.target)
                dur_samples = to_samples(evt.duration)
                start_pitch = cur_pitch
                end_pitch = freq_to_pitch(target_freq,
                                          cur_inst.sample.native_freq)

                # Generate automation points
                steps = max(1, dur_samples // AUTOMATION_STEP)
                for s in range(steps + 1):
                    t = s / steps
                    if evt.curve == 'exponential' and cur_freq > 0:
                        # Exponential: pitch ∝ 2^(t * semitones)
                        ratio = target_freq / cur_freq
                        interp_freq = cur_freq * (ratio ** t)
                        p = freq_to_pitch(interp_freq,
                                          cur_inst.sample.native_freq)
                    else:
                        p = int(round(start_pitch + (end_pitch - start_pitch) * t))
                        p = max(0, min(0x3FFF, p))
                    sample_pos = pos + int(s * dur_samples / steps) - dur_samples
                    if sample_pos < 0:
                        sample_pos = pos - dur_samples
                    # Pitch bend doesn't advance pos — it overlays on the
                    # previous note's duration. Writes go backward from pos.
                    actual_pos = max(0, pos - dur_samples + int(s * dur_samples / steps))
                    self._emit(actual_pos, v | 0x02, p & 0xFF)
                    self._emit(actual_pos, v | 0x03, (p >> 8) & 0x3F)

                cur_freq = target_freq
                cur_pitch = end_pitch
                # PitchBend does NOT advance pos

            elif isinstance(evt, VolumeSlide):
                dur_samples = to_samples(evt.duration)
                start_vel = cur_vel
                end_vel = evt.target_velocity
                start_pan = cur_pan
                end_pan = evt.target_pan if evt.target_pan is not None else cur_pan

                steps = max(1, dur_samples // AUTOMATION_STEP)
                for s in range(steps + 1):
                    t = s / steps
                    vel = start_vel + (end_vel - start_vel) * t
                    pan = start_pan
                    if start_pan is not None and end_pan is not None:
                        pan = start_pan + (end_pan - start_pan) * t
                    vl, vr = _pan_to_volumes(
                        *cur_inst.default_volume, pan, vel)
                    actual_pos = max(0, pos - dur_samples + int(s * dur_samples / steps))
                    self._emit(actual_pos, v | 0x00, vl & 0xFF)
                    self._emit(actual_pos, v | 0x01, vr & 0xFF)

                cur_vel = end_vel
                if evt.target_pan is not None:
                    cur_pan = evt.target_pan

            elif isinstance(evt, Vibrato):
                if cur_freq is None:
                    continue
                delay_samples = to_samples(evt.delay)
                dur_samples = to_samples(evt.duration)
                base_pitch = cur_pitch

                start_pos = pos - to_samples(evt.duration + evt.delay)
                start_pos = max(0, start_pos)

                steps = max(1, dur_samples // AUTOMATION_STEP)
                for s in range(steps + 1):
                    t_sec = s * (dur_samples / steps) / SAMPLE_RATE
                    offset_semi = evt.depth * math.sin(
                        2.0 * math.pi * evt.rate * t_sec)
                    freq = cur_freq * (2.0 ** (offset_semi / 12.0))
                    p = freq_to_pitch(freq, cur_inst.sample.native_freq)
                    actual_pos = start_pos + delay_samples + int(s * dur_samples / steps)
                    self._emit(actual_pos, v | 0x02, p & 0xFF)
                    self._emit(actual_pos, v | 0x03, (p >> 8) & 0x3F)

                # Restore base pitch at the end
                self._emit(start_pos + delay_samples + dur_samples,
                           v | 0x02, base_pitch & 0xFF)
                self._emit(start_pos + delay_samples + dur_samples,
                           v | 0x03, (base_pitch >> 8) & 0x3F)

            elif isinstance(evt, Tremolo):
                dur_samples = to_samples(evt.duration)
                delay_samples = to_samples(evt.delay)

                start_pos = pos - to_samples(evt.duration + evt.delay)
                start_pos = max(0, start_pos)

                base_vel = cur_vel
                steps = max(1, dur_samples // AUTOMATION_STEP)
                for s in range(steps + 1):
                    t_sec = s * (dur_samples / steps) / SAMPLE_RATE
                    mod = 1.0 - evt.depth * abs(
                        math.sin(2.0 * math.pi * evt.rate * t_sec))
                    vel = base_vel * mod
                    vl, vr = _pan_to_volumes(
                        *cur_inst.default_volume, cur_pan, vel)
                    actual_pos = start_pos + delay_samples + int(s * dur_samples / steps)
                    self._emit(actual_pos, v | 0x00, vl & 0xFF)
                    self._emit(actual_pos, v | 0x01, vr & 0xFF)

            elif isinstance(evt, SetEnvelope):
                cur_env = evt.envelope

            elif isinstance(evt, SetInstrument):
                cur_inst = evt.instrument
                cur_env = evt.instrument.envelope

            elif isinstance(evt, RawRegWrite):
                self._emit(pos, evt.register, evt.value)
