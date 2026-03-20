"""
Synthesis subpackage for beatmaker.

Re-exports all public synthesis components so that
``from beatmaker.synthesis import DrumSynth`` (and similar) works.
"""

# Waveform generators
from .waveforms import (
    sine_wave,
    square_wave,
    sawtooth_wave,
    triangle_wave,
    white_noise,
    pink_noise,
)

# Oscillator & envelope
from .oscillator import (
    Waveform,
    Oscillator,
    ADSREnvelope,
)

# Drum synthesis
from .drums import DrumSynth

# Bass synthesis
from .bass import BassSynth

# Modulation & filtering
from .modulation import LFO, Filter

# Pad synthesis
from .pads import PadSynth, create_pad

# Lead synthesis
from .leads import LeadSynth, create_lead

# Pluck synthesis
from .plucks import PluckSynth, create_pluck

# FX synthesis
from .fx import FXSynth

__all__ = [
    # Waveforms
    "sine_wave",
    "square_wave",
    "sawtooth_wave",
    "triangle_wave",
    "white_noise",
    "pink_noise",
    # Oscillator & envelope
    "Waveform",
    "Oscillator",
    "ADSREnvelope",
    # Synths
    "DrumSynth",
    "BassSynth",
    "LFO",
    "Filter",
    "PadSynth",
    "LeadSynth",
    "PluckSynth",
    "FXSynth",
    # Convenience functions
    "create_pad",
    "create_lead",
    "create_pluck",
]
