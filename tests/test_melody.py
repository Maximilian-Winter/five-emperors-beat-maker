"""Tests for beatmaker.melody — Note, Phrase, and Melody abstractions."""

import pytest
from beatmaker.melody import Note, Phrase, Melody


class TestNote:
    """Note tests."""

    def test_from_name(self):
        n = Note.from_name("C4")
        assert n.pitch == 60
        assert n.duration == 1.0
        assert n.velocity == 1.0

    def test_from_name_with_params(self):
        n = Note.from_name("A4", 0.5, 0.8)
        assert n.pitch == 69
        assert n.duration == 0.5
        assert n.velocity == 0.8

    def test_rest(self):
        r = Note.rest(2.0)
        assert r.is_rest
        assert r.duration == 2.0
        assert r.name == "R"

    def test_is_rest_false(self):
        n = Note.from_name("C4")
        assert not n.is_rest

    def test_name_property(self):
        n = Note.from_name("C4")
        assert n.name == "C4"

    def test_transpose(self):
        n = Note.from_name("C4")
        t = n.transpose(12)
        assert t.pitch == 72  # C5

    def test_transpose_rest(self):
        r = Note.rest()
        t = r.transpose(12)
        assert t.is_rest

    def test_transpose_clamps(self):
        n = Note(pitch=126, duration=1.0)
        t = n.transpose(5)
        assert t.pitch <= 127

    def test_with_duration(self):
        n = Note.from_name("C4", 1.0)
        n2 = n.with_duration(2.0)
        assert n2.duration == 2.0
        assert n.duration == 1.0  # Frozen

    def test_with_velocity(self):
        n = Note.from_name("C4")
        n2 = n.with_velocity(0.5)
        assert n2.velocity == 0.5

    def test_frozen(self):
        n = Note.from_name("C4")
        with pytest.raises(AttributeError):
            n.pitch = 64


class TestPhrase:
    """Phrase tests."""

    def test_from_string(self):
        p = Phrase.from_string("C4:1 D4:0.5 E4:0.5")
        assert len(p) == 3
        assert p.total_duration == 2.0

    def test_from_string_defaults(self):
        p = Phrase.from_string("E4 G4 A4")
        assert len(p) == 3
        assert p.total_duration == 3.0  # All quarter notes (1.0 each)

    def test_from_string_rest(self):
        p = Phrase.from_string("C4:1 R:1 E4:1")
        assert len(p) == 3
        assert p.notes[1].is_rest

    def test_from_notes(self):
        p = Phrase.from_notes(["C4", "E4", "G4"], duration=0.5)
        assert len(p) == 3
        assert p.total_duration == 1.5

    def test_transpose(self):
        p = Phrase.from_string("C4:1 E4:1")
        t = p.transpose(12)
        assert t.notes[0].pitch == 72
        assert t.notes[1].pitch == 76

    def test_reverse(self):
        p = Phrase.from_string("C4:1 E4:1 G4:1")
        r = p.reverse()
        assert r.notes[0].name == "G4"
        assert r.notes[2].name == "C4"

    def test_invert(self):
        p = Phrase.from_string("C4:1 E4:1")
        inv = p.invert()
        # Axis = C4 (60), E4 (64) inverts to 60 - (64 - 60) = 56
        assert inv.notes[1].pitch == 56

    def test_augment(self):
        p = Phrase.from_string("C4:1 E4:1")
        a = p.augment(2.0)
        assert a.total_duration == 4.0

    def test_diminish(self):
        p = Phrase.from_string("C4:2 E4:2")
        d = p.diminish(2.0)
        assert d.total_duration == 2.0

    def test_repeat(self):
        p = Phrase.from_string("C4:1")
        r = p.repeat(3)
        assert len(r) == 3
        assert r.total_duration == 3.0

    def test_then(self):
        p1 = Phrase.from_string("C4:1")
        p2 = Phrase.from_string("E4:1")
        combined = p1.then(p2)
        assert len(combined) == 2

    def test_add_operator(self):
        p1 = Phrase.from_string("C4:1")
        p2 = Phrase.from_string("E4:1")
        combined = p1 + p2
        assert len(combined) == 2

    def test_to_events(self):
        p = Phrase.from_string("C4:1 R:1 E4:0.5")
        events = p.to_events()
        assert len(events) == 2  # Rest omitted
        assert events[0] == (0.0, 60, 1.0, 1.0)
        assert events[1][0] == 2.0  # After C4 + rest

    def test_pitches(self):
        p = Phrase.from_string("C4:1 R:1 E4:1")
        assert p.pitches == [60, 64]


class TestMelody:
    """Melody tests."""

    def test_creation(self):
        m = Melody("test")
        assert m.total_duration == 0.0

    def test_add_phrase(self):
        m = Melody("test")
        p = Phrase.from_string("C4:1 E4:1")
        m.add(p)
        assert m.total_duration == 2.0

    def test_add_auto_sequence(self):
        m = Melody("test")
        p1 = Phrase.from_string("C4:1")
        p2 = Phrase.from_string("E4:1")
        m.add(p1)
        m.add(p2)
        assert m.total_duration == 2.0

    def test_add_at_beat(self):
        m = Melody("test")
        p = Phrase.from_string("C4:1")
        m.add(p, start_beat=4.0)
        assert m.total_duration == 5.0

    def test_add_sequence(self):
        m = Melody("test")
        phrases = [Phrase.from_string("C4:1"), Phrase.from_string("E4:1")]
        m.add_sequence(phrases)
        assert m.total_duration == 2.0

    def test_to_events(self):
        m = Melody("test")
        m.add(Phrase.from_string("C4:1 E4:1"))
        events = m.to_events()
        assert len(events) == 2
        # Should be sorted by beat
        assert events[0][0] <= events[1][0]
