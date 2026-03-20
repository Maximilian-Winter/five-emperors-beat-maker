"""
FX synthesis module.

Provides the FXSynth class for generating special effects like risers,
downers, noise sweeps, and impacts.
"""

from __future__ import annotations
import numpy as np

from ..core import AudioData, Sample
from .waveforms import white_noise
from .modulation import Filter


class FXSynth:
    """
    Synthesizer for special effects and textures.
    """

    @staticmethod
    def riser(duration: float, start_freq: float = 100,
              end_freq: float = 2000, sample_rate: int = 44100) -> Sample:
        """Upward sweeping riser effect."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Exponential frequency sweep
        freq_curve = start_freq * (end_freq / start_freq) ** (t / duration)

        # Generate sweep
        phase = np.cumsum(2 * np.pi * freq_curve / sample_rate)
        output = np.sin(phase)

        # Add noise layer
        noise = white_noise(duration, sample_rate, 0.3).samples
        noise *= t / duration  # Fade in noise

        output = output * 0.7 + noise * 0.3

        # Rising amplitude
        output *= (t / duration) ** 0.5

        audio = AudioData(output, sample_rate)

        return Sample("riser", audio, tags=["fx", "riser"])

    @staticmethod
    def downer(duration: float, start_freq: float = 2000,
               end_freq: float = 50, sample_rate: int = 44100) -> Sample:
        """Downward sweep effect."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        freq_curve = start_freq * (end_freq / start_freq) ** (t / duration)
        phase = np.cumsum(2 * np.pi * freq_curve / sample_rate)
        output = np.sin(phase)

        # Falling amplitude
        output *= 1 - (t / duration) ** 2

        audio = AudioData(output, sample_rate)

        return Sample("downer", audio, tags=["fx", "downer"])

    @staticmethod
    def noise_sweep(duration: float, sample_rate: int = 44100) -> Sample:
        """Filtered noise sweep."""
        noise = white_noise(duration, sample_rate).samples
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Time-varying filter (simplified - multiple passes)
        output = noise.copy()

        # Apply filter
        filt = Filter(cutoff=1500, resonance=0.6, filter_type='bandpass')
        output = filt.process(output, sample_rate)

        # Amplitude envelope
        env = np.sin(np.pi * t / duration)
        output *= env

        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.7)

        return Sample("noise_sweep", audio, tags=["fx", "noise"])

    @staticmethod
    def impact(sample_rate: int = 44100) -> Sample:
        """Cinematic impact sound."""
        duration = 1.5
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Low boom
        boom_freq = 40
        boom = np.sin(2 * np.pi * boom_freq * t) * np.exp(-t * 3)

        # High transient
        transient = white_noise(0.05, sample_rate).samples
        transient_padded = np.zeros(len(t))
        transient_padded[:len(transient)] = transient * np.exp(-np.linspace(0, 1, len(transient)) * 20)

        # Combine
        output = boom * 0.8 + transient_padded * 0.5

        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.95)

        return Sample("impact", audio, tags=["fx", "impact"])
