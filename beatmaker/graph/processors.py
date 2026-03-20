"""
Processing nodes: nodes that transform signals.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ..core import AudioData, AudioEffect
from ..synths import Filter
from .core import SignalNode


class EffectNode(SignalNode):
    """
    Wraps any existing AudioEffect as a graph node.

    Every Gain, Reverb, Compressor, Delay, and Chorus can flow
    through the signal graph without modification.
    """

    def __init__(self, effect: AudioEffect, name: str = ""):
        self.effect = effect
        super().__init__(name=name or f"fx_{effect.__class__.__name__}")

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        audio = AudioData(signal, sample_rate, 1)
        result = self.effect.process(audio)
        if result.channels > 1:
            result = result.to_mono()
        samples = result.samples
        if len(samples) > num_samples:
            samples = samples[:num_samples]
        elif len(samples) < num_samples:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            samples = padded
        return {"main": samples}


class GainNode(SignalNode):
    """
    Amplitude control with optional CV modulation.

    If a signal is connected to the gain_cv input,
    it is used as a per-sample multiplier (amplitude modulation).
    Otherwise, the static level parameter is applied.
    """

    def __init__(self, level: float = 1.0, name: str = "gain"):
        self.level = level
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("gain_cv")  # Optional: per-sample gain control
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        if "gain_cv" in inputs:
            cv = inputs["gain_cv"]
            return {"main": signal * cv}
        else:
            return {"main": signal * self.level}


class FilterNode(SignalNode):
    """
    Resonant filter with optional cutoff modulation.

    Wraps the biquad Filter from synths.py. If cutoff_cv is connected,
    the filter cutoff is modulated per-block (not per-sample, for efficiency).
    """

    def __init__(self, cutoff: float = 1000.0, resonance: float = 0.0,
                 filter_type: str = 'lowpass', name: str = "filter"):
        self.cutoff = cutoff
        self.resonance = resonance
        self.filter_type = filter_type
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("cutoff_cv")  # Optional: modulates cutoff
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        if "cutoff_cv" in inputs:
            cv = inputs["cutoff_cv"]
            block_size = 256
            output = np.zeros(num_samples)
            for start in range(0, num_samples, block_size):
                end = min(start + block_size, num_samples)
                avg_cv = np.mean(cv[start:end])
                effective_cutoff = max(20.0, self.cutoff + avg_cv)
                filt = Filter(
                    cutoff=effective_cutoff,
                    resonance=self.resonance,
                    filter_type=self.filter_type
                )
                output[start:end] = filt.process(signal[start:end], sample_rate)
            return {"main": output}
        else:
            filt = Filter(
                cutoff=self.cutoff,
                resonance=self.resonance,
                filter_type=self.filter_type
            )
            return {"main": filt.process(signal, sample_rate)}


class CompressorNode(SignalNode):
    """
    Dynamic range compressor with optional sidechain input.

    When a sidechain signal is connected, the compressor's envelope
    follows the sidechain rather than the main input.
    """

    def __init__(self, threshold: float = -10.0, ratio: float = 4.0,
                 attack: float = 0.01, release: float = 0.1,
                 makeup_gain: float = 0.0, name: str = "compressor"):
        self.threshold = threshold
        self.ratio = ratio
        self.attack = attack
        self.release = release
        self.makeup_gain = makeup_gain
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("sidechain")  # Optional: external key signal
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        key_signal = inputs.get("sidechain", signal)

        threshold_linear = 10 ** (self.threshold / 20)
        attack_coef = np.exp(-1 / (self.attack * sample_rate))
        release_coef = np.exp(-1 / (self.release * sample_rate))

        envelope = np.abs(key_signal)
        smooth_env = np.zeros(num_samples)
        smooth_env[0] = envelope[0]
        for i in range(1, num_samples):
            if envelope[i] > smooth_env[i - 1]:
                smooth_env[i] = attack_coef * smooth_env[i - 1] + (1 - attack_coef) * envelope[i]
            else:
                smooth_env[i] = release_coef * smooth_env[i - 1] + (1 - release_coef) * envelope[i]

        gain = np.ones(num_samples)
        above = smooth_env > threshold_linear
        gain[above] = (
            threshold_linear +
            (smooth_env[above] - threshold_linear) / self.ratio
        ) / smooth_env[above]

        output = signal * gain * (10 ** (self.makeup_gain / 20))
        return {"main": output}
