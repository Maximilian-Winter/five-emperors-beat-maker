"""Tests for beatmaker.io — audio file I/O and SampleLibrary."""

import pytest
import tempfile
from pathlib import Path
import numpy as np

from beatmaker.io import load_audio, save_audio, SampleLibrary, SampleLibraryConfig
from beatmaker.core import AudioData


class TestLoadSaveAudio:
    """WAV file I/O roundtrip tests."""

    def test_save_and_load_mono(self, sample_audio):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            save_audio(sample_audio, path)
            loaded = load_audio(path)
            assert loaded.channels == 1
            assert loaded.sample_rate == sample_audio.sample_rate
            assert loaded.num_samples == sample_audio.num_samples
        finally:
            path.unlink(missing_ok=True)

    def test_save_and_load_stereo(self, stereo_audio):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            save_audio(stereo_audio, path)
            loaded = load_audio(path)
            assert loaded.channels == 2
        finally:
            path.unlink(missing_ok=True)


class TestSampleLibraryConfig:
    """SampleLibraryConfig tests."""

    def test_defaults(self):
        cfg = SampleLibraryConfig()
        assert '.wav' in cfg.extensions
        assert cfg.auto_tag is True
        assert cfg.lazy is False

    def test_custom(self):
        cfg = SampleLibraryConfig(
            normalize=True,
            target_sample_rate=22050,
            trim_silence=True,
        )
        assert cfg.normalize is True
        assert cfg.target_sample_rate == 22050


class TestSampleLibrary:
    """SampleLibrary tests."""

    def test_create_empty(self):
        lib = SampleLibrary()
        assert len(lib) == 0

    def test_add_and_get(self, sample_audio):
        from beatmaker.core import Sample
        lib = SampleLibrary()
        s = Sample("kick", sample_audio, tags=["drums"])
        lib.add(s)
        assert lib["kick"] is s

    def test_by_tag(self, sample_audio):
        from beatmaker.core import Sample
        lib = SampleLibrary()
        lib.add(Sample("kick", sample_audio, tags=["drums", "kick"]))
        lib.add(Sample("snare", sample_audio, tags=["drums", "snare"]))
        lib.add(Sample("bass", sample_audio, tags=["bass"]))
        found = lib.by_tag("drums")
        assert len(found) == 2
