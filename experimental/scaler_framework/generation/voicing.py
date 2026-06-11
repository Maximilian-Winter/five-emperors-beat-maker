"""
Chord voicing engine.

Transforms abstract chords (root + quality) into concrete MIDI note
sets with specific voicing styles: close position, open, drop-2,
drop-3, spread, guitar-style, piano-style, etc.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

from scaler_framework.theory.constants import CHORD_TEMPLATES, pc_to_name
from scaler_framework.theory.chord import Chord


class VoicingStyle(Enum):
    CLOSE = "close"           # all notes within one octave
    OPEN = "open"             # spread across ~2 octaves
    DROP_2 = "drop_2"         # second voice from top dropped an octave
    DROP_3 = "drop_3"         # third voice from top dropped an octave
    SPREAD = "spread"         # wide spacing, root + fifth low, upper extensions high
    PIANO_LH = "piano_lh"    # left hand: root + fifth in bass register
    PIANO_RH = "piano_rh"    # right hand: 3rd, 7th, extensions
    PIANO_FULL = "piano_full" # both hands combined
    GUITAR = "guitar"         # guitar-friendly open voicing
    PAD = "pad"               # dense pad voicing across 2 octaves
    POWER = "power"           # root + fifth only (power chord)
    SHELL = "shell"           # root + 3rd + 7th (jazz shell voicing)


@dataclass
class VoicedChord:
    """A chord realized as specific MIDI note numbers."""
    chord: Chord
    style: VoicingStyle
    notes: list[int]         # MIDI note numbers, sorted low to high
    bass_note: int           # lowest note (may differ from notes[0] if separate bass)

    @property
    def note_names(self) -> list[str]:
        return [f"{pc_to_name(n % 12)}{n // 12 - 1}" for n in self.notes]

    def __repr__(self):
        names = ", ".join(self.note_names)
        return f"VoicedChord({self.chord.name} {self.style.value}: [{names}])"


class VoicingEngine:
    """
    Generates voiced chords from abstract Chord objects.

    Usage:
        engine = VoicingEngine()
        chord = Chord.from_string("Cmaj7")
        voiced = engine.voice(chord, style=VoicingStyle.DROP_2, octave=4)
        print(voiced.notes)      # [48, 59, 64, 67]
        print(voiced.note_names) # ['C3', 'B3', 'E4', 'G4']
    """

    def voice(self, chord: Chord, style: VoicingStyle = VoicingStyle.CLOSE,
              octave: int = 4, inversion: int = 0) -> VoicedChord:
        """
        Voice a chord.

        Args:
            chord: The abstract chord to voice.
            style: Voicing style.
            octave: Base octave (MIDI octave, middle C = octave 4 = MIDI 60).
            inversion: 0 = root position, 1 = first inversion, etc.
        """
        base_midi = (octave + 1) * 12  # octave 4 -> MIDI 60
        intervals = list(chord.intervals)

        # Build close-position notes in root position
        close_notes = [(chord.root + iv) % 12 + base_midi for iv in intervals]
        # Ensure ascending order
        for i in range(1, len(close_notes)):
            while close_notes[i] <= close_notes[i - 1]:
                close_notes[i] += 12

        # Apply inversion (rotate lowest notes up an octave)
        for _ in range(inversion % len(close_notes)):
            close_notes.append(close_notes.pop(0) + 12)

        # Apply voicing style
        if style == VoicingStyle.CLOSE:
            notes = close_notes

        elif style == VoicingStyle.OPEN:
            notes = self._open_voicing(close_notes)

        elif style == VoicingStyle.DROP_2:
            notes = self._drop_n(close_notes, 2)

        elif style == VoicingStyle.DROP_3:
            notes = self._drop_n(close_notes, 3)

        elif style == VoicingStyle.SPREAD:
            notes = self._spread_voicing(chord, base_midi)

        elif style == VoicingStyle.PIANO_LH:
            notes = self._piano_lh(chord, base_midi)

        elif style == VoicingStyle.PIANO_RH:
            notes = self._piano_rh(chord, base_midi)

        elif style == VoicingStyle.PIANO_FULL:
            lh = self._piano_lh(chord, base_midi)
            rh = self._piano_rh(chord, base_midi)
            notes = sorted(set(lh + rh))

        elif style == VoicingStyle.GUITAR:
            notes = self._guitar_voicing(chord, base_midi)

        elif style == VoicingStyle.PAD:
            notes = self._pad_voicing(chord, base_midi)

        elif style == VoicingStyle.POWER:
            notes = self._power_chord(chord, base_midi)

        elif style == VoicingStyle.SHELL:
            notes = self._shell_voicing(chord, base_midi)

        else:
            notes = close_notes

        notes = sorted(notes)
        bass = notes[0] if notes else base_midi + chord.root

        return VoicedChord(chord=chord, style=style, notes=notes, bass_note=bass)

    def voice_progression(self, chords: list[Chord],
                          style: VoicingStyle = VoicingStyle.CLOSE,
                          octave: int = 4,
                          voice_lead: bool = True) -> list[VoicedChord]:
        """
        Voice a sequence of chords with optional voice leading optimization.

        When voice_lead=True, inversions are chosen to minimize the total
        movement between consecutive chords.
        """
        if not chords:
            return []

        voiced = [self.voice(chords[0], style=style, octave=octave)]

        for chord in chords[1:]:
            if voice_lead:
                # Try all inversions, pick the one closest to previous voicing
                best_inv = 0
                best_dist = float('inf')
                n_inv = len(chord.intervals)
                for inv in range(n_inv):
                    candidate = self.voice(chord, style=style, octave=octave, inversion=inv)
                    dist = self._voice_leading_distance(voiced[-1].notes, candidate.notes)
                    if dist < best_dist:
                        best_dist = dist
                        best_inv = inv
                voiced.append(self.voice(chord, style=style, octave=octave, inversion=best_inv))
            else:
                voiced.append(self.voice(chord, style=style, octave=octave))

        return voiced

    # --- Voicing implementations ---

    def _open_voicing(self, close_notes: list[int]) -> list[int]:
        """Every other note raised an octave."""
        notes = list(close_notes)
        for i in range(1, len(notes), 2):
            notes[i] += 12
        return notes

    def _drop_n(self, close_notes: list[int], n: int) -> list[int]:
        """Drop the nth voice from the top down an octave."""
        if len(close_notes) < n:
            return close_notes
        notes = sorted(close_notes, reverse=True)
        if n - 1 < len(notes):
            notes[n - 1] -= 12
        return notes

    def _spread_voicing(self, chord: Chord, base_midi: int) -> list[int]:
        """Root low, fifth mid, upper tones high."""
        intervals = list(chord.intervals)
        notes = []
        # Root in bass (octave below base)
        notes.append((chord.root % 12) + base_midi - 12)
        # Fifth in mid register if present
        if 7 in intervals:
            notes.append((chord.root + 7) % 12 + base_midi)
        # Other tones in upper register
        for iv in intervals:
            if iv not in (0, 7):
                notes.append((chord.root + iv) % 12 + base_midi + 12)
        return notes

    def _piano_lh(self, chord: Chord, base_midi: int) -> list[int]:
        """Left hand: root + fifth in bass register."""
        root = (chord.root % 12) + base_midi - 12
        fifth = (chord.root + 7) % 12 + base_midi - 12
        if fifth <= root:
            fifth += 12
        return [root, fifth]

    def _piano_rh(self, chord: Chord, base_midi: int) -> list[int]:
        """Right hand: 3rd, 7th, and extensions."""
        intervals = list(chord.intervals)
        # Exclude root and fifth for right hand
        rh_intervals = [iv for iv in intervals if iv not in (0, 7)]
        if not rh_intervals:
            rh_intervals = [iv for iv in intervals if iv != 0]
        notes = []
        for iv in rh_intervals:
            n = (chord.root + iv) % 12 + base_midi
            notes.append(n)
        # Ensure ascending
        for i in range(1, len(notes)):
            while notes[i] <= notes[i - 1]:
                notes[i] += 12
        return notes

    def _guitar_voicing(self, chord: Chord, base_midi: int) -> list[int]:
        """Guitar-friendly: open strings style, ~6 notes across 2 octaves."""
        intervals = list(chord.intervals)
        notes = []
        # Bass note
        notes.append((chord.root % 12) + base_midi - 12)
        # Build up through the chord tones across range
        for octave_offset in [0, 12]:
            for iv in intervals[:4]:  # max 4 chord tones per octave
                n = (chord.root + iv) % 12 + base_midi + octave_offset
                if n not in notes:
                    notes.append(n)
        return sorted(notes)[:6]  # guitar has 6 strings

    def _pad_voicing(self, chord: Chord, base_midi: int) -> list[int]:
        """Dense pad: chord tones doubled across 2 octaves."""
        intervals = list(chord.intervals)
        notes = []
        for octave_offset in [-12, 0, 12]:
            for iv in intervals:
                n = (chord.root + iv) % 12 + base_midi + octave_offset
                if n not in notes:
                    notes.append(n)
        return sorted(notes)

    def _power_chord(self, chord: Chord, base_midi: int) -> list[int]:
        """Root + fifth + octave."""
        root = (chord.root % 12) + base_midi - 12
        fifth = root + 7
        octave = root + 12
        return [root, fifth, octave]

    def _shell_voicing(self, chord: Chord, base_midi: int) -> list[int]:
        """Jazz shell: root + 3rd + 7th (skip the 5th)."""
        intervals = list(chord.intervals)
        notes = [(chord.root % 12) + base_midi - 12]  # root in bass

        # Find the 3rd (interval 3 or 4)
        third = next((iv for iv in intervals if iv in (3, 4)), None)
        if third is not None:
            notes.append((chord.root + third) % 12 + base_midi)

        # Find the 7th (interval 10 or 11)
        seventh = next((iv for iv in intervals if iv in (10, 11)), None)
        if seventh is not None:
            n = (chord.root + seventh) % 12 + base_midi
            if n <= notes[-1]:
                n += 12
            notes.append(n)

        return notes

    # --- Voice leading ---

    def _voice_leading_distance(self, prev_notes: list[int],
                                next_notes: list[int]) -> float:
        """Sum of absolute pitch movement between two voiced chords."""
        if not prev_notes or not next_notes:
            return float('inf')
        # Pad shorter list
        p = list(prev_notes)
        n = list(next_notes)
        while len(p) < len(n):
            p.append(p[-1])
        while len(n) < len(p):
            n.append(n[-1])
        return sum(abs(a - b) for a, b in zip(p, n))
