"""
Backward-compatibility stub.

All sidechain classes have moved to beatmaker.effects.sidechain.
This module re-exports them so existing imports continue to work.
"""

from .effects.sidechain import (
    SidechainCompressor,
    SidechainEnvelope,
    PumpingBass,
    SidechainBuilder,
    SidechainPresets,
    create_sidechain,
)

__all__ = [
    "SidechainCompressor",
    "SidechainEnvelope",
    "PumpingBass",
    "SidechainBuilder",
    "SidechainPresets",
    "create_sidechain",
]
