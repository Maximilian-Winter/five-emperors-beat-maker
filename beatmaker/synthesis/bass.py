"""
Bass synthesis module.

Provides the BassSynth class for generating sub-bass and acid bass sounds.
"""

import numpy as np
from typing import Optional

from ..core import AudioData, Sample
from .waveforms import sine_wave, sawtooth_wave
from .oscillator import ADSREnvelope


class BassSynth:
    """Synthesizer for bass sounds."""

    @staticmethod
    def sub_bass(frequency: float, duration: float,
                 envelope: Optional[ADSREnvelope] = None,
                 sample_rate: int = 44100) -> Sample:
        """Pure sub-bass sine wave."""
        audio = sine_wave(frequency, duration, sample_rate)

        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.1)

        audio = envelope.apply(audio)
        return Sample(f"sub_bass_{frequency}hz", audio, tags=["bass", "sub"])

    @staticmethod
    def acid_bass(frequency: float, duration: float,
                  filter_freq: float = 500.0, resonance: float = 0.7,
                  envelope: Optional[ADSREnvelope] = None,
                  sample_rate: int = 44100) -> Sample:
        """Classic acid bass (303-style)."""
        # Sawtooth base
        audio = sawtooth_wave(frequency, duration, sample_rate)

        # Simple low-pass filter simulation with envelope
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        filter_env = np.exp(-3 * t) * filter_freq + 100

        # Apply very basic filtering (proper implementation would use scipy)
        samples = audio.samples
        filtered = np.zeros_like(samples)
        cutoff = 0.1  # Simplified cutoff

        for i in range(1, len(samples)):
            filtered[i] = filtered[i-1] + cutoff * (samples[i] - filtered[i-1])

        audio = AudioData(filtered, sample_rate)

        if envelope is None:
            envelope = ADSREnvelope(attack=0.001, decay=0.2, sustain=0.5, release=0.1)

        audio = envelope.apply(audio)
        return Sample(f"acid_bass_{frequency}hz", audio, tags=["bass", "acid"])
