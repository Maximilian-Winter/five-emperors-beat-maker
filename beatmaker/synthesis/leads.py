"""
Lead synthesis module.

Provides the LeadSynth class for generating saw, square, and FM lead sounds,
and the create_lead convenience function.
"""

from __future__ import annotations
from typing import Optional
import numpy as np

from ..core import AudioData, Sample
from .waveforms import sine_wave, sawtooth_wave, square_wave
from .oscillator import ADSREnvelope
from .modulation import Filter


class LeadSynth:
    """
    Synthesizer for lead sounds.

    Creates cutting, expressive lead tones.
    """

    @staticmethod
    def saw_lead(frequency: float, duration: float,
                 envelope: Optional[ADSREnvelope] = None,
                 filter_env: bool = True,
                 sample_rate: int = 44100) -> Sample:
        """Classic saw lead with filter envelope."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.2, sustain=0.7, release=0.3)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Two slightly detuned saws
        saw1 = sawtooth_wave(frequency, duration, sample_rate).samples
        saw2 = sawtooth_wave(frequency * 1.005, duration, sample_rate).samples

        output = (saw1 + saw2) / 2

        if filter_env:
            # Filter envelope (opens then closes)
            filter_env_time = np.exp(-t * 5)
            cutoff_base = 500
            cutoff_range = 4000

            # Approximate time-varying filter
            for i, cutoff in enumerate(cutoff_base + filter_env_time * cutoff_range):
                pass  # Simplified - just use static filter

            filt = Filter(cutoff=2500, resonance=0.4)
            output = filt.process(output, sample_rate)

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        audio = audio.normalize(0.9)

        return Sample(f"saw_lead_{frequency:.0f}hz", audio, tags=["lead", "saw"])

    @staticmethod
    def square_lead(frequency: float, duration: float,
                    pulse_width: float = 0.5,
                    envelope: Optional[ADSREnvelope] = None,
                    sample_rate: int = 44100) -> Sample:
        """Square/pulse wave lead."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.2)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Pulse wave with adjustable width
        phase = (t * frequency) % 1.0
        output = np.where(phase < pulse_width, 1.0, -1.0).astype(np.float64)

        # Add sub oscillator
        sub = sine_wave(frequency / 2, duration, sample_rate).samples * 0.3
        output += sub

        # Filter
        filt = Filter(cutoff=3000, resonance=0.3)
        output = filt.process(output, sample_rate)

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)

        return Sample(f"square_lead_{frequency:.0f}hz", audio, tags=["lead", "square"])

    @staticmethod
    def fm_lead(frequency: float, duration: float,
                mod_ratio: float = 2.0, mod_index: float = 3.0,
                envelope: Optional[ADSREnvelope] = None,
                sample_rate: int = 44100) -> Sample:
        """FM synthesis lead."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.15, sustain=0.6, release=0.25)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Modulator
        mod_freq = frequency * mod_ratio
        modulator = np.sin(2 * np.pi * mod_freq * t) * mod_index

        # Carrier with FM
        output = np.sin(2 * np.pi * frequency * t + modulator)

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)

        return Sample(f"fm_lead_{frequency:.0f}hz", audio, tags=["lead", "fm"])


def create_lead(note: str, duration: float, lead_type: str = 'saw') -> Sample:
    """Quick lead creation."""
    from ..music import note_to_freq
    freq = note_to_freq(note)

    if lead_type == 'saw':
        return LeadSynth.saw_lead(freq, duration)
    elif lead_type == 'square':
        return LeadSynth.square_lead(freq, duration)
    elif lead_type == 'fm':
        return LeadSynth.fm_lead(freq, duration)
    else:
        return LeadSynth.saw_lead(freq, duration)
