"""
Signal combination nodes: mix, multiply, crossfade.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from .core import SignalNode


class MixNode(SignalNode):
    """
    Weighted sum of multiple input signals.

    Input ports are named input_0, input_1, ..., input_N-1.
    Each can have a weight (default: equal weighting).
    """

    def __init__(self, num_inputs: int = 2,
                 weights: Optional[List[float]] = None,
                 name: str = "mix"):
        self.num_inputs = num_inputs
        self.weights = weights or [1.0 / num_inputs] * num_inputs
        super().__init__(name=name)

    def _setup_ports(self):
        for i in range(self.num_inputs):
            self._add_input(f"input_{i}")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        output = np.zeros(num_samples)
        for i in range(self.num_inputs):
            port_name = f"input_{i}"
            if port_name in inputs:
                weight = self.weights[i] if i < len(self.weights) else 1.0
                signal = inputs[port_name]
                length = min(len(signal), num_samples)
                output[:length] += signal[:length] * weight
        return {"main": output}


class MultiplyNode(SignalNode):
    """
    Element-wise multiplication of two signals.

    This is the fundamental building block for:
    - Ring modulation (two audio-rate signals)
    - Amplitude modulation (audio x envelope)
    - VCA (audio x control signal)
    """

    def __init__(self, name: str = "multiply"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("a")
        self._add_input("b")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        a = inputs.get("a", np.zeros(num_samples))
        b = inputs.get("b", np.zeros(num_samples))
        return {"main": a * b}


class CrossfadeNode(SignalNode):
    """
    Blend between two signals with a mix parameter.

    mix=0.0 outputs signal a, mix=1.0 outputs signal b.
    If a mix_cv signal is connected, it overrides the static mix.
    """

    def __init__(self, mix: float = 0.5, name: str = "crossfade"):
        self.mix = mix
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("a")
        self._add_input("b")
        self._add_input("mix_cv")  # Optional: per-sample mix control
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        a = inputs.get("a", np.zeros(num_samples))
        b = inputs.get("b", np.zeros(num_samples))

        if "mix_cv" in inputs:
            mix = np.clip(inputs["mix_cv"], 0.0, 1.0)
        else:
            mix = self.mix

        return {"main": a * (1 - mix) + b * mix}
