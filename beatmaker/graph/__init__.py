"""
Signal Graph subpackage -- declarative audio signal processing graphs.
"""

from .core import (
    PortDirection,
    Port,
    SignalNode,
    Connection,
    SignalGraph,
)

from .sources import (
    AudioInput,
    TrackInput,
    OscillatorNode,
    NoiseNode,
)

from .processors import (
    EffectNode,
    GainNode,
    FilterNode,
    CompressorNode,
)

from .combiners import (
    MixNode,
    MultiplyNode,
    CrossfadeNode,
)

from .analysis import (
    EnvelopeFollower,
    FilterBankNode,
)

from .channels import (
    ChannelSplitNode,
    StereoMergeNode,
)

from .bridge import (
    GraphEffect,
)

__all__ = [
    # Core
    "PortDirection",
    "Port",
    "SignalNode",
    "Connection",
    "SignalGraph",
    # Sources
    "AudioInput",
    "TrackInput",
    "OscillatorNode",
    "NoiseNode",
    # Processors
    "EffectNode",
    "GainNode",
    "FilterNode",
    "CompressorNode",
    # Combiners
    "MixNode",
    "MultiplyNode",
    "CrossfadeNode",
    # Analysis
    "EnvelopeFollower",
    "FilterBankNode",
    # Channels
    "ChannelSplitNode",
    "StereoMergeNode",
    # Bridge
    "GraphEffect",
]
