"""
Filter effects: LowPassFilter, HighPassFilter, BitCrusher.
"""

import numpy as np
from dataclasses import dataclass

from ..core import AudioEffect, AudioData


@dataclass
class LowPassFilter(AudioEffect):
    """Simple one-pole low-pass filter."""
    cutoff: float = 1000.0  # Cutoff frequency in Hz

    def process(self, audio: AudioData) -> AudioData:
        # Calculate coefficient
        rc = 1.0 / (2 * np.pi * self.cutoff)
        dt = 1.0 / audio.sample_rate
        alpha = dt / (rc + dt)

        if audio.channels == 1:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = output[i-1] + alpha * (audio.samples[i] - output[i-1])
        else:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = output[i-1] + alpha * (audio.samples[i] - output[i-1])

        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class HighPassFilter(AudioEffect):
    """Simple one-pole high-pass filter."""
    cutoff: float = 100.0  # Cutoff frequency in Hz

    def process(self, audio: AudioData) -> AudioData:
        rc = 1.0 / (2 * np.pi * self.cutoff)
        dt = 1.0 / audio.sample_rate
        alpha = rc / (rc + dt)

        if audio.channels == 1:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = alpha * (output[i-1] + audio.samples[i] - audio.samples[i-1])
        else:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = alpha * (output[i-1] + audio.samples[i] - audio.samples[i-1])

        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class BitCrusher(AudioEffect):
    """Lo-fi bit depth reduction effect."""
    bit_depth: int = 8        # Target bit depth (1-16)
    sample_hold: int = 1      # Sample-and-hold factor for rate reduction

    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples.copy()

        # Bit reduction
        levels = 2 ** self.bit_depth
        samples = np.round(samples * levels) / levels

        # Sample rate reduction via sample-and-hold
        if self.sample_hold > 1:
            if audio.channels == 1:
                for i in range(len(samples)):
                    if i % self.sample_hold != 0:
                        samples[i] = samples[i - (i % self.sample_hold)]
            else:
                for i in range(len(samples)):
                    if i % self.sample_hold != 0:
                        samples[i] = samples[i - (i % self.sample_hold)]

        return AudioData(samples, audio.sample_rate, audio.channels)
