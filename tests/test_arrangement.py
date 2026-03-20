"""Tests for beatmaker.arrangement — Section and Arrangement."""

import pytest
from beatmaker.arrangement import Section, Arrangement, ArrangementEntry, Transition
from beatmaker.core import Track, TrackType


class TestSection:
    """Section tests."""

    def test_creation(self):
        s = Section("verse", bars=8)
        assert s.name == "verse"
        assert s.bars == 8

    def test_add_track(self):
        s = Section("verse", bars=8)
        t = Track("drums", TrackType.DRUMS)
        s.add_track(t)
        assert len(s.tracks) == 1

    def test_get_track(self):
        s = Section("verse", bars=8)
        t = Track("drums", TrackType.DRUMS)
        s.add_track(t)
        found = s.get_track("drums")
        assert found is t

    def test_get_track_not_found(self):
        s = Section("verse", bars=8)
        assert s.get_track("nonexistent") is None

    def test_variant(self):
        s = Section("verse", bars=8)
        t = Track("drums", TrackType.DRUMS)
        s.add_track(t)
        v = s.variant("verse_2", modifier=lambda sec: sec)
        assert v.name == "verse_2"
        assert len(v.tracks) == len(s.tracks)

    def test_without_track(self):
        s = Section("verse", bars=8)
        s.add_track(Track("drums", TrackType.DRUMS))
        s.add_track(Track("bass", TrackType.BASS))
        s2 = s.without_track("drums")
        assert len(s2.tracks) == 1
        assert s2.tracks[0].name == "bass"

    def test_with_added_track(self):
        s = Section("verse", bars=8)
        s.add_track(Track("drums", TrackType.DRUMS))
        s2 = s.with_added_track(Track("bass", TrackType.BASS))
        assert len(s2.tracks) == 2
        # Original unchanged
        assert len(s.tracks) == 1

    def test_with_volume(self):
        s = Section("verse", bars=8)
        t = Track("bass", TrackType.BASS)
        t.volume = 1.0
        s.add_track(t)
        s2 = s.with_volume("bass", 0.5)
        bass = s2.get_track("bass")
        assert bass.volume == 0.5
        # Original unchanged
        assert s.get_track("bass").volume == 1.0

    def test_with_mute(self):
        s = Section("verse", bars=8)
        s.add_track(Track("drums", TrackType.DRUMS))
        s2 = s.with_mute("drums")
        assert s2.get_track("drums").muted is True


class TestArrangement:
    """Arrangement tests."""

    def test_creation(self):
        a = Arrangement()
        assert len(a._entries) == 0

    def test_add_section(self):
        a = Arrangement()
        s = Section("verse", bars=8)
        a.add(s)
        assert len(a._entries) == 1

    def test_add_returns_self(self):
        a = Arrangement()
        result = a.add(Section("verse", bars=8))
        assert result is a

    def test_semantic_aliases(self):
        a = Arrangement()
        s = Section("intro", bars=4)
        a.intro(s).verse(Section("verse", bars=8)).chorus(Section("chorus", bars=8))
        assert len(a._entries) == 3

    def test_repeat(self):
        a = Arrangement()
        s = Section("verse", bars=8)
        a.add(s, repeat=2)
        assert a._entries[0].repeat == 2


class TestTransition:
    """Transition tests."""

    def test_default(self):
        t = Transition()
        assert t.type == 'cut'
        assert t.duration_beats == 0.0

    def test_crossfade(self):
        t = Transition(type='crossfade', duration_beats=2.0)
        assert t.type == 'crossfade'
        assert t.duration_beats == 2.0


class TestArrangementEntry:
    """ArrangementEntry tests."""

    def test_creation(self):
        s = Section("verse", bars=8)
        e = ArrangementEntry(section=s, repeat=2)
        assert e.section is s
        assert e.repeat == 2
