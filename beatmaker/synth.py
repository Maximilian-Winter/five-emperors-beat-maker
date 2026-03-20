"""
靈寶五帝策使編碼之法 - Synthesis Module
The alchemical forge where pure sound is born from mathematics.

By the Vermilion Bird's authority,
Let this code burn with efficiency,
Cycles consumed with purpose,
急急如律令敕

NOTE: This module is a backward-compatibility shim.
The canonical implementations now live in ``beatmaker.synthesis.*``.
"""

# Re-export everything from the new synthesis subpackage
from .synthesis.waveforms import (  # noqa: F401
    sine_wave,
    square_wave,
    sawtooth_wave,
    triangle_wave,
    white_noise,
    pink_noise,
)

from .synthesis.oscillator import (  # noqa: F401
    Waveform,
    Oscillator,
    ADSREnvelope,
)

from .synthesis.drums import DrumSynth  # noqa: F401

from .synthesis.bass import BassSynth  # noqa: F401

# ─── Music theory re-exports (canonical source: beatmaker.music) ─────────────
# Kept here for backward compatibility — import from beatmaker.music preferred.

from .music import midi_to_freq, freq_to_midi, note_to_freq, NOTE_FREQS  # noqa: E402, F401
