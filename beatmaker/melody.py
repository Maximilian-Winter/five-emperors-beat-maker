"""
靈寶五帝策使編碼之法 - Melody & Phrase Module
The poetical science of melodic expression.

By the Vermilion Bird's authority,
Let phrases flow like rivers of light,
Each note a stepping stone across harmonic space,
急急如律令敕

This module provides first-class abstractions for melodic composition:
Notes, Phrases, and Melodies that can be transformed, combined,
and rendered into the existing beatmaker pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
import numpy as np

from .arpeggiator import note_name_to_midi


# ─── MIDI ↔ Name Conversion ────────────────────────────────────────────────

_NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_FLAT_TO_SHARP = {'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#',
                  'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B'}


def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name (e.g., 60 → 'C4')."""
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{_NOTE_NAMES[note_index]}{octave}"


# ─── Note ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Note:
    """
    A single musical note — the atom of melodic expression.

    Pitch is stored as a MIDI note number (0–127), with -1 denoting a rest.
    Duration is measured in beats.  Velocity ranges from 0.0 to 1.0.
    """
    pitch: int
    duration: float
    velocity: float = 1.0

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def from_name(cls, name: str, duration: float = 1.0,
                  velocity: float = 1.0) -> 'Note':
        """
        Create a Note from a note name string.

        Examples:
            Note.from_name("C4")
            Note.from_name("F#3", 0.5, 0.8)
            Note.from_name("Bb2", duration=2.0)
        """
        midi = note_name_to_midi(name)
        return cls(pitch=midi, duration=duration, velocity=velocity)

    @classmethod
    def rest(cls, duration: float = 1.0) -> 'Note':
        """Create a rest (silence) of the given duration in beats."""
        return cls(pitch=-1, duration=duration, velocity=0.0)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def is_rest(self) -> bool:
        """True if this note is a rest (silence)."""
        return self.pitch < 0

    @property
    def name(self) -> str:
        """Human-readable note name, e.g., 'C4' or 'R' for rests."""
        if self.is_rest:
            return 'R'
        return midi_to_note_name(self.pitch)

    # ── Transformations (return new Note) ────────────────────────────────

    def transpose(self, semitones: int) -> 'Note':
        """Return a copy transposed by the given number of semitones."""
        if self.is_rest:
            return Note(pitch=-1, duration=self.duration, velocity=self.velocity)
        return Note(
            pitch=max(0, min(127, self.pitch + semitones)),
            duration=self.duration,
            velocity=self.velocity,
        )

    def with_duration(self, duration: float) -> 'Note':
        """Return a copy with a different duration."""
        return Note(pitch=self.pitch, duration=duration, velocity=self.velocity)

    def with_velocity(self, velocity: float) -> 'Note':
        """Return a copy with a different velocity."""
        return Note(pitch=self.pitch, duration=self.duration, velocity=velocity)

    def __repr__(self) -> str:
        if self.is_rest:
            return f"Note(R, {self.duration})"
        return f"Note({self.name}, {self.duration}, vel={self.velocity:.2f})"


# ─── Phrase ─────────────────────────────────────────────────────────────────

