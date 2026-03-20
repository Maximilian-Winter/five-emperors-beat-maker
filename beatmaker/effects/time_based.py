"""
Time-based effects: Delay, Reverb, Chorus.
"""

import numpy as np
from dataclasses import dataclass

from ..core import AudioEffect, AudioData


@dataclass
class Delay(AudioEffect):
    """Simple delay effect."""
    delay_time: float = 0.25  # Delay time in seconds
    feedback: float = 0.3     # Feedback amount (0.0 - 1.0)
    mix: float = 0.5          # Wet/dry mix (0.0 = dry, 1.0 = wet)

    def process(self, audio: AudioData) -> AudioData:
        delay_samples = int(self.delay_time * audio.sample_rate)

        if audio.channels == 1:
            output = np.zeros(len(audio.samples) + delay_samples * 3)
            output[:len(audio.samples)] = audio.samples

            # Apply feedback delay
            for i in range(3):  # 3 delay taps
                offset = delay_samples * (i + 1)
                gain = self.feedback ** (i + 1)
                output[offset:offset + len(audio.samples)] += audio.samples * gain

            # Trim to original length + some tail
            output = output[:len(audio.samples) + delay_samples * 2]
        else:
            output = np.zeros((len(audio.samples) + delay_samples * 3, audio.channels))
            output[:len(audio.samples)] = audio.samples

            for i in range(3):
                offset = delay_samples * (i + 1)
                gain = self.feedback ** (i + 1)
                output[offset:offset + len(audio.samples)] += audio.samples * gain

            output = output[:len(audio.samples) + delay_samples * 2]

        # Mix dry and wet
        result = np.zeros_like(output)
        dry_length = min(len(audio.samples), len(output))
        result[:dry_length] = audio.samples[:dry_length] * (1 - self.mix)
        result += output * self.mix

        return AudioData(result, audio.sample_rate, audio.channels)


@dataclass
class Reverb(AudioEffect):
    """
    Simple algorithmic reverb using comb and allpass filters.
    """
    room_size: float = 0.5   # 0.0 - 1.0
    damping: float = 0.5     # High frequency damping
    mix: float = 0.3         # Wet/dry mix

    def process(self, audio: AudioData) -> AudioData:
        # Convert to mono for processing if stereo
        if audio.channels == 2:
            mono = audio.to_mono()
        else:
            mono = audio

        samples = mono.samples
        sr = audio.sample_rate

        # Comb filter delays (in samples) scaled by room size
        comb_delays = [
            int(0.0297 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0371 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0411 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0437 * sr * (0.5 + self.room_size * 0.5)),
        ]

        # Allpass filter delays
        allpass_delays = [
            int(0.0050 * sr),
            int(0.0017 * sr),
        ]

        # Process through parallel comb filters
        output_length = len(samples) + max(comb_delays) * 4
        comb_output = np.zeros(output_length)

        for delay in comb_delays:
            buffer = np.zeros(output_length)
            buffer[:len(samples)] = samples

            feedback = 0.84 * (0.5 + self.room_size * 0.5)
            lp = 0.0  # Low-pass state

            for i in range(delay, output_length):
                lp = buffer[i - delay] * (1 - self.damping) + lp * self.damping
                buffer[i] += lp * feedback

            comb_output += buffer / len(comb_delays)

        # Process through series allpass filters
        output = comb_output
        for delay in allpass_delays:
            temp = np.zeros_like(output)
            g = 0.5

            for i in range(delay, len(output)):
                temp[i] = -g * output[i] + output[i - delay] + g * temp[i - delay]

            output = temp

        # Trim and mix
        output = output[:len(samples) + int(0.5 * sr)]  # Keep 0.5s tail

        # Mix dry and wet
        result = np.zeros(len(output))
        result[:len(samples)] = samples * (1 - self.mix)
        result += output * self.mix

        # Convert back to stereo if needed
        if audio.channels == 2:
            result = np.column_stack([result, result])

        return AudioData(result, audio.sample_rate, audio.channels)


@dataclass
class Chorus(AudioEffect):
    """Chorus effect using modulated delay lines."""
    rate: float = 1.5         # LFO rate in Hz
    depth: float = 0.002      # Modulation depth in seconds
    mix: float = 0.5          # Wet/dry mix
    voices: int = 2           # Number of chorus voices

    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples
        sr = audio.sample_rate
        length = len(samples)

        # Base delay
        base_delay = int(0.02 * sr)  # 20ms base delay
        max_mod = int(self.depth * sr)

        output = samples.copy()

        for voice in range(self.voices):
            # Each voice has different phase
            phase_offset = voice * 2 * np.pi / self.voices

            # Generate LFO
            t = np.arange(length) / sr
            lfo = np.sin(2 * np.pi * self.rate * t + phase_offset)
            delay_mod = base_delay + (lfo * max_mod).astype(int)

            # Apply modulated delay
            if audio.channels == 1:
                delayed = np.zeros_like(samples)
                for i in range(length):
                    idx = i - delay_mod[i]
                    if 0 <= idx < length:
                        delayed[i] = samples[idx]
            else:
                delayed = np.zeros_like(samples)
                for i in range(length):
                    idx = i - delay_mod[i]
                    if 0 <= idx < length:
                        delayed[i] = samples[idx]

            output = output + delayed * (self.mix / self.voices)

        # Normalize mix
        output = samples * (1 - self.mix) + output * self.mix

        return AudioData(output, audio.sample_rate, audio.channels)
