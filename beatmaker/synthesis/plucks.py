"""
Pluck synthesis module.

Provides the PluckSynth class for generating plucked string, synth pluck,
and bell sounds, and the create_pluck convenience function.
"""

from __future__ import annotations
from typing import Optional
import numpy as np

from ..core import AudioData, Sample
from .waveforms import sawtooth_wave, square_wave
from .oscillator import ADSREnvelope
from .modulation import Filter


class PluckSynth:
    """
    Synthesizer for plucked string sounds.

    Uses Karplus-Strong and other techniques.
    """

    @staticmethod
    def karplus_strong(frequency: float, duration: float,
                       brightness: float = 0.5,
                       sample_rate: int = 44100) -> Sample:
        """
        Karplus-Strong plucked string synthesis.

        Args:
            frequency: Note frequency in Hz
            duration: Duration in seconds
            brightness: Tone brightness 0-1 (affects decay)
        """
        num_samples = int(duration * sample_rate)
        delay_samples = int(sample_rate / frequency)

        # Initialize buffer with noise burst
        buffer = np.random.random(delay_samples) * 2 - 1
        output = np.zeros(num_samples)

        # Damping factor based on brightness
        damping = 0.996 - (1 - brightness) * 0.01

        for i in range(num_samples):
            # Read from buffer
            output[i] = buffer[i % delay_samples]

            # Average two adjacent samples and apply damping
            idx = i % delay_samples
            next_idx = (i + 1) % delay_samples
            buffer[idx] = damping * 0.5 * (buffer[idx] + buffer[next_idx])

        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.9)

        return Sample(f"pluck_{frequency:.0f}hz", audio, tags=["pluck", "string"])

    @staticmethod
    def synth_pluck(frequency: float, duration: float,
                    envelope: Optional[ADSREnvelope] = None,
                    sample_rate: int = 44100) -> Sample:
        """Synthesized pluck sound."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.001, decay=0.3, sustain=0.0, release=0.2)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Mix of waves
        saw = sawtooth_wave(frequency, duration, sample_rate).samples
        sq = square_wave(frequency, duration, sample_rate, duty_cycle=0.3).samples

        output = saw * 0.7 + sq * 0.3

        # Aggressive filter envelope
        filter_env = np.exp(-t * 20)
        cutoff_values = 500 + filter_env * 5000

        # Static filter approximation
        filt = Filter(cutoff=2000, resonance=0.5)
        output = filt.process(output, sample_rate)

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)

        return Sample(f"synth_pluck_{frequency:.0f}hz", audio, tags=["pluck", "synth"])

    @staticmethod
    def bell(frequency: float, duration: float,
             sample_rate: int = 44100) -> Sample:
        """Bell-like FM pluck."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # FM bell synthesis
        mod_freq = frequency * 1.4  # Inharmonic ratio for bell character
        mod_index = 5 * np.exp(-t * 3)  # Decaying modulation

        modulator = np.sin(2 * np.pi * mod_freq * t) * mod_index
        carrier = np.sin(2 * np.pi * frequency * t + modulator)

        # Add higher partial
        partial = np.sin(2 * np.pi * frequency * 2.76 * t) * 0.3 * np.exp(-t * 4)

        output = carrier + partial

        # Amplitude envelope
        amp_env = np.exp(-t * 2)
        output *= amp_env

        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.8)

        return Sample(f"bell_{frequency:.0f}hz", audio, tags=["pluck", "bell"])


def create_pluck(note: str, duration: float = 1.0, pluck_type: str = 'karplus') -> Sample:
    """Quick pluck creation."""
    from ..music import note_to_freq
    freq = note_to_freq(note)

    if pluck_type == 'karplus':
        return PluckSynth.karplus_strong(freq, duration)
    elif pluck_type == 'synth':
        return PluckSynth.synth_pluck(freq, duration)
    elif pluck_type == 'bell':
        return PluckSynth.bell(freq, duration)
    else:
        return PluckSynth.karplus_strong(freq, duration)
