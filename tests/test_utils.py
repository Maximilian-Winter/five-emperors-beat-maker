"""Tests for beatmaker.utils — audio processing utilities."""

import pytest
import numpy as np

from beatmaker.utils import (
    detect_bpm, time_stretch, pitch_shift,
    reverse, loop, crossfade, concatenate, mix,
)
from beatmaker.core import AudioData


@pytest.fixture
def tone_1sec():
    """1-second 440Hz sine tone."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, False)
    samples = np.sin(2 * np.pi * 440 * t)
    return AudioData(samples, sr)


class TestReverse:
    """reverse() tests."""

    def test_reverses_audio(self, sample_audio):
        rev = reverse(sample_audio)
        assert rev.num_samples == sample_audio.num_samples
        assert rev.samples[0] == pytest.approx(sample_audio.samples[-1])

    def test_double_reverse_identity(self, sample_audio):
        double = reverse(reverse(sample_audio))
        np.testing.assert_array_almost_equal(double.samples, sample_audio.samples)


class TestLoop:
    """loop() tests."""

    def test_loop_doubles(self, sample_audio):
        looped = loop(sample_audio, 2)
        assert looped.num_samples == pytest.approx(sample_audio.num_samples * 2, abs=10)


class TestConcatenate:
    """concatenate() tests."""

    def test_concat_two(self, sample_audio):
        result = concatenate(sample_audio, sample_audio)
        assert result.num_samples == pytest.approx(sample_audio.num_samples * 2, abs=10)


class TestMix:
    """mix() tests."""

    def test_mix_same_length(self, sample_audio):
        result = mix(sample_audio, sample_audio)
        assert result.num_samples == sample_audio.num_samples


class TestTimeStretch:
    """time_stretch() tests."""

    def test_stretch_doubles_duration(self, tone_1sec):
        stretched = time_stretch(tone_1sec, 2.0)
        assert stretched.duration == pytest.approx(2.0, abs=0.1)

    def test_stretch_halves_duration(self, tone_1sec):
        stretched = time_stretch(tone_1sec, 0.5)
        assert stretched.duration == pytest.approx(0.5, abs=0.1)


class TestPitchShift:
    """pitch_shift() tests."""

    def test_shift_changes_duration(self, tone_1sec):
        shifted = pitch_shift(tone_1sec, 12)
        # pitch_shift via resampling changes duration (halves for +12 semitones)
        assert shifted.duration == pytest.approx(0.5, abs=0.1)

    def test_shift_returns_audio(self, tone_1sec):
        shifted = pitch_shift(tone_1sec, 5)
        assert isinstance(shifted, AudioData)
        assert shifted.sample_rate == tone_1sec.sample_rate


class TestDetectBpm:
    """detect_bpm() tests."""

    def test_returns_float(self, tone_1sec):
        bpm = detect_bpm(tone_1sec)
        assert isinstance(bpm, float)
        assert 60 <= bpm <= 200
