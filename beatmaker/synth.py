"""
靈寶五帝策使編碼之法 - Synthesis Module
The alchemical forge where pure sound is born from mathematics.

By the Vermilion Bird's authority,
Let this code burn with efficiency,
Cycles consumed with purpose,
急急如律令敕
"""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum, auto

from .core import AudioData, Sample


class Waveform(Enum):
    """Basic waveform types."""
    SINE = auto()
    SQUARE = auto()
    SAWTOOTH = auto()
    TRIANGLE = auto()
    NOISE = auto()


def sine_wave(frequency: float, duration: float, 
              sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    samples = amplitude * np.sin(2 * np.pi * frequency * t)
    return AudioData(samples, sample_rate)


def square_wave(frequency: float, duration: float,
                sample_rate: int = 44100, amplitude: float = 1.0,
                duty_cycle: float = 0.5) -> AudioData:
    """Generate a square wave with adjustable duty cycle."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    phase = (t * frequency) % 1.0
    samples = amplitude * np.where(phase < duty_cycle, 1.0, -1.0)
    return AudioData(samples.astype(np.float64), sample_rate)


def sawtooth_wave(frequency: float, duration: float,
                  sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a sawtooth wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    samples = amplitude * (2.0 * ((t * frequency) % 1.0) - 1.0)
    return AudioData(samples, sample_rate)


def triangle_wave(frequency: float, duration: float,
                  sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData:
    """Generate a triangle wave."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    phase = (t * frequency) % 1.0
    samples = amplitude * (4.0 * np.abs(phase - 0.5) - 1.0)
    return AudioData(samples, sample_rate)


def white_noise(duration: float, sample_rate: int = 44100, 
                amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData:
    """Generate white noise."""
    if seed is not None:
        np.random.seed(seed)
    num_samples = int(duration * sample_rate)
    samples = amplitude * (2.0 * np.random.random(num_samples) - 1.0)
    return AudioData(samples, sample_rate)


def pink_noise(duration: float, sample_rate: int = 44100,
               amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData:
    """Generate pink noise (1/f spectrum) using the Voss-McCartney algorithm."""
    if seed is not None:
        np.random.seed(seed)
    
    num_samples = int(duration * sample_rate)
    num_octaves = 16
    
    # Initialize
    values = np.zeros(num_octaves)
    running_sum = 0.0
    samples = np.zeros(num_samples)
    
    for i in range(num_samples):
        # Determine which octave to update
        k = i
        n_zeros = 0
        while k > 0 and (k & 1) == 0:
            k >>= 1
            n_zeros += 1
        
        if n_zeros < num_octaves:
            running_sum -= values[n_zeros]
            values[n_zeros] = np.random.random() * 2 - 1
            running_sum += values[n_zeros]
        
        samples[i] = running_sum / num_octaves
    
    # Normalize and apply amplitude
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = amplitude * samples / max_val
    
    return AudioData(samples, sample_rate)


@dataclass
class ADSREnvelope:
    """
    Attack-Decay-Sustain-Release envelope generator.
    
    Creates amplitude envelopes for shaping sound over time.
    """
    attack: float = 0.01   # Attack time in seconds
    decay: float = 0.1     # Decay time in seconds
    sustain: float = 0.7   # Sustain level (0.0 - 1.0)
    release: float = 0.2   # Release time in seconds
    
    def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Generate envelope samples for the given duration."""
        # Calculate sample counts
        attack_samples = int(self.attack * sample_rate)
        decay_samples = int(self.decay * sample_rate)
        release_samples = int(self.release * sample_rate)
        total_samples = int(duration * sample_rate)
        
        # Sustain fills the rest
        sustain_samples = max(0, total_samples - attack_samples - decay_samples - release_samples)
        
        # Build envelope segments
        envelope = np.zeros(total_samples)
        idx = 0
        
        # Attack
        if attack_samples > 0:
            attack_end = min(attack_samples, total_samples)
            envelope[idx:attack_end] = np.linspace(0, 1, attack_end - idx)
            idx = attack_end
        
        # Decay
        if idx < total_samples and decay_samples > 0:
            decay_end = min(idx + decay_samples, total_samples)
            envelope[idx:decay_end] = np.linspace(1, self.sustain, decay_end - idx)
            idx = decay_end
        
        # Sustain
        if idx < total_samples and sustain_samples > 0:
            sustain_end = min(idx + sustain_samples, total_samples)
            envelope[idx:sustain_end] = self.sustain
            idx = sustain_end
        
        # Release
        if idx < total_samples:
            envelope[idx:] = np.linspace(self.sustain, 0, total_samples - idx)
        
        return envelope
    
    def apply(self, audio: AudioData) -> AudioData:
        """Apply the envelope to audio data."""
        envelope = self.generate(audio.duration, audio.sample_rate)
        
        # Ensure envelope matches audio length exactly
        if len(envelope) != len(audio.samples):
            if len(envelope) > len(audio.samples):
                envelope = envelope[:len(audio.samples)]
            else:
                padded = np.zeros(len(audio.samples))
                padded[:len(envelope)] = envelope
                envelope = padded
        
        if audio.channels == 1:
            samples = audio.samples * envelope
        else:
            samples = audio.samples * envelope[:, np.newaxis]
        
        return AudioData(samples, audio.sample_rate, audio.channels)


class Oscillator:
    """
    Versatile oscillator for synthesis.
    
    Supports multiple waveforms with various modulation options.
    """
    
    def __init__(self, waveform: Waveform = Waveform.SINE,
                 detune: float = 0.0,
                 phase: float = 0.0):
        self.waveform = waveform
        self.detune = detune  # In cents (100 cents = 1 semitone)
        self.phase = phase    # Phase offset in radians
    
    def generate(self, frequency: float, duration: float,
                 sample_rate: int = 44100) -> AudioData:
        """Generate audio at the specified frequency."""
        # Apply detune
        actual_freq = frequency * (2 ** (self.detune / 1200))
        
        if self.waveform == Waveform.SINE:
            audio = sine_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.SQUARE:
            audio = square_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.SAWTOOTH:
            audio = sawtooth_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.TRIANGLE:
            audio = triangle_wave(actual_freq, duration, sample_rate)
        elif self.waveform == Waveform.NOISE:
            audio = white_noise(duration, sample_rate)
        else:
            raise ValueError(f"Unknown waveform: {self.waveform}")
        
        # Apply phase offset
        if self.phase != 0:
            phase_samples = int((self.phase / (2 * np.pi)) * sample_rate / actual_freq)
            if phase_samples > 0:
                audio.samples = np.roll(audio.samples, phase_samples)
        
        return audio


class DrumSynth:
    """
    Synthesizer optimized for drum and percussion sounds.
    """
    
    @staticmethod
    def kick(duration: float = 0.5, pitch: float = 60.0, 
             punch: float = 0.8, sample_rate: int = 44100) -> Sample:
        """Synthesize a kick drum."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Pitch envelope - rapid drop from high to low
        pitch_env = pitch * np.exp(-30 * t) + 40
        
        # Generate sine wave with pitch envelope
        phase = np.cumsum(2 * np.pi * pitch_env / sample_rate)
        tone = np.sin(phase)
        
        # Add punch (click transient)
        click_duration = 0.01
        click_samples = int(click_duration * sample_rate)
        click = white_noise(click_duration, sample_rate, punch).samples
        click *= np.exp(-t[:click_samples] * 200)
        
        # Combine
        samples = tone.copy()
        samples[:click_samples] += click
        
        # Apply amplitude envelope
        amp_env = np.exp(-5 * t)
        samples *= amp_env
        
        audio = AudioData(samples, sample_rate)
        return Sample("kick", audio, tags=["drums", "kick"])
    
    @staticmethod
    def snare(duration: float = 0.3, tone_pitch: float = 180.0,
              noise_amount: float = 0.6, sample_rate: int = 44100) -> Sample:
        """Synthesize a snare drum."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Tone component (body)
        tone_env = np.exp(-20 * t)
        tone = np.sin(2 * np.pi * tone_pitch * t) * tone_env
        
        # Noise component (snares)
        noise = white_noise(duration, sample_rate).samples
        noise_env = np.exp(-15 * t)
        noise *= noise_env * noise_amount
        
        # Combine
        samples = tone * (1 - noise_amount) + noise
        
        audio = AudioData(samples, sample_rate)
        return Sample("snare", audio, tags=["drums", "snare"])
    
    @staticmethod
    def hihat(duration: float = 0.1, open_amount: float = 0.0,
              sample_rate: int = 44100) -> Sample:
        """Synthesize a hi-hat (closed to open based on open_amount)."""
        # Longer duration for open hi-hat
        actual_duration = duration + (open_amount * 0.4)
        t = np.linspace(0, actual_duration, int(actual_duration * sample_rate), False)
        
        # Metallic noise (band-limited)
        noise = white_noise(actual_duration, sample_rate).samples
        
        # Add some tonal content
        tone1 = np.sin(2 * np.pi * 3000 * t) * 0.3
        tone2 = np.sin(2 * np.pi * 6000 * t) * 0.2
        
        samples = noise * 0.5 + tone1 + tone2
        
        # Envelope (faster decay for closed)
        decay_rate = 30 - (open_amount * 25)  # 30 for closed, 5 for open
        envelope = np.exp(-decay_rate * t)
        samples *= envelope
        
        name = "hihat_open" if open_amount > 0.5 else "hihat_closed"
        audio = AudioData(samples, sample_rate)
        return Sample(name, audio, tags=["drums", "hihat"])
    
    @staticmethod
    def clap(duration: float = 0.2, spread: float = 0.02,
             sample_rate: int = 44100) -> Sample:
        """Synthesize a clap sound with multiple transients."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        num_samples = len(t)
        samples = np.zeros(num_samples)
        
        # Multiple noise bursts (simulating multiple hands)
        num_bursts = 4
        burst_times = np.linspace(0, spread, num_bursts)
        
        for burst_time in burst_times:
            burst_start = int(burst_time * sample_rate)
            burst_duration = 0.02
            burst_samples = int(burst_duration * sample_rate)
            
            if burst_start + burst_samples <= num_samples:
                burst = white_noise(burst_duration, sample_rate).samples
                burst *= np.exp(-np.linspace(0, 1, burst_samples) * 30)
                samples[burst_start:burst_start + burst_samples] += burst
        
        # Add tail
        tail_env = np.exp(-15 * t)
        tail = white_noise(duration, sample_rate).samples * tail_env * 0.3
        samples += tail
        
        audio = AudioData(samples, sample_rate).normalize()
        return Sample("clap", audio, tags=["drums", "clap"])


class BassSynth:
    """Synthesizer for bass sounds."""
    
    @staticmethod
    def sub_bass(frequency: float, duration: float,
                 envelope: Optional[ADSREnvelope] = None,
                 sample_rate: int = 44100) -> Sample:
        """Pure sub-bass sine wave."""
        audio = sine_wave(frequency, duration, sample_rate)
        
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.1)
        
        audio = envelope.apply(audio)
        return Sample(f"sub_bass_{frequency}hz", audio, tags=["bass", "sub"])
    
    @staticmethod
    def acid_bass(frequency: float, duration: float,
                  filter_freq: float = 500.0, resonance: float = 0.7,
                  envelope: Optional[ADSREnvelope] = None,
                  sample_rate: int = 44100) -> Sample:
        """Classic acid bass (303-style)."""
        # Sawtooth base
        audio = sawtooth_wave(frequency, duration, sample_rate)
        
        # Simple low-pass filter simulation with envelope
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        filter_env = np.exp(-3 * t) * filter_freq + 100
        
        # Apply very basic filtering (proper implementation would use scipy)
        samples = audio.samples
        filtered = np.zeros_like(samples)
        cutoff = 0.1  # Simplified cutoff
        
        for i in range(1, len(samples)):
            filtered[i] = filtered[i-1] + cutoff * (samples[i] - filtered[i-1])
        
        audio = AudioData(filtered, sample_rate)
        
        if envelope is None:
            envelope = ADSREnvelope(attack=0.001, decay=0.2, sustain=0.5, release=0.1)
        
        audio = envelope.apply(audio)
        return Sample(f"acid_bass_{frequency}hz", audio, tags=["bass", "acid"])


def midi_to_freq(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def freq_to_midi(frequency: float) -> int:
    """Convert frequency in Hz to nearest MIDI note number."""
    return int(round(69 + 12 * np.log2(frequency / 440.0)))


# Common note frequencies
NOTE_FREQS = {
    'C': [16.35, 32.70, 65.41, 130.81, 261.63, 523.25, 1046.50, 2093.00],
    'D': [18.35, 36.71, 73.42, 146.83, 293.66, 587.33, 1174.66, 2349.32],
    'E': [20.60, 41.20, 82.41, 164.81, 329.63, 659.25, 1318.51, 2637.02],
    'F': [21.83, 43.65, 87.31, 174.61, 349.23, 698.46, 1396.91, 2793.83],
    'G': [24.50, 49.00, 98.00, 196.00, 392.00, 783.99, 1567.98, 3135.96],
    'A': [27.50, 55.00, 110.00, 220.00, 440.00, 880.00, 1760.00, 3520.00],
    'B': [30.87, 61.74, 123.47, 246.94, 493.88, 987.77, 1975.53, 3951.07],
}


def note_to_freq(note: str) -> float:
    """
    Convert note name to frequency.
    
    Examples: 'A4' -> 440.0, 'C3' -> 130.81
    """
    note_name = note[:-1].upper()
    octave = int(note[-1])
    
    if note_name not in NOTE_FREQS:
        # Handle sharps/flats
        base_note = note_name[0]
        if len(note_name) > 1 and note_name[1] == '#':
            base_idx = list(NOTE_FREQS.keys()).index(base_note)
            next_note = list(NOTE_FREQS.keys())[(base_idx + 1) % 7]
            freq = (NOTE_FREQS[base_note][octave] + NOTE_FREQS[next_note][octave]) / 2
            return freq
        elif len(note_name) > 1 and note_name[1] == 'B':
            # Flat: one semitone below base note
            freq = NOTE_FREQS[base_note][octave] / (2 ** (1 / 12))
            return freq
        raise ValueError(f"Unknown note: {note}")
    
    return NOTE_FREQS[note_name][octave]
