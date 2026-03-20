"""
Source nodes: nodes that generate or inject signal into the graph.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from ..core import AudioData, Track
from ..synth import (
    sine_wave, sawtooth_wave, square_wave, triangle_wave,
    white_noise, pink_noise,
)
from .core import SignalNode


class AudioInput(SignalNode):
    """
    Injects existing AudioData into the graph.

    This is how external audio enters the signal graph --
    a voice recording, a synthesized tone, a loaded sample.
    """

    def __init__(self, audio: Optional[AudioData] = None,
                 name: str = "input"):
        self.audio = audio
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def set_audio(self, audio: AudioData):
        """Set or replace the audio data (used by GraphEffect)."""
        self.audio = audio

    def process_graph(self, inputs, sample_rate, num_samples):
        if self.audio is None:
            return {"main": np.zeros(num_samples)}

        audio = self.audio
        if audio.sample_rate != sample_rate:
            audio = audio.resample(sample_rate)

        if audio.channels > 1:
            audio = audio.to_mono()

        samples = audio.samples
        if len(samples) >= num_samples:
            return {"main": samples[:num_samples].copy()}
        else:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            return {"main": padded}


class TrackInput(SignalNode):
    """Render a Track and inject it into the graph."""

    def __init__(self, track: Track, bpm: float = 120.0, name: str = "track"):
        self.track = track
        self.bpm = bpm
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        audio = self.track.render(sample_rate, 1, self.bpm)
        samples = audio.samples
        if len(samples) >= num_samples:
            return {"main": samples[:num_samples].copy()}
        else:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            return {"main": padded}


class OscillatorNode(SignalNode):
    """
    Generates a periodic waveform.

    Wraps the existing waveform generators, producing continuous
    signal for the duration of the graph render.
    """

    def __init__(self, frequency: float = 440.0,
                 waveform: str = 'sine',
                 amplitude: float = 1.0,
                 name: str = ""):
        self.frequency = frequency
        self.waveform = waveform
        self.amplitude = amplitude
        super().__init__(name=name or f"osc_{frequency:.0f}hz")

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        duration = num_samples / sample_rate

        if self.waveform == 'sine':
            audio = sine_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'saw' or self.waveform == 'sawtooth':
            audio = sawtooth_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'square':
            audio = square_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'triangle':
            audio = triangle_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'noise' or self.waveform == 'white':
            audio = white_noise(duration, sample_rate, self.amplitude)
        elif self.waveform == 'pink':
            audio = pink_noise(duration, sample_rate, self.amplitude)
        else:
            audio = sine_wave(self.frequency, duration, sample_rate, self.amplitude)

        samples = audio.samples[:num_samples]
        return {"main": samples}


class NoiseNode(SignalNode):
    """Generates white or pink noise."""

    def __init__(self, color: str = 'white', amplitude: float = 1.0,
                 name: str = "noise"):
        self.color = color
        self.amplitude = amplitude
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        duration = num_samples / sample_rate
        if self.color == 'pink':
            audio = pink_noise(duration, sample_rate, self.amplitude)
        else:
            audio = white_noise(duration, sample_rate, self.amplitude)
        return {"main": audio.samples[:num_samples]}