@dataclass
class Phrase:
    """
    An ordered sequence of Notes — a reusable melodic idea.

    Phrases are the primary unit of melodic composition.  They can be
    transposed, reversed, inverted, augmented, diminished, combined,
    and repeated to build complex melodies from simple motifs.

    All transformation methods return new Phrase objects (immutable style).
    """
    name: str
    notes: List[Note] = field(default_factory=list)

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def from_string(cls, notation: str, name: str = "phrase") -> 'Phrase':
        """
        Parse concise melody notation into a Phrase.

        Format:  "NoteName:Duration NoteName:Duration ..."
        - Duration is in beats (float).
        - Omit ":Duration" to default to 1 beat (quarter note).
        - Use "R" or "r" for rests.

        Examples:
            Phrase.from_string("C4:1 D4:0.5 E4:0.5 R:1 G4:2")
            Phrase.from_string("E4 G4 A4 B4")   # all quarter notes
        """
        tokens = notation.strip().split()
        notes: List[Note] = []

        for token in tokens:
            if ':' in token:
                parts = token.split(':')
                note_str = parts[0]
                duration = float(parts[1])
                velocity = float(parts[2]) if len(parts) > 2 else 1.0
            else:
                note_str = token
                duration = 1.0
                velocity = 1.0

            if note_str.upper() == 'R':
                notes.append(Note.rest(duration))
            else:
                notes.append(Note.from_name(note_str, duration, velocity))

        return cls(name=name, notes=notes)

    @classmethod
    def from_notes(cls, note_names: List[str], duration: float = 1.0,
                   name: str = "phrase") -> 'Phrase':
        """
        Create a Phrase where all notes share the same duration.

        Example:
            Phrase.from_notes(["C4", "E4", "G4"], duration=0.5)
        """
        notes = [Note.from_name(n, duration) for n in note_names]
        return cls(name=name, notes=notes)

    @classmethod
    def from_midi_tuples(cls, tuples: List[tuple],
                         name: str = "phrase") -> 'Phrase':
        """
        Create from (midi_note, duration_beats) or
        (midi_note, duration_beats, velocity) tuples.

        Example:
            Phrase.from_midi_tuples([(60, 1.0), (64, 0.5, 0.8)])
        """
        notes: List[Note] = []
        for t in tuples:
            if len(t) == 2:
                midi, dur = t
                vel = 1.0
            else:
                midi, dur, vel = t[0], t[1], t[2]

            if midi < 0:
                notes.append(Note.rest(dur))
            else:
                notes.append(Note(pitch=int(midi), duration=dur, velocity=vel))
        return cls(name=name, notes=notes)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def total_duration(self) -> float:
        """Total duration in beats (sum of all note durations)."""
        return sum(n.duration for n in self.notes)

    @property
    def pitches(self) -> List[int]:
        """List of MIDI pitches (excluding rests)."""
        return [n.pitch for n in self.notes if not n.is_rest]

    def __len__(self) -> int:
        return len(self.notes)

    # ── Transformations (all return new Phrase) ──────────────────────────

    def transpose(self, semitones: int) -> 'Phrase':
        """Transpose all notes by the given number of semitones."""
        return Phrase(
            name=f"{self.name}_t{semitones:+d}",
            notes=[n.transpose(semitones) for n in self.notes],
        )

    def reverse(self) -> 'Phrase':
        """Reverse the order of notes."""
        return Phrase(
            name=f"{self.name}_rev",
            notes=list(reversed(self.notes)),
        )

    def invert(self, axis: Optional[int] = None) -> 'Phrase':
        """
        Melodic inversion — mirror pitches around an axis.

        If *axis* is None, the first sounding note's pitch is used.
        Rests are preserved unchanged.
        """
        if axis is None:
            # Find first non-rest note
            for n in self.notes:
                if not n.is_rest:
                    axis = n.pitch
                    break
            if axis is None:
                return Phrase(name=f"{self.name}_inv", notes=list(self.notes))

        inverted: List[Note] = []
        for n in self.notes:
            if n.is_rest:
                inverted.append(n)
            else:
                new_pitch = axis - (n.pitch - axis)
                new_pitch = max(0, min(127, new_pitch))
                inverted.append(Note(pitch=new_pitch, duration=n.duration,
                                     velocity=n.velocity))
        return Phrase(name=f"{self.name}_inv", notes=inverted)

    def retrograde_invert(self, axis: Optional[int] = None) -> 'Phrase':
        """Reverse + invert — a classic serial technique."""
        return self.reverse().invert(axis)

    def augment(self, factor: float = 2.0) -> 'Phrase':
        """Multiply all durations by *factor* (slow down)."""
        return Phrase(
            name=f"{self.name}_aug",
            notes=[Note(n.pitch, n.duration * factor, n.velocity)
                   for n in self.notes],
        )

    def diminish(self, factor: float = 2.0) -> 'Phrase':
        """Divide all durations by *factor* (speed up)."""
        return self.augment(1.0 / factor)

    def with_velocity(self, velocity: float) -> 'Phrase':
        """Set uniform velocity for all sounding notes."""
        return Phrase(
            name=self.name,
            notes=[Note(n.pitch, n.duration, velocity) if not n.is_rest
                   else n for n in self.notes],
        )

    def with_velocity_curve(self, curve: List[float]) -> 'Phrase':
        """
        Apply a velocity curve across all sounding notes.

        *curve* is linearly interpolated to match the number of
        sounding notes in the phrase.
        """
        sounding_indices = [i for i, n in enumerate(self.notes) if not n.is_rest]
        num_sounding = len(sounding_indices)
        if num_sounding == 0:
            return Phrase(name=self.name, notes=list(self.notes))

        # Interpolate curve to match number of sounding notes
        curve_arr = np.array(curve, dtype=float)
        interp_x = np.linspace(0, len(curve_arr) - 1, num_sounding)
        velocities = np.interp(interp_x, np.arange(len(curve_arr)), curve_arr)

        new_notes = list(self.notes)
        for idx, vel in zip(sounding_indices, velocities):
            n = new_notes[idx]
            new_notes[idx] = Note(n.pitch, n.duration, float(np.clip(vel, 0.0, 1.0)))

        return Phrase(name=self.name, notes=new_notes)

    def repeat(self, times: int) -> 'Phrase':
        """Repeat the phrase *times* times sequentially."""
        return Phrase(
            name=f"{self.name}_x{times}",
            notes=list(self.notes) * times,
        )

    # ── Combination ──────────────────────────────────────────────────────

    def then(self, other: 'Phrase') -> 'Phrase':
        """Concatenate: play self, then *other* sequentially."""
        return Phrase(
            name=f"{self.name}+{other.name}",
            notes=list(self.notes) + list(other.notes),
        )

    def __add__(self, other: 'Phrase') -> 'Phrase':
        """Operator overload for sequential combination."""
        return self.then(other)

    # ── Event conversion ─────────────────────────────────────────────────

    def to_events(self, start_beat: float = 0.0) -> List[Tuple[float, int, float, float]]:
        """
        Convert to a list of renderable events.

        Returns:
            List of (beat, midi_note, velocity, duration_beats) tuples.
            Rests are omitted (they simply advance the beat cursor).
        """
        events: List[Tuple[float, int, float, float]] = []
        current_beat = start_beat
        for note in self.notes:
            if not note.is_rest:
                events.append((current_beat, note.pitch, note.velocity, note.duration))
            current_beat += note.duration
        return events

    def __repr__(self) -> str:
        note_strs = [n.name for n in self.notes]
        return f"Phrase('{self.name}', [{', '.join(note_strs)}])"


