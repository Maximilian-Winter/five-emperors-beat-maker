"""Tests for beatmaker.core — fundamental audio types."""

import pytest
import numpy as np

from beatmaker.core import (
    AudioData, Sample, Track, TrackType, TimeSignature,
    SamplePlacement, NoteValue, AudioEffect,
)


class TestAudioData:
    """AudioData container tests."""

    def test_creation(self, sample_audio):
        assert sample_audio.sample_rate == 44100
        assert sample_audio.channels == 1

    def test_duration(self, sample_audio):
        assert sample_audio.duration == pytest.approx(0.1, abs=0.001)

    def test_num_samples(self, sample_audio):
        assert sample_audio.num_samples == int(0.1 * 44100)

    def test_stereo_detection(self, stereo_audio):
        assert stereo_audio.channels == 2

    def test_to_mono(self, stereo_audio):
        mono = stereo_audio.to_mono()
        assert mono.channels == 1
        assert mono.num_samples == stereo_audio.num_samples

    def test_to_mono_idempotent(self, sample_audio):
        result = sample_audio.to_mono()
        assert result is sample_audio

    def test_to_stereo(self, sample_audio):
        stereo = sample_audio.to_stereo()
        assert stereo.channels == 2
        assert stereo.num_samples == sample_audio.num_samples

    def test_to_stereo_idempotent(self, stereo_audio):
        result = stereo_audio.to_stereo()
        assert result is stereo_audio

    def test_normalize(self, sample_audio):
        normalized = sample_audio.normalize(0.95)
        assert np.max(np.abs(normalized.samples)) == pytest.approx(0.95, abs=0.01)

    def test_normalize_silent(self):
        silent = AudioData.silence(0.1)
        result = silent.normalize()
        assert result is silent

    def test_resample(self, sample_audio):
        resampled = sample_audio.resample(22050)
        assert resampled.sample_rate == 22050
        # Duration should be approximately the same
        assert resampled.duration == pytest.approx(sample_audio.duration, abs=0.01)

    def test_resample_same_rate(self, sample_audio):
        result = sample_audio.resample(44100)
        assert result is sample_audio

    def test_slice(self, sample_audio):
        sliced = sample_audio.slice(0.02, 0.05)
        assert sliced.duration == pytest.approx(0.03, abs=0.001)
        assert sliced.sample_rate == sample_audio.sample_rate

    def test_fade_in(self, sample_audio):
        faded = sample_audio.fade_in(0.02)
        assert faded.samples[0] == pytest.approx(0.0)
        assert faded.num_samples == sample_audio.num_samples

    def test_fade_out(self, sample_audio):
        faded = sample_audio.fade_out(0.02)
        assert faded.samples[-1] == pytest.approx(0.0, abs=0.01)
        assert faded.num_samples == sample_audio.num_samples

    def test_silence(self):
        silent = AudioData.silence(0.5, 44100)
        assert silent.duration == pytest.approx(0.5, abs=0.001)
        assert np.all(silent.samples == 0)
        assert silent.channels == 1

    def test_silence_stereo(self):
        silent = AudioData.silence(0.5, 44100, channels=2)
        assert silent.channels == 2

    def test_from_generator(self):
        audio = AudioData.from_generator(
            lambda t: np.sin(2 * np.pi * 440 * t),
            duration=0.1, sample_rate=44100
        )
        assert audio.duration == pytest.approx(0.1, abs=0.001)
        assert audio.channels == 1


class TestSample:
    """Sample tests."""

    def test_creation(self, sample_audio):
        s = Sample("test", sample_audio, tags=["test"])
        assert s.name == "test"
        assert "test" in s.tags

    def test_with_tags(self, sample_audio):
        s = Sample("test", sample_audio)
        s2 = s.with_tags("drums", "kick")
        assert "drums" in s2.tags
        assert "kick" in s2.tags
        # Original unchanged
        assert len(s.tags) == 0

    def test_pitched(self, sample_audio):
        s = Sample("test", sample_audio, root_note=60)
        s2 = s.pitched(12)
        assert s2.root_note == 72
        assert "pitch" in s2.name


class TestSamplePlacement:
    """SamplePlacement tests."""

    def test_end_time(self, sample_audio):
        s = Sample("test", sample_audio)
        p = SamplePlacement(s, time=1.0)
        assert p.end_time == pytest.approx(1.0 + sample_audio.duration, abs=0.001)


class TestTrack:
    """Track tests."""

    def test_creation(self):
        t = Track("drums", TrackType.DRUMS)
        assert t.name == "drums"
        assert t.track_type == TrackType.DRUMS
        assert len(t.placements) == 0

    def test_add(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        t.add(s, 0.0)
        assert len(t.placements) == 1

    def test_add_returns_self(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        result = t.add(s, 0.0)
        assert result is t

    def test_duration(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        t.add(s, 1.0)
        assert t.duration == pytest.approx(1.0 + sample_audio.duration, abs=0.001)

    def test_duration_empty(self):
        t = Track("drums")
        assert t.duration == 0.0

    def test_add_pattern(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        pattern = [True, False, True, False]
        t.add_pattern(s, pattern, step_duration=0.5)
        assert len(t.placements) == 2  # Two True values

    def test_add_effect(self, sample_audio):
        class FakeEffect(AudioEffect):
            def process(self, audio):
                return audio
        t = Track("drums")
        t.add_effect(FakeEffect())
        assert len(t.effects) == 1

    def test_clear(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        t.add(s, 0.0)
        t.clear()
        assert len(t.placements) == 0

    def test_iter(self, sample_audio):
        t = Track("drums")
        s = Sample("kick", sample_audio)
        t.add(s, 1.0)
        t.add(s, 0.0)
        times = [p.time for p in t]
        assert times == [0.0, 1.0]  # Sorted

    def test_render_empty(self):
        t = Track("drums")
        result = t.render()
        assert result.num_samples == 0


class TestTimeSignature:
    """TimeSignature tests."""

    def test_beats_to_seconds(self):
        ts = TimeSignature(4, 4)
        assert ts.beats_to_seconds(4, 120) == pytest.approx(2.0)

    def test_bars_to_seconds(self):
        ts = TimeSignature(4, 4)
        assert ts.bars_to_seconds(1, 120) == pytest.approx(2.0)
        assert ts.bars_to_seconds(2, 120) == pytest.approx(4.0)


class TestNoteValue:
    """NoteValue enum tests."""

    def test_quarter(self):
        assert NoteValue.QUARTER.value == 0.25

    def test_whole(self):
        assert NoteValue.WHOLE.value == 1.0

    def test_sixteenth(self):
        assert NoteValue.SIXTEENTH.value == 0.0625


class TestTrackType:
    """TrackType enum tests."""

    def test_all_types(self):
        types = [TrackType.DRUMS, TrackType.BASS, TrackType.LEAD,
                 TrackType.PAD, TrackType.VOCAL, TrackType.FX, TrackType.BACKING]
        assert len(types) == 7
