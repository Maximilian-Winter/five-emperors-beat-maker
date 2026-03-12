"""
靈寶五帝策使編碼之法 - Extended Synthesizers Module
A garden of sonic textures for melodic expression.

By the Dark Turtle's authority,
Let frequencies flow and interweave,
Deep harmonics rising like mist,
急急如律令敕
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Tuple
import numpy as np

from .core import AudioData, Sample
from .synth import (
    ADSREnvelope, Oscillator, Waveform,
    sine_wave, sawtooth_wave, square_wave, triangle_wave,
    white_noise, midi_to_freq
)


@dataclass
class LFO:
    """Low Frequency Oscillator for modulation."""
    rate: float = 1.0      # Hz
    depth: float = 1.0     # Modulation depth
    waveform: str = 'sine'  # sine, triangle, saw, square, random
    phase: float = 0.0     # Starting phase (0-1)
    
    def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Generate LFO signal."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        phase_offset = self.phase * 2 * np.pi
        
        if self.waveform == 'sine':
            signal = np.sin(2 * np.pi * self.rate * t + phase_offset)
        elif self.waveform == 'triangle':
            signal = 2 * np.abs(2 * ((t * self.rate + self.phase) % 1) - 1) - 1
        elif self.waveform == 'saw':
            signal = 2 * ((t * self.rate + self.phase) % 1) - 1
        elif self.waveform == 'square':
            signal = np.sign(np.sin(2 * np.pi * self.rate * t + phase_offset))
        elif self.waveform == 'random':
            # Sample and hold random
            samples_per_cycle = int(sample_rate / self.rate)
            num_cycles = int(duration * self.rate) + 1
            values = np.random.random(num_cycles) * 2 - 1
            signal = np.repeat(values, samples_per_cycle)[:int(duration * sample_rate)]
        else:
            signal = np.sin(2 * np.pi * self.rate * t)
        
        return signal * self.depth


@dataclass
class Filter:
    """Simple resonant filter."""
    cutoff: float = 1000.0
    resonance: float = 0.0  # 0-1
    filter_type: str = 'lowpass'  # lowpass, highpass, bandpass
    
    def process(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply filter to samples."""
        # Normalized cutoff
        w0 = 2 * np.pi * self.cutoff / sample_rate
        w0 = min(w0, np.pi * 0.99)  # Prevent instability
        
        # Resonance (Q factor)
        Q = 0.5 + self.resonance * 10
        alpha = np.sin(w0) / (2 * Q)
        
        cos_w0 = np.cos(w0)
        
        # Biquad coefficients
        if self.filter_type == 'lowpass':
            b0 = (1 - cos_w0) / 2
            b1 = 1 - cos_w0
            b2 = (1 - cos_w0) / 2
        elif self.filter_type == 'highpass':
            b0 = (1 + cos_w0) / 2
            b1 = -(1 + cos_w0)
            b2 = (1 + cos_w0) / 2
        elif self.filter_type == 'bandpass':
            b0 = alpha
            b1 = 0
            b2 = -alpha
        else:
            return samples
        
        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha
        
        # Normalize
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0
        
        # Apply filter
        output = np.zeros_like(samples)
        x1, x2, y1, y2 = 0.0, 0.0, 0.0, 0.0
        
        for i in range(len(samples)):
            x0 = samples[i]
            y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            output[i] = y0
            
            x2, x1 = x1, x0
            y2, y1 = y1, y0
        
        return output


