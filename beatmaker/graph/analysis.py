"""
Analysis and routing nodes: envelope followers and filter banks.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from ..synths import Filter
from .core import SignalNode


class EnvelopeFollower(SignalNode):
    """
    Extracts the amplitude envelope of a signal.

    Produces a slowly-varying control signal that traces
    the loudness contour of the input. Essential for vocoders,
    auto-wah, and dynamic processing.
    """

    def __init__(self, attack: float = 0.005, release: float = 0.02,
                 name: str = "envelope_follower"):
        self.attack = attack
        self.release = release
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("envelope")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        rectified = np.abs(signal)

        attack_coef = np.exp(-1.0 / (self.attack * sample_rate)) if self.attack > 0 else 0.0
        release_coef = np.exp(-1.0 / (self.release * sample_rate)) if self.release > 0 else 0.0

        envelope = np.zeros(num_samples)
        envelope[0] = rectified[0]

        for i in range(1, num_samples):
            if rectified[i] > envelope[i - 1]:
                envelope[i] = attack_coef * envelope[i - 1] + (1 - attack_coef) * rectified[i]
            else:
                envelope[i] = release_coef * envelope[i - 1] + (1 - release_coef) * rectified[i]

        return {"envelope": envelope}


class FilterBankNode(SignalNode):
    """
    Splits a signal into frequency bands using cascaded bandpass filters.

    Given N-1 crossover frequencies, produces N bands:
    band_0 (below lowest freq) through band_N-1 (above highest freq).
    """

    def __init__(self, crossover_freqs: List[float],
                 resonance: float = 0.3,
                 name: str = "filterbank"):
        self.crossover_freqs = sorted(crossover_freqs)
        self.resonance = resonance
        self.num_bands = len(crossover_freqs) + 1
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        for i in range(self.num_bands):
            self._add_output(f"band_{i}")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        outputs = {}

        for i in range(self.num_bands):
            if i == 0:
                filt = Filter(
                    cutoff=self.crossover_freqs[0],
                    resonance=self.resonance,
                    filter_type='lowpass'
                )
                outputs[f"band_{i}"] = filt.process(signal.copy(), sample_rate)
            elif i == self.num_bands - 1:
                filt = Filter(
                    cutoff=self.crossover_freqs[-1],
                    resonance=self.resonance,
                    filter_type='highpass'
                )
                outputs[f"band_{i}"] = filt.process(signal.copy(), sample_rate)
            else:
                low_freq = self.crossover_freqs[i - 1]
                high_freq = self.crossover_freqs[i]

                lp = Filter(
                    cutoff=high_freq,
                    resonance=self.resonance,
                    filter_type='lowpass'
                )
                hp = Filter(
                    cutoff=low_freq,
                    resonance=self.resonance,
                    filter_type='highpass'
                )
                band = lp.process(signal.copy(), sample_rate)
                band = hp.process(band, sample_rate)
                outputs[f"band_{i}"] = band

        return outputs
