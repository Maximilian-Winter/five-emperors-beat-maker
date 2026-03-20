"""
Drum synthesis module.

Provides the DrumSynth class for generating kick, snare, hi-hat,
and clap sounds from scratch.
"""

import numpy as np

from ..core import AudioData, Sample
from .waveforms import white_noise


class DrumSynth:
    """
    Synthesizer optimized for drum and percussion sounds.
    """

    @staticmethod
    def kick(duration: float = 0.5, pitch: float = 60.0,
             punch: float = 0.8, sample_rate: int = 44100) -> Sample:
        """Synthesize a kick drum."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Pitch envelope - rapid drop from high to low
        pitch_env = pitch * np.exp(-30 * t) + 40

        # Generate sine wave with pitch envelope
        phase = np.cumsum(2 * np.pi * pitch_env / sample_rate)
        tone = np.sin(phase)

        # Add punch (click transient)
        click_duration = 0.01
        click_samples = int(click_duration * sample_rate)
        click = white_noise(click_duration, sample_rate, punch).samples
        click *= np.exp(-t[:click_samples] * 200)

        # Combine
        samples = tone.copy()
        samples[:click_samples] += click

        # Apply amplitude envelope
        amp_env = np.exp(-5 * t)
        samples *= amp_env

        audio = AudioData(samples, sample_rate)
        return Sample("kick", audio, tags=["drums", "kick"])

    @staticmethod
    def snare(duration: float = 0.3, tone_pitch: float = 180.0,
              noise_amount: float = 0.6, sample_rate: int = 44100) -> Sample:
        """Synthesize a snare drum."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)

        # Tone component (body)
        tone_env = np.exp(-20 * t)
        tone = np.sin(2 * np.pi * tone_pitch * t) * tone_env

        # Noise component (snares)
        noise = white_noise(duration, sample_rate).samples
        noise_env = np.exp(-15 * t)
        noise *= noise_env * noise_amount

        # Combine
        samples = tone * (1 - noise_amount) + noise

        audio = AudioData(samples, sample_rate)
        return Sample("snare", audio, tags=["drums", "snare"])

    @staticmethod
    def hihat(duration: float = 0.1, open_amount: float = 0.0,
              sample_rate: int = 44100) -> Sample:
        """Synthesize a hi-hat (closed to open based on open_amount)."""
        # Longer duration for open hi-hat
        actual_duration = duration + (open_amount * 0.4)
        t = np.linspace(0, actual_duration, int(actual_duration * sample_rate), False)

        # Metallic noise (band-limited)
        noise = white_noise(actual_duration, sample_rate).samples

        # Add some tonal content
        tone1 = np.sin(2 * np.pi * 3000 * t) * 0.3
        tone2 = np.sin(2 * np.pi * 6000 * t) * 0.2

        samples = noise * 0.5 + tone1 + tone2

        # Envelope (faster decay for closed)
        decay_rate = 30 - (open_amount * 25)  # 30 for closed, 5 for open
        envelope = np.exp(-decay_rate * t)
        samples *= envelope

        name = "hihat_open" if open_amount > 0.5 else "hihat_closed"
        audio = AudioData(samples, sample_rate)
        return Sample(name, audio, tags=["drums", "hihat"])

    @staticmethod
    def clap(duration: float = 0.2, spread: float = 0.02,
             sample_rate: int = 44100) -> Sample:
        """Synthesize a clap sound with multiple transients."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        num_samples = len(t)
        samples = np.zeros(num_samples)

        # Multiple noise bursts (simulating multiple hands)
        num_bursts = 4
        burst_times = np.linspace(0, spread, num_bursts)

        for burst_time in burst_times:
            burst_start = int(burst_time * sample_rate)
            burst_duration = 0.02
            burst_samples = int(burst_duration * sample_rate)

            if burst_start + burst_samples <= num_samples:
                burst = white_noise(burst_duration, sample_rate).samples
                burst *= np.exp(-np.linspace(0, 1, burst_samples) * 30)
                samples[burst_start:burst_start + burst_samples] += burst

        # Add tail
        tail_env = np.exp(-15 * t)
        tail = white_noise(duration, sample_rate).samples * tail_env * 0.3
        samples += tail

        audio = AudioData(samples, sample_rate).normalize()
        return Sample("clap", audio, tags=["drums", "clap"])
