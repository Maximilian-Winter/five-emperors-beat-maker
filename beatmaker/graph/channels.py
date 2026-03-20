"""
Channel manipulation nodes: split and merge stereo channels.
"""

from __future__ import annotations

import numpy as np

from .core import SignalNode


class ChannelSplitNode(SignalNode):
    """Split a stereo signal into left and right mono channels."""

    def __init__(self, name: str = "channel_split"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("left")
        self._add_output("right")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        return {
            "left": signal.copy(),
            "right": signal.copy(),
        }


class StereoMergeNode(SignalNode):
    """Combine left and right mono signals into stereo."""

    def __init__(self, name: str = "stereo_merge"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("left")
        self._add_input("right")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        left = inputs.get("left", np.zeros(num_samples))
        right = inputs.get("right", np.zeros(num_samples))
        return {"main": (left + right) * 0.5}
