"""
Modulation and filtering components for synthesis.

Contains the LFO (Low Frequency Oscillator) and Filter classes.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class LFO:
    """Low Frequency Oscillator for modulation."""
    rate: float = 1.0      # Hz
    depth: float = 1.0     # Modulation depth
    waveform: str = 'sine'  # sine, triangle, saw, square, random
    phase: float = 0.0     # Starting phase (0-1)

    def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Generate LFO signal."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        phase_offset = self.phase * 2 * np.pi

        if self.waveform == 'sine':
            signal = np.sin(2 * np.pi * self.rate * t + phase_offset)
        elif self.waveform == 'triangle':
            signal = 2 * np.abs(2 * ((t * self.rate + self.phase) % 1) - 1) - 1
        elif self.waveform == 'saw':
            signal = 2 * ((t * self.rate + self.phase) % 1) - 1
        elif self.waveform == 'square':
            signal = np.sign(np.sin(2 * np.pi * self.rate * t + phase_offset))
        elif self.waveform == 'random':
            # Sample and hold random
            samples_per_cycle = int(sample_rate / self.rate)
            num_cycles = int(duration * self.rate) + 1
            values = np.random.random(num_cycles) * 2 - 1
            signal = np.repeat(values, samples_per_cycle)[:int(duration * sample_rate)]
        else:
            signal = np.sin(2 * np.pi * self.rate * t)

        return signal * self.depth


@dataclass
class Filter:
    """Simple resonant filter."""
    cutoff: float = 1000.0
    resonance: float = 0.0  # 0-1
    filter_type: str = 'lowpass'  # lowpass, highpass, bandpass

    def process(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply filter to samples."""
        # Normalized cutoff
        w0 = 2 * np.pi * self.cutoff / sample_rate
        w0 = min(w0, np.pi * 0.99)  # Prevent instability

        # Resonance (Q factor)
        Q = 0.5 + self.resonance * 10
        alpha = np.sin(w0) / (2 * Q)

        cos_w0 = np.cos(w0)

        # Biquad coefficients
        if self.filter_type == 'lowpass':
            b0 = (1 - cos_w0) / 2
            b1 = 1 - cos_w0
            b2 = (1 - cos_w0) / 2
        elif self.filter_type == 'highpass':
            b0 = (1 + cos_w0) / 2
            b1 = -(1 + cos_w0)
            b2 = (1 + cos_w0) / 2
        elif self.filter_type == 'bandpass':
            b0 = alpha
            b1 = 0
            b2 = -alpha
        else:
            return samples

        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha

        # Normalize
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0

        # Apply filter
        output = np.zeros_like(samples)
        x1, x2, y1, y2 = 0.0, 0.0, 0.0, 0.0

        for i in range(len(samples)):
            x0 = samples[i]
            y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            output[i] = y0

            x2, x1 = x1, x0
            y2, y1 = y1, y0

        return output
