"""
Oscillator and envelope components for synthesis.

Contains the Waveform enum, Oscillator class, and ADSREnvelope dataclass.
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum, auto

from ..core import AudioData
from .waveforms import sine_wave, square_wave, sawtooth_wave, triangle_wave, white_noise


class Waveform(Enum):
    """Basic waveform types."""
    SINE = auto()
    SQUARE = auto()
    SAWTOOTH = auto()
    TRIANGLE = auto()
    NOISE = auto()


@dataclass
class ADSREnvelope:
    """
    Attack-Decay-Sustain-Release envelope generator.

    Creates amplitude envelopes for shaping sound over time.
    """
    attack: float = 0.01   # Attack time in seconds
    decay: float = 0.1     # Decay time in seconds
    sustain: float = 0.7   # Sustain level (0.0 - 1.0)
    release: float = 0.2   # Release time in seconds

    def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Generate envelope samples for the given duration."""
        # Calculate sample counts
        attack_samples = int(self.attack * sample_rate)
        decay_samples = int(self.decay * sample_rate)
        release_samples = int(self.release * sample_rate)
        total_samples = int(duration * sample_rate)

        # Sustain fills the rest
        sustain_samples = max(0, total_samples - attack_samples - decay_samples - release_samples)

        # Build envelope segments
        envelope = np.zeros(total_samples)
        idx = 0

        # Attack
        if attack_samples > 0:
            attack_end = min(attack_samples, total_samples)
            envelope[idx:attack_end] = np.linspace(0, 1, attack_end - idx)
            idx = attack_end

        # Decay
        if idx < total_samples and decay_samples > 0:
            decay_end = min(idx + decay_samples, total_samples)
            envelope[idx:decay_end] = np.linspace(1, self.sustain, decay_end - idx)
            idx = decay_end

        # Sustain
        if idx < total_samples and sustain_samples > 0:
            sustain_end = min(idx + sustain_samples, total_samples)
            envelope[idx:sustain_end] = self.sustain
            idx = sustain_end

        # Release
        if idx < total_samples:
            envelope[idx:] = np.linspace(self.sustain, 0, total_samples - idx)

        return envelope

    def apply(self, audio: AudioData) -> AudioData:
        """Apply the envelope to audio data."""
        envelope = self.generate(audio.duration, audio.sample_rate)

        # Ensure envelope matches audio length exactly
        if len(envelope) != len(audio.samples):
            if len(envelope) > len(audio.samples):
                envelope = envelope[:len(audio.samples)]
            else:
                padded = np.zeros(len(audio.samples))
                padded[:len(envelope)] = envelope
                envelope = padded

        if audio.channels == 1:
            samples = audio.samples * envelope
        else:
            samples = audio.samples * envelope[:, np.newaxis]

        return AudioData(samples, audio.sample_rate, audio.channels)


class Oscillator:
    """
    Versatile oscillator for synthesis.

    Supports multiple waveforms with various modulation options.
    """

    def __init__(self, waveform: Waveform = Waveform.SINE,
                 detune: float = 0.0,
                 phase: float = 0.0):
        self.waveform = waveform
        self.detune = detune  # In cents (100 cents = 1 semitone)
        self.phase = phase    # Phase offset in radians

    def generate(self, frequency: float, duration: float,
                 sample_rate: int = 44100) -> AudioData:
        """Generate audio at the specified frequency."""
        # Apply detune
        actual_freq = frequency * (2 ** (self.detune / 1200))

        if self.waveform == Waveform.SINE:
            audio = sine_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.SQUARE:
            audio = square_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.SAWTOOTH:
            audio = sawtooth_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.TRIANGLE:
            audio = triangle_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.NOISE:
            audio = white_noise(duration, sample_rate)
        else:
            raise ValueError(f"Unknown waveform: {self.waveform}")

        # Apply phase offset
        if self.phase != 0:
            phase_samples = int((self.phase / (2 * np.pi)) * sample_rate / actual_freq)
            if phase_samples > 0:
                audio.samples = np.roll(audio.samples, phase_samples)

        return audio
