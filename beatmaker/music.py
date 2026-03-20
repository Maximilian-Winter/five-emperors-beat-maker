"""
靈寶五帝策使編碼之法 - Music Theory Utilities
The celestial constants and conversions that underpin all harmonic endeavour.

By the Yellow Dragon's authority,
Let all modules draw from one well of pitch and scale,
Foundation stable, balance perfect,
急急如律令敕

Shared music-theory primitives used across synthesis, melody, harmony,
and arpeggiator modules.  Consolidating them here eliminates circular
dependencies and provides a single source of truth for note ↔ MIDI ↔
frequency conversions, scale definitions, and chord shapes.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np


# ─── Note ↔ MIDI ↔ Frequency Conversions ─────────────────────────────────────

_NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_FLAT_TO_SHARP = {'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#',
                  'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B'}

# Common note frequencies (octaves 0-7)
NOTE_FREQS = {
    'C': [16.35, 32.70, 65.41, 130.81, 261.63, 523.25, 1046.50, 2093.00],
    'D': [18.35, 36.71, 73.42, 146.83, 293.66, 587.33, 1174.66, 2349.32],
    'E': [20.60, 41.20, 82.41, 164.81, 329.63, 659.25, 1318.51, 2637.02],
    'F': [21.83, 43.65, 87.31, 174.61, 349.23, 698.46, 1396.91, 2793.83],
    'G': [24.50, 49.00, 98.00, 196.00, 392.00, 783.99, 1567.98, 3135.96],
    'A': [27.50, 55.00, 110.00, 220.00, 440.00, 880.00, 1760.00, 3520.00],
    'B': [30.87, 61.74, 123.47, 246.94, 493.88, 987.77, 1975.53, 3951.07],
}


def note_name_to_midi(note: str) -> int:
    """
    Convert note name (e.g., 'C4', 'F#3', 'Bb2') to MIDI number.

    Examples:
        >>> note_name_to_midi('C4')
        60
        >>> note_name_to_midi('A4')
        69
        >>> note_name_to_midi('F#3')
        54
    """
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


def midi_to_note_name(midi_note: int) -> str:
    """
    Convert MIDI note number to note name (e.g., 60 → 'C4').

    Examples:
        >>> midi_to_note_name(60)
        'C4'
        >>> midi_to_note_name(69)
        'A4'
    """
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{_NOTE_NAMES[note_index]}{octave}"


def midi_to_freq(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz (A4 = 440 Hz)."""
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def freq_to_midi(frequency: float) -> int:
    """Convert frequency in Hz to nearest MIDI note number."""
    return int(round(69 + 12 * np.log2(frequency / 440.0)))


def note_to_freq(note: str) -> float:
    """
    Convert note name to frequency.

    Examples:
        >>> note_to_freq('A4')
        440.0
        >>> note_to_freq('C3')
        130.81
    """
    note_name = note[:-1].upper()
    octave = int(note[-1])

    if note_name not in NOTE_FREQS:
        # Handle sharps/flats
        base_note = note_name[0]
        if len(note_name) > 1 and note_name[1] == '#':
            base_idx = list(NOTE_FREQS.keys()).index(base_note)
            next_note = list(NOTE_FREQS.keys())[(base_idx + 1) % 7]
            freq = (NOTE_FREQS[base_note][octave] + NOTE_FREQS[next_note][octave]) / 2
            return freq
        elif len(note_name) > 1 and note_name[1] == 'B':
            # Flat: one semitone below base note
            freq = NOTE_FREQS[base_note][octave] / (2 ** (1 / 12))
            return freq
        raise ValueError(f"Unknown note: {note}")

    return NOTE_FREQS[note_name][octave]


# ─── Scale ────────────────────────────────────────────────────────────────────

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

    # Common scales (set after class definition)
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


# ─── ChordShape ──────────────────────────────────────────────────────────────

@dataclass
class ChordShape:
    """Define a chord by intervals from root."""
    name: str
    intervals: List[int]  # Semitones from root

    # Common chord shapes (set after class definition)
    MAJOR = None
    MINOR = None
    DIM = None
    AUG = None
    SUS2 = None
    SUS4 = None
    MAJOR7 = None
    MINOR7 = None
    DOM7 = None
    ADD9 = None


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
def _chord_custom(cls, name: str, intervals: list) -> 'ChordShape':
    """Create a custom chord shape from arbitrary semitone intervals."""
    return cls(name=name, intervals=intervals)


ChordShape.custom = _chord_custom
