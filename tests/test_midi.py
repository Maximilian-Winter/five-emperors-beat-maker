"""Tests for beatmaker.midi — MIDI file I/O."""

import pytest
import tempfile
from pathlib import Path

from beatmaker.midi import (
    MIDINote, MIDITrack, MIDIFile,
    MIDIReader, MIDIWriter,
    create_midi, save_midi, load_midi,
)


class TestMIDINote:
    """MIDINote tests."""

    def test_creation(self):
        n = MIDINote(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
        assert n.pitch == 60
        assert n.velocity == 100

    def test_end_tick(self):
        n = MIDINote(pitch=60, velocity=100, start_tick=100, duration_ticks=480)
        assert n.end_tick == 580

    def test_to_seconds(self):
        n = MIDINote(pitch=60, velocity=100, start_tick=480, duration_ticks=480)
        start, dur = n.to_seconds(ticks_per_beat=480, bpm=120)
        assert start == pytest.approx(0.5)  # One beat at 120bpm
        assert dur == pytest.approx(0.5)


class TestMIDITrack:
    """MIDITrack tests."""

    def test_creation(self):
        t = MIDITrack(name="Piano")
        assert t.name == "Piano"
        assert len(t.notes) == 0

    def test_add_note(self):
        t = MIDITrack()
        t.add_note(60, 100, 0, 480)
        assert len(t.notes) == 1

    def test_add_note_returns_self(self):
        t = MIDITrack()
        result = t.add_note(60, 100, 0, 480)
        assert result is t

    def test_get_notes_in_range(self):
        t = MIDITrack()
        t.add_note(60, 100, 0, 480)
        t.add_note(64, 100, 480, 480)
        t.add_note(67, 100, 960, 480)
        notes = t.get_notes_in_range(0, 480)
        assert len(notes) == 1
        assert notes[0].pitch == 60

    def test_duration_ticks(self):
        t = MIDITrack()
        t.add_note(60, 100, 0, 480)
        t.add_note(64, 100, 480, 480)
        assert t.duration_ticks == 960


class TestMIDIFile:
    """MIDIFile tests."""

    def test_creation(self):
        f = create_midi(bpm=120)
        assert isinstance(f, MIDIFile)

    def test_save_load_roundtrip(self):
        """Write a MIDI file and read it back."""
        f = create_midi(bpm=120)
        t = MIDITrack(name="Test")
        t.add_note(60, 100, 0, 480)
        t.add_note(64, 100, 480, 480)
        f.tracks.append(t)

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            save_midi(f, tmp_path)
            loaded = load_midi(tmp_path)
            assert isinstance(loaded, MIDIFile)
            # Should have at least the notes we wrote
            total_notes = sum(len(t.notes) for t in loaded.tracks)
            assert total_notes >= 2
        finally:
            tmp_path.unlink(missing_ok=True)
