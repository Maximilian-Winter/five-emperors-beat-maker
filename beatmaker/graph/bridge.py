"""
Integration adapter: wraps a SignalGraph as an AudioEffect.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..core import AudioData, AudioEffect
from .core import SignalGraph
from .sources import AudioInput


class GraphEffect(AudioEffect):
    """
    Wraps a SignalGraph as a standard AudioEffect.

    This adapter allows any signal graph to be used wherever an
    AudioEffect is expected: in Track.effects, EffectChain, or
    Song.master_effects.

    The process() input audio is fed into the graph's designated
    AudioInput node. Additional fixed audio sources (e.g., a carrier
    signal for a vocoder) are set via fixed_sources.
    """

    def __init__(self, graph: SignalGraph,
                 input_node_name: str = "input",
                 fixed_sources: Optional[Dict[str, AudioData]] = None):
        self._graph = graph
        self._input_node_name = input_node_name
        self._fixed_sources = fixed_sources or {}

    def _find_audio_input(self, name: str) -> Optional[AudioInput]:
        """Find an AudioInput node by name."""
        for node in self._graph.nodes:
            if isinstance(node, AudioInput) and node.name == name:
                return node
        return None

    def process(self, audio: AudioData) -> AudioData:
        """Apply the graph as an effect to the input audio."""
        input_node = self._find_audio_input(self._input_node_name)
        if input_node is not None:
            input_node.set_audio(audio)

        for name, source_audio in self._fixed_sources.items():
            source_node = self._find_audio_input(name)
            if source_node is not None:
                source_node.set_audio(source_audio)

        result = self._graph.render(audio.duration, audio.sample_rate)

        if audio.channels == 2 and result.channels == 1:
            result = result.to_stereo()
        elif audio.channels == 1 and result.channels == 2:
            result = result.to_mono()

        return result
