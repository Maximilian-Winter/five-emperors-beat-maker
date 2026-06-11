"""
Unified chord and chord progression representations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from scaler_framework.theory.constants import (
    NOTE_NAMES, CHORD_TEMPLATES, CHORD_SYMBOL_MAP,
    note_name_to_pc, pc_to_name,
)


@dataclass
class Chord:
    """
    A chord with root, quality, and duration.

    Can be constructed from a symbol string:
        Chord.from_string("Cmaj7")
        Chord.from_string("F#m7", duration_beats=2.0)

    Or directly:
        Chord(root=0, quality="maj7", duration_beats=4.0)
    """
    root: int               # pitch class 0-11
    quality: str            # key into CHORD_TEMPLATES
    duration_beats: float = 4.0

    @property
    def intervals(self) -> tuple[int, ...]:
        return CHORD_TEMPLATES.get(self.quality, (0, 4, 7))

    @property
    def pitch_classes(self) -> set[int]:
        return {(self.root + iv) % 12 for iv in self.intervals}

    @property
    def name(self) -> str:
        suffix = self.quality if self.quality != "maj" else ""
        return f"{pc_to_name(self.root)}{suffix}"

    @property
    def symbol(self) -> str:
        return f"{pc_to_name(self.root)}{self.quality}"

    @classmethod
    def from_string(cls, symbol: str, duration_beats: float = 4.0) -> Chord:
        """Parse chord symbol like 'Cmaj7', 'F#m7', 'Bb7', 'Dsus4'."""
        symbol = symbol.strip()
        if not symbol:
            raise ValueError("Empty chord symbol")

        # Extract root note (1 or 2 chars)
        if len(symbol) >= 2 and symbol[1] in ('#', 'b'):
            root_str = symbol[:2]
            suffix = symbol[2:]
        else:
            root_str = symbol[0]
            suffix = symbol[1:]

        root_pc = note_name_to_pc(root_str)

        # Match suffix to chord quality (try longest match first)
        quality = None
        for length in range(len(suffix), -1, -1):
            candidate = suffix[:length]
            if candidate in CHORD_SYMBOL_MAP:
                quality = CHORD_SYMBOL_MAP[candidate]
                break

        if quality is None:
            quality = "maj"

        return cls(root=root_pc, quality=quality, duration_beats=duration_beats)

    @classmethod
    def from_detection(cls, root: int, chord_type: str,
                       start_tick: int = 0, end_tick: int = 0,
                       confidence: float = 1.0, inversion: int = 0,
                       ticks_per_beat: int = 480) -> DetectedChord:
        """Create a DetectedChord from detection results."""
        duration = (end_tick - start_tick) / ticks_per_beat if ticks_per_beat else 0
        return DetectedChord(
            root=root, quality=chord_type, duration_beats=duration,
            start_tick=start_tick, end_tick=end_tick,
            confidence=confidence, inversion=inversion,
        )

    def __repr__(self):
        return f"Chord({self.name}, {self.duration_beats}b)"


@dataclass
class DetectedChord(Chord):
    """A chord with detection metadata (timing, confidence, inversion)."""
    start_tick: int = 0
    end_tick: int = 0
    confidence: float = 1.0
    inversion: int = 0
    source_notes: list = field(default_factory=list)

    @property
    def duration_ticks(self) -> int:
        return self.end_tick - self.start_tick

    def __repr__(self):
        inv_str = f" inv:{self.inversion}" if self.inversion else ""
        return f"{self.symbol} [{self.confidence:.0%}]{inv_str}"


@dataclass
class ChordProgression:
    """
    An ordered sequence of chords with a tempo.

    Create from a string:
        ChordProgression.from_string("Cmaj7 | Am7 | Dm7 | G7")
        ChordProgression.from_string("C Am F G", beats_per_chord=2)
    """
    chords: list[Chord] = field(default_factory=list)
    bpm: float = 120.0

    @classmethod
    def from_string(cls, progression: str, beats_per_chord: float = 4.0,
                    bpm: float = 120.0) -> ChordProgression:
        """Parse 'Cmaj7 | Am7 | Dm7 | G7' or 'C Am F G'."""
        progression = progression.replace("|", " ")
        tokens = progression.split()
        chords = [Chord.from_string(t, beats_per_chord) for t in tokens if t.strip()]
        return cls(chords=chords, bpm=bpm)

    @classmethod
    def from_detected(cls, detected: list[DetectedChord],
                      ticks_per_beat: int = 480, bpm: float = 120.0) -> ChordProgression:
        """Build a progression from detected chords."""
        chords = []
        for dc in detected:
            dur = dc.duration_ticks / ticks_per_beat if ticks_per_beat else 4.0
            chords.append(Chord(root=dc.root, quality=dc.quality, duration_beats=dur))
        return cls(chords=chords, bpm=bpm)

    @property
    def total_beats(self) -> float:
        return sum(c.duration_beats for c in self.chords)

    def chord_at_beat(self, beat: float) -> Chord:
        """Return which chord is active at a given beat position."""
        acc = 0.0
        for chord in self.chords:
            if acc + chord.duration_beats > beat:
                return chord
            acc += chord.duration_beats
        return self.chords[-1]

    def symbols(self) -> list[str]:
        return [c.name for c in self.chords]

    def __repr__(self):
        return " | ".join(c.name for c in self.chords)

    def __len__(self):
        return len(self.chords)

    def __iter__(self):
        return iter(self.chords)

    def __getitem__(self, idx):
        return self.chords[idx]