class PadSynth:
    """
    Synthesizer for lush pad sounds.
    
    Creates warm, evolving textures perfect for ambient and melodic use.
    """
    
    @staticmethod
    def warm_pad(frequency: float, duration: float,
                 num_voices: int = 4, detune: float = 0.1,
                 envelope: Optional[ADSREnvelope] = None,
                 sample_rate: int = 44100) -> Sample:
        """
        Create a warm detuned pad.
        
        Args:
            frequency: Base frequency in Hz
            duration: Note duration in seconds
            num_voices: Number of detuned voices (more = thicker)
            detune: Detune amount in semitones
            envelope: ADSR envelope (default: slow attack pad)
        """
        if envelope is None:
            envelope = ADSREnvelope(attack=0.5, decay=0.3, sustain=0.7, release=0.8)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        output = np.zeros_like(t)
        
        # Generate detuned voices
        for i in range(num_voices):
            # Spread detune evenly around center
            voice_detune = (i - num_voices / 2) * (detune / num_voices)
            voice_freq = frequency * (2 ** (voice_detune / 12))
            
            # Mix of saw and sine for warmth
            saw = sawtooth_wave(voice_freq, duration, sample_rate).samples
            sine = sine_wave(voice_freq, duration, sample_rate).samples
            
            voice = saw * 0.6 + sine * 0.4
            output += voice / num_voices
        
        # Apply slow LFO for movement
        lfo = LFO(rate=0.3, depth=0.02, waveform='sine')
        modulation = 1 + lfo.generate(duration, sample_rate)
        output *= modulation
        
        # Low-pass filter for smoothness
        filt = Filter(cutoff=2000, resonance=0.2)
        output = filt.process(output, sample_rate)
        
        # Apply envelope
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        
        return Sample(f"warm_pad_{frequency:.0f}hz", audio, tags=["pad", "warm"])
    
    @staticmethod
    def string_pad(frequency: float, duration: float,
                   envelope: Optional[ADSREnvelope] = None,
                   sample_rate: int = 44100) -> Sample:
        """Create a string-like pad sound."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.3, decay=0.2, sustain=0.8, release=0.5)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Multiple harmonics for string-like character
        output = np.zeros_like(t)
        harmonics = [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.2), (5, 0.1)]
        
        for harmonic, amplitude in harmonics:
            # Slight detuning for chorus effect
            detune = np.random.uniform(-0.02, 0.02)
            freq = frequency * harmonic * (1 + detune)
            
            wave = sawtooth_wave(freq, duration, sample_rate).samples
            output += wave * amplitude
        
        # Gentle filtering
        filt = Filter(cutoff=3000, resonance=0.1)
        output = filt.process(output, sample_rate)
        
        # Normalize
        output /= np.max(np.abs(output))
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        
        return Sample(f"string_pad_{frequency:.0f}hz", audio, tags=["pad", "string"])
    
    @staticmethod
    def ambient_pad(frequency: float, duration: float,
                    sample_rate: int = 44100) -> Sample:
        """Create an evolving ambient pad."""
        envelope = ADSREnvelope(attack=2.0, decay=1.0, sustain=0.6, release=2.0)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Base tone
        base = sine_wave(frequency, duration, sample_rate).samples
        
        # Add subtle harmonics
        harm2 = sine_wave(frequency * 2, duration, sample_rate).samples * 0.3
        harm3 = sine_wave(frequency * 3, duration, sample_rate).samples * 0.1
        
        output = base + harm2 + harm3
        
        # Evolving filter with LFO
        lfo = LFO(rate=0.1, depth=500, waveform='sine')
        filter_mod = 1000 + lfo.generate(duration, sample_rate)
        
        # Apply time-varying filter (simplified)
        filt = Filter(cutoff=1500, resonance=0.3)
        output = filt.process(output, sample_rate)
        
        # Add subtle noise
        noise = white_noise(duration, sample_rate, 0.02).samples
        output += noise
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        audio = audio.normalize(0.8)
        
        return Sample(f"ambient_pad_{frequency:.0f}hz", audio, tags=["pad", "ambient"])


class LeadSynth:
    """
    Synthesizer for lead sounds.
    
    Creates cutting, expressive lead tones.
    """
    
    @staticmethod
    def saw_lead(frequency: float, duration: float,
                 envelope: Optional[ADSREnvelope] = None,
                 filter_env: bool = True,
                 sample_rate: int = 44100) -> Sample:
        """Classic saw lead with filter envelope."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.2, sustain=0.7, release=0.3)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Two slightly detuned saws
        saw1 = sawtooth_wave(frequency, duration, sample_rate).samples
        saw2 = sawtooth_wave(frequency * 1.005, duration, sample_rate).samples
        
        output = (saw1 + saw2) / 2
        
        if filter_env:
            # Filter envelope (opens then closes)
            filter_env_time = np.exp(-t * 5)
            cutoff_base = 500
            cutoff_range = 4000
            
            # Approximate time-varying filter
            for i, cutoff in enumerate(cutoff_base + filter_env_time * cutoff_range):
                pass  # Simplified - just use static filter
            
            filt = Filter(cutoff=2500, resonance=0.4)
            output = filt.process(output, sample_rate)
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        audio = audio.normalize(0.9)
        
        return Sample(f"saw_lead_{frequency:.0f}hz", audio, tags=["lead", "saw"])
    
    @staticmethod
    def square_lead(frequency: float, duration: float,
                    pulse_width: float = 0.5,
                    envelope: Optional[ADSREnvelope] = None,
                    sample_rate: int = 44100) -> Sample:
        """Square/pulse wave lead."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.2)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Pulse wave with adjustable width
        phase = (t * frequency) % 1.0
        output = np.where(phase < pulse_width, 1.0, -1.0).astype(np.float64)
        
        # Add sub oscillator
        sub = sine_wave(frequency / 2, duration, sample_rate).samples * 0.3
        output += sub
        
        # Filter
        filt = Filter(cutoff=3000, resonance=0.3)
        output = filt.process(output, sample_rate)
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        
        return Sample(f"square_lead_{frequency:.0f}hz", audio, tags=["lead", "square"])
    
    @staticmethod
    def fm_lead(frequency: float, duration: float,
                mod_ratio: float = 2.0, mod_index: float = 3.0,
                envelope: Optional[ADSREnvelope] = None,
                sample_rate: int = 44100) -> Sample:
        """FM synthesis lead."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.01, decay=0.15, sustain=0.6, release=0.25)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Modulator
        mod_freq = frequency * mod_ratio
        modulator = np.sin(2 * np.pi * mod_freq * t) * mod_index
        
        # Carrier with FM
        output = np.sin(2 * np.pi * frequency * t + modulator)
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        
        return Sample(f"fm_lead_{frequency:.0f}hz", audio, tags=["lead", "fm"])


