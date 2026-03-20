"""
beatmaker-spc700 — SPC700 (SNES) sound chip integration for beatmaker.

A faithful Python emulator of the Super Nintendo's SPC700 sound system:
BRR sample compression, 8-voice DSP with Gaussian interpolation,
hardware ADSR/GAIN envelopes, and 8-tap FIR echo/reverb.

Provides bridge classes that connect beatmaker's audio pipeline with
the SPC700 DSP emulator for SNES-authentic sound processing.
"""

# Bridge classes (beatmaker integration)
from .bridge import (
    SPC700Sound,
    SPC700Engine,
    SPC700SongBuilder,
    SPC700Echo,
)

# SPC700 composition types (no SPC_ prefix needed in this package)
from .spc700_synth import (
    ADSR,
    Gain,
    EchoConfig,
    Instrument,
    Sample,
    Song,
    Track,
    Note,
    Rest,
    PitchBend,
    VolumeSlide,
    Vibrato,
    Tremolo,
    SetEnvelope,
    SetInstrument,
    RawRegWrite,
    load_sample_folder,
    load_drum_kit,
    load_synth_bank,
    midi_to_freq,
    note_to_midi,
    freq_to_pitch,
    resolve_pitch,
    SAMPLE_RATE,
    MAX_VOICES,
    RAM_SIZE,
)

# BRR encoding
from .spc700_brr import (
    encode_brr,
    load_and_encode,
    load_wav,
    resample,
    DSP_SAMPLE_RATE,
    BRR_BLOCK_SAMPLES,
    BRR_BLOCK_BYTES,
)

# DSP engine
from .spc700_dsp import DSP

# SPC file playback
from .spc700_emu import load_spc, render_wav

# CPU (exposed for advanced use / SPC playback)
from .spc700_cpu import SPC700

__all__ = [
    # Bridge
    'SPC700Sound', 'SPC700Engine', 'SPC700SongBuilder', 'SPC700Echo',
    # Composition
    'ADSR', 'Gain', 'EchoConfig', 'Instrument', 'Sample',
    'Song', 'Track', 'Note', 'Rest', 'PitchBend', 'VolumeSlide',
    'Vibrato', 'Tremolo', 'SetEnvelope', 'SetInstrument', 'RawRegWrite',
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
