"""
靈寶五帝策使編碼之法 - Harmony & Key Module
The science of operations upon harmonic relations.

By the Yellow Dragon's authority,
Let chords progress as celestial spheres rotate,
Each degree a planet in the harmonic firmament,
急急如律令敕

This module provides a Key context, Roman numeral chord progressions,
voice leading, and diatonic harmonic analysis.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import re

# Music theory — canonical source is beatmaker.music
from .music import Scale, ChordShape, note_name_to_midi, midi_to_note_name


# ─── Constants ──────────────────────────────────────────────────────────────

_NOTE_NAMES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_NOTE_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Which root notes conventionally use flats
_FLAT_KEYS = {'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb',
              'Dm', 'Gm', 'Cm', 'Fm', 'Bbm', 'Ebm'}

# Triad quality for each degree of major scale (1-indexed)
_MAJOR_TRIAD_QUALITY = {
    1: 'major', 2: 'minor', 3: 'minor', 4: 'major',
    5: 'major', 6: 'minor', 7: 'dim',
}

# Triad quality for each degree of natural minor scale
_MINOR_TRIAD_QUALITY = {
    1: 'minor', 2: 'dim', 3: 'major', 4: 'minor',
    5: 'minor', 6: 'major', 7: 'major',
}

# Chord quality to ChordShape mapping
_QUALITY_TO_SHAPE: Dict[str, ChordShape] = {
    'major': ChordShape.MAJOR,
    'minor': ChordShape.MINOR,
    'dim': ChordShape.DIM,
    'aug': ChordShape.AUG,
}


def _root_name_to_pc(name: str) -> int:
    """Convert root name (e.g. 'C', 'F#', 'Bb') to pitch class 0-11."""
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    base = note_map.get(name[0].upper(), 0)
    if len(name) > 1:
        if name[1] == '#':
            base += 1
        elif name[1].lower() == 'b':
            base -= 1
    return base % 12


# ─── Key ────────────────────────────────────────────────────────────────────

@dataclass
class Key:
    """
    A musical key — the harmonic context for composition.

    Provides scale degrees, diatonic chord construction, modulation,
    and diatonic membership checks.
    """
    root: str
    scale: Scale

    def __post_init__(self):
        self._root_pc: int = _root_name_to_pc(self.root)

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def major(cls, root: str) -> 'Key':
        """Create a major key.  Example: Key.major('C')"""
        return cls(root=root, scale=Scale.MAJOR)

    @classmethod
    def minor(cls, root: str) -> 'Key':
        """Create a natural minor key.  Example: Key.minor('A')"""
        return cls(root=root, scale=Scale.MINOR)

    @classmethod
    def harmonic_minor(cls, root: str) -> 'Key':
        """Create a harmonic minor key."""
        return cls(root=root, scale=Scale.HARMONIC_MINOR)

    @classmethod
    def melodic_minor(cls, root: str) -> 'Key':
        """Create a melodic minor key."""
        return cls(root=root, scale=Scale.MELODIC_MINOR)

    @classmethod
    def dorian(cls, root: str) -> 'Key':
        return cls(root=root, scale=Scale.DORIAN)

    @classmethod
    def mixolydian(cls, root: str) -> 'Key':
        return cls(root=root, scale=Scale.MIXOLYDIAN)

    @classmethod
    def pentatonic_minor(cls, root: str) -> 'Key':
        return cls(root=root, scale=Scale.MINOR_PENTATONIC)

    @classmethod
    def pentatonic_major(cls, root: str) -> 'Key':
        return cls(root=root, scale=Scale.MAJOR_PENTATONIC)

    @classmethod
    def blues(cls, root: str) -> 'Key':
        return cls(root=root, scale=Scale.BLUES)

    # ── Scale degree access ──────────────────────────────────────────────

    @property
    def root_pc(self) -> int:
        """Root pitch class (0–11)."""
        return self._root_pc

    def degree_pc(self, degree: int) -> int:
        """
        Pitch class (0–11) for the given 1-indexed scale degree.

        Example: Key.major('C').degree_pc(5) → 7 (G)
        """
        idx = (degree - 1) % len(self.scale.intervals)
        octave_offset = (degree - 1) // len(self.scale.intervals)
        return (self._root_pc + self.scale.intervals[idx] + octave_offset * 12) % 12

    def degree(self, degree: int, octave: int = 4) -> int:
        """
        MIDI note for the given 1-indexed scale degree in the given octave.

        Example: Key.major('C').degree(1, 4) → 60 (middle C)
        """
        idx = (degree - 1) % len(self.scale.intervals)
        extra_octaves = (degree - 1) // len(self.scale.intervals)
        base_midi = (octave + 1) * 12 + self._root_pc
        return base_midi + self.scale.intervals[idx] + extra_octaves * 12

    def scale_notes(self, octave: int = 4) -> List[int]:
        """All MIDI notes in the key for a single octave."""
        return self.scale.get_notes(self.degree(1, octave), 1)

    def scale_notes_range(self, low_octave: int = 3,
                          high_octave: int = 5) -> List[int]:
        """All MIDI notes in the key across a range of octaves."""
        notes: List[int] = []
        for o in range(low_octave, high_octave + 1):
            notes.extend(self.scale_notes(o))
        return sorted(set(notes))

    # ── Diatonic chords ──────────────────────────────────────────────────

    def _diatonic_quality(self, degree: int) -> str:
        """Get the triad quality for a diatonic degree."""
        deg_1 = ((degree - 1) % 7) + 1
        if self.scale.name in ('major', 'lydian', 'mixolydian'):
            return _MAJOR_TRIAD_QUALITY.get(deg_1, 'major')
        elif self.scale.name in ('minor', 'dorian', 'phrygian', 'locrian',
                                  'harmonic_minor', 'melodic_minor'):
            return _MINOR_TRIAD_QUALITY.get(deg_1, 'minor')
        # Fallback: build from scale intervals
        return 'major'

    def chord(self, degree: int, extensions: int = 3,
              octave: int = 4) -> Tuple[int, ChordShape]:
        """
        Get a diatonic chord built on a scale degree.

        Args:
            degree: 1-indexed scale degree
            extensions: 3 = triad, 4 = seventh chord
            octave: base octave for the root

        Returns:
            (root_midi, ChordShape) tuple
        """
        root_midi = self.degree(degree, octave)

        if extensions >= 4:
            # Build seventh chord from scale intervals
            intervals = self._build_diatonic_intervals(degree, 4)
            quality = self._diatonic_quality(degree)
            shape_name = f"{quality}7"
            shape = ChordShape(shape_name, intervals)
        else:
            quality = self._diatonic_quality(degree)
            shape = _QUALITY_TO_SHAPE.get(quality, ChordShape.MAJOR)

        return (root_midi, shape)

    def _build_diatonic_intervals(self, degree: int, num_notes: int) -> List[int]:
        """Build diatonic chord intervals by stacking scale thirds."""
        intervals = [0]
        scale_len = len(self.scale.intervals)
        for i in range(1, num_notes):
            # Walk up the scale by 2 degrees (thirds)
            target_degree = degree + i * 2
            target_idx = (target_degree - 1) % scale_len
            target_octave = (target_degree - 1) // scale_len
            root_idx = (degree - 1) % scale_len
            root_octave = (degree - 1) // scale_len

            interval = (
                self.scale.intervals[target_idx] + target_octave * 12
                - self.scale.intervals[root_idx] - root_octave * 12
            )
            intervals.append(interval)
        return intervals

    def chord_name(self, degree: int) -> str:
        """
        Human-readable chord name for a diatonic degree.

        Example: Key.major('C').chord_name(2) → 'Dm'
        """
        pc = self.degree_pc(degree)
        use_flats = self.root in _FLAT_KEYS
        name_table = _NOTE_NAMES_FLAT if use_flats else _NOTE_NAMES_SHARP
        root_name = name_table[pc]
        quality = self._diatonic_quality(degree)

        suffix_map = {'major': '', 'minor': 'm', 'dim': 'dim', 'aug': 'aug'}
        return root_name + suffix_map.get(quality, '')

    # ── Modulation ───────────────────────────────────────────────────────

    def modulate(self, new_root: str,
                 new_scale: Optional[Scale] = None) -> 'Key':
        """Return a new Key modulated to *new_root*."""
        return Key(root=new_root, scale=new_scale or self.scale)

    def relative_minor(self) -> 'Key':
        """Return the relative minor of a major key (vi degree)."""
        minor_pc = (self._root_pc + 9) % 12
        use_flats = self.root in _FLAT_KEYS
        name_table = _NOTE_NAMES_FLAT if use_flats else _NOTE_NAMES_SHARP
        return Key(root=name_table[minor_pc], scale=Scale.MINOR)

    def relative_major(self) -> 'Key':
        """Return the relative major of a minor key (III degree)."""
        major_pc = (self._root_pc + 3) % 12
        use_flats = self.root in _FLAT_KEYS
        name_table = _NOTE_NAMES_FLAT if use_flats else _NOTE_NAMES_SHARP
        return Key(root=name_table[major_pc], scale=Scale.MAJOR)

    def parallel_minor(self) -> 'Key':
        """Same root, minor scale."""
        return Key(root=self.root, scale=Scale.MINOR)

    def parallel_major(self) -> 'Key':
        """Same root, major scale."""
        return Key(root=self.root, scale=Scale.MAJOR)

    # ── Utility ──────────────────────────────────────────────────────────

    def is_diatonic(self, midi_note: int) -> bool:
        """Check if a MIDI note belongs to this key."""
        pc = midi_note % 12
        for interval in self.scale.intervals:
            if (self._root_pc + interval) % 12 == pc:
                return True
        return False

    def nearest_diatonic(self, midi_note: int) -> int:
        """Snap a MIDI note to the nearest diatonic pitch."""
        if self.is_diatonic(midi_note):
            return midi_note

        # Try ±1 semitone, then ±2
        for offset in [1, -1, 2, -2]:
            candidate = midi_note + offset
            if self.is_diatonic(candidate):
                return candidate
        return midi_note  # fallback

    def __repr__(self) -> str:
        return f"Key({self.root} {self.scale.name})"


# ─── Roman Numeral Parsing ──────────────────────────────────────────────────

_ROMAN_VALUES = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7,
}

_ROMAN_PATTERN = re.compile(
    r'^(b|#)?'                  # optional accidental
    r'(III|VII|II|IV|VI|V|I'    # uppercase roman
    r'|iii|vii|ii|iv|vi|v|i)'   # lowercase roman
    r'(dim|aug|sus2|sus4)?'     # quality modifier
    r'(maj7|7|9|11|13)?'        # extension
    r'$'
)


def _parse_roman(numeral_str: str) -> Tuple[int, str, bool, str]:
    """
    Parse a Roman numeral string.

    Returns:
        (degree_1indexed, quality, is_minor, extension)
        quality: 'major'|'minor'|'dim'|'aug'|'sus2'|'sus4'
        extension: ''|'7'|'maj7'|'9'|'11'|'13'
    """
    numeral_str = numeral_str.strip()
    m = _ROMAN_PATTERN.match(numeral_str)
    if not m:
        raise ValueError(f"Cannot parse Roman numeral: '{numeral_str}'")

    accidental = m.group(1) or ''
    roman = m.group(2)
    quality_mod = m.group(3) or ''
    extension = m.group(4) or ''

    degree = _ROMAN_VALUES.get(roman, 1)

    # Case determines default quality
    is_lower = roman[0].islower()

    if quality_mod == 'dim':
        quality = 'dim'
    elif quality_mod == 'aug':
        quality = 'aug'
    elif quality_mod in ('sus2', 'sus4'):
        quality = quality_mod
    elif is_lower:
        quality = 'minor'
    else:
        quality = 'major'

    return (degree, quality, is_lower, extension)


def _quality_extension_to_shape(quality: str, extension: str) -> ChordShape:
    """Map quality + extension to a ChordShape."""
    if extension == 'maj7':
        if quality == 'major':
            return ChordShape.MAJOR7
        elif quality == 'minor':
            return ChordShape("minmaj7", [0, 3, 7, 11])
        return ChordShape.MAJOR7
    elif extension == '7':
        if quality == 'major':
            return ChordShape.DOM7
        elif quality == 'minor':
            return ChordShape.MINOR7
        elif quality == 'dim':
            return ChordShape("dim7", [0, 3, 6, 9])
        return ChordShape.DOM7
    elif extension == '9':
        if quality == 'major':
            return ChordShape("maj9", [0, 4, 7, 11, 14])
        elif quality == 'minor':
            return ChordShape("min9", [0, 3, 7, 10, 14])
        return ChordShape("dom9", [0, 4, 7, 10, 14])
    elif extension == '11':
        return ChordShape("11", [0, 4, 7, 10, 14, 17])
    elif extension == '13':
        return ChordShape("13", [0, 4, 7, 10, 14, 21])

    # No extension — triad
    shape_map = {
        'major': ChordShape.MAJOR,
        'minor': ChordShape.MINOR,
        'dim': ChordShape.DIM,
        'aug': ChordShape.AUG,
        'sus2': ChordShape.SUS2,
        'sus4': ChordShape.SUS4,
    }
    return shape_map.get(quality, ChordShape.MAJOR)


# ─── ChordProgression ──────────────────────────────────────────────────────

@dataclass
class ChordEntry:
    """A single chord in a progression."""
    degree: int
    shape: ChordShape
    root_midi: int
    duration_beats: float

    @property
    def midi_notes(self) -> List[int]:
        """MIDI notes of this chord."""
        return [self.root_midi + i for i in self.shape.intervals]


@dataclass
class ChordProgression:
    """
    A sequence of chords in a key.

    Supports Roman numeral notation, common presets,
    voice leading, and conversion to renderable events.
    """
    key: Key
    chords: List[ChordEntry] = field(default_factory=list)

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def from_roman(cls, key: Key, numerals: str,
                   beats_per_chord: float = 4.0,
                   octave: int = 3) -> 'ChordProgression':
        """
        Parse a chord progression from Roman numeral notation.

        Numerals are separated by ' - ' or spaces.
        Uppercase = major, lowercase = minor.

        Examples:
            "I - IV - V - I"
            "i - iv - v - i"
            "I - V - vi - IV"       (pop progression)
            "ii7 - V7 - Imaj7"     (jazz ii-V-I)
        """
        # Split on ' - ' or whitespace
        parts = [p.strip() for p in re.split(r'\s*-\s*|\s+', numerals) if p.strip()]

        entries: List[ChordEntry] = []
        for part in parts:
            degree, quality, _, extension = _parse_roman(part)
            shape = _quality_extension_to_shape(quality, extension)

            # Compute root MIDI from key degree
            root_midi = key.degree(degree, octave)

            entries.append(ChordEntry(
                degree=degree,
                shape=shape,
                root_midi=root_midi,
                duration_beats=beats_per_chord,
            ))

        return cls(key=key, chords=entries)

    @classmethod
    def from_degrees(cls, key: Key, degrees: List[int],
                     beats_per_chord: float = 4.0,
                     octave: int = 3) -> 'ChordProgression':
        """Create from a list of 1-indexed scale degree numbers (all triads)."""
        entries: List[ChordEntry] = []
        for deg in degrees:
            root_midi, shape = key.chord(deg, extensions=3, octave=octave)
            entries.append(ChordEntry(
                degree=deg, shape=shape,
                root_midi=root_midi,
                duration_beats=beats_per_chord,
            ))
        return cls(key=key, chords=entries)

    # ── Preset progressions ──────────────────────────────────────────────

    @classmethod
    def pop(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """I - V - vi - IV  (the ubiquitous pop progression)."""
        return cls.from_roman(key, "I - V - vi - IV", beats_per_chord)

    @classmethod
    def blues(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """12-bar blues: I I I I - IV IV I I - V IV I V"""
        return cls.from_roman(
            key, "I - I - I - I - IV - IV - I - I - V - IV - I - V",
            beats_per_chord)

    @classmethod
    def jazz_ii_v_i(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """ii7 - V7 - Imaj7"""
        return cls.from_roman(key, "ii7 - V7 - Imaj7", beats_per_chord)

    @classmethod
    def andalusian(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """i - VII - VI - V  (flamenco/Andalusian cadence)."""
        return cls.from_roman(key, "i - VII - VI - V", beats_per_chord)

    @classmethod
    def canon(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """I - V - vi - iii - IV - I - IV - V  (Pachelbel's Canon)."""
        return cls.from_roman(key, "I - V - vi - iii - IV - I - IV - V",
                              beats_per_chord)

    @classmethod
    def fifties(cls, key: Key, beats_per_chord: float = 4.0) -> 'ChordProgression':
        """I - vi - IV - V  (the '50s doo-wop progression)."""
        return cls.from_roman(key, "I - vi - IV - V", beats_per_chord)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def total_duration(self) -> float:
        """Total duration in beats."""
        return sum(c.duration_beats for c in self.chords)

    def __len__(self) -> int:
        return len(self.chords)

    # ── Voice leading ────────────────────────────────────────────────────

    def voice_lead(self, num_voices: int = 4,
                   base_octave: int = 3) -> List[List[int]]:
        """
        Generate voice-led MIDI notes for each chord.

        Uses minimal movement: each voice moves to the nearest available
        chord tone.  The first chord is arranged in close position from
        *base_octave*.

        Returns:
            List of chords, each a sorted list of MIDI notes.
        """
        if not self.chords:
            return []

        result: List[List[int]] = []

        # Arrange first chord in close position
        first = self.chords[0]
        first_notes = sorted(first.midi_notes[:num_voices])
        # Extend if fewer notes than voices
        while len(first_notes) < num_voices:
            first_notes.append(first_notes[-1] + 12)
        first_notes = first_notes[:num_voices]
        result.append(sorted(first_notes))

        # For subsequent chords: find nearest voicing
        prev_notes = first_notes
        for entry in self.chords[1:]:
            target_pcs = [(entry.root_midi + iv) % 12 for iv in entry.shape.intervals]
            # Extend target pitch classes if fewer than voices
            while len(target_pcs) < num_voices:
                target_pcs.append(target_pcs[0])
            target_pcs = target_pcs[:num_voices]

            new_notes: List[int] = []
            used_pcs = set()
            for prev_note in prev_notes:
                # Find nearest MIDI note from target pitch classes
                best_note = prev_note
                best_dist = 999
                for pc in target_pcs:
                    if pc in used_pcs and len(set(target_pcs)) > 1:
                        continue
                    # Candidate notes near prev_note
                    for octave_shift in range(-1, 2):
                        candidate = (prev_note // 12 + octave_shift) * 12 + pc
                        dist = abs(candidate - prev_note)
                        if dist < best_dist:
                            best_dist = dist
                            best_note = candidate
                new_notes.append(best_note)
                used_pcs.add(best_note % 12)

            result.append(sorted(new_notes))
            prev_notes = new_notes

        return result

    # ── Conversion ───────────────────────────────────────────────────────

    def to_arp_progression(self) -> List[Tuple[str, ChordShape]]:
        """
        Convert to format compatible with existing Arpeggiator.generate_from_progression().

        Returns list of (root_note_name, ChordShape) tuples.
        """
        entries = []
        for chord in self.chords:
            root_name = midi_to_note_name(chord.root_midi)
            entries.append((root_name, chord.shape))
        return entries

    def to_events(self, start_beat: float = 0.0,
                  voice_led: bool = False,
                  num_voices: int = 4) -> List[Tuple[float, int, float, float]]:
        """
        Convert to renderable note events.

        If *voice_led* is True, uses voice leading for smooth transitions.

        Returns:
            List of (beat, midi_note, velocity, duration_beats) tuples.
        """
        events: List[Tuple[float, int, float, float]] = []
        current_beat = start_beat

        if voice_led:
            voicings = self.voice_lead(num_voices)
            for i, entry in enumerate(self.chords):
                for midi_note in voicings[i]:
                    events.append((current_beat, midi_note, 0.8, entry.duration_beats))
                current_beat += entry.duration_beats
        else:
            for entry in self.chords:
                for midi_note in entry.midi_notes:
                    events.append((current_beat, midi_note, 0.8, entry.duration_beats))
                current_beat += entry.duration_beats

        return events

    def __repr__(self) -> str:
        names = [self.key.chord_name(c.degree) for c in self.chords]
        return f"ChordProgression({self.key}, [{' - '.join(names)}])"
