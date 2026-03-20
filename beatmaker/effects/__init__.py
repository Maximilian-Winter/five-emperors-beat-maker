"""
Effects subpackage - re-exports all effects for backward compatibility.

Usage:
    from beatmaker.effects import Gain, Limiter, EffectChain
    from beatmaker.effects import SidechainCompressor, SidechainPresets
"""

from .dynamics import Gain, Limiter, SoftClipper, Compressor
from .time_based import Delay, Reverb, Chorus
from .filters import LowPassFilter, HighPassFilter, BitCrusher
from .base import EffectChain
from .sidechain import (
    SidechainCompressor,
    SidechainEnvelope,
    PumpingBass,
    SidechainBuilder,
    SidechainPresets,
    create_sidechain,
)

__all__ = [
    # Dynamics
    "Gain",
    "Limiter",
    "SoftClipper",
    "Compressor",
    # Time-based
    "Delay",
    "Reverb",
    "Chorus",
    # Filters
    "LowPassFilter",
    "HighPassFilter",
    "BitCrusher",
    # Chain
    "EffectChain",
    # Sidechain
    "SidechainCompressor",
    "SidechainEnvelope",
    "PumpingBass",
    "SidechainBuilder",
    "SidechainPresets",
    "create_sidechain",
]
