"""
靈寶五帝策使編碼之法 - Core Audio Module
The foundation upon which all sound manifestations rest.

By the Yellow Dragon's authority,
Let these components unite in harmony,
Foundation stable, balance perfect,
急急如律令敕
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Callable, Iterator
import numpy as np
from abc import ABC, abstractmethod


class NoteValue(Enum):
    """Musical note durations relative to a whole note."""
    WHOLE = 1.0
    HALF = 0.5
    QUARTER = 0.25
    EIGHTH = 0.125
    SIXTEENTH = 0.0625
    THIRTY_SECOND = 0.03125
    DOTTED_HALF = 0.75
    DOTTED_QUARTER = 0.375
    DOTTED_EIGHTH = 0.1875
    TRIPLET_QUARTER = 1/6
    TRIPLET_EIGHTH = 1/12


class TrackType(Enum):
    """Classification of track purposes."""
    DRUMS = auto()
    BASS = auto()
    LEAD = auto()
    PAD = auto()
    VOCAL = auto()
    FX = auto()
    BACKING = auto()


@dataclass
class TimeSignature:
    """Musical time signature."""
    beats_per_bar: int = 4
    beat_value: int = 4  # 4 = quarter note gets one beat
    
    def beats_to_seconds(self, beats: float, bpm: float) -> float:
        """Convert beat count to seconds at given BPM."""
        return (beats * 60.0) / bpm
    
    def bars_to_seconds(self, bars: float, bpm: float) -> float:
        """Convert bar count to seconds at given BPM."""
        return self.beats_to_seconds(bars * self.beats_per_bar, bpm)


@dataclass
class AudioData:
    """
    Raw audio data container - the atomic unit of sound.
    
    Attributes:
        samples: numpy array of audio samples (mono or stereo)
        sample_rate: samples per second (typically 44100 or 48000)
        channels: 1 for mono, 2 for stereo
    """
    samples: np.ndarray
    sample_rate: int = 44100
    channels: int = 1
    
    def __post_init__(self):
        if self.samples.ndim == 1:
            self.channels = 1
        elif self.samples.ndim == 2:
            self.channels = self.samples.shape[1]
    
    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return len(self.samples) / self.sample_rate
    
    @property
    def num_samples(self) -> int:
        """Total number of samples."""
        return len(self.samples)
    
    def to_mono(self) -> 'AudioData':
        """Convert to mono by averaging channels."""
        if self.channels == 1:
            return self
        mono_samples = np.mean(self.samples, axis=1)
        return AudioData(mono_samples, self.sample_rate, 1)
    
    def to_stereo(self) -> 'AudioData':
        """Convert to stereo by duplicating mono channel."""
        if self.channels == 2:
            return self
        stereo_samples = np.column_stack([self.samples, self.samples])
        return AudioData(stereo_samples, self.sample_rate, 2)
    
    def normalize(self, peak: float = 0.95) -> 'AudioData':
        """Normalize audio to specified peak level."""
        max_val = np.max(np.abs(self.samples))
        if max_val > 0:
            normalized = self.samples * (peak / max_val)
            return AudioData(normalized, self.sample_rate, self.channels)
        return self
    
    def resample(self, target_rate: int) -> 'AudioData':
        """Resample to a different sample rate."""
        if self.sample_rate == target_rate:
            return self
        
        ratio = target_rate / self.sample_rate
        new_length = int(len(self.samples) * ratio)
        
        if self.channels == 1:
            resampled = np.interp(
                np.linspace(0, len(self.samples) - 1, new_length),
                np.arange(len(self.samples)),
                self.samples
            )
        else:
            resampled = np.zeros((new_length, self.channels))
            for ch in range(self.channels):
                resampled[:, ch] = np.interp(
                    np.linspace(0, len(self.samples) - 1, new_length),
                    np.arange(len(self.samples)),
                    self.samples[:, ch]
                )
        
        return AudioData(resampled, target_rate, self.channels)
    
    def slice(self, start_sec: float, end_sec: float) -> 'AudioData':
        """Extract a time slice of the audio."""
        start_sample = int(start_sec * self.sample_rate)
        end_sample = int(end_sec * self.sample_rate)
        return AudioData(
            self.samples[start_sample:end_sample].copy(),
            self.sample_rate,
            self.channels
        )
    
    def fade_in(self, duration: float) -> 'AudioData':
        """Apply linear fade in."""
        num_samples = int(duration * self.sample_rate)
        num_samples = min(num_samples, len(self.samples))
        
        fade = np.linspace(0, 1, num_samples)
        result = self.samples.copy()
        
        if self.channels == 1:
            result[:num_samples] *= fade
        else:
            result[:num_samples] *= fade[:, np.newaxis]
        
        return AudioData(result, self.sample_rate, self.channels)
    
    def fade_out(self, duration: float) -> 'AudioData':
        """Apply linear fade out."""
        num_samples = int(duration * self.sample_rate)
        num_samples = min(num_samples, len(self.samples))
        
        fade = np.linspace(1, 0, num_samples)
        result = self.samples.copy()
        
        if self.channels == 1:
            result[-num_samples:] *= fade
        else:
            result[-num_samples:] *= fade[:, np.newaxis]
        
        return AudioData(result, self.sample_rate, self.channels)
    
    @classmethod
    def silence(cls, duration: float, sample_rate: int = 44100, 
                channels: int = 1) -> 'AudioData':
        """Create silent audio of specified duration."""
        num_samples = int(duration * sample_rate)
        if channels == 1:
            samples = np.zeros(num_samples)
        else:
            samples = np.zeros((num_samples, channels))
        return cls(samples, sample_rate, channels)
    
    @classmethod
    def from_generator(cls, generator: Callable[[np.ndarray], np.ndarray],
                       duration: float, sample_rate: int = 44100) -> 'AudioData':
        """Create audio from a generator function."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        samples = generator(t)
        return cls(samples, sample_rate, 1)


