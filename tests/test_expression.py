"""Tests for beatmaker.expression — musical expressiveness."""

import pytest
import numpy as np

from beatmaker.expression import (
    Vibrato, PitchBend, Portamento, NoteExpression,
    Humanizer, GrooveTemplate, VelocityCurve,
)
from beatmaker.core import AudioData, Track, TrackType, Sample, SamplePlacement


class TestVibrato:
    """Vibrato tests."""

    def test_creation(self):
        v = Vibrato(rate=5.0, depth=0.5, delay=0.1)
        assert v.rate == 5.0
        assert v.depth == 0.5

    def test_apply(self, sample_audio):
        v = Vibrato(rate=5.0, depth=0.5, delay=0.0)
        result = v.apply(sample_audio, base_freq=440.0)
        assert isinstance(result, AudioData)
        assert result.num_samples == sample_audio.num_samples


class TestPitchBend:
    """PitchBend tests."""

    def test_creation(self):
        pb = PitchBend(semitones=2.0, start_offset=0.0, end_offset=0.5)
        assert pb.semitones == 2.0
        assert pb.start_offset == 0.0

    def test_generate_curve(self):
        pb = PitchBend(semitones=2.0)
        curve = pb.generate_curve(1000)
        assert len(curve) == 1000


class TestHumanizer:
    """Humanizer tests."""

    def test_creation(self):
        h = Humanizer(timing_jitter=0.01, velocity_variation=0.1)
        assert h.timing_jitter == 0.01
        assert h.velocity_variation == 0.1

    def test_apply_to_events(self):
        h = Humanizer(timing_jitter=0.01, velocity_variation=0.1, seed=42)
        events = [(0.0, 60, 1.0, 0.5), (0.5, 64, 1.0, 0.5)]
        result = h.apply_to_events(events, bpm=120)
        assert len(result) == 2
        # Times/velocities should be slightly different
        # (but with seed=42 this is deterministic)


class TestGrooveTemplate:
    """GrooveTemplate tests."""

    def test_creation(self):
        g = GrooveTemplate(
            name="swing",
            timing_offsets=[0.0, 0.02, 0.0, 0.02],
            velocity_scales=[1.0, 0.8, 1.0, 0.8],
        )
        assert g.name == "swing"
        assert len(g.timing_offsets) == 4
        assert len(g.velocity_scales) == 4
