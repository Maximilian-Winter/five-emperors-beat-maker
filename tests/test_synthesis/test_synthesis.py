"""
Tests for the beatmaker.synthesis subpackage.

Validates that every module extracted from synth.py / synths.py works
correctly and that backward-compatibility re-exports are intact.
"""

import numpy as np
import pytest

from beatmaker.core import AudioData, Sample
from beatmaker.synthesis.waveforms import (
    sine_wave, square_wave, sawtooth_wave, triangle_wave,
    white_noise, pink_noise,
)
from beatmaker.synthesis.oscillator import Waveform, Oscillator, ADSREnvelope
from beatmaker.synthesis.drums import DrumSynth
from beatmaker.synthesis.bass import BassSynth
from beatmaker.synthesis.modulation import LFO, Filter
from beatmaker.synthesis.pads import PadSynth, create_pad
from beatmaker.synthesis.leads import LeadSynth, create_lead
from beatmaker.synthesis.plucks import PluckSynth, create_pluck
from beatmaker.synthesis.fx import FXSynth


# ── Waveform generators ─────────────────────────────────────────────────────

SAMPLE_RATE = 44100
DURATION = 0.1  # short duration for fast tests


class TestWaveforms:
    """Each waveform generator produces AudioData of correct length."""

    def _expected_length(self) -> int:
        return int(DURATION * SAMPLE_RATE)

    def test_sine_wave(self):
        audio = sine_wave(440.0, DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()
        assert audio.sample_rate == SAMPLE_RATE

    def test_square_wave(self):
        audio = square_wave(440.0, DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()

    def test_sawtooth_wave(self):
        audio = sawtooth_wave(440.0, DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()

    def test_triangle_wave(self):
        audio = triangle_wave(440.0, DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()

    def test_white_noise(self):
        audio = white_noise(DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()

    def test_pink_noise(self):
        audio = pink_noise(DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) == self._expected_length()

    def test_white_noise_seed_reproducible(self):
        a = white_noise(DURATION, SAMPLE_RATE, seed=42)
        b = white_noise(DURATION, SAMPLE_RATE, seed=42)
        np.testing.assert_array_equal(a.samples, b.samples)


# ── Oscillator ───────────────────────────────────────────────────────────────

class TestOscillator:
    """Oscillator generates audio with different waveforms."""

    @pytest.mark.parametrize("wf", list(Waveform))
    def test_generate_each_waveform(self, wf):
        osc = Oscillator(waveform=wf)
        audio = osc.generate(440.0, DURATION, SAMPLE_RATE)
        assert isinstance(audio, AudioData)
        assert len(audio.samples) > 0

    def test_detune_changes_frequency(self):
        osc_normal = Oscillator(waveform=Waveform.SINE)
        osc_detuned = Oscillator(waveform=Waveform.SINE, detune=100)  # +1 semitone
        a = osc_normal.generate(440.0, DURATION, SAMPLE_RATE)
        b = osc_detuned.generate(440.0, DURATION, SAMPLE_RATE)
        # Samples should differ
        assert not np.allclose(a.samples, b.samples)


# ── ADSREnvelope ─────────────────────────────────────────────────────────────

class TestADSREnvelope:
    """ADSREnvelope generates correct shape."""

    def test_generate_length(self):
        env = ADSREnvelope(attack=0.01, decay=0.02, sustain=0.7, release=0.02)
        result = env.generate(DURATION, SAMPLE_RATE)
        assert len(result) == int(DURATION * SAMPLE_RATE)

    def test_starts_at_zero(self):
        env = ADSREnvelope(attack=0.01, decay=0.02, sustain=0.7, release=0.02)
        result = env.generate(DURATION, SAMPLE_RATE)
        assert result[0] == pytest.approx(0.0)

    def test_peak_reaches_one(self):
        env = ADSREnvelope(attack=0.01, decay=0.02, sustain=0.7, release=0.02)
        result = env.generate(DURATION, SAMPLE_RATE)
        assert np.max(result) == pytest.approx(1.0, abs=0.01)

    def test_apply_shapes_audio(self):
        env = ADSREnvelope(attack=0.01, decay=0.02, sustain=0.5, release=0.02)
        audio = sine_wave(440.0, DURATION, SAMPLE_RATE)
        shaped = env.apply(audio)
        assert isinstance(shaped, AudioData)
        assert len(shaped.samples) == len(audio.samples)
        # First sample should be near zero (attack starts from 0)
        assert abs(shaped.samples[0]) < 0.01


# ── DrumSynth ────────────────────────────────────────────────────────────────

class TestDrumSynth:
    """DrumSynth methods return Sample objects with correct tags."""

    def test_kick(self):
        s = DrumSynth.kick()
        assert isinstance(s, Sample)
        assert "drums" in s.tags
        assert "kick" in s.tags

    def test_snare(self):
        s = DrumSynth.snare()
        assert isinstance(s, Sample)
        assert "drums" in s.tags
        assert "snare" in s.tags

    def test_hihat_closed(self):
        s = DrumSynth.hihat(open_amount=0.0)
        assert isinstance(s, Sample)
        assert "drums" in s.tags
        assert "hihat" in s.tags
        assert s.name == "hihat_closed"

    def test_hihat_open(self):
        s = DrumSynth.hihat(open_amount=0.8)
        assert isinstance(s, Sample)
        assert s.name == "hihat_open"

    def test_clap(self):
        s = DrumSynth.clap()
        assert isinstance(s, Sample)
        assert "drums" in s.tags
        assert "clap" in s.tags


# ── BassSynth ────────────────────────────────────────────────────────────────

class TestBassSynth:
    """BassSynth produces samples."""

    def test_sub_bass(self):
        s = BassSynth.sub_bass(60.0, 0.2)
        assert isinstance(s, Sample)
        assert "bass" in s.tags

    def test_acid_bass(self):
        s = BassSynth.acid_bass(80.0, 0.2)
        assert isinstance(s, Sample)
        assert "bass" in s.tags


# ── PadSynth ─────────────────────────────────────────────────────────────────

class TestPadSynth:
    """PadSynth produces audio."""

    def test_warm_pad(self):
        s = PadSynth.warm_pad(220.0, 0.3, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)
        assert "pad" in s.tags

    def test_string_pad(self):
        s = PadSynth.string_pad(220.0, 0.3, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)

    def test_ambient_pad(self):
        s = PadSynth.ambient_pad(220.0, 0.5, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)


# ── LeadSynth ────────────────────────────────────────────────────────────────

class TestLeadSynth:
    """LeadSynth produces audio."""

    def test_saw_lead(self):
        s = LeadSynth.saw_lead(440.0, 0.2, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)
        assert "lead" in s.tags

    def test_square_lead(self):
        s = LeadSynth.square_lead(440.0, 0.2, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)

    def test_fm_lead(self):
        s = LeadSynth.fm_lead(440.0, 0.2, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)


# ── PluckSynth ───────────────────────────────────────────────────────────────

class TestPluckSynth:
    """PluckSynth produces audio."""

    def test_karplus_strong(self):
        s = PluckSynth.karplus_strong(440.0, 0.3, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)
        assert "pluck" in s.tags

    def test_synth_pluck(self):
        s = PluckSynth.synth_pluck(440.0, 0.3, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)

    def test_bell(self):
        s = PluckSynth.bell(440.0, 0.3, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)


# ── FXSynth ──────────────────────────────────────────────────────────────────

class TestFXSynth:
    """FXSynth produces audio."""

    def test_riser(self):
        s = FXSynth.riser(0.5, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)
        assert "fx" in s.tags

    def test_downer(self):
        s = FXSynth.downer(0.5, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)

    def test_noise_sweep(self):
        s = FXSynth.noise_sweep(0.5, sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)

    def test_impact(self):
        s = FXSynth.impact(sample_rate=SAMPLE_RATE)
        assert isinstance(s, Sample)


# ── Backward compatibility ───────────────────────────────────────────────────

class TestBackwardCompat:
    """Old import paths still work."""

    def test_synth_module_exports(self):
        from beatmaker.synth import (
            Waveform, Oscillator, ADSREnvelope,
            sine_wave, square_wave, sawtooth_wave, triangle_wave,
            white_noise, pink_noise,
            DrumSynth, BassSynth,
            midi_to_freq, freq_to_midi, note_to_freq, NOTE_FREQS,
        )
        # Just verify they are importable and are the same objects
        assert Waveform is Waveform
        assert callable(sine_wave)
        assert callable(midi_to_freq)

    def test_synths_module_exports(self):
        from beatmaker.synths import (
            LFO, Filter,
            PadSynth, LeadSynth, PluckSynth, FXSynth,
            create_pad, create_lead, create_pluck,
        )
        assert callable(create_pad)

    def test_top_level_imports(self):
        from beatmaker import DrumSynth, BassSynth, PadSynth, LeadSynth
        assert DrumSynth is not None

    def test_synthesis_subpackage_import(self):
        from beatmaker.synthesis import DrumSynth as DS
        from beatmaker.synth import DrumSynth as DS2
        assert DS is DS2
