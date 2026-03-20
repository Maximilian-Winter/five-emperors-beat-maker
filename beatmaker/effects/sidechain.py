"""
Sidechain effects: SidechainCompressor, SidechainEnvelope, PumpingBass,
SidechainBuilder, SidechainPresets, create_sidechain.

The pumping breath of electronic music.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
import numpy as np

from ..core import AudioData, AudioEffect, Track


@dataclass
class SidechainCompressor(AudioEffect):
    """
    Sidechain compressor for that classic pumping effect.

    Uses a trigger signal (typically kick drum) to duck
    the main signal, creating the pumping effect.
    """
    threshold: float = -20.0  # dB - trigger threshold
    ratio: float = 8.0        # Compression ratio
    attack: float = 0.001     # Attack time in seconds (fast)
    release: float = 0.15     # Release time in seconds
    hold: float = 0.0         # Hold time before release
    range: float = -24.0      # Maximum gain reduction in dB

    _trigger: Optional[AudioData] = field(default=None, repr=False)

    def set_trigger(self, trigger: AudioData) -> 'SidechainCompressor':
        """Set the sidechain trigger signal."""
        self._trigger = trigger
        return self

    def process(self, audio: AudioData) -> AudioData:
        """Apply sidechain compression."""
        if self._trigger is None:
            return audio

        trigger = self._trigger

        # Resample trigger if needed
        if trigger.sample_rate != audio.sample_rate:
            trigger = trigger.resample(audio.sample_rate)

        # Get mono envelope from trigger
        if trigger.channels > 1:
            trigger_mono = np.mean(trigger.samples, axis=1)
        else:
            trigger_mono = trigger.samples

        # Extend or truncate trigger to match audio length
        if len(trigger_mono) < len(audio.samples):
            trigger_mono = np.pad(trigger_mono,
                                   (0, len(audio.samples) - len(trigger_mono)))
        else:
            trigger_mono = trigger_mono[:len(audio.samples)]

        # Convert threshold to linear
        threshold_linear = 10 ** (self.threshold / 20)
        range_linear = 10 ** (self.range / 20)

        # Calculate envelope from trigger
        envelope = np.abs(trigger_mono)

        # Smooth envelope with attack/release
        sr = audio.sample_rate
        attack_coef = np.exp(-1 / (self.attack * sr)) if self.attack > 0 else 0
        release_coef = np.exp(-1 / (self.release * sr)) if self.release > 0 else 0
        hold_samples = int(self.hold * sr)

        smoothed = np.zeros_like(envelope)
        smoothed[0] = envelope[0]
        hold_counter = 0

        for i in range(1, len(envelope)):
            if envelope[i] > smoothed[i-1]:
                smoothed[i] = attack_coef * smoothed[i-1] + (1 - attack_coef) * envelope[i]
                hold_counter = hold_samples
            else:
                if hold_counter > 0:
                    smoothed[i] = smoothed[i-1]
                    hold_counter -= 1
                else:
                    smoothed[i] = release_coef * smoothed[i-1] + (1 - release_coef) * envelope[i]

        # Calculate gain reduction
        gain = np.ones_like(smoothed)
        above = smoothed > threshold_linear

        # Apply ratio-based compression
        gain[above] = (
            threshold_linear *
            (smoothed[above] / threshold_linear) ** (1 / self.ratio)
        ) / smoothed[above]

        # Apply range limit
        gain = np.maximum(gain, range_linear)

        # Apply gain to audio
        if audio.channels == 1:
            output = audio.samples * gain
        else:
            output = audio.samples * gain[:, np.newaxis]

        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class SidechainEnvelope(AudioEffect):
    """
    Envelope-based sidechain effect.

    Creates pumping without needing a trigger signal -
    generates envelope based on tempo and pattern.
    """
    bpm: float = 120.0
    pattern: str = "1/4"  # Beat division ("1/4", "1/8", "1/2", "1/1")
    depth: float = 0.8    # How much to duck (0-1)
    attack: float = 0.01  # Attack curve (0-1, 0=instant)
    release: float = 0.5  # Release curve shape (0-1)
    shape: str = "exp"    # "exp", "linear", "log"
    offset: float = 0.0   # Phase offset in beats

    def _parse_pattern(self) -> float:
        """Convert pattern string to beat duration."""
        if '/' in self.pattern:
            num, denom = self.pattern.split('/')
            return float(num) / float(denom)
        return float(self.pattern)

    def _generate_envelope(self, duration: float, sample_rate: int) -> np.ndarray:
        """Generate the pumping envelope."""
        beat_duration = 60.0 / self.bpm
        pattern_duration = self._parse_pattern() * beat_duration

        num_samples = int(duration * sample_rate)
        envelope = np.ones(num_samples)

        t = np.arange(num_samples) / sample_rate

        # Apply offset
        t = t - (self.offset * beat_duration)

        # Calculate phase within each pattern cycle
        phase = (t % pattern_duration) / pattern_duration

        # Generate envelope shape
        attack_point = self.attack

        for i in range(num_samples):
            p = phase[i]

            if p < attack_point:
                # Attack phase - quick duck
                if self.shape == "exp":
                    env_val = 1.0 - self.depth * (1 - np.exp(-10 * p / attack_point))
                elif self.shape == "log":
                    env_val = 1.0 - self.depth * (p / attack_point) ** 0.5
                else:  # linear
                    env_val = 1.0 - self.depth * (p / attack_point)
            else:
                # Release phase
                release_phase = (p - attack_point) / (1 - attack_point)
                release_curve = release_phase ** (1 / (self.release + 0.1))

                if self.shape == "exp":
                    env_val = (1.0 - self.depth) + self.depth * (1 - np.exp(-3 * release_curve))
                elif self.shape == "log":
                    env_val = (1.0 - self.depth) + self.depth * release_curve ** 2
                else:
                    env_val = (1.0 - self.depth) + self.depth * release_curve

            envelope[i] = env_val

        return envelope

    def process(self, audio: AudioData) -> AudioData:
        """Apply envelope-based sidechain."""
        envelope = self._generate_envelope(audio.duration, audio.sample_rate)

        # Ensure envelope matches audio length exactly
        if len(envelope) != len(audio.samples):
            if len(envelope) > len(audio.samples):
                envelope = envelope[:len(audio.samples)]
            else:
                padded = np.ones(len(audio.samples))
                padded[:len(envelope)] = envelope
                envelope = padded

        if audio.channels == 1:
            output = audio.samples * envelope
        else:
            output = audio.samples * envelope[:, np.newaxis]

        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class PumpingBass(AudioEffect):
    """
    Specialized sidechain effect for bass that pumps with the kick.

    Combines filtering with volume ducking for cleaner low-end.
    """
    bpm: float = 120.0
    depth: float = 0.9
    release: float = 0.3
    filter_freq: float = 200.0  # Low-pass when ducked

    def process(self, audio: AudioData) -> AudioData:
        # Apply volume envelope
        sidechain = SidechainEnvelope(
            bpm=self.bpm,
            pattern="1/4",
            depth=self.depth,
            release=self.release
        )

        ducked = sidechain.process(audio)

        return ducked


class SidechainBuilder:
    """Fluent builder for sidechain effects."""

    def __init__(self):
        self._params = {
            'type': 'envelope',
            'bpm': 120.0,
            'depth': 0.8,
            'attack': 0.01,
            'release': 0.3,
            'pattern': '1/4',
            'shape': 'exp',
            'trigger': None,
        }

    def tempo(self, bpm: float) -> 'SidechainBuilder':
        self._params['bpm'] = bpm
        return self

    def depth(self, value: float) -> 'SidechainBuilder':
        """Set ducking depth (0-1)."""
        self._params['depth'] = value
        return self

    def attack(self, seconds: float) -> 'SidechainBuilder':
        self._params['attack'] = seconds
        return self

    def release(self, seconds: float) -> 'SidechainBuilder':
        self._params['release'] = seconds
        return self

    def quarter_notes(self) -> 'SidechainBuilder':
        self._params['pattern'] = '1/4'
        return self

    def eighth_notes(self) -> 'SidechainBuilder':
        self._params['pattern'] = '1/8'
        return self

    def half_notes(self) -> 'SidechainBuilder':
        self._params['pattern'] = '1/2'
        return self

    def pattern(self, value: str) -> 'SidechainBuilder':
        self._params['pattern'] = value
        return self

    def shape_exp(self) -> 'SidechainBuilder':
        self._params['shape'] = 'exp'
        return self

    def shape_linear(self) -> 'SidechainBuilder':
        self._params['shape'] = 'linear'
        return self

    def shape_log(self) -> 'SidechainBuilder':
        self._params['shape'] = 'log'
        return self

    def trigger(self, audio: AudioData) -> 'SidechainBuilder':
        """Use actual audio as trigger (true sidechain)."""
        self._params['type'] = 'compressor'
        self._params['trigger'] = audio
        return self

    def from_track(self, track: Track, sample_rate: int = 44100) -> 'SidechainBuilder':
        """Use a track's audio as trigger."""
        audio = track.render(sample_rate, 2)
        return self.trigger(audio)

    def build(self) -> AudioEffect:
        """Build the sidechain effect."""
        if self._params['type'] == 'compressor' and self._params['trigger']:
            sc = SidechainCompressor(
                attack=self._params['attack'],
                release=self._params['release'],
                range=-20 * self._params['depth'],
            )
            sc.set_trigger(self._params['trigger'])
            return sc
        else:
            return SidechainEnvelope(
                bpm=self._params['bpm'],
                pattern=self._params['pattern'],
                depth=self._params['depth'],
                attack=self._params['attack'],
                release=self._params['release'],
                shape=self._params['shape'],
            )