class PluckSynth:
    """
    Synthesizer for plucked string sounds.
    
    Uses Karplus-Strong and other techniques.
    """
    
    @staticmethod
    def karplus_strong(frequency: float, duration: float,
                       brightness: float = 0.5,
                       sample_rate: int = 44100) -> Sample:
        """
        Karplus-Strong plucked string synthesis.
        
        Args:
            frequency: Note frequency in Hz
            duration: Duration in seconds
            brightness: Tone brightness 0-1 (affects decay)
        """
        num_samples = int(duration * sample_rate)
        delay_samples = int(sample_rate / frequency)
        
        # Initialize buffer with noise burst
        buffer = np.random.random(delay_samples) * 2 - 1
        output = np.zeros(num_samples)
        
        # Damping factor based on brightness
        damping = 0.996 - (1 - brightness) * 0.01
        
        for i in range(num_samples):
            # Read from buffer
            output[i] = buffer[i % delay_samples]
            
            # Average two adjacent samples and apply damping
            idx = i % delay_samples
            next_idx = (i + 1) % delay_samples
            buffer[idx] = damping * 0.5 * (buffer[idx] + buffer[next_idx])
        
        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.9)
        
        return Sample(f"pluck_{frequency:.0f}hz", audio, tags=["pluck", "string"])
    
    @staticmethod
    def synth_pluck(frequency: float, duration: float,
                    envelope: Optional[ADSREnvelope] = None,
                    sample_rate: int = 44100) -> Sample:
        """Synthesized pluck sound."""
        if envelope is None:
            envelope = ADSREnvelope(attack=0.001, decay=0.3, sustain=0.0, release=0.2)
        
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Mix of waves
        saw = sawtooth_wave(frequency, duration, sample_rate).samples
        square = square_wave(frequency, duration, sample_rate, duty_cycle=0.3).samples
        
        output = saw * 0.7 + square * 0.3
        
        # Aggressive filter envelope
        filter_env = np.exp(-t * 20)
        cutoff_values = 500 + filter_env * 5000
        
        # Static filter approximation
        filt = Filter(cutoff=2000, resonance=0.5)
        output = filt.process(output, sample_rate)
        
        audio = AudioData(output, sample_rate)
        audio = envelope.apply(audio)
        
        return Sample(f"synth_pluck_{frequency:.0f}hz", audio, tags=["pluck", "synth"])
    
    @staticmethod
    def bell(frequency: float, duration: float,
             sample_rate: int = 44100) -> Sample:
        """Bell-like FM pluck."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # FM bell synthesis
        mod_freq = frequency * 1.4  # Inharmonic ratio for bell character
        mod_index = 5 * np.exp(-t * 3)  # Decaying modulation
        
        modulator = np.sin(2 * np.pi * mod_freq * t) * mod_index
        carrier = np.sin(2 * np.pi * frequency * t + modulator)
        
        # Add higher partial
        partial = np.sin(2 * np.pi * frequency * 2.76 * t) * 0.3 * np.exp(-t * 4)
        
        output = carrier + partial
        
        # Amplitude envelope
        amp_env = np.exp(-t * 2)
        output *= amp_env
        
        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.8)
        
        return Sample(f"bell_{frequency:.0f}hz", audio, tags=["pluck", "bell"])


class FXSynth:
    """
    Synthesizer for special effects and textures.
    """
    
    @staticmethod
    def riser(duration: float, start_freq: float = 100,
              end_freq: float = 2000, sample_rate: int = 44100) -> Sample:
        """Upward sweeping riser effect."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Exponential frequency sweep
        freq_curve = start_freq * (end_freq / start_freq) ** (t / duration)
        
        # Generate sweep
        phase = np.cumsum(2 * np.pi * freq_curve / sample_rate)
        output = np.sin(phase)
        
        # Add noise layer
        noise = white_noise(duration, sample_rate, 0.3).samples
        noise *= t / duration  # Fade in noise
        
        output = output * 0.7 + noise * 0.3
        
        # Rising amplitude
        output *= (t / duration) ** 0.5
        
        audio = AudioData(output, sample_rate)
        
        return Sample("riser", audio, tags=["fx", "riser"])
    
    @staticmethod
    def downer(duration: float, start_freq: float = 2000,
               end_freq: float = 50, sample_rate: int = 44100) -> Sample:
        """Downward sweep effect."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        freq_curve = start_freq * (end_freq / start_freq) ** (t / duration)
        phase = np.cumsum(2 * np.pi * freq_curve / sample_rate)
        output = np.sin(phase)
        
        # Falling amplitude
        output *= 1 - (t / duration) ** 2
        
        audio = AudioData(output, sample_rate)
        
        return Sample("downer", audio, tags=["fx", "downer"])
    
    @staticmethod
    def noise_sweep(duration: float, sample_rate: int = 44100) -> Sample:
        """Filtered noise sweep."""
        noise = white_noise(duration, sample_rate).samples
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Time-varying filter (simplified - multiple passes)
        output = noise.copy()
        
        # Apply filter
        filt = Filter(cutoff=1500, resonance=0.6, filter_type='bandpass')
        output = filt.process(output, sample_rate)
        
        # Amplitude envelope
        env = np.sin(np.pi * t / duration)
        output *= env
        
        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.7)
        
        return Sample("noise_sweep", audio, tags=["fx", "noise"])
    
    @staticmethod
    def impact(sample_rate: int = 44100) -> Sample:
        """Cinematic impact sound."""
        duration = 1.5
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Low boom
        boom_freq = 40
        boom = np.sin(2 * np.pi * boom_freq * t) * np.exp(-t * 3)
        
        # High transient
        transient = white_noise(0.05, sample_rate).samples
        transient_padded = np.zeros(len(t))
        transient_padded[:len(transient)] = transient * np.exp(-np.linspace(0, 1, len(transient)) * 20)
        
        # Combine
        output = boom * 0.8 + transient_padded * 0.5
        
        audio = AudioData(output, sample_rate)
        audio = audio.normalize(0.95)
        
        return Sample("impact", audio, tags=["fx", "impact"])


# Convenience functions
def create_pad(note: str, duration: float, pad_type: str = 'warm') -> Sample:
    """Quick pad creation."""
    from .synth import note_to_freq
    freq = note_to_freq(note)
    
    if pad_type == 'warm':
        return PadSynth.warm_pad(freq, duration)
    elif pad_type == 'string':
        return PadSynth.string_pad(freq, duration)
    elif pad_type == 'ambient':
        return PadSynth.ambient_pad(freq, duration)
    else:
        return PadSynth.warm_pad(freq, duration)


def create_lead(note: str, duration: float, lead_type: str = 'saw') -> Sample:
    """Quick lead creation."""
    from .synth import note_to_freq
    freq = note_to_freq(note)
    
    if lead_type == 'saw':
        return LeadSynth.saw_lead(freq, duration)
    elif lead_type == 'square':
        return LeadSynth.square_lead(freq, duration)
    elif lead_type == 'fm':
        return LeadSynth.fm_lead(freq, duration)
    else:
        return LeadSynth.saw_lead(freq, duration)


def create_pluck(note: str, duration: float = 1.0, pluck_type: str = 'karplus') -> Sample:
    """Quick pluck creation."""
    from .synth import note_to_freq
    freq = note_to_freq(note)
    
    if pluck_type == 'karplus':
        return PluckSynth.karplus_strong(freq, duration)
    elif pluck_type == 'synth':
        return PluckSynth.synth_pluck(freq, duration)
    elif pluck_type == 'bell':
        return PluckSynth.bell(freq, duration)
    else:
        return PluckSynth.karplus_strong(freq, duration)