@dataclass
class Sample:
    """
    A named audio sample - the building block of beats.
    
    Samples are immutable audio units with metadata that can be
    placed on tracks at specific times.
    """
    name: str
    audio: AudioData
    tags: List[str] = field(default_factory=list)
    root_note: Optional[int] = None  # MIDI note number
    
    @classmethod
    def from_file(cls, path: Path | str, name: Optional[str] = None) -> 'Sample':
        """Load a sample from an audio file."""
        from .io import load_audio
        path = Path(path)
        audio = load_audio(path)
        return cls(
            name=name or path.stem,
            audio=audio
        )
    
    @classmethod
    def from_synthesis(cls, name: str, generator: Callable[[np.ndarray], np.ndarray],
                       duration: float, sample_rate: int = 44100) -> 'Sample':
        """Create a sample from a synthesis function."""
        audio = AudioData.from_generator(generator, duration, sample_rate)
        return cls(name=name, audio=audio)
    
    def with_tags(self, *tags: str) -> 'Sample':
        """Return a copy with additional tags."""
        return Sample(
            name=self.name,
            audio=self.audio,
            tags=list(self.tags) + list(tags),
            root_note=self.root_note
        )
    
    def pitched(self, semitones: float) -> 'Sample':
        """Return a pitch-shifted copy (by resampling)."""
        ratio = 2 ** (semitones / 12)
        new_rate = int(self.audio.sample_rate * ratio)
        resampled = self.audio.resample(new_rate)
        # Resample back to original rate to change pitch
        final = AudioData(
            resampled.samples,
            self.audio.sample_rate,
            resampled.channels
        )
        return Sample(
            name=f"{self.name}_pitch{semitones:+.1f}",
            audio=final,
            tags=self.tags,
            root_note=self.root_note + int(semitones) if self.root_note else None
        )


@dataclass
class SamplePlacement:
    """A sample placed at a specific time with modifications."""
    sample: Sample
    time: float  # Start time in seconds
    velocity: float = 1.0  # Volume multiplier 0.0 - 1.0
    pan: float = 0.0  # -1.0 (left) to 1.0 (right)
    
    @property
    def end_time(self) -> float:
        """End time of this placement."""
        return self.time + self.sample.audio.duration


class AudioEffect(ABC):
    """Base class for audio effects."""
    
    @abstractmethod
    def process(self, audio: AudioData) -> AudioData:
        """Apply the effect to audio data."""
        pass