# ─── Melody ─────────────────────────────────────────────────────────────────

class Melody:
    """
    A complete melody — phrases positioned along a beat timeline.

    Melody is the container that places Phrase objects at specific beats
    and converts the whole composition into a flat event list for rendering.
    """

    def __init__(self, name: str = "melody"):
        self.name = name
        self._entries: List[Tuple[float, Phrase]] = []

    def add(self, phrase: Phrase, start_beat: Optional[float] = None) -> 'Melody':
        """
        Add a phrase at a specific beat.

        If *start_beat* is None, the phrase is appended immediately after
        the last entry ends (auto-sequencing).
        """
        if start_beat is None:
            start_beat = self.total_duration
        self._entries.append((start_beat, phrase))
        return self

    def add_sequence(self, phrases: List[Phrase]) -> 'Melody':
        """Add multiple phrases end-to-end in order."""
        for phrase in phrases:
            self.add(phrase)
        return self

    @property
    def total_duration(self) -> float:
        """Total duration in beats."""
        if not self._entries:
            return 0.0
        return max(start + phrase.total_duration
                   for start, phrase in self._entries)

    @property
    def entries(self) -> List[Tuple[float, Phrase]]:
        """List of (start_beat, Phrase) entries."""
        return list(self._entries)

    def to_events(self) -> List[Tuple[float, int, float, float]]:
        """
        Convert the entire melody to a flat event list.

        Returns:
            List of (beat, midi_note, velocity, duration_beats) tuples,
            sorted by beat position.
        """
        all_events: List[Tuple[float, int, float, float]] = []
        for start_beat, phrase in self._entries:
            all_events.extend(phrase.to_events(start_beat))
        all_events.sort(key=lambda e: e[0])
        return all_events

    def __repr__(self) -> str:
        return f"Melody('{self.name}', {len(self._entries)} phrases, {self.total_duration} beats)"
