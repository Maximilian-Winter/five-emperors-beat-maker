"""
靈寶五帝策使編碼之法 - Arpeggiator Module
Melodic patterns that dance through harmonic space.

By the Vermilion Bird's authority,
Let notes cascade like sparks ascending,
Each tone igniting the next,
急急如律令敕
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Union
from enum import Enum, auto
import numpy as np

from .core import AudioData, Sample, Track, TrackType
from .synth import midi_to_freq, note_to_freq, ADSREnvelope


class ArpDirection(Enum):
    """Arpeggiator direction modes."""
    UP = auto()
    DOWN = auto()
    UP_DOWN = auto()
    DOWN_UP = auto()
    RANDOM = auto()
    ORDER = auto()  # As input


class ArpMode(Enum):
    """Arpeggiator note modes."""
    NORMAL = auto()
    OCTAVE = auto()      # Add octave above
    DOUBLE_OCTAVE = auto()  # Add two octaves
    POWER = auto()       # Root + fifth + octave


@dataclass
class ChordShape:
    """Define a chord by intervals from root."""
    name: str
    intervals: List[int]  # Semitones from root
    
    # Common chord shapes
    MAJOR = None  # Will be set after class definition
    MINOR = None
    DIM = None
    AUG = None
    SUS2 = None
    SUS4 = None
    MAJOR7 = None
    MINOR7 = None
    DOM7 = None
    ADD9 = None


# Define chord shapes after class
ChordShape.MAJOR = ChordShape("major", [0, 4, 7])
ChordShape.MINOR = ChordShape("minor", [0, 3, 7])
ChordShape.DIM = ChordShape("dim", [0, 3, 6])
ChordShape.AUG = ChordShape("aug", [0, 4, 8])
ChordShape.SUS2 = ChordShape("sus2", [0, 2, 7])
ChordShape.SUS4 = ChordShape("sus4", [0, 5, 7])
ChordShape.MAJOR7 = ChordShape("maj7", [0, 4, 7, 11])
ChordShape.MINOR7 = ChordShape("min7", [0, 3, 7, 10])
ChordShape.DOM7 = ChordShape("dom7", [0, 4, 7, 10])
ChordShape.ADD9 = ChordShape("add9", [0, 4, 7, 14])
ChordShape.DIM7 = ChordShape("dim7", [0, 3, 6, 9])
ChordShape.HALF_DIM7 = ChordShape("half_dim7", [0, 3, 6, 10])
ChordShape.MAJ9 = ChordShape("maj9", [0, 4, 7, 11, 14])
ChordShape.MIN9 = ChordShape("min9", [0, 3, 7, 10, 14])
ChordShape.DOM9 = ChordShape("dom9", [0, 4, 7, 10, 14])
ChordShape.ADD11 = ChordShape("add11", [0, 4, 7, 17])
ChordShape.MAJ13 = ChordShape("maj13", [0, 4, 7, 11, 14, 21])

@classmethod
def custom(cls, name: str, intervals: list) -> 'ChordShape':
    """Create a custom chord shape from arbitrary semitone intervals."""
    return cls(name=name, intervals=intervals)

ChordShape.custom = custom


@dataclass
class Scale:
    """Musical scale definition."""
    name: str
    intervals: List[int]  # Semitones from root
    
    def get_notes(self, root_midi: int, octaves: int = 1) -> List[int]:
        """Get MIDI notes for scale starting from root."""
        notes = []
        for octave in range(octaves):
            for interval in self.intervals:
                notes.append(root_midi + interval + (octave * 12))
        return notes
    
    # Common scales
    MAJOR = None
    MINOR = None
    DORIAN = None
    PHRYGIAN = None
    LYDIAN = None
    MIXOLYDIAN = None
    LOCRIAN = None
    MINOR_PENTATONIC = None
    MAJOR_PENTATONIC = None
    BLUES = None
    HARMONIC_MINOR = None
    MELODIC_MINOR = None


# Define scales
Scale.MAJOR = Scale("major", [0, 2, 4, 5, 7, 9, 11])
Scale.MINOR = Scale("minor", [0, 2, 3, 5, 7, 8, 10])
Scale.DORIAN = Scale("dorian", [0, 2, 3, 5, 7, 9, 10])
Scale.PHRYGIAN = Scale("phrygian", [0, 1, 3, 5, 7, 8, 10])
Scale.LYDIAN = Scale("lydian", [0, 2, 4, 6, 7, 9, 11])
Scale.MIXOLYDIAN = Scale("mixolydian", [0, 2, 4, 5, 7, 9, 10])
Scale.LOCRIAN = Scale("locrian", [0, 1, 3, 5, 6, 8, 10])
Scale.MINOR_PENTATONIC = Scale("minor_pent", [0, 3, 5, 7, 10])
Scale.MAJOR_PENTATONIC = Scale("major_pent", [0, 2, 4, 7, 9])
Scale.BLUES = Scale("blues", [0, 3, 5, 6, 7, 10])
Scale.HARMONIC_MINOR = Scale("harmonic_minor", [0, 2, 3, 5, 7, 8, 11])
Scale.MELODIC_MINOR = Scale("melodic_minor", [0, 2, 3, 5, 7, 9, 11])


def note_name_to_midi(note: str) -> int:
    """Convert note name (e.g., 'C4', 'F#3') to MIDI number."""
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    
    name = note[:-1].upper()
    octave = int(note[-1])
    
    base = note_map.get(name[0], 0)
    
    if len(name) > 1:
        if name[1] == '#':
            base += 1
        elif name[1] == 'B':
            base -= 1
    
    return base + (octave + 1) * 12


@dataclass
class Arpeggiator:
    """
    Musical arpeggiator for creating melodic patterns.
    
    Takes a chord or scale and creates rhythmic patterns from its notes.
    """
    bpm: float = 120.0
    direction: ArpDirection = ArpDirection.UP
    mode: ArpMode = ArpMode.NORMAL
    octaves: int = 1
    rate: float = 0.25  # Note duration in beats (0.25 = 16th notes)
    gate: float = 0.8  # Note length as fraction of rate
    swing: float = 0.0
    velocity_pattern: Optional[List[float]] = None
    
    def _apply_mode(self, notes: List[int]) -> List[int]:
        """Apply mode transformations to notes."""
        if self.mode == ArpMode.NORMAL:
            return notes
        elif self.mode == ArpMode.OCTAVE:
            return notes + [n + 12 for n in notes]
        elif self.mode == ArpMode.DOUBLE_OCTAVE:
            return notes + [n + 12 for n in notes] + [n + 24 for n in notes]
        elif self.mode == ArpMode.POWER:
            # Add fifth and octave for each note
            result = []
            for n in notes:
                result.extend([n, n + 7, n + 12])
            return result
        return notes
    
    def _apply_octaves(self, notes: List[int]) -> List[int]:
        """Extend notes across octaves."""
        result = []
        for octave in range(self.octaves):
            for note in notes:
                result.append(note + octave * 12)
        return result
    
    def _apply_direction(self, notes: List[int]) -> List[int]:
        """Apply direction to note sequence."""
        if self.direction == ArpDirection.UP:
            return sorted(notes)
        elif self.direction == ArpDirection.DOWN:
            return sorted(notes, reverse=True)
        elif self.direction == ArpDirection.UP_DOWN:
            up = sorted(notes)
            down = sorted(notes, reverse=True)[1:-1]  # Exclude endpoints
            return up + down
        elif self.direction == ArpDirection.DOWN_UP:
            down = sorted(notes, reverse=True)
            up = sorted(notes)[1:-1]
            return down + up
        elif self.direction == ArpDirection.RANDOM:
            shuffled = notes.copy()
            np.random.shuffle(shuffled)
            return shuffled
        else:  # ORDER - as input
            return notes
    
    def generate_pattern(self, notes: List[int], beats: int = 4) -> List[tuple]:
        """
        Generate arpeggio events.
        
        Args:
            notes: List of MIDI note numbers
            beats: Pattern length in beats
        
        Returns:
            List of (time, midi_note, velocity, duration) tuples
        """
        # Apply transformations
        processed = self._apply_mode(notes)
        processed = self._apply_octaves(processed)
        processed = self._apply_direction(processed)
        
        if not processed:
            return []
        
        events = []
        beat_duration = 60.0 / self.bpm
        note_duration = self.rate * beat_duration * self.gate
        
        # Calculate number of notes that fit
        total_time = beats * beat_duration
        time = 0.0
        note_index = 0
        step = 0
        
        while time < total_time:
            midi_note = processed[note_index % len(processed)]
            
            # Get velocity
            if self.velocity_pattern:
                velocity = self.velocity_pattern[step % len(self.velocity_pattern)]
            else:
                velocity = 1.0
            
            # Apply swing to off-beats
            actual_time = time
            if self.swing > 0 and step % 2 == 1:
                actual_time += self.rate * beat_duration * self.swing * 0.5
            
            events.append((actual_time, midi_note, velocity, note_duration))
            
            time += self.rate * beat_duration
            note_index += 1
            step += 1
        
        return events
    
    def generate_from_chord(self, root: Union[str, int], 
                            chord: ChordShape,
                            beats: int = 4) -> List[tuple]:
        """Generate arpeggio from a chord."""
        if isinstance(root, str):
            root_midi = note_name_to_midi(root)
        else:
            root_midi = root
        
        notes = [root_midi + interval for interval in chord.intervals]
        return self.generate_pattern(notes, beats)
    
    def generate_from_scale(self, root: Union[str, int],
                            scale: Scale,
                            beats: int = 4) -> List[tuple]:
        """Generate arpeggio from a scale."""
        if isinstance(root, str):
            root_midi = note_name_to_midi(root)
        else:
            root_midi = root
        
        notes = scale.get_notes(root_midi, 1)
        return self.generate_pattern(notes, beats)
    
    def generate_from_progression(self, progression: List[tuple],
                                   beats_per_chord: int = 4) -> List[tuple]:
        """
        Generate arpeggio from chord progression.
        
        Args:
            progression: List of (root, chord_shape) tuples
            beats_per_chord: Beats per chord
        
        Example:
            progression = [
                ('C3', ChordShape.MAJOR),
                ('G3', ChordShape.MAJOR),
                ('A3', ChordShape.MINOR),
                ('F3', ChordShape.MAJOR),
            ]
        """
        events = []
        time_offset = 0.0
        beat_duration = 60.0 / self.bpm
        
        for root, chord in progression:
            chord_events = self.generate_from_chord(root, chord, beats_per_chord)
            
            # Offset events
            for time, note, vel, dur in chord_events:
                events.append((time + time_offset, note, vel, dur))
            
            time_offset += beats_per_chord * beat_duration
        
        return events


@dataclass
class ArpeggiatorBuilder:
    """Fluent builder for arpeggiator configuration."""
    
    _arp: Arpeggiator = field(default_factory=Arpeggiator)
    
    def tempo(self, bpm: float) -> 'ArpeggiatorBuilder':
        self._arp.bpm = bpm
        return self
    
    def up(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.UP
        return self
    
    def down(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.DOWN
        return self
    
    def up_down(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.UP_DOWN
        return self
    
    def down_up(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.DOWN_UP
        return self
    
    def random(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.RANDOM
        return self
    
    def as_played(self) -> 'ArpeggiatorBuilder':
        self._arp.direction = ArpDirection.ORDER
        return self
    
    def rate(self, beats: float) -> 'ArpeggiatorBuilder':
        """Set note rate in beats (0.25 = 16th, 0.5 = 8th, 1 = quarter)."""
        self._arp.rate = beats
        return self
    
    def sixteenth(self) -> 'ArpeggiatorBuilder':
        return self.rate(0.25)
    
    def eighth(self) -> 'ArpeggiatorBuilder':
        return self.rate(0.5)
    
    def quarter(self) -> 'ArpeggiatorBuilder':
        return self.rate(1.0)
    
    def triplet(self) -> 'ArpeggiatorBuilder':
        return self.rate(1/3)
    
    def gate(self, value: float) -> 'ArpeggiatorBuilder':
        """Set gate length (0-1, fraction of note duration)."""
        self._arp.gate = value
        return self
    
    def staccato(self) -> 'ArpeggiatorBuilder':
        return self.gate(0.3)
    
    def legato(self) -> 'ArpeggiatorBuilder':
        return self.gate(1.0)
    
    def octaves(self, num: int) -> 'ArpeggiatorBuilder':
        self._arp.octaves = num
        return self
    
    def swing(self, amount: float) -> 'ArpeggiatorBuilder':
        self._arp.swing = amount
        return self
    
    def with_octave(self) -> 'ArpeggiatorBuilder':
        self._arp.mode = ArpMode.OCTAVE
        return self
    
    def with_double_octave(self) -> 'ArpeggiatorBuilder':
        self._arp.mode = ArpMode.DOUBLE_OCTAVE
        return self
    
    def power_chords(self) -> 'ArpeggiatorBuilder':
        self._arp.mode = ArpMode.POWER
        return self
    
    def velocity_pattern(self, pattern: List[float]) -> 'ArpeggiatorBuilder':
        self._arp.velocity_pattern = pattern
        return self
    
    def accent_downbeat(self) -> 'ArpeggiatorBuilder':
        """Accent every 4th note."""
        return self.velocity_pattern([1.0, 0.6, 0.7, 0.6])
    
    def build(self) -> Arpeggiator:
        return self._arp


def create_arpeggiator() -> ArpeggiatorBuilder:
    """Create a new arpeggiator builder."""
    return ArpeggiatorBuilder()


class ArpSynthesizer:
    """
    Synthesizer that works with arpeggiator events.
    
    Converts MIDI note events to audio.
    """
    
    def __init__(self, 
                 waveform: str = 'saw',
                 envelope: Optional[ADSREnvelope] = None,
                 sample_rate: int = 44100):
        self.waveform = waveform
        self.envelope = envelope or ADSREnvelope(0.01, 0.1, 0.7, 0.1)
        self.sample_rate = sample_rate
    
    def render_note(self, midi_note: int, duration: float, 
                    velocity: float = 1.0) -> AudioData:
        """Render a single note."""
        from .synth import sine_wave, sawtooth_wave, square_wave, triangle_wave
        
        freq = midi_to_freq(midi_note)
        
        if self.waveform == 'sine':
            audio = sine_wave(freq, duration, self.sample_rate)
        elif self.waveform == 'saw':
            audio = sawtooth_wave(freq, duration, self.sample_rate)
        elif self.waveform == 'square':
            audio = square_wave(freq, duration, self.sample_rate)
        elif self.waveform == 'triangle':
            audio = triangle_wave(freq, duration, self.sample_rate)
        else:
            audio = sawtooth_wave(freq, duration, self.sample_rate)
        
        # Apply envelope
        audio = self.envelope.apply(audio)
        
        # Apply velocity
        audio.samples *= velocity
        
        return audio
    
    def render_events(self, events: List[tuple]) -> AudioData:
        """Render a list of arpeggiator events to audio."""
        if not events:
            return AudioData.silence(0.0, self.sample_rate)
        
        # Calculate total duration
        max_time = max(time + dur for time, _, _, dur in events)
        total_samples = int(max_time * self.sample_rate) + self.sample_rate
        
        output = np.zeros(total_samples)
        
        for time, midi_note, velocity, duration in events:
            note_audio = self.render_note(midi_note, duration, velocity)
            
            start_idx = int(time * self.sample_rate)
            end_idx = start_idx + len(note_audio.samples)
            
            if end_idx <= total_samples:
                output[start_idx:end_idx] += note_audio.samples
            else:
                available = total_samples - start_idx
                output[start_idx:] += note_audio.samples[:available]
        
        return AudioData(output, self.sample_rate)


# Convenience functions
def arp_chord(root: str, chord: ChordShape, beats: int = 4,
              direction: ArpDirection = ArpDirection.UP,
              rate: float = 0.25, bpm: float = 120) -> List[tuple]:
    """Quick arpeggio generation from a chord."""
    arp = Arpeggiator(bpm=bpm, direction=direction, rate=rate)
    return arp.generate_from_chord(root, chord, beats)


def arp_scale(root: str, scale: Scale, beats: int = 4,
              direction: ArpDirection = ArpDirection.UP,
              rate: float = 0.25, bpm: float = 120) -> List[tuple]:
    """Quick arpeggio generation from a scale."""
    arp = Arpeggiator(bpm=bpm, direction=direction, rate=rate)
    return arp.generate_from_scale(root, scale, beats)
