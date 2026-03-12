"""
靈寶五帝策使編碼之法 - Automation Module
The art of parameters in motion — time-varying control.

By the Black Emperor's authority,
Let values flow like rivers through time,
No parameter need remain static,
急急如律令敕

This module provides automation curves that can be attached to
any parameter — track volume, pan, effect cutoff, or any numerical
value — to make it evolve over the duration of a song.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum, auto
from abc import abstractmethod
import numpy as np

from .core import AudioData, AudioEffect


# ─── Curve Types ────────────────────────────────────────────────────────────

class CurveType(Enum):
    """Interpolation method between automation breakpoints."""
    LINEAR = auto()
    EXPONENTIAL = auto()
    LOGARITHMIC = auto()
    STEP = auto()
    SMOOTH = auto()  # Cosine interpolation


# ─── AutomationPoint ────────────────────────────────────────────────────────

@dataclass
class AutomationPoint:
    """A single automation breakpoint at a specific beat."""
    beat: float
    value: float
    curve: CurveType = CurveType.LINEAR


# ─── AutomationCurve ────────────────────────────────────────────────────────

@dataclass
class AutomationCurve:
    """
    A curve of parameter values over time (in beats).

    Automation curves define how a parameter changes across the
    duration of a track or song.  They can be attached to track
    volume, pan, or any effect parameter that supports automation.
    """
    name: str
    points: List[AutomationPoint] = field(default_factory=list)
    default_value: float = 0.0

    # ── Building ─────────────────────────────────────────────────────────

    def add_point(self, beat: float, value: float,
                  curve: CurveType = CurveType.LINEAR) -> 'AutomationCurve':
        """Add a breakpoint at the given beat."""
        self.points.append(AutomationPoint(beat, value, curve))
        self.points.sort(key=lambda p: p.beat)
        return self

    def ramp(self, start_beat: float, end_beat: float,
             start_value: float, end_value: float,
             curve: CurveType = CurveType.LINEAR) -> 'AutomationCurve':
        """Add a ramp (two breakpoints) between two values."""
        self.add_point(start_beat, start_value, curve)
        self.add_point(end_beat, end_value, curve)
        return self

    def lfo(self, start_beat: float, end_beat: float,
            center: float, depth: float, rate_hz: float,
            waveform: str = 'sine',
            bpm: float = 120.0) -> 'AutomationCurve':
        """
        Generate LFO-style automation by adding many breakpoints.

        Args:
            start_beat, end_beat: range in beats
            center: center value
            depth: amplitude of oscillation
            rate_hz: oscillation rate in Hz
            waveform: 'sine', 'triangle', 'square', 'saw'
            bpm: tempo (needed to convert beats to time)
        """
        beat_duration = 60.0 / bpm
        num_points = max(32, int((end_beat - start_beat) * 4))
        beats = np.linspace(start_beat, end_beat, num_points)

        for b in beats:
            t = (b - start_beat) * beat_duration
            phase = 2 * np.pi * rate_hz * t

            if waveform == 'sine':
                mod = np.sin(phase)
            elif waveform == 'triangle':
                mod = 2 * np.abs(2 * ((t * rate_hz) % 1.0) - 1.0) - 1.0
            elif waveform == 'square':
                mod = 1.0 if np.sin(phase) >= 0 else -1.0
            elif waveform == 'saw':
                mod = 2 * ((t * rate_hz) % 1.0) - 1.0
            else:
                mod = np.sin(phase)

            value = center + depth * float(mod)
            self.points.append(AutomationPoint(float(b), value, CurveType.LINEAR))

        self.points.sort(key=lambda p: p.beat)
        return self

    # ── Sampling ─────────────────────────────────────────────────────────

    def sample_at(self, beat: float) -> float:
        """Get the interpolated value at a specific beat."""
        if not self.points:
            return self.default_value

        # Before first point
        if beat <= self.points[0].beat:
            return self.points[0].value

        # After last point
        if beat >= self.points[-1].beat:
            return self.points[-1].value

        # Find surrounding points
        for i in range(len(self.points) - 1):
            p0 = self.points[i]
            p1 = self.points[i + 1]
            if p0.beat <= beat <= p1.beat:
                return self._interpolate(p0, p1, beat)

        return self.default_value

    def _interpolate(self, p0: AutomationPoint, p1: AutomationPoint,
                     beat: float) -> float:
        """Interpolate between two points."""
        if p1.beat == p0.beat:
            return p1.value

        t = (beat - p0.beat) / (p1.beat - p0.beat)  # 0..1

        if p0.curve == CurveType.LINEAR:
            return p0.value + t * (p1.value - p0.value)

        elif p0.curve == CurveType.EXPONENTIAL:
            # Avoid log(0) issues
            if p0.value <= 0:
                return p0.value + (t ** 2) * (p1.value - p0.value)
            ratio = p1.value / max(p0.value, 1e-6)
            return p0.value * (ratio ** t)

        elif p0.curve == CurveType.LOGARITHMIC:
            return p0.value + np.log1p(t * (np.e - 1)) * (p1.value - p0.value)

        elif p0.curve == CurveType.STEP:
            return p0.value  # Hold until next point

        elif p0.curve == CurveType.SMOOTH:
            # Cosine interpolation
            t_smooth = (1 - np.cos(t * np.pi)) / 2
            return p0.value + t_smooth * (p1.value - p0.value)

        return p0.value + t * (p1.value - p0.value)

    def render(self, bpm: float, sample_rate: int,
               duration_beats: float) -> np.ndarray:
        """
        Render the automation curve to a per-sample numpy array.

        Args:
            bpm: song tempo
            sample_rate: audio sample rate
            duration_beats: total length in beats

        Returns:
            1D numpy array of values, one per audio sample.
        """
        beat_duration = 60.0 / bpm
        total_seconds = duration_beats * beat_duration
        num_samples = int(total_seconds * sample_rate)

        if num_samples <= 0:
            return np.array([self.default_value])

        output = np.zeros(num_samples)
        for i in range(num_samples):
            time_sec = i / sample_rate
            beat = time_sec / beat_duration
            output[i] = self.sample_at(beat)

        return output

    # ── Preset curves ────────────────────────────────────────────────────

    @classmethod
    def fade_in(cls, beats: float) -> 'AutomationCurve':
        """Volume fade in over the given number of beats."""
        return cls("fade_in", default_value=0.0).ramp(0, beats, 0.0, 1.0)

    @classmethod
    def fade_out(cls, start_beat: float, duration: float) -> 'AutomationCurve':
        """Volume fade out starting at *start_beat*."""
        return cls("fade_out", default_value=1.0).ramp(
            start_beat, start_beat + duration, 1.0, 0.0)

    @classmethod
    def filter_sweep(cls, start_beat: float, end_beat: float,
                     start_freq: float, end_freq: float) -> 'AutomationCurve':
        """Exponential filter cutoff sweep."""
        return cls("filter_sweep", default_value=start_freq).ramp(
            start_beat, end_beat, start_freq, end_freq, CurveType.EXPONENTIAL)

    @classmethod
    def swell(cls, peak_beat: float, peak_value: float = 1.0,
              start_value: float = 0.0) -> 'AutomationCurve':
        """Rise to peak_beat then fall back — a crescendo-decrescendo."""
        return (cls("swell", default_value=start_value)
                .ramp(0, peak_beat, start_value, peak_value, CurveType.SMOOTH)
                .ramp(peak_beat, peak_beat * 2, peak_value, start_value, CurveType.SMOOTH))

    def __repr__(self) -> str:
        return f"AutomationCurve('{self.name}', {len(self.points)} points)"


# ─── AutomatableEffect ──────────────────────────────────────────────────────

class AutomatableEffect(AudioEffect):
    """
    An audio effect whose parameters can be automated over time.

    Subclasses define which parameters are automatable by checking
    _automations in their process() method.
    """

    def __init__(self):
        self._automations: Dict[str, AutomationCurve] = {}
        self._bpm: float = 120.0
        self._start_beat: float = 0.0

    def automate(self, param_name: str,
                 curve: AutomationCurve) -> 'AutomatableEffect':
        """Attach an automation curve to a named parameter."""
        self._automations[param_name] = curve
        return self

    def set_context(self, bpm: float, start_beat: float = 0.0) -> None:
        """Set the temporal context for rendering automation."""
        self._bpm = bpm
        self._start_beat = start_beat

    def _get_param_array(self, param_name: str, default: float,
                         num_samples: int, sample_rate: int) -> np.ndarray:
        """
        Get per-sample parameter values.

        If the parameter has an automation curve attached, renders it;
        otherwise returns a constant array.
        """
        if param_name in self._automations:
            beat_duration = 60.0 / self._bpm
            duration_beats = (num_samples / sample_rate) / beat_duration
            return self._automations[param_name].render(
                self._bpm, sample_rate, duration_beats)
        return np.full(num_samples, default)

    @abstractmethod
    def process(self, audio: AudioData) -> AudioData:
        pass


# ─── Concrete Automated Effects ─────────────────────────────────────────────

class AutomatedGain(AutomatableEffect):
    """
    Gain effect with automatable level.

    Automatable parameters: 'level'
    """

    def __init__(self, level: float = 1.0):
        super().__init__()
        self.level = level

    def process(self, audio: AudioData) -> AudioData:
        n = len(audio.samples) if audio.channels == 1 else len(audio.samples)
        gain_arr = self._get_param_array('level', self.level, n, audio.sample_rate)

        if audio.channels == 1:
            return AudioData(audio.samples * gain_arr, audio.sample_rate)
        else:
            return AudioData(
                audio.samples * gain_arr[:len(audio.samples), np.newaxis],
                audio.sample_rate, audio.channels)


class AutomatedFilter(AutomatableEffect):
    """
    Low-pass filter with automatable cutoff frequency.

    Automatable parameters: 'cutoff', 'resonance'

    Uses a biquad filter with per-block coefficient updates for
    time-varying cutoff.
    """

    def __init__(self, cutoff: float = 1000.0, resonance: float = 0.707):
        super().__init__()
        self.cutoff = cutoff
        self.resonance = resonance

    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples.copy()
        sr = audio.sample_rate
        n = len(samples)

        cutoff_arr = self._get_param_array('cutoff', self.cutoff, n, sr)
        res_arr = self._get_param_array('resonance', self.resonance, n, sr)

        # Block-based processing for efficiency (update coefficients every 64 samples)
        block_size = 64
        if audio.channels == 1:
            output = self._filter_mono(samples, cutoff_arr, res_arr, sr, block_size)
        else:
            # Process each channel
            left = self._filter_mono(samples[:, 0], cutoff_arr, res_arr, sr, block_size)
            right = self._filter_mono(samples[:, 1], cutoff_arr, res_arr, sr, block_size)
            output = np.column_stack([left, right])

        return AudioData(output, sr, audio.channels)

    def _filter_mono(self, samples: np.ndarray, cutoff: np.ndarray,
                     resonance: np.ndarray, sr: int,
                     block_size: int) -> np.ndarray:
        """Apply time-varying lowpass filter to mono signal."""
        n = len(samples)
        output = np.zeros(n)

        # State variables for biquad
        x1 = x2 = y1 = y2 = 0.0

        for start in range(0, n, block_size):
            end = min(start + block_size, n)
            mid = (start + end) // 2

            # Compute coefficients at block midpoint
            fc = float(np.clip(cutoff[mid], 20.0, sr / 2 - 1))
            q = float(np.clip(resonance[mid], 0.1, 10.0))

            w0 = 2 * np.pi * fc / sr
            alpha = np.sin(w0) / (2 * q)

            b0 = (1 - np.cos(w0)) / 2
            b1 = 1 - np.cos(w0)
            b2 = b0
            a0 = 1 + alpha
            a1 = -2 * np.cos(w0)
            a2 = 1 - alpha

            # Normalize
            b0 /= a0
            b1 /= a0
            b2 /= a0
            a1 /= a0
            a2 /= a0

            for i in range(start, end):
                x0 = samples[i]
                y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
                output[i] = y0
                x2, x1 = x1, x0
                y2, y1 = y1, y0

        return output
