"""
SPC700 — SNES S-DSP Emulator Subpackage

A faithful Python emulator of the Super Nintendo's SPC700 sound system:
BRR sample compression, 8-voice DSP with Gaussian interpolation,
hardware ADSR/GAIN envelopes, and 8-tap FIR echo/reverb.

Modules:
    spc700_brr   — BRR encoder/decoder and WAV loader
    spc700_cpu   — Full SPC700 CPU interpreter (256 opcodes)
    spc700_dsp   — S-DSP emulator (sample-accurate audio generation)
    spc700_emu   — SPC file loader and WAV renderer
    spc700_synth — High-level composition API (Song, Track, Instrument)
"""

# Composition API
from .spc700_synth import (
    Song, Track, Sample, Instrument, ADSR, Gain, EchoConfig,
    Note, Rest, PitchBend, VolumeSlide, Vibrato, Tremolo,
    SetEnvelope, SetInstrument, RawRegWrite,
    load_sample_folder, load_drum_kit, load_synth_bank,
    midi_to_freq, note_to_midi, freq_to_pitch, resolve_pitch,
    SAMPLE_RATE, MAX_VOICES, RAM_SIZE,
)

# BRR encoding
from .spc700_brr import (
    encode_brr, load_and_encode, load_wav, resample,
    DSP_SAMPLE_RATE, BRR_BLOCK_SAMPLES, BRR_BLOCK_BYTES,
)

# DSP engine
from .spc700_dsp import DSP

# SPC file playback
from .spc700_emu import load_spc, render_wav

# CPU (exposed for advanced use / SPC playback)
from .spc700_cpu import SPC700

__all__ = [
    # Composition
    'Song', 'Track', 'Sample', 'Instrument', 'ADSR', 'Gain', 'EchoConfig',
    'Note', 'Rest', 'PitchBend', 'VolumeSlide', 'Vibrato', 'Tremolo',
    'SetEnvelope', 'SetInstrument', 'RawRegWrite',
    'load_sample_folder', 'load_drum_kit', 'load_synth_bank',
    'midi_to_freq', 'note_to_midi', 'freq_to_pitch', 'resolve_pitch',
    'SAMPLE_RATE', 'MAX_VOICES', 'RAM_SIZE',
    # BRR
    'encode_brr', 'load_and_encode', 'load_wav', 'resample',
    'DSP_SAMPLE_RATE', 'BRR_BLOCK_SAMPLES', 'BRR_BLOCK_BYTES',
    # DSP
    'DSP',
    # SPC playback
    'load_spc', 'render_wav',
    # CPU
    'SPC700',
]
