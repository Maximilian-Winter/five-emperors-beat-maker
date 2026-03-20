"""
Shared test fixtures for the beatmaker test suite.
"""

import pytest
import numpy as np


@pytest.fixture
def sample_rate():
    """Standard sample rate for tests."""
    return 44100


@pytest.fixture
def sample_audio(sample_rate):
    """A short AudioData (0.1s sine wave at 440Hz)."""
    from beatmaker.core import AudioData

    duration = 0.1
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    samples = np.sin(2 * np.pi * 440 * t)
    return AudioData(samples, sample_rate)


@pytest.fixture
def stereo_audio(sample_rate):
    """A short stereo AudioData."""
    from beatmaker.core import AudioData

    duration = 0.1
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, False)
    left = np.sin(2 * np.pi * 440 * t)
    right = np.sin(2 * np.pi * 554 * t)
    samples = np.column_stack([left, right])
    return AudioData(samples, sample_rate, channels=2)


@pytest.fixture
def drum_samples():
    """Pre-built drum samples for builder tests."""
    from beatmaker.synth import DrumSynth

    return {
        "kick": DrumSynth.kick(),
        "snare": DrumSynth.snare(),
        "hihat": DrumSynth.hihat(),
        "clap": DrumSynth.clap(),
    }