@dataclass
class Track:
    """
    A track containing placed samples with effects.

    Tracks are the organizational unit for grouping related sounds
    (e.g., all drums, bass line, vocals).
    """
    name: str
    track_type: TrackType = TrackType.DRUMS
    placements: List[SamplePlacement] = field(default_factory=list)
    effects: List[AudioEffect] = field(default_factory=list)
    volume: float = 1.0
    pan: float = 0.0
    muted: bool = False
    solo: bool = False
    volume_automation: Optional[object] = None  # AutomationCurve (optional)
    pan_automation: Optional[object] = None     # AutomationCurve (optional)
    
    def add(self, sample: Sample, time: float, 
            velocity: float = 1.0, pan: float = 0.0) -> 'Track':
        """Add a sample placement to the track."""
        self.placements.append(SamplePlacement(sample, time, velocity, pan))
        return self
    
    def add_at_beat(self, sample: Sample, beat: float, bpm: float,
                    velocity: float = 1.0, pan: float = 0.0) -> 'Track':
        """Add a sample at a specific beat position."""
        time = (beat * 60.0) / bpm
        return self.add(sample, time, velocity, pan)
    
    def add_pattern(self, sample: Sample, pattern: List[bool], 
                    step_duration: float, start_time: float = 0.0,
                    velocity: float = 1.0) -> 'Track':
        """Add a sample following a step pattern."""
        for i, hit in enumerate(pattern):
            if hit:
                time = start_time + (i * step_duration)
                self.add(sample, time, velocity)
        return self
    
    def add_effect(self, effect: AudioEffect) -> 'Track':
        """Add an effect to the track's effect chain."""
        self.effects.append(effect)
        return self
    
    @property
    def duration(self) -> float:
        """Total duration of the track."""
        if not self.placements:
            return 0.0
        return max(p.end_time for p in self.placements)
    
    def render(self, sample_rate: int = 44100, channels: int = 2,
               bpm: float = 120.0) -> AudioData:
        """
        Render all placements to a single AudioData.

        Args:
            sample_rate: output sample rate
            channels: 1 (mono) or 2 (stereo)
            bpm: song tempo (used for automation curves)
        """
        if not self.placements:
            return AudioData.silence(0.0, sample_rate, channels)

        duration = self.duration
        num_samples = int(duration * sample_rate) + sample_rate  # +1 sec buffer

        if channels == 1:
            output = np.zeros(num_samples)
        else:
            output = np.zeros((num_samples, channels))

        for placement in self.placements:
            audio = placement.sample.audio

            # Resample if needed
            if audio.sample_rate != sample_rate:
                audio = audio.resample(sample_rate)

            # Convert to target channel count
            if channels == 2 and audio.channels == 1:
                audio = audio.to_stereo()
            elif channels == 1 and audio.channels == 2:
                audio = audio.to_mono()

            # Apply velocity
            samples = audio.samples * placement.velocity * self.volume

            # Apply panning for stereo
            if channels == 2:
                total_pan = max(-1.0, min(1.0, placement.pan + self.pan))
                left_gain = np.sqrt(0.5 * (1 - total_pan))
                right_gain = np.sqrt(0.5 * (1 + total_pan))
                samples = samples.copy()
                samples[:, 0] *= left_gain
                samples[:, 1] *= right_gain

            # Place in output
            start_idx = int(placement.time * sample_rate)
            end_idx = start_idx + len(samples)

            if end_idx <= num_samples:
                output[start_idx:end_idx] += samples
            else:
                available = num_samples - start_idx
                output[start_idx:] += samples[:available]

        # Apply volume automation
        if self.volume_automation is not None:
            beat_duration = 60.0 / bpm
            duration_beats = duration / beat_duration
            vol_array = self.volume_automation.render(bpm, sample_rate, duration_beats)
            # Ensure length matches
            vol_len = min(len(vol_array), num_samples)
            if channels == 1:
                output[:vol_len] *= vol_array[:vol_len]
            else:
                output[:vol_len] *= vol_array[:vol_len, np.newaxis]

        # Apply pan automation
        if self.pan_automation is not None:
            beat_duration = 60.0 / bpm
            duration_beats = duration / beat_duration
            pan_array = self.pan_automation.render(bpm, sample_rate, duration_beats)
            pan_len = min(len(pan_array), num_samples)
            if channels == 2:
                left_gain = np.sqrt(0.5 * (1 - pan_array[:pan_len]))
                right_gain = np.sqrt(0.5 * (1 + pan_array[:pan_len]))
                output[:pan_len, 0] *= left_gain
                output[:pan_len, 1] *= right_gain

        # Apply effects
        result = AudioData(output, sample_rate, channels)
        for effect in self.effects:
            # Set automation context on automatable effects
            if hasattr(effect, 'set_context'):
                effect.set_context(bpm)
            result = effect.process(result)

        return result
    
    def clear(self) -> 'Track':
        """Remove all placements."""
        self.placements.clear()
        return self
    
    def __iter__(self) -> Iterator[SamplePlacement]:
        """Iterate over placements."""
        return iter(sorted(self.placements, key=lambda p: p.time))
