"""
Pad synthesis module.

Provides the PadSynth class for generating warm, string, and ambient pad sounds,
and the create_pad convenience function.
"""

from __future__ import annotations
from typing import Optional
import numpy as np

from ..core import AudioData, Sample
from .waveforms import sine_wave, sawtooth_wave, white_noise
from .oscillator import ADSREnvelope
from .modulation import LFO, Filter


class PadSynth:
    """
    Synthesizer for lush pad sounds.

    Creates warm, evolving textures perfect for ambient and melodic use.
    """

    @staticmethod
    def warm_pad(frequency: float, duration: float,
                 num_voices: int = 4, detune: float = 0.1,
                 envelope: Optional[ADSREnvelope] = None,
                 sample_rate: int = 44100) -> Sample:
        """
        Create a warm detuned pad.

        Args:
            frequency: Base frequency in Hz
            duration: Note duration in seconds
            num_voices: Number of detuned voices (more = thicker)
            detune: Detune amount in semitones
            envelope: ADSR envelope (default: slow attack pad)
        """
        if envelope is None:
            envelope = ADSREnvelope(attack=0.5, decay=0.3, sustain=0.7, release=0.8)

        t = np.linspace(0, duration, int(duration * sample_rate), False)
        output = np.zeros_like(t)

        # Generate detuned voices
        for i in range(num_voices):
            # Spread detune evenly around center
            voice_detune = (i - num_voices / 2) * (detune / num_voices)
            voice_freq = frequency * (2 ** (voice_detune / 12))

            # Mix of saw and sine for warmth
            saw = sawtooth_wave(voice_freq, duration, sample_rate).samples
            sine = sine_wave(voice_freq, duration, sample_rate).samples

            voice = saw * 0.6 + sine * 0.4
            output += voice / num_voices

        # Apply slow LFO for movement
        lfo = LFO(rate=0.3, depth=0.02, waveform='sine')
        modulation = 1 + lfo.generate(duration, sample_rate)
        output *= modulation

        # Low-pass filter for smoothness
        filt = Filter(cutoff=2000, resonance=0.2)
        output = filt.process(output, sample_rate)

        # Apply envelope
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)

        return Sample(f"warm_pad_{frequency:.0f}hz", audio, tags=["pad", "warm"])

    @staticmethod
    def string_pad(frequency: float, duration: float,
                   envelope: Optional[ADSREnvelope] = None,
                   sample_rate: int = 44100) -> Sample:
        """Create a string-like pad sound."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.3, decay=0.2, sustain=0.8, release=0.5)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Multiple harmonics for string-like character
        output = np.zeros_like(t)
        harmonics = [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.2), (5, 0.1)]

        for harmonic, amplitude in harmonics:
            # Slight detuning for chorus effect
            detune = np.random.uniform(-0.02, 0.02)
            freq = frequency * harmonic * (1 + detune)

            wave = sawtooth_wave(freq, duration, sample_rate).samples
            output += wave * amplitude

        # Gentle filtering
        filt = Filter(cutoff=3000, resonance=0.1)
        output = filt.process(output, sample_rate)

        # Normalize
        output /= np.max(np.abs(output))

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)

        return Sample(f"string_pad_{frequency:.0f}hz", audio, tags=["pad", "string"])

    @staticmethod
    def ambient_pad(frequency: float, duration: float,
                    sample_rate: int = 44100) -> Sample:
        """Create an evolving ambient pad."""
        envelope = ADSREnvelope(attack=2.0, decay=1.0, sustain=0.6, release=2.0)

        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Base tone
        base = sine_wave(frequency, duration, sample_rate).samples

        # Add subtle harmonics
        harm2 = sine_wave(frequency * 2, duration, sample_rate).samples * 0.3
        harm3 = sine_wave(frequency * 3, duration, sample_rate).samples * 0.1

        output = base + harm2 + harm3

        # Evolving filter with LFO
        lfo = LFO(rate=0.1, depth=500, waveform='sine')
        filter_mod = 1000 + lfo.generate(duration, sample_rate)

        # Apply time-varying filter (simplified)
        filt = Filter(cutoff=1500, resonance=0.3)
        output = filt.process(output, sample_rate)

        # Add subtle noise
        noise = white_noise(duration, sample_rate, 0.02).samples
        output += noise

        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        audio = audio.normalize(0.8)

        return Sample(f"ambient_pad_{frequency:.0f}hz", audio, tags=["pad", "ambient"])


def create_pad(note: str, duration: float, pad_type: str = 'warm') -> Sample:
    """Quick pad creation."""
    from ..music import note_to_freq
    freq = note_to_freq(note)

    if pad_type == 'warm':
        return PadSynth.warm_pad(freq, duration)
    elif pad_type == 'string':
        return PadSynth.string_pad(freq, duration)
    elif pad_type == 'ambient':
        return PadSynth.ambient_pad(freq, duration)
    else:
        return PadSynth.warm_pad(freq, duration)
