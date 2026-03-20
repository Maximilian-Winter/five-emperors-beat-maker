"""Tests for beatmaker.harmony — Key, ChordProgression, and harmonic analysis."""

import pytest
from beatmaker.harmony import Key, ChordProgression, ChordEntry
from beatmaker.music import Scale, ChordShape


class TestKey:
    """Key tests."""

    def test_major(self):
        k = Key.major("C")
        assert k.root == "C"

    def test_minor(self):
        k = Key.minor("A")
        assert k.root == "A"

    def test_degree(self):
        k = Key.major("C")
        # Degree 1 in C major (octave 4) = MIDI 60 (middle C)
        midi = k.degree(1, 4)
        assert midi == 60

    def test_degree_fifth(self):
        k = Key.major("C")
        # Degree 5 in C major = G = MIDI 67
        midi = k.degree(5, 4)
        assert midi == 67

    def test_is_diatonic(self):
        k = Key.major("C")
        # C (pc 0) is diatonic to C major
        assert k.is_diatonic(0)

    def test_modulate(self):
        k = Key.major("C")
        k2 = k.modulate("G")  # Modulate to G major
        assert k2.root == "G"
        assert k2.scale == Scale.MAJOR

    def test_scale_notes(self):
        k = Key.major("C")
        notes = k.scale_notes(4)
        assert len(notes) == 7
        assert 60 in notes  # Middle C


class TestChordProgression:
    """ChordProgression tests."""

    def test_from_roman(self):
        k = Key.major("C")
        prog = ChordProgression.from_roman(k, "I - IV - V - I")
        assert len(prog.chords) == 4

    def test_from_roman_spaces(self):
        k = Key.major("C")
        prog = ChordProgression.from_roman(k, "I IV V I")
        assert len(prog.chords) == 4

    def test_entries_are_chord_entries(self):
        k = Key.major("C")
        prog = ChordProgression.from_roman(k, "I V")
        assert all(isinstance(e, ChordEntry) for e in prog.chords)


class TestChordEntry:
    """ChordEntry tests."""

    def test_creation(self):
        e = ChordEntry(degree=1, shape=ChordShape.MAJOR,
                       root_midi=60, duration_beats=4.0)
        assert e.degree == 1
        assert e.duration_beats == 4.0

    def test_midi_notes(self):
        e = ChordEntry(degree=1, shape=ChordShape.MAJOR,
                       root_midi=60, duration_beats=4.0)
        notes = e.midi_notes
        assert notes == [60, 64, 67]  # C E G
