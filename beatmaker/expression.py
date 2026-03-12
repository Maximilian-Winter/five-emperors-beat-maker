"""
靈寶五帝策使編碼之法 - Expression Module
The breath of life in mechanical music — the human touch.

By the White Emperor's authority,
Let perfection yield to beauty,
Timing waver, velocity breathe,
急急如律令敕

This module provides pitch expression (vibrato, bend, portamento),
humanization (timing jitter, velocity variation), groove templates,
and velocity curves — everything needed to make programmatic music
feel alive.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable
import numpy as np

from .core import AudioData, Track, SamplePlacement


# ─── Pitch Expression ───────────────────────────────────────────────────────

@dataclass
class Vibrato:
    """
    Vibrato — periodic pitch oscillation applied during a note.

    Creates a subtle pitch wavering that adds warmth and expressiveness,
    particularly for sustained notes.
    """
    rate: float = 5.0          # Oscillation rate in Hz
    depth: float = 0.5         # Depth in semitones
    delay: float = 0.1         # Seconds before vibrato onset

    def apply(self, audio: AudioData, base_freq: float) -> AudioData:
        """Apply vibrato to audio via phase modulation of the waveform."""
        samples = audio.samples.copy()
        sr = audio.sample_rate
        n = len(samples) if audio.channels == 1 else samples.shape[0]

        t = np.arange(n) / sr
        delay_samples = int(self.delay * sr)

        # Build modulation signal: ramp in after delay
        mod = np.zeros(n)
        if delay_samples < n:
            # Smooth onset ramp (100ms fade-in)
            ramp_samples = min(int(0.1 * sr), n - delay_samples)
            ramp = np.linspace(0, 1, ramp_samples)
            active_t = t[delay_samples:]
            mod_signal = self.depth * np.sin(2 * np.pi * self.rate * active_t)
            mod[delay_samples:] = mod_signal
            mod[delay_samples:delay_samples + ramp_samples] *= ramp

        # Convert semitone modulation to frequency ratio
        freq_ratio = 2.0 ** (mod / 12.0)

        # Apply via resampling (phase accumulation)
        phase = np.cumsum(freq_ratio) / sr * base_freq * 2 * np.pi
        modulated = np.sin(phase) * np.max(np.abs(samples)) if np.max(np.abs(samples)) > 0 else samples

        # Preserve original envelope shape
        env = np.abs(samples) if audio.channels == 1 else np.abs(samples).max(axis=1)
        env_smooth = np.convolve(env, np.ones(256) / 256, mode='same')
        mod_env = np.abs(modulated)
        mod_env_smooth = np.convolve(mod_env, np.ones(256) / 256, mode='same')

        # Normalize modulated to match original envelope
        scale = np.where(mod_env_smooth > 1e-6,
                         env_smooth / mod_env_smooth, 1.0)
        modulated *= scale

        if audio.channels == 1:
            return AudioData(modulated, sr)
        else:
            return AudioData(
                np.column_stack([modulated, modulated]),
                sr, audio.channels)


@dataclass
class PitchBend:
    """
    Pitch bend — a targeted pitch shift within a note's duration.

    Useful for slides, scoops, and falls.
    """
    start_offset: float = 0.0   # Start time as fraction of note duration (0..1)
    end_offset: float = 0.5     # End time as fraction of note duration (0..1)
    semitones: float = 2.0      # Bend amount in semitones

    def generate_curve(self, num_samples: int) -> np.ndarray:
        """
        Generate a per-sample pitch multiplier curve.

        Returns array of frequency multipliers (1.0 = no bend).
        """
        curve = np.ones(num_samples)
        start_idx = int(self.start_offset * num_samples)
        end_idx = int(self.end_offset * num_samples)
        start_idx = max(0, min(start_idx, num_samples))
        end_idx = max(start_idx, min(end_idx, num_samples))

        bend_length = end_idx - start_idx
        if bend_length > 0:
            bend_semitones = np.linspace(0, self.semitones, bend_length)
            curve[start_idx:end_idx] = 2.0 ** (bend_semitones / 12.0)

        # Hold bend value after bend region
        if end_idx < num_samples:
            curve[end_idx:] = 2.0 ** (self.semitones / 12.0)

        return curve


@dataclass
class Portamento:
    """
    Portamento / glide — smooth pitch transition between notes.

    Applied between consecutive notes in a phrase.
    """
    glide_time: float = 0.1    # Glide duration in seconds
    curve: str = 'exponential'  # 'linear' or 'exponential'

    def generate_glide(self, from_freq: float, to_freq: float,
                       sample_rate: int) -> np.ndarray:
        """
        Generate glide samples from one frequency to another.

        Returns audio samples (mono).
        """
        num_samples = int(self.glide_time * sample_rate)
        if num_samples <= 0:
            return np.array([])

        t = np.linspace(0, 1, num_samples)

        if self.curve == 'exponential':
            # Exponential frequency sweep
            freqs = from_freq * (to_freq / from_freq) ** t
        else:
            # Linear frequency sweep
            freqs = from_freq + (to_freq - from_freq) * t

        # Generate audio from frequency sweep
        phase = np.cumsum(2 * np.pi * freqs / sample_rate)
        return np.sin(phase)


@dataclass
class NoteExpression:
    """
    Full expression data for a single note.

    Bundle vibrato, pitch bend, and portamento into one container
    that can be attached to a Note.
    """
    vibrato: Optional[Vibrato] = None
    pitch_bend: Optional[PitchBend] = None
    portamento: Optional[Portamento] = None


# ─── Humanization ────────────────────────────────────────────────────────────

@dataclass
class Humanizer:
    """
    Add human-like imperfections to timing and velocity.

    Transforms perfectly quantized music into something that breathes.
    """
    timing_jitter: float = 0.01      # Max timing offset in seconds
    velocity_variation: float = 0.1   # Max velocity variation (0..1)
    seed: Optional[int] = None

    def apply_to_events(self, events: List[Tuple[float, int, float, float]],
                        bpm: float) -> List[Tuple[float, int, float, float]]:
        """
        Apply humanization to beat-based event tuples.

        Args:
            events: List of (beat, midi_note, velocity, duration) tuples
            bpm: song tempo (used for timing conversion)

        Returns:
            New list with humanized timing and velocity.
        """
        rng = np.random.RandomState(self.seed)
        beat_duration = 60.0 / bpm
        jitter_beats = self.timing_jitter / beat_duration

        humanized = []
        for beat, note, vel, dur in events:
            t_offset = rng.uniform(-jitter_beats, jitter_beats)
            new_beat = max(0, beat + t_offset)
            v_offset = rng.uniform(-self.velocity_variation,
                                   self.velocity_variation)
            new_vel = float(np.clip(vel + v_offset, 0.01, 1.0))
            humanized.append((new_beat, note, new_vel, dur))

        return humanized

    def apply_to_track(self, track: Track) -> Track:
        """
        Apply timing jitter to all placements in a track (in-place).

        Returns the same track for chaining.
        """
        rng = np.random.RandomState(self.seed)

        for placement in track.placements:
            t_offset = rng.uniform(-self.timing_jitter, self.timing_jitter)
            placement.time = max(0.0, placement.time + t_offset)
            v_offset = rng.uniform(-self.velocity_variation,
                                   self.velocity_variation)
            placement.velocity = float(np.clip(placement.velocity + v_offset,
                                               0.01, 1.0))
        return track


# ─── Groove Templates ────────────────────────────────────────────────────────

@dataclass
class GrooveTemplate:
    """
    A groove template — per-step timing and velocity offsets.

    Each position in the template maps to a 16th-note position
    within a bar (16 positions per bar in 4/4 time).  The offsets
    repeat cyclically across the duration of a track or pattern.
    """
    name: str
    timing_offsets: List[float]     # Timing shift per step (fraction of step duration)
    velocity_scales: List[float]    # Velocity multiplier per step

    @property
    def length(self) -> int:
        return len(self.timing_offsets)

    def apply_to_events(self, events: List[Tuple[float, int, float, float]],
                        bpm: float,
                        steps_per_beat: int = 4
                        ) -> List[Tuple[float, int, float, float]]:
        """
        Apply groove template to beat-based event tuples.

        Each event is quantized to its nearest step position, and the
        corresponding timing offset and velocity scale are applied.
        """
        step_duration_beats = 1.0 / steps_per_beat
        grooved = []

        for beat, note, vel, dur in events:
            # Determine which step this event falls on
            step_index = int(round(beat / step_duration_beats))
            groove_idx = step_index % self.length

            # Apply timing offset
            offset = self.timing_offsets[groove_idx] * step_duration_beats
            new_beat = max(0, beat + offset)

            # Apply velocity scale
            new_vel = float(np.clip(vel * self.velocity_scales[groove_idx],
                                    0.01, 1.0))

            grooved.append((new_beat, note, new_vel, dur))

        return grooved

    def apply_to_track(self, track: Track, bpm: float,
                       steps_per_beat: int = 4) -> Track:
        """
        Apply groove template to all placements in a track (in-place).

        Returns the same track for chaining.
        """
        beat_duration = 60.0 / bpm
        step_duration_sec = beat_duration / steps_per_beat

        for placement in track.placements:
            step_index = int(round(placement.time / step_duration_sec))
            groove_idx = step_index % self.length

            offset = self.timing_offsets[groove_idx] * step_duration_sec
            placement.time = max(0.0, placement.time + offset)

            placement.velocity = float(np.clip(
                placement.velocity * self.velocity_scales[groove_idx],
                0.01, 1.0))

        return track

    # ── Preset groove templates ──────────────────────────────────────────

    @classmethod
    def mpc_swing(cls, amount: float = 0.6) -> 'GrooveTemplate':
        """
        MPC-style swing — delays every other 16th note.

        amount: 0.5 = straight, 0.67 = classic swing, 1.0 = full triplet
        """
        swing_delay = (amount - 0.5) * 2  # Normalize to 0..1
        timing = [0.0, swing_delay * 0.5] * 8
        velocity = [1.0, 0.75] * 8
        return cls("mpc_swing", timing[:16], velocity[:16])

    @classmethod
    def funk(cls) -> 'GrooveTemplate':
        """Funk groove — pushed offbeats and syncopated accents."""
        timing = [
            0.0, -0.05, 0.0, 0.08,
            0.0, -0.03, 0.0, 0.06,
            0.0, -0.05, 0.0, 0.08,
            0.0, -0.03, 0.0, 0.06,
        ]
        velocity = [
            1.0, 0.5, 0.8, 0.6,
            0.9, 0.5, 0.7, 0.6,
            1.0, 0.5, 0.8, 0.6,
            0.9, 0.5, 0.7, 0.6,
        ]
        return cls("funk", timing, velocity)

    @classmethod
    def shuffle(cls, depth: float = 0.67) -> 'GrooveTemplate':
        """Shuffle / triplet feel — swing with emphasis on downbeats."""
        swing_delay = (depth - 0.5) * 2
        timing = [0.0, swing_delay * 0.33] * 8
        velocity = [1.0, 0.6] * 8
        return cls("shuffle", timing[:16], velocity[:16])

    @classmethod
    def lazy(cls) -> 'GrooveTemplate':
        """Laid-back feel — everything slightly behind the beat."""
        timing = [
            0.02, 0.04, 0.02, 0.03,
            0.02, 0.04, 0.02, 0.03,
            0.02, 0.04, 0.02, 0.03,
            0.02, 0.04, 0.02, 0.03,
        ]
        velocity = [
            0.9, 0.6, 0.8, 0.5,
            0.85, 0.55, 0.75, 0.5,
            0.9, 0.6, 0.8, 0.5,
            0.85, 0.55, 0.75, 0.5,
        ]
        return cls("lazy", timing, velocity)

    @classmethod
    def driving(cls) -> 'GrooveTemplate':
        """Driving/rushing feel — slightly ahead of the beat."""
        timing = [
            -0.02, -0.01, -0.02, -0.01,
            -0.02, -0.01, -0.02, -0.01,
            -0.02, -0.01, -0.02, -0.01,
            -0.02, -0.01, -0.02, -0.01,
        ]
        velocity = [
            1.0, 0.7, 0.9, 0.7,
            1.0, 0.7, 0.9, 0.7,
            1.0, 0.7, 0.9, 0.7,
            1.0, 0.7, 0.9, 0.7,
        ]
        return cls("driving", timing, velocity)

    @classmethod
    def hip_hop(cls) -> 'GrooveTemplate':
        """Hip-hop groove — heavy downbeats, lazy backbeats."""
        timing = [
            0.0, 0.03, 0.0, 0.05,
            0.02, 0.04, 0.0, 0.03,
            0.0, 0.03, 0.0, 0.05,
            0.02, 0.04, 0.0, 0.03,
        ]
        velocity = [
            1.0, 0.4, 0.6, 0.5,
            0.95, 0.4, 0.55, 0.5,
            1.0, 0.4, 0.6, 0.5,
            0.95, 0.4, 0.55, 0.5,
        ]
        return cls("hip_hop", timing, velocity)

    def __repr__(self) -> str:
        return f"GrooveTemplate('{self.name}', {self.length} steps)"


# ─── Velocity Curves ─────────────────────────────────────────────────────────

class VelocityCurve:
    """
    Maps input velocity to output velocity — shaping dynamics.

    Use these to add dynamic contour to flat-velocity sequences,
    or to remap the dynamic range of existing events.
    """

    @staticmethod
    def linear(velocity: float) -> float:
        """Identity mapping."""
        return velocity

    @staticmethod
    def exponential(velocity: float, power: float = 2.0) -> float:
        """Exponential curve — quieter soft, louder loud."""
        return float(velocity ** power)

    @staticmethod
    def logarithmic(velocity: float) -> float:
        """Logarithmic curve — louder soft, gentler loud."""
        return float(np.log1p(velocity * (np.e - 1)))

    @staticmethod
    def compressed(velocity: float, amount: float = 0.5) -> float:
        """Reduce dynamic range by mixing with constant."""
        return float(velocity * (1 - amount) + amount)

    @staticmethod
    def s_curve(velocity: float) -> float:
        """S-curve — accentuate extremes, flatten middle."""
        return float(3 * velocity ** 2 - 2 * velocity ** 3)

    @staticmethod
    def apply_to_events(events: List[Tuple[float, int, float, float]],
                        curve_fn: Callable[[float], float]
                        ) -> List[Tuple[float, int, float, float]]:
        """Apply a velocity curve function to all events."""
        return [(t, n, float(np.clip(curve_fn(v), 0.01, 1.0)), d)
                for t, n, v, d in events]
