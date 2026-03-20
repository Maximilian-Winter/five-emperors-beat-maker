"""
Dynamics effects: Gain, Limiter, SoftClipper, Compressor.
"""

import numpy as np
from dataclasses import dataclass

from ..core import AudioEffect, AudioData


@dataclass
class Gain(AudioEffect):
    """Simple gain/volume adjustment."""
    level: float = 1.0  # Linear gain multiplier

    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples * self.level
        return AudioData(samples, audio.sample_rate, audio.channels)

    @classmethod
    def from_db(cls, db: float) -> 'Gain':
        """Create gain from decibel value."""
        return cls(level=10 ** (db / 20))


@dataclass
class Limiter(AudioEffect):
    """Hard limiter to prevent clipping."""
    threshold: float = 0.95

    def process(self, audio: AudioData) -> AudioData:
        samples = np.clip(audio.samples, -self.threshold, self.threshold)
        return AudioData(samples, audio.sample_rate, audio.channels)


@dataclass
class SoftClipper(AudioEffect):
    """Soft clipping for warm saturation."""
    drive: float = 1.0  # Amount of drive/saturation

    def process(self, audio: AudioData) -> AudioData:
        # Apply drive
        samples = audio.samples * self.drive
        # Soft clip using tanh
        samples = np.tanh(samples)
        return AudioData(samples, audio.sample_rate, audio.channels)


@dataclass
class Compressor(AudioEffect):
    """Dynamic range compressor."""
    threshold: float = -10.0  # dB
    ratio: float = 4.0        # Compression ratio
    attack: float = 0.01      # Attack time in seconds
    release: float = 0.1      # Release time in seconds
    makeup_gain: float = 0.0  # Makeup gain in dB

    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples.copy()
        sr = audio.sample_rate

        # Convert threshold to linear
        threshold_linear = 10 ** (self.threshold / 20)

        # Time constants
        attack_coef = np.exp(-1 / (self.attack * sr))
        release_coef = np.exp(-1 / (self.release * sr))

        # Envelope follower
        if audio.channels == 1:
            envelope = np.abs(samples)
        else:
            envelope = np.max(np.abs(samples), axis=1)

        # Smooth envelope
        smooth_env = np.zeros_like(envelope)
        smooth_env[0] = envelope[0]
        for i in range(1, len(envelope)):
            if envelope[i] > smooth_env[i-1]:
                smooth_env[i] = attack_coef * smooth_env[i-1] + (1 - attack_coef) * envelope[i]
            else:
                smooth_env[i] = release_coef * smooth_env[i-1] + (1 - release_coef) * envelope[i]

        # Calculate gain reduction
        gain = np.ones_like(smooth_env)
        above_threshold = smooth_env > threshold_linear
        gain[above_threshold] = (
            threshold_linear +
            (smooth_env[above_threshold] - threshold_linear) / self.ratio
        ) / smooth_env[above_threshold]

        # Apply gain
        if audio.channels == 1:
            output = samples * gain
        else:
            output = samples * gain[:, np.newaxis]

        # Apply makeup gain
        makeup_linear = 10 ** (self.makeup_gain / 20)
        output *= makeup_linear

        return AudioData(output, audio.sample_rate, audio.channels)
