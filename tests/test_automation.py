"""Tests for beatmaker.automation — parameter automation curves."""

import pytest
import numpy as np

from beatmaker.automation import (
    AutomationCurve, AutomationPoint, CurveType,
    AutomatableEffect, AutomatedGain, AutomatedFilter,
)


class TestAutomationPoint:
    """AutomationPoint tests."""

    def test_creation(self):
        p = AutomationPoint(beat=1.0, value=0.5)
        assert p.beat == 1.0
        assert p.value == 0.5
        assert p.curve == CurveType.LINEAR


class TestAutomationCurve:
    """AutomationCurve tests."""

    def test_add_point(self):
        c = AutomationCurve("vol")
        c.add_point(0.0, 0.0)
        c.add_point(4.0, 1.0)
        assert len(c.points) == 2

    def test_points_sorted(self):
        c = AutomationCurve("vol")
        c.add_point(4.0, 1.0)
        c.add_point(0.0, 0.0)
        assert c.points[0].beat == 0.0
        assert c.points[1].beat == 4.0

    def test_ramp(self):
        c = AutomationCurve("vol")
        c.ramp(0.0, 4.0, 0.0, 1.0)
        assert len(c.points) == 2
        assert c.points[0].value == 0.0
        assert c.points[1].value == 1.0

    def test_render_linear(self):
        c = AutomationCurve("vol")
        c.ramp(0.0, 4.0, 0.0, 1.0)
        # Render at 120 BPM, 44100 SR, 4 beats
        rendered = c.render(120, 44100, 4.0)
        assert len(rendered) > 0
        # Start should be near 0, end near 1
        assert rendered[0] == pytest.approx(0.0, abs=0.01)
        assert rendered[-1] == pytest.approx(1.0, abs=0.01)

    def test_render_step(self):
        c = AutomationCurve("vol")
        c.add_point(0.0, 0.0, CurveType.STEP)
        c.add_point(2.0, 1.0, CurveType.STEP)
        rendered = c.render(120, 44100, 4.0)
        # Before beat 2 should be 0, after should be 1
        mid = len(rendered) // 2
        assert rendered[0] == pytest.approx(0.0, abs=0.01)
        assert rendered[-1] == pytest.approx(1.0, abs=0.01)


class TestCurveType:
    """CurveType enum tests."""

    def test_all_types(self):
        types = [CurveType.LINEAR, CurveType.EXPONENTIAL,
                 CurveType.LOGARITHMIC, CurveType.STEP, CurveType.SMOOTH]
        assert len(types) == 5
