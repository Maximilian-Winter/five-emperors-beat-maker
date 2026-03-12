"""
SPC700 DSP Integration Bridge

Connects beatmaker's audio pipeline with the SPC700 DSP emulator,
enabling SNES-authentic sound processing as a second stage in the
synthesis pipeline.

The SPC700 S-DSP imparts distinctive character upon any audio that
passes through it: BRR compression artefacts, Gaussian interpolation
warmth, hardware ADSR envelopes, and the legendary 8-tap FIR echo.

Three integration surfaces are provided:

    SPC700Sound  — Convert beatmaker Samples to SPC700 Instruments
    SPC700Engine — Manage sounds, compose, and render through the DSP
    SPC700Echo   — The SPC700 echo/FIR unit as a standalone AudioEffect

Usage:
    from beatmaker.spc import SPC700Engine, SPC700Sound, SPC700Echo
    from beatmaker.spc700 import EchoConfig, ADSR

    # Set up the engine
    engine = SPC700Engine(echo=EchoConfig.reverb())
    engine.sound("kick", SPC700Sound.drum("samples/kick.wav"))
    engine.sound("lead", SPC700Sound.synth("AKWF_saw.wav", preset='lead'))

    # Compose and render
    spc_song = engine.create_song(bpm=120)
    t = spc_song.add_track(engine.get("kick"))
    t.note(duration=0.25).rest(0.75).repeat(7)
    audio = engine.render(spc_song)
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional, Union, Callable

import numpy as np

from .core import AudioData, AudioEffect, Sample as BeatmakerSample

from .spc700 import (
    # Composition types
    Song as SPCSong,
    Track as SPCTrack,
    Sample as SPCSample,
    Instrument as SPCInstrument,
    ADSR,
    Gain,
    EchoConfig,
    # BRR encoding
    encode_brr,
    load_and_encode,
    load_wav,
    resample as brr_resample,
    DSP_SAMPLE_RATE,
    # DSP
    DSP,
    # Pitch utilities
    midi_to_freq,
    note_to_midi,
    resolve_pitch,
    # Constants
    SAMPLE_RATE as SPC_SAMPLE_RATE,
    RAM_SIZE,
)


# ═══════════════════════════════════════════════════════════════════════
#  Conversion Helpers
# ═══════════════════════════════════════════════════════════════════════

def _audio_to_pcm_int16(audio: AudioData) -> list[int]:
    """Convert beatmaker AudioData to mono int16 PCM list.

    The SPC700 BRR encoder expects a list of Python ints in [-32768, 32767].
    """
    # Ensure mono
    if audio.channels > 1:
        audio = audio.to_mono()

    samples = audio.samples
    # Convert float [-1, 1] to int16
    clipped = np.clip(samples, -1.0, 1.0)
    int16 = (clipped * 32767.0).astype(np.int16)
    return int16.tolist()


def _pitch_to_freq(pitch) -> float:
    """Resolve a pitch specification to Hz.

    Accepts:
        str  — note name ('C4', 'A#3')
        int  — MIDI note number
        float — frequency in Hz
    """
    if isinstance(pitch, str):
        return midi_to_freq(note_to_midi(pitch))
    if isinstance(pitch, int):
        return midi_to_freq(pitch)
    if isinstance(pitch, float):
        return pitch
    raise ValueError(f"Cannot resolve pitch: {pitch!r}")


def _resolve_source(source, pitch=None, loop_start=None,
                    target_rate=SPC_SAMPLE_RATE,
                    trim_silence=True) -> tuple[SPCSample, float]:
    """Resolve a sample source to an SPC700 Sample + native frequency.

    Sources can be:
        - beatmaker Sample (AudioData-backed)
        - str or Path (WAV file path)
        - SPCSample (already converted — passthrough)

    Returns:
        (spc_sample, native_freq)
    """
    if isinstance(source, SPCSample):
        return source, source.native_freq

    if isinstance(source, (str, Path)):
        path = Path(source)
        # Check if this is a single-cycle waveform (very short)
        pcm_raw, src_rate = load_wav(str(path))
        duration_ms = len(pcm_raw) / src_rate * 1000
        if duration_ms < 10:
            # Single-cycle waveform: native_freq = fundamental
            spc_sample = SPCSample.from_single_cycle(
                path, target_rate=target_rate)
            return spc_sample, spc_sample.native_freq
        else:
            spc_sample = SPCSample.from_wav(
                path, target_rate=target_rate,
                loop_start=loop_start, trim_silence=trim_silence)
            native_freq = _pitch_to_freq(pitch) if pitch else float(target_rate)
            return spc_sample, native_freq

    if isinstance(source, BeatmakerSample):
        audio = source.audio
        pcm = _audio_to_pcm_int16(audio)

        # Resample to SPC700 rate if needed
        if audio.sample_rate != target_rate:
            pcm = brr_resample(pcm, audio.sample_rate, target_rate)

        # Encode to BRR
        brr_data, loop_offset = encode_brr(pcm, loop_start)

        # Determine native frequency
        if pitch is not None:
            native_freq = _pitch_to_freq(pitch)
        elif source.root_note is not None:
            native_freq = midi_to_freq(source.root_note)
        else:
            native_freq = float(target_rate)

        spc_sample = SPCSample(
            name=source.name,
            brr_data=brr_data,
            native_freq=native_freq,
            loop_offset=loop_offset,
        )
        return spc_sample, native_freq

    raise TypeError(
        f"Unsupported source type: {type(source).__name__}. "
        f"Expected beatmaker Sample, file path, or SPC700 Sample."
    )


# ═══════════════════════════════════════════════════════════════════════
#  SPC700Sound — Sample Bridge
# ═══════════════════════════════════════════════════════════════════════

class SPC700Sound:
    """Bridge between beatmaker audio sources and SPC700 Instruments.

    Converts beatmaker Samples, WAV files, or single-cycle waveforms
    into SPC700 Instruments with BRR encoding and ADSR/GAIN envelopes.

    Every factory method accepts any of these source types:
        - beatmaker Sample (with AudioData)
        - str or Path pointing to a WAV file
        - SPC700 Sample (already BRR-encoded, passthrough)

    Examples:
        # From a beatmaker synth
        kick_sample = DrumSynth.kick(freq=55, duration=0.3)
        kick = SPC700Sound.drum(kick_sample)

        # From a WAV file
        snare = SPC700Sound.drum("samples/snare.wav")

        # From a single-cycle waveform (AKWF)
        lead = SPC700Sound.synth("AKWF-FREE/AKWF_saw/AKWF_saw_0001.wav",
                                 preset='lead')

        # From a SampleLibrary
        pad = SPC700Sound.pad(library["pads/warm"], loop_start=0)
    """

    @classmethod
    def from_sample(cls, source, pitch='C4',
                    envelope: ADSR | Gain | None = None,
                    loop: bool = False,
                    volume: tuple[int, int] = (127, 127),
                    name: str | None = None) -> SPCInstrument:
        """Convert any audio source to an SPC700 Instrument.

        Args:
            source:   beatmaker Sample, WAV path, or SPC700 Sample.
            pitch:    The pitch this sample represents ('C4', 60, 261.63).
                      Used to set native_freq for correct playback tuning.
            envelope: ADSR or Gain envelope. Default: full organ sustain.
            loop:     If True and source is not pre-looped, loop from start.
            volume:   Default stereo volume (left, right), each 0-127.
            name:     Display name (default: derived from source).
        """
        loop_start = 0 if loop else None
        spc_sample, native_freq = _resolve_source(
            source, pitch=pitch, loop_start=loop_start)

        if name is None:
            name = spc_sample.name

        if envelope is None:
            envelope = ADSR(attack=15, decay=7, sustain_level=7, sustain_rate=0)

        # Override native_freq if pitch was explicitly given
        if pitch is not None:
            spc_sample = SPCSample(
                name=spc_sample.name,
                brr_data=spc_sample.brr_data,
                native_freq=_pitch_to_freq(pitch),
                loop_offset=spc_sample.loop_offset,
            )

        return SPCInstrument(
            name=name, sample=spc_sample,
            envelope=envelope, default_volume=volume,
        )

    @classmethod
    def drum(cls, source, name: str | None = None,
             volume: tuple[int, int] = (127, 127)) -> SPCInstrument:
        """Drum preset: fast attack, punchy decay, no sustain, no loop.

        Ideal for kicks, snares, hats, and percussion.
        """
        spc_sample, _ = _resolve_source(source, trim_silence=True)
        if name is None:
            name = spc_sample.name
        return SPCInstrument(
            name=name, sample=spc_sample,
            envelope=ADSR(attack=15, decay=5, sustain_level=0, sustain_rate=31),
            default_volume=volume,
        )

    @classmethod
    def pad(cls, source, pitch='C4',
            loop_start: int = 0,
            name: str | None = None,
            volume: tuple[int, int] = (100, 100)) -> SPCInstrument:
        """Pad preset: slow attack, full sustain, looped.

        Ideal for sustained chords and atmospheric textures.
        """
        spc_sample, _ = _resolve_source(
            source, pitch=pitch, loop_start=loop_start)
        if name is None:
            name = spc_sample.name

        if pitch is not None:
            spc_sample = SPCSample(
                name=spc_sample.name,
                brr_data=spc_sample.brr_data,
                native_freq=_pitch_to_freq(pitch),
                loop_offset=spc_sample.loop_offset,
            )

        return SPCInstrument(
            name=name, sample=spc_sample,
            envelope=ADSR(attack=10, decay=7, sustain_level=6, sustain_rate=0),
            default_volume=volume,
        )

    @classmethod
    def bass(cls, source, pitch='C2',
             name: str | None = None,
             volume: tuple[int, int] = (120, 120)) -> SPCInstrument:
        """Bass preset: fast attack, medium sustain.

        Ideal for bass lines and low-frequency melodic content.
        """
        spc_sample, _ = _resolve_source(source, pitch=pitch)
        if name is None:
            name = spc_sample.name

        if pitch is not None:
            spc_sample = SPCSample(
                name=spc_sample.name,
                brr_data=spc_sample.brr_data,
                native_freq=_pitch_to_freq(pitch),
                loop_offset=spc_sample.loop_offset,
            )

        return SPCInstrument(
            name=name, sample=spc_sample,
            envelope=ADSR(attack=15, decay=5, sustain_level=3, sustain_rate=8),
            default_volume=volume,
        )

    @classmethod
    def lead(cls, source, pitch='C4',
             name: str | None = None,
             volume: tuple[int, int] = (100, 100)) -> SPCInstrument:
        """Lead preset: medium attack, sustained.

        Ideal for melodic leads and solo voices.
        """
        spc_sample, _ = _resolve_source(source, pitch=pitch, loop_start=0)
        if name is None:
            name = spc_sample.name

        if pitch is not None:
            spc_sample = SPCSample(
                name=spc_sample.name,
                brr_data=spc_sample.brr_data,
                native_freq=_pitch_to_freq(pitch),
                loop_offset=spc_sample.loop_offset,
            )

        return SPCInstrument(
            name=name, sample=spc_sample,
            envelope=ADSR(attack=13, decay=6, sustain_level=5, sustain_rate=5),
            default_volume=volume,
        )

    @classmethod
    def synth(cls, waveform_path: str | Path,
              preset: str = 'lead',
              name: str | None = None,
              volume: tuple[int, int] = (100, 100)) -> SPCInstrument:
        """Single-cycle waveform synthesizer.

        Wraps Instrument.synth() for AKWF and similar waveform collections.
        These tiny looping samples can be pitched to any note.

        Presets: 'pad', 'lead', 'pluck', 'bass', 'organ', 'string', 'bell'
        """
        return SPCInstrument.synth(
            waveform_path, preset=preset, name=name, volume=volume)


# ═══════════════════════════════════════════════════════════════════════
#  SPC700Engine — Rendering Engine
# ═══════════════════════════════════════════════════════════════════════

class SPC700Engine:
    """SPC700 DSP rendering engine for beatmaker integration.

    Manages named sounds, creates compositions, and renders through the
    SPC700 DSP to produce beatmaker-compatible AudioData.

    The engine provides:
        - Sound registration with named lookup
        - Song creation pre-configured with echo, master volume, etc.
        - In-memory rendering to AudioData (resampled to any target rate)
        - Direct WAV export at native 32kHz

    Example:
        from beatmaker.spc import SPC700Engine, SPC700Sound
        from beatmaker.spc700 import EchoConfig

        engine = SPC700Engine(echo=EchoConfig.reverb(delay=5, feedback=80))
        engine.sound("kick", SPC700Sound.drum("kick.wav"))
        engine.sound("lead", SPC700Sound.synth("AKWF_saw.wav", preset='lead'))

        song = engine.create_song(bpm=120)
        drums = song.add_track(engine.get("kick"))
        drums.note(duration=0.25).rest(0.75).repeat(7)
        melody = song.add_track(engine.get("lead"))
        melody.note("C4", 2.0).note("E4", 2.0)

        audio = engine.render(song)  # -> AudioData at 44100Hz
    """

    def __init__(self,
                 echo: EchoConfig | None = None,
                 master_volume: tuple[int, int] = (127, 127),
                 noise_clock: int = 0):
        """
        Args:
            echo:          Echo/reverb configuration. None = no echo.
            master_volume: Global stereo volume (left, right), each 0-127.
            noise_clock:   Noise generator rate (FLG bits 0-4), 0-31.
        """
        self._sounds: dict[str, SPCInstrument] = {}
        self._echo = echo or EchoConfig()
        self._master_volume = master_volume
        self._noise_clock = noise_clock

    def sound(self, name: str, instrument: SPCInstrument) -> 'SPC700Engine':
        """Register a sound by name.

        Args:
            name:       Lookup key for this sound.
            instrument: SPC700 Instrument (use SPC700Sound to create one).

        Returns:
            self for chaining.
        """
        self._sounds[name] = instrument
        return self

    def get(self, name: str) -> SPCInstrument:
        """Retrieve a registered sound by name.

        Raises:
            KeyError: If the name is not registered.
        """
        if name not in self._sounds:
            available = ', '.join(sorted(self._sounds)) or '(none)'
            raise KeyError(
                f"Sound {name!r} not registered. Available: {available}")
        return self._sounds[name]

    def list_sounds(self) -> list[str]:
        """Return all registered sound names."""
        return sorted(self._sounds.keys())

    def create_song(self, bpm: float) -> SPCSong:
        """Create a new SPC700 Song pre-configured with engine settings.

        The song inherits the engine's echo, master volume, and noise clock.
        Use song.add_track(engine.get("name")) to add voices.

        Args:
            bpm: Tempo in beats per minute.

        Returns:
            A configured spc700.Song ready for track composition.
        """
        song = SPCSong(bpm=bpm)
        song.echo = EchoConfig(
            enabled=self._echo.enabled,
            delay=self._echo.delay,
            feedback=self._echo.feedback,
            volume_left=self._echo.volume_left,
            volume_right=self._echo.volume_right,
            voices=self._echo.voices,
            fir=self._echo.fir,
        )
        song.master_volume = self._master_volume
        song.noise_clock = self._noise_clock
        return song

    def render(self, song: SPCSong,
               sample_rate: int = 44100,
               tail: float = 2.0,
               progress: bool = False) -> AudioData:
        """Render an SPC700 Song to beatmaker AudioData.

        Pipeline:
            1. Compile song → RAM image + register write timeline
            2. Render through DSP → raw stereo 16-bit PCM at 32kHz
            3. Resample to target sample_rate
            4. Wrap in AudioData

        Args:
            song:        SPC700 Song to render.
            sample_rate: Output sample rate (default 44100Hz).
            tail:        Extra seconds after last note for echo decay.
            progress:    Print rendering progress to stdout.

        Returns:
            Stereo AudioData at the requested sample rate.
        """
        compiled = song.compile()
        pcm_bytes, total_samples = compiled.render_to_buffer(
            tail=tail, progress=progress)

        # Unpack stereo int16 PCM
        num_frames = total_samples
        raw = np.frombuffer(pcm_bytes, dtype=np.int16)
        stereo = raw.reshape(-1, 2)

        # Convert int16 → float [-1, 1]
        audio_float = stereo.astype(np.float64) / 32768.0

        audio = AudioData(audio_float, SPC_SAMPLE_RATE, 2)

        # Resample to target rate if needed
        if sample_rate != SPC_SAMPLE_RATE:
            audio = audio.resample(sample_rate)

        return audio

    def render_to_wav(self, song: SPCSong, path: str | Path,
                      duration: float | None = None,
                      tail: float = 2.0,
                      progress: bool = True) -> None:
        """Render directly to WAV at native 32kHz.

        Uses the SPC700's own WAV writer for maximum fidelity
        (no resampling step).

        Args:
            song:     SPC700 Song to render.
            path:     Output WAV file path.
            duration: Total duration (None = song length + tail).
            tail:     Extra seconds for echo decay.
            progress: Print progress to stdout.
        """
        song.render(str(path), duration=duration, tail=tail, progress=progress)


# ═══════════════════════════════════════════════════════════════════════
#  SPC700SongBuilder — Fluent Composition Wrapper
# ═══════════════════════════════════════════════════════════════════════

class SPC700SongBuilder:
    """Fluent builder for SPC700 compositions using named sounds.

    Provides a chainable API for composing through the SPC700 DSP,
    using sound names registered with an SPC700Engine.

    Example:
        sb = SPC700SongBuilder(engine, bpm=120)
        sb.track("kick", lambda t: t
            .note(duration=0.25).rest(0.75).repeat(7)
        ).track("lead", lambda t: t
            .note("C4", 2.0).note("E4", 1.0).vibrato(0.5, 6.0, 1.0)
            .note("G4", 1.0)
        )
        audio = sb.render()
    """

    def __init__(self, engine: SPC700Engine, bpm: float):
        self._engine = engine
        self._spc_song = engine.create_song(bpm)

    def track(self, sound_name: str,
              builder: Callable[[SPCTrack], SPCTrack | None],
              voice: int | None = None) -> 'SPC700SongBuilder':
        """Add a track using a registered sound name.

        Args:
            sound_name: Key registered with engine.sound().
            builder:    Callback receiving the SPC700 Track for composition.
                        Use the fluent API: t.note(...).rest(...).vibrato(...)
            voice:      Explicit DSP voice number (0-7). None = auto-assign.

        Returns:
            self for chaining.
        """
        instrument = self._engine.get(sound_name)
        spc_track = self._spc_song.add_track(instrument, voice)
        builder(spc_track)
        return self

    def echo(self, config: EchoConfig) -> 'SPC700SongBuilder':
        """Override the engine's echo configuration for this song."""
        self._spc_song.echo = config
        return self

    def master_volume(self, left: int = 127,
                      right: int = 127) -> 'SPC700SongBuilder':
        """Set master volume."""
        self._spc_song.master_volume = (left, right)
        return self

    def pmon(self, mask: int) -> 'SPC700SongBuilder':
        """Set pitch modulation bitmask (voice N modulated by voice N-1)."""
        self._spc_song.pmon = mask
        return self

    def noise(self, clock: int) -> 'SPC700SongBuilder':
        """Set noise generator clock rate (0-31)."""
        self._spc_song.noise_clock = clock
        return self

    def render(self, sample_rate: int = 44100,
               tail: float = 2.0,
               progress: bool = False) -> AudioData:
        """Render this composition to beatmaker AudioData."""
        return self._engine.render(
            self._spc_song, sample_rate=sample_rate,
            tail=tail, progress=progress)

    def render_to_wav(self, path: str | Path, **kwargs) -> None:
        """Render directly to WAV at native 32kHz."""
        self._engine.render_to_wav(self._spc_song, path, **kwargs)

    def build(self) -> SPCSong:
        """Return the underlying SPC700 Song for direct manipulation."""
        return self._spc_song


