"""Tests for beatmaker.music — shared music theory utilities."""

import pytest
from beatmaker.music import (
    note_name_to_midi,
    midi_to_note_name,
    midi_to_freq,
    freq_to_midi,
    note_to_freq,
    Scale,
    ChordShape,
    NOTE_FREQS,
)


class TestNoteNameToMidi:
    """note_name_to_midi conversion tests."""

    def test_middle_c(self):
        assert note_name_to_midi("C4") == 60

    def test_a4(self):
        assert note_name_to_midi("A4") == 69

    def test_c0(self):
        assert note_name_to_midi("C0") == 12

    def test_sharp(self):
        assert note_name_to_midi("F#3") == 54

    def test_flat(self):
        assert note_name_to_midi("Bb2") == 46

    def test_all_naturals_octave4(self):
        expected = {"C4": 60, "D4": 62, "E4": 64, "F4": 65, "G4": 67, "A4": 69, "B4": 71}
        for name, midi in expected.items():
            assert note_name_to_midi(name) == midi, f"{name} should be {midi}"


class TestMidiToNoteName:
    """midi_to_note_name conversion tests."""

    def test_middle_c(self):
        assert midi_to_note_name(60) == "C4"

    def test_a4(self):
        assert midi_to_note_name(69) == "A4"

    def test_roundtrip(self):
        """note_name_to_midi(midi_to_note_name(n)) should return n for natural notes."""
        for midi in [60, 62, 64, 65, 67, 69, 71]:
            name = midi_to_note_name(midi)
            assert note_name_to_midi(name) == midi


class TestMidiToFreq:
    """midi_to_freq conversion tests."""

    def test_a4(self):
        assert midi_to_freq(69) == pytest.approx(440.0)

    def test_a3(self):
        assert midi_to_freq(57) == pytest.approx(220.0)

    def test_octave_doubles(self):
        f_low = midi_to_freq(60)
        f_high = midi_to_freq(72)
        assert f_high == pytest.approx(f_low * 2)


class TestFreqToMidi:
    """freq_to_midi conversion tests."""

    def test_440(self):
        assert freq_to_midi(440.0) == 69

    def test_roundtrip(self):
        for midi in [48, 60, 72, 84]:
            freq = midi_to_freq(midi)
            assert freq_to_midi(freq) == midi


class TestNoteToFreq:
    """note_to_freq conversion tests."""

    def test_a4(self):
        assert note_to_freq("A4") == pytest.approx(440.0)

    def test_c3(self):
        assert note_to_freq("C3") == pytest.approx(130.81)

    def test_unknown_note_raises(self):
        with pytest.raises(ValueError):
            note_to_freq("X4")


class TestScale:
    """Scale tests."""

    def test_major_intervals(self):
        assert Scale.MAJOR.intervals == [0, 2, 4, 5, 7, 9, 11]

    def test_minor_intervals(self):
        assert Scale.MINOR.intervals == [0, 2, 3, 5, 7, 8, 10]

    def test_get_notes_one_octave(self):
        notes = Scale.MAJOR.get_notes(60, octaves=1)
        assert notes == [60, 62, 64, 65, 67, 69, 71]

    def test_get_notes_two_octaves(self):
        notes = Scale.MAJOR.get_notes(60, octaves=2)
        assert len(notes) == 14
        # Second octave should be 12 semitones higher
        assert notes[7] == notes[0] + 12

    def test_all_scales_defined(self):
        """Every class-level scale should be a Scale instance."""
        for name in ["MAJOR", "MINOR", "DORIAN", "PHRYGIAN", "LYDIAN",
                      "MIXOLYDIAN", "LOCRIAN", "MINOR_PENTATONIC",
                      "MAJOR_PENTATONIC", "BLUES", "HARMONIC_MINOR",
                      "MELODIC_MINOR"]:
            scale = getattr(Scale, name)
            assert isinstance(scale, Scale), f"Scale.{name} not defined"
            assert len(scale.intervals) > 0


class TestChordShape:
    """ChordShape tests."""

    def test_major_triad(self):
        assert ChordShape.MAJOR.intervals == [0, 4, 7]

    def test_minor_triad(self):
        assert ChordShape.MINOR.intervals == [0, 3, 7]

    def test_dom7(self):
        assert ChordShape.DOM7.intervals == [0, 4, 7, 10]

    def test_custom(self):
        custom = ChordShape.custom("test", [0, 5, 10])
        assert custom.name == "test"
        assert custom.intervals == [0, 5, 10]

    def test_all_shapes_defined(self):
        for name in ["MAJOR", "MINOR", "DIM", "AUG", "SUS2", "SUS4",
                      "MAJOR7", "MINOR7", "DOM7", "ADD9", "DIM7",
                      "HALF_DIM7", "MAJ9", "MIN9", "DOM9", "ADD11", "MAJ13"]:
            shape = getattr(ChordShape, name)
            assert isinstance(shape, ChordShape), f"ChordShape.{name} not defined"


class TestBackwardCompatImports:
    """Verify backward-compat re-exports from original modules."""

    def test_synth_exports(self):
        from beatmaker.synth import midi_to_freq, freq_to_midi, note_to_freq
        assert midi_to_freq(69) == pytest.approx(440.0)

    def test_arpeggiator_exports(self):
        from beatmaker.arpeggiator import ChordShape, Scale, note_name_to_midi
        assert note_name_to_midi("C4") == 60
        assert isinstance(Scale.MAJOR, Scale)
        assert isinstance(ChordShape.MAJOR, ChordShape)

    def test_melody_exports(self):
        from beatmaker.melody import note_name_to_midi, midi_to_note_name
        assert note_name_to_midi("A4") == 69
        assert midi_to_note_name(69) == "A4"
