"""Tests for beatmaker.arpeggiator — arpeggiator and builder."""

import pytest
from beatmaker.arpeggiator import (
    Arpeggiator, ArpeggiatorBuilder, ArpDirection, ArpMode,
    ArpSynthesizer, create_arpeggiator, arp_chord, arp_scale,
)
from beatmaker.music import ChordShape, Scale


class TestArpeggiator:
    """Arpeggiator tests."""

    def test_generate_pattern_up(self):
        arp = Arpeggiator(bpm=120, direction=ArpDirection.UP)
        notes = [60, 64, 67]  # C major triad
        events = arp.generate_pattern(notes, beats=4)
        assert len(events) > 0
        # Notes should be ascending
        midi_notes = [e[1] for e in events[:3]]
        assert midi_notes == sorted(midi_notes)

    def test_generate_pattern_down(self):
        arp = Arpeggiator(bpm=120, direction=ArpDirection.DOWN)
        notes = [60, 64, 67]
        events = arp.generate_pattern(notes, beats=4)
        midi_notes = [e[1] for e in events[:3]]
        assert midi_notes == sorted(midi_notes, reverse=True)

    def test_generate_from_chord(self):
        arp = Arpeggiator(bpm=120)
        events = arp.generate_from_chord("C4", ChordShape.MAJOR, beats=4)
        assert len(events) > 0

    def test_generate_from_scale(self):
        arp = Arpeggiator(bpm=120)
        events = arp.generate_from_scale("C4", Scale.MAJOR, beats=4)
        assert len(events) > 0

    def test_empty_notes(self):
        arp = Arpeggiator()
        events = arp.generate_pattern([], beats=4)
        assert events == []

    def test_velocity_pattern(self):
        arp = Arpeggiator(velocity_pattern=[1.0, 0.5])
        events = arp.generate_pattern([60, 64, 67], beats=4)
        velocities = [e[2] for e in events[:4]]
        assert velocities[0] == 1.0
        assert velocities[1] == 0.5

    def test_generate_from_progression(self):
        arp = Arpeggiator(bpm=120)
        prog = [("C4", ChordShape.MAJOR), ("G4", ChordShape.MAJOR)]
        events = arp.generate_from_progression(prog, beats_per_chord=4)
        assert len(events) > 0


class TestArpeggiatorBuilder:
    """ArpeggiatorBuilder fluent API tests."""

    def test_build(self):
        arp = create_arpeggiator().tempo(140).up().sixteenth().build()
        assert isinstance(arp, Arpeggiator)
        assert arp.bpm == 140
        assert arp.direction == ArpDirection.UP
        assert arp.rate == 0.25

    def test_chaining(self):
        builder = (create_arpeggiator()
                   .tempo(120)
                   .down()
                   .eighth()
                   .gate(0.5)
                   .octaves(2)
                   .swing(0.3))
        arp = builder.build()
        assert arp.bpm == 120
        assert arp.direction == ArpDirection.DOWN
        assert arp.rate == 0.5
        assert arp.gate == 0.5
        assert arp.octaves == 2
        assert arp.swing == 0.3

    def test_staccato(self):
        arp = create_arpeggiator().staccato().build()
        assert arp.gate == 0.3

    def test_legato(self):
        arp = create_arpeggiator().legato().build()
        assert arp.gate == 1.0


class TestArpConvenienceFunctions:
    """arp_chord and arp_scale convenience function tests."""

    def test_arp_chord(self):
        events = arp_chord("C4", ChordShape.MAJOR, beats=4)
        assert len(events) > 0

    def test_arp_scale(self):
        events = arp_scale("C4", Scale.MINOR, beats=4)
        assert len(events) > 0


class TestArpSynthesizer:
    """ArpSynthesizer audio rendering tests."""

    def test_render_note(self):
        synth = ArpSynthesizer(waveform='sine')
        audio = synth.render_note(60, 0.5)
        assert audio.duration == pytest.approx(0.5, abs=0.01)

    def test_render_events(self):
        synth = ArpSynthesizer(waveform='saw')
        events = [(0.0, 60, 1.0, 0.25), (0.25, 64, 0.8, 0.25)]
        audio = synth.render_events(events)
        assert audio.duration > 0

    def test_render_empty(self):
        synth = ArpSynthesizer()
        audio = synth.render_events([])
        assert audio.num_samples == 0
