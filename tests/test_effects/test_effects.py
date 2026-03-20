"""
Tests for the beatmaker.effects subpackage.

Each effect is tested to ensure it can process audio and produces
output with the correct length and sample rate.
"""

import numpy as np
import pytest

from beatmaker.core import AudioData
from beatmaker.effects import (
    Gain,
    Limiter,
    SoftClipper,
    Compressor,
    Delay,
    Reverb,
    Chorus,
    LowPassFilter,
    HighPassFilter,
    BitCrusher,
    EffectChain,
    SidechainCompressor,
    SidechainEnvelope,
    PumpingBass,
    SidechainBuilder,
    SidechainPresets,
    create_sidechain,
)


@pytest.fixture
def mono_audio():
    """Create a short mono test signal (440 Hz sine, 0.1s)."""
    sr = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    samples = np.sin(2 * np.pi * 440 * t) * 0.5
    return AudioData(samples, sr, 1)


@pytest.fixture
def stereo_audio():
    """Create a short stereo test signal."""
    sr = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    left = np.sin(2 * np.pi * 440 * t) * 0.5
    right = np.sin(2 * np.pi * 880 * t) * 0.5
    samples = np.column_stack([left, right])
    return AudioData(samples, sr, 2)


class TestGain:
    def test_process_preserves_length(self, mono_audio):
        result = Gain(level=0.5).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate

    def test_from_db(self):
        g = Gain.from_db(0.0)
        assert abs(g.level - 1.0) < 1e-10

    def test_gain_scales_amplitude(self, mono_audio):
        result = Gain(level=2.0).process(mono_audio)
        np.testing.assert_allclose(result.samples, mono_audio.samples * 2.0)


class TestLimiter:
    def test_process_preserves_length(self, mono_audio):
        result = Limiter(threshold=0.3).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate

    def test_clips_signal(self, mono_audio):
        result = Limiter(threshold=0.3).process(mono_audio)
        assert np.max(np.abs(result.samples)) <= 0.3 + 1e-10


class TestSoftClipper:
    def test_process_preserves_length(self, mono_audio):
        result = SoftClipper(drive=2.0).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestCompressor:
    def test_process_preserves_length(self, mono_audio):
        result = Compressor().process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate

    def test_stereo(self, stereo_audio):
        result = Compressor().process(stereo_audio)
        assert len(result.samples) == len(stereo_audio.samples)
        assert result.channels == 2


class TestDelay:
    def test_process_returns_audio(self, mono_audio):
        result = Delay(delay_time=0.05).process(mono_audio)
        # Delay extends the signal
        assert len(result.samples) >= len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestReverb:
    def test_process_returns_audio(self, mono_audio):
        result = Reverb(room_size=0.3, mix=0.2).process(mono_audio)
        assert len(result.samples) >= len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestChorus:
    def test_process_preserves_length(self, mono_audio):
        result = Chorus().process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestLowPassFilter:
    def test_process_preserves_length(self, mono_audio):
        result = LowPassFilter(cutoff=500.0).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestHighPassFilter:
    def test_process_preserves_length(self, mono_audio):
        result = HighPassFilter(cutoff=500.0).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestBitCrusher:
    def test_process_preserves_length(self, mono_audio):
        result = BitCrusher(bit_depth=4).process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestEffectChain:
    def test_chain_processes_in_order(self, mono_audio):
        chain = EffectChain(Gain(level=0.5), Limiter(threshold=0.2))
        result = chain.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate
        assert np.max(np.abs(result.samples)) <= 0.2 + 1e-10

    def test_add_method(self):
        chain = EffectChain()
        chain.add(Gain(level=1.0)).add(Limiter())
        assert len(list(chain)) == 2


class TestSidechainEnvelope:
    def test_process_preserves_length(self, mono_audio):
        sc = SidechainEnvelope(bpm=120.0, depth=0.5)
        result = sc.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestPumpingBass:
    def test_process_preserves_length(self, mono_audio):
        pb = PumpingBass(bpm=120.0)
        result = pb.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestSidechainCompressor:
    def test_no_trigger_passthrough(self, mono_audio):
        sc = SidechainCompressor()
        result = sc.process(mono_audio)
        np.testing.assert_array_equal(result.samples, mono_audio.samples)

    def test_with_trigger(self, mono_audio):
        sc = SidechainCompressor()
        sc.set_trigger(mono_audio)
        result = sc.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)
        assert result.sample_rate == mono_audio.sample_rate


class TestSidechainPresets:
    def test_classic_house(self, mono_audio):
        sc = SidechainPresets.classic_house(bpm=128)
        result = sc.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)

    def test_heavy_edm(self, mono_audio):
        sc = SidechainPresets.heavy_edm()
        result = sc.process(mono_audio)
        assert len(result.samples) == len(mono_audio.samples)


class TestSidechainBuilder:
    def test_build_envelope(self):
        sc = create_sidechain().tempo(128).depth(0.7).quarter_notes().build()
        assert isinstance(sc, SidechainEnvelope)

    def test_build_compressor(self, mono_audio):
        sc = create_sidechain().trigger(mono_audio).build()
        assert isinstance(sc, SidechainCompressor)


class TestBackwardCompatImports:
    def test_import_from_beatmaker_sidechain(self):
        """Ensure old import path still works."""
        from beatmaker.sidechain import SidechainCompressor as SC
        assert SC is SidechainCompressor

    def test_import_from_beatmaker_effects(self):
        """Ensure effects are importable from the package."""
        from beatmaker.effects import Gain as G
        assert G is Gain
