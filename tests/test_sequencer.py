"""Tests for beatmaker.sequencer — step sequencing and patterns."""

import pytest
from beatmaker.sequencer import (
    Step, StepValue, Pattern, StepSequencer,
    ClassicPatterns, EuclideanPattern, PolyrhythmGenerator,
)


class TestStep:
    """Step factory and properties tests."""

    def test_on(self):
        s = Step.on()
        assert s.active is True
        assert s.velocity == 1.0

    def test_off(self):
        s = Step.off()
        assert s.active is False

    def test_accent(self):
        s = Step.accent()
        assert s.active is True
        assert s.velocity > 1.0

    def test_ghost(self):
        s = Step.ghost()
        assert s.active is True
        assert s.velocity < 0.5

    def test_roll(self):
        s = Step.roll(4)
        assert s.active is True
        assert s.num_hits == 4

    def test_prob(self):
        s = Step.prob(0.5)
        assert s.probability == 0.5
        assert s.active is True


class TestPattern:
    """Pattern creation and manipulation tests."""

    def test_default_length(self):
        p = Pattern()
        assert p.length == 16
        assert len(p.steps) == 16

    def test_from_string(self):
        p = Pattern.from_string("x...x...x...x...")
        active = [s.active for s in p.steps]
        assert active == [True, False, False, False,
                          True, False, False, False,
                          True, False, False, False,
                          True, False, False, False]

    def test_from_string_accent(self):
        p = Pattern.from_string("X...x...")
        assert p.steps[0].velocity > p.steps[4].velocity

    def test_from_string_ghost(self):
        p = Pattern.from_string("x...o...")
        assert p.steps[4].velocity < 0.5

    def test_from_list(self):
        p = Pattern.from_list([1, 0, 1, 0, 1, 0, 1, 0])
        assert sum(1 for s in p.steps if s.active) == 4

    def test_from_positions(self):
        p = Pattern.from_positions([0, 4, 8, 12], length=16)
        assert p.steps[0].active
        assert p.steps[4].active
        assert not p.steps[1].active

    def test_rotate(self):
        p = Pattern.from_string("x...")
        r = p.rotate(1)
        assert r.steps[0].active is False
        assert r.steps[1].active is True

    def test_reverse(self):
        p = Pattern.from_string("x..x")
        r = p.reverse()
        assert r.steps[0].active  # Was last
        assert r.steps[3].active  # Was first

    def test_combine_or(self):
        p1 = Pattern.from_string("x...", name="a")
        p2 = Pattern.from_string("..x.", name="b")
        combined = p1.combine(p2, mode='or')
        assert combined.steps[0].active
        assert combined.steps[2].active


class TestEuclideanPattern:
    """Euclidean rhythm tests."""

    def test_basic(self):
        p = EuclideanPattern.generate(4, 16)
        active = sum(1 for s in p.steps if s.active)
        assert active == 4

    def test_all_on(self):
        p = EuclideanPattern.generate(8, 8)
        assert all(s.active for s in p.steps)

    def test_one_hit(self):
        p = EuclideanPattern.generate(1, 8)
        active = sum(1 for s in p.steps if s.active)
        assert active == 1


class TestClassicPatterns:
    """Verify classic pattern presets exist and are valid."""

    def test_four_on_floor(self):
        p = ClassicPatterns.FOUR_ON_FLOOR
        assert isinstance(p, Pattern)
        active = sum(1 for s in p.steps if s.active)
        assert active == 4

    def test_backbeat(self):
        p = ClassicPatterns.BACKBEAT
        assert isinstance(p, Pattern)

    def test_offbeat_hats(self):
        p = ClassicPatterns.OFFBEAT_HATS
        assert isinstance(p, Pattern)