def create_sidechain() -> SidechainBuilder:
    """Create a sidechain effect builder."""
    return SidechainBuilder()


# Preset sidechain effects
class SidechainPresets:
    """Common sidechain presets."""

    @staticmethod
    def classic_house(bpm: float = 128) -> SidechainEnvelope:
        """Classic house pumping."""
        return SidechainEnvelope(
            bpm=bpm, pattern="1/4", depth=0.7,
            attack=0.01, release=0.4, shape="exp"
        )

    @staticmethod
    def heavy_edm(bpm: float = 128) -> SidechainEnvelope:
        """Heavy EDM pumping."""
        return SidechainEnvelope(
            bpm=bpm, pattern="1/4", depth=0.95,
            attack=0.005, release=0.5, shape="exp"
        )

    @staticmethod
    def subtle_groove(bpm: float = 120) -> SidechainEnvelope:
        """Subtle groove pumping."""
        return SidechainEnvelope(
            bpm=bpm, pattern="1/4", depth=0.3,
            attack=0.02, release=0.25, shape="linear"
        )

    @staticmethod
    def fast_trance(bpm: float = 140) -> SidechainEnvelope:
        """Fast trance gating."""
        return SidechainEnvelope(
            bpm=bpm, pattern="1/8", depth=0.6,
            attack=0.01, release=0.2, shape="exp"
        )

    @staticmethod
    def half_time(bpm: float = 140) -> SidechainEnvelope:
        """Half-time feel."""
        return SidechainEnvelope(
            bpm=bpm, pattern="1/2", depth=0.5,
            attack=0.02, release=0.6, shape="log"
        )
