"""Tests for beatmaker.builder — Song/Track builder integration tests."""

import pytest
import numpy as np

from beatmaker.builder import (
    Song, SongBuilder, TrackBuilder, DrumTrackBuilder,
    BassTrackBuilder, MelodyTrackBuilder, HarmonyTrackBuilder,
    SectionBuilder, create_song,
)
from beatmaker.core import AudioData, Sample, Track, TrackType
from beatmaker.synth import DrumSynth


class TestSong:
    """Song tests."""

    def test_creation(self):
        s = Song(name="Test")
        assert s.name == "Test"
        assert s.bpm == 120.0

    def test_add_track(self):
        s = Song()
        t = Track("drums", TrackType.DRUMS)
        s.add_track(t)
        assert len(s.tracks) == 1

    def test_get_track(self):
        s = Song()
        t = Track("drums", TrackType.DRUMS)
        s.add_track(t)
        assert s.get_track("drums") is t
        assert s.get_track("nonexistent") is None

    def test_duration_empty(self):
        s = Song()
        assert s.duration == 0.0

    def test_beat_to_seconds(self):
        s = Song(bpm=120.0)
        assert s.beat_to_seconds(4) == pytest.approx(2.0)

    def test_render_empty(self):
        s = Song()
        audio = s.render()
        assert audio.num_samples == 0


class TestCreateSong:
    """create_song factory and SongBuilder tests."""

    def test_create_song_returns_builder(self):
        builder = create_song("My Beat")
        assert isinstance(builder, SongBuilder)

    def test_tempo(self):
        builder = create_song("Test").tempo(140)
        assert isinstance(builder, SongBuilder)

    def test_build_empty(self):
        song = create_song("Test").tempo(120).bars(4).build()
        assert isinstance(song, Song)
        assert song.name == "Test"
        assert song.bpm == 120.0


class TestDrumTrackBuilder:
    """DrumTrackBuilder tests."""

    def test_four_on_floor(self):
        song = (create_song("Drums Test")
                .tempo(120)
                .bars(1)
                .add_drums(lambda d: d.four_on_floor())
                .build())
        assert len(song.tracks) == 1
        # Should have kick placements at beats 0, 1, 2, 3
        assert len(song.tracks[0].placements) >= 4

    def test_backbeat(self):
        song = (create_song("Drums Test")
                .tempo(120)
                .bars(1)
                .add_drums(lambda d: d.backbeat())
                .build())
        assert len(song.tracks) == 1

    def test_chaining_returns_correct_type(self):
        """TrackBuilder.volume() should return the subclass type (DrumTrackBuilder)."""
        song = (create_song("Test")
                .tempo(120)
                .bars(1)
                .add_drums(lambda d: d
                    .four_on_floor()
                    .volume(0.8)
                    .pan(0.1)
                )
                .build())
        assert song.tracks[0].volume == 0.8
        assert song.tracks[0].pan == 0.1

    def test_render_produces_audio(self):
        song = (create_song("Test")
                .tempo(120)
                .bars(1)
                .add_drums(lambda d: d.four_on_floor())
                .build())
        audio = song.render()
        assert isinstance(audio, AudioData)
        assert audio.duration > 0
        # Should have actual sound content
        assert np.max(np.abs(audio.samples)) > 0


class TestBassTrackBuilder:
    """BassTrackBuilder tests."""

    def test_basic_bass(self):
        song = (create_song("Bass Test")
                .tempo(120)
                .bars(1)
                .add_bass(lambda b: b
                    .note("C2", beat=0, duration=2)
                    .note("G2", beat=2, duration=2)
                )
                .build())
        assert len(song.tracks) == 1


class TestMultipleTracks:
    """Tests for songs with multiple tracks."""

    def test_drums_and_bass(self):
        song = (create_song("Multi")
                .tempo(128)
                .bars(1)
                .add_drums(lambda d: d.four_on_floor())
                .add_bass(lambda b: b.note("C2", 0, 4))
                .build())
        assert len(song.tracks) == 2

    def test_export_render(self):
        """Full integration: build + render."""
        song = (create_song("Full Test")
                .tempo(120)
                .bars(1)
                .add_drums(lambda d: d
                    .four_on_floor()
                    .backbeat()
                )
                .build())
        audio = song.render(channels=2)
        assert audio.channels == 2
        assert audio.duration > 0
