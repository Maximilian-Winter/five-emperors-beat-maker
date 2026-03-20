"""
Waveform generators for synthesis.

Pure functions that generate basic waveform AudioData from frequency,
duration, and sample rate parameters.
"""

import numpy as np
from typing import Optional

from ..core import AudioData


def sine_wave(frequency: float, duration: float,
              sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    samples = amplitude * np.sin(2 * np.pi * frequency * t)
    return AudioData(samples, sample_rate)


def square_wave(frequency: float, duration: float,
                sample_rate: int = 44100, amplitude: float = 1.0,
                duty_cycle: float = 0.5) -> AudioData:
    """Generate a square wave with adjustable duty cycle."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    phase = (t * frequency) % 1.0
    samples = amplitude * np.where(phase < duty_cycle, 1.0, -1.0)
    return AudioData(samples.astype(np.float64), sample_rate)


def sawtooth_wave(frequency: float, duration: float,
                  sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a sawtooth wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    samples = amplitude * (2.0 * ((t * frequency) % 1.0) - 1.0)
    return AudioData(samples, sample_rate)


def triangle_wave(frequency: float, duration: float,
                  sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a triangle wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    phase = (t * frequency) % 1.0
    samples = amplitude * (4.0 * np.abs(phase - 0.5) - 1.0)
    return AudioData(samples, sample_rate)


def white_noise(duration: float, sample_rate: int = 44100,
                amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData:
    """Generate white noise."""
    if seed is not None:
        np.random.seed(seed)
    num_samples = int(duration * sample_rate)
    samples = amplitude * (2.0 * np.random.random(num_samples) - 1.0)
    return AudioData(samples, sample_rate)


def pink_noise(duration: float, sample_rate: int = 44100,
               amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData:
    """Generate pink noise (1/f spectrum) using the Voss-McCartney algorithm."""
    if seed is not None:
        np.random.seed(seed)

    num_samples = int(duration * sample_rate)
    num_octaves = 16

    # Initialize
    values = np.zeros(num_octaves)
    running_sum = 0.0
    samples = np.zeros(num_samples)

    for i in range(num_samples):
        # Determine which octave to update
        k = i
        n_zeros = 0
        while k > 0 and (k & 1) == 0:
            k >>= 1
            n_zeros += 1

        if n_zeros < num_octaves:
            running_sum -= values[n_zeros]
            values[n_zeros] = np.random.random() * 2 - 1
            running_sum += values[n_zeros]

        samples[i] = running_sum / num_octaves

    # Normalize and apply amplitude
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = amplitude * samples / max_val

    return AudioData(samples, sample_rate)