# ═══════════════════════════════════════════════════════════════════════
#  SPC700Echo — Standalone AudioEffect
# ═══════════════════════════════════════════════════════════════════════

class SPC700Echo(AudioEffect):
    """SPC700 hardware echo/reverb as a beatmaker AudioEffect.

    Processes audio through the SPC700 DSP's echo unit, imparting the
    distinctive SNES reverb character: the 8-tap FIR filter that gives
    the Super Nintendo its unmistakable spatial quality.

    The audio is BRR-encoded and played through the DSP with GAIN set
    to direct passthrough, so only the echo/FIR colouration is added.

    Usage:
        # As a track effect
        track.add_effect(SPC700Echo(delay=4, feedback=80))

        # As a master effect
        song_builder.master_effect(SPC700Echo.reverb())

        # Lowpass echo for a warmer, filtered character
        song_builder.master_effect(SPC700Echo.lowpass_echo())
    """

    def __init__(self, delay: int = 4, feedback: int = 60,
                 volume: int = 50,
                 fir: tuple[int, ...] = (127, 0, 0, 0, 0, 0, 0, 0)):
        """
        Args:
            delay:    Echo delay 0-15 (each unit = 16ms, i.e., 512 samples).
            feedback: Echo feedback -128 to 127 (higher = longer tail).
            volume:   Echo wet volume 0-127.
            fir:      8-tap FIR filter coefficients (signed 8-bit each).
        """
        self._delay = delay
        self._feedback = feedback
        self._volume = volume
        self._fir = tuple(fir)

    def process(self, audio: AudioData) -> AudioData:
        """Process audio through the SPC700 echo unit.

        Pipeline:
            1. Convert to mono, resample to 32kHz, encode to BRR
            2. Load BRR data + echo config into DSP RAM
            3. Play through voice 0 with direct GAIN (passthrough envelope)
            4. Capture stereo output (dry signal + FIR-filtered echo)
            5. Resample back to original sample rate
        """
        original_rate = audio.sample_rate
        original_channels = audio.channels

        # --- Stage 1: Prepare BRR sample ---
        pcm = _audio_to_pcm_int16(audio)
        if audio.sample_rate != SPC_SAMPLE_RATE:
            pcm = brr_resample(pcm, audio.sample_rate, SPC_SAMPLE_RATE)

        brr_data, _ = encode_brr(pcm)

        # --- Stage 2: Build RAM image ---
        ram = bytearray(RAM_SIZE)

        # Echo buffer at top of RAM
        echo_size = max(self._delay * 2048, 4)
        echo_base = (RAM_SIZE - echo_size) & 0xFF00

        # Directory at page 2
        dir_page = 0x02
        dir_base = dir_page * 0x100
        brr_start = dir_base + 4  # one directory entry

        # Check BRR fits before echo
        if brr_start + len(brr_data) > echo_base:
            # Truncate if audio is too large for RAM
            max_brr = echo_base - brr_start
            brr_data = brr_data[:max_brr - (max_brr % 9)]

        # Write BRR data
        ram[brr_start:brr_start + len(brr_data)] = brr_data

        # Mark last BRR block as end (no loop)
        if len(brr_data) >= 9:
            last_block = brr_start + len(brr_data) - 9
            ram[last_block] |= 0x01  # end flag

        # Directory entry: start address, loop address
        ram[dir_base + 0] = brr_start & 0xFF
        ram[dir_base + 1] = (brr_start >> 8) & 0xFF
        ram[dir_base + 2] = brr_start & 0xFF  # loop = start (unused)
        ram[dir_base + 3] = (brr_start >> 8) & 0xFF

        # --- Stage 3: Configure DSP ---
        dsp = DSP(ram)

        # Directory register
        dsp.dsp_write(0x5D, dir_page)

        # Master volume
        dsp.dsp_write(0x0C, 127)   # MVOL_L
        dsp.dsp_write(0x1C, 127)   # MVOL_R

        # Voice 0 configuration: direct gain passthrough
        dsp.dsp_write(0x04, 0)     # SRCN = 0
        dsp.dsp_write(0x05, 0)     # ADSR1 off (use GAIN)
        dsp.dsp_write(0x07, 127)   # GAIN = direct, max level
        dsp.dsp_write(0x00, 127)   # VOL_L
        dsp.dsp_write(0x01, 127)   # VOL_R

        # Pitch: play at native rate (1:1 ratio = 0x1000)
        dsp.dsp_write(0x02, 0x00)  # Pitch low
        dsp.dsp_write(0x03, 0x10)  # Pitch high (0x1000 >> 8)

        # Echo configuration
        dsp.dsp_write(0x6D, echo_base >> 8)  # ESA
        dsp.dsp_write(0x7D, self._delay)      # EDL
        dsp.dsp_write(0x0D, self._feedback & 0xFF)  # EFB
        dsp.dsp_write(0x2C, self._volume & 0xFF)     # EVOL_L
        dsp.dsp_write(0x3C, self._volume & 0xFF)     # EVOL_R
        dsp.dsp_write(0x4D, 0x01)  # EON: voice 0 feeds echo

        # FIR coefficients
        for i, coeff in enumerate(self._fir):
            dsp.dsp_write(i * 0x10 + 0x0F, coeff & 0xFF)

        # FLG: enable echo writes, set noise clock to 0
        dsp.dsp_write(0x6C, 0x00)

        # Key on voice 0
        dsp.dsp_write(0x4C, 0x01)

        # --- Stage 4: Generate audio ---
        # Calculate how many samples we need:
        # BRR samples / pitch_ratio + echo tail
        brr_samples = (len(brr_data) // 9) * 16
        echo_tail = self._delay * 512 * 3  # ~3x echo delay for tail
        total_dsp_samples = brr_samples + echo_tail

        buf = bytearray()
        for _ in range(total_dsp_samples):
            left, right = dsp.generate_sample()
            buf += struct.pack("<hh", left, right)

        # --- Stage 5: Convert back to AudioData ---
        raw = np.frombuffer(bytes(buf), dtype=np.int16)
        stereo = raw.reshape(-1, 2).astype(np.float64) / 32768.0

        result = AudioData(stereo, SPC_SAMPLE_RATE, 2)

        # Resample back to original rate
        if original_rate != SPC_SAMPLE_RATE:
            result = result.resample(original_rate)

        # Match original channel count
        if original_channels == 1:
            result = result.to_mono()

        return result

    @classmethod
    def reverb(cls, delay: int = 6, feedback: int = 80,
               volume: int = 50) -> 'SPC700Echo':
        """Classic SNES reverb.

        The signature spatial quality heard in games like Chrono Trigger
        and Final Fantasy VI.
        """
        return cls(delay=delay, feedback=feedback, volume=volume,
                   fir=(127, 0, 0, 0, 0, 0, 0, 0))

    @classmethod
    def slapback(cls) -> 'SPC700Echo':
        """Short slapback delay for rhythmic doubling."""
        return cls(delay=2, feedback=40, volume=60,
                   fir=(127, 0, 0, 0, 0, 0, 0, 0))

    @classmethod
    def lowpass_echo(cls, delay: int = 4, feedback: int = 90,
                     volume: int = 50) -> 'SPC700Echo':
        """Echo with lowpass FIR filtering.

        Each echo repetition is progressively darker, creating a warm,
        receding spatial effect — like sound disappearing into distance.
        """
        return cls(delay=delay, feedback=feedback, volume=volume,
                   fir=(64, 64, 32, 16, 8, 4, 2, 1))

    @classmethod
    def cathedral(cls) -> 'SPC700Echo':
        """Long, diffuse reverb with maximum delay."""
        return cls(delay=15, feedback=100, volume=60,
                   fir=(80, 40, 20, 10, 5, 3, 2, 1))

    def __repr__(self) -> str:
        return (f"SPC700Echo(delay={self._delay}, feedback={self._feedback}, "
                f"volume={self._volume})")


# ═══════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════

__all__ = [
    'SPC700Sound',
    'SPC700Engine',
    'SPC700SongBuilder',
    'SPC700Echo',
]
