"""
靈寶五帝策使編碼之法 - Effects Module
Transformations that shape and color the raw sound.

By the White Tiger's authority,
Let no flaw escape the hunt,
Sharp as blade, vigilant as guardian,
急急如律令敕
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod

from .core import AudioData, AudioEffect


@dataclass
class Gain(AudioEffect):
    """Simple gain/volume adjustment."""
    level: float = 1.0  # Linear gain multiplier
    
    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples * self.level
        return AudioData(samples, audio.sample_rate, audio.channels)
    
    @classmethod
    def from_db(cls, db: float) -> 'Gain':
        """Create gain from decibel value."""
        return cls(level=10 ** (db / 20))


@dataclass
class Limiter(AudioEffect):
    """Hard limiter to prevent clipping."""
    threshold: float = 0.95
    
    def process(self, audio: AudioData) -> AudioData:
        samples = np.clip(audio.samples, -self.threshold, self.threshold)
        return AudioData(samples, audio.sample_rate, audio.channels)


@dataclass
class SoftClipper(AudioEffect):
    """Soft clipping for warm saturation."""
    drive: float = 1.0  # Amount of drive/saturation
    
    def process(self, audio: AudioData) -> AudioData:
        # Apply drive
        samples = audio.samples * self.drive
        # Soft clip using tanh
        samples = np.tanh(samples)
        return AudioData(samples, audio.sample_rate, audio.channels)


@dataclass
class Delay(AudioEffect):
    """Simple delay effect."""
    delay_time: float = 0.25  # Delay time in seconds
    feedback: float = 0.3     # Feedback amount (0.0 - 1.0)
    mix: float = 0.5          # Wet/dry mix (0.0 = dry, 1.0 = wet)
    
    def process(self, audio: AudioData) -> AudioData:
        delay_samples = int(self.delay_time * audio.sample_rate)
        
        if audio.channels == 1:
            output = np.zeros(len(audio.samples) + delay_samples * 3)
            output[:len(audio.samples)] = audio.samples
            
            # Apply feedback delay
            for i in range(3):  # 3 delay taps
                offset = delay_samples * (i + 1)
                gain = self.feedback ** (i + 1)
                output[offset:offset + len(audio.samples)] += audio.samples * gain
            
            # Trim to original length + some tail
            output = output[:len(audio.samples) + delay_samples * 2]
        else:
            output = np.zeros((len(audio.samples) + delay_samples * 3, audio.channels))
            output[:len(audio.samples)] = audio.samples
            
            for i in range(3):
                offset = delay_samples * (i + 1)
                gain = self.feedback ** (i + 1)
                output[offset:offset + len(audio.samples)] += audio.samples * gain
            
            output = output[:len(audio.samples) + delay_samples * 2]
        
        # Mix dry and wet
        result = np.zeros_like(output)
        dry_length = min(len(audio.samples), len(output))
        result[:dry_length] = audio.samples[:dry_length] * (1 - self.mix)
        result += output * self.mix
        
        return AudioData(result, audio.sample_rate, audio.channels)


@dataclass
class Reverb(AudioEffect):
    """
    Simple algorithmic reverb using comb and allpass filters.
    """
    room_size: float = 0.5   # 0.0 - 1.0
    damping: float = 0.5     # High frequency damping
    mix: float = 0.3         # Wet/dry mix
    
    def process(self, audio: AudioData) -> AudioData:
        # Convert to mono for processing if stereo
        if audio.channels == 2:
            mono = audio.to_mono()
        else:
            mono = audio
        
        samples = mono.samples
        sr = audio.sample_rate
        
        # Comb filter delays (in samples) scaled by room size
        comb_delays = [
            int(0.0297 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0371 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0411 * sr * (0.5 + self.room_size * 0.5)),
            int(0.0437 * sr * (0.5 + self.room_size * 0.5)),
        ]
        
        # Allpass filter delays
        allpass_delays = [
            int(0.0050 * sr),
            int(0.0017 * sr),
        ]
        
        # Process through parallel comb filters
        output_length = len(samples) + max(comb_delays) * 4
        comb_output = np.zeros(output_length)
        
        for delay in comb_delays:
            buffer = np.zeros(output_length)
            buffer[:len(samples)] = samples
            
            feedback = 0.84 * (0.5 + self.room_size * 0.5)
            lp = 0.0  # Low-pass state
            
            for i in range(delay, output_length):
                lp = buffer[i - delay] * (1 - self.damping) + lp * self.damping
                buffer[i] += lp * feedback
            
            comb_output += buffer / len(comb_delays)
        
        # Process through series allpass filters
        output = comb_output
        for delay in allpass_delays:
            temp = np.zeros_like(output)
            g = 0.5
            
            for i in range(delay, len(output)):
                temp[i] = -g * output[i] + output[i - delay] + g * temp[i - delay]
            
            output = temp
        
        # Trim and mix
        output = output[:len(samples) + int(0.5 * sr)]  # Keep 0.5s tail
        
        # Mix dry and wet
        result = np.zeros(len(output))
        result[:len(samples)] = samples * (1 - self.mix)
        result += output * self.mix
        
        # Convert back to stereo if needed
        if audio.channels == 2:
            result = np.column_stack([result, result])
        
        return AudioData(result, audio.sample_rate, audio.channels)


@dataclass  
class LowPassFilter(AudioEffect):
    """Simple one-pole low-pass filter."""
    cutoff: float = 1000.0  # Cutoff frequency in Hz
    
    def process(self, audio: AudioData) -> AudioData:
        # Calculate coefficient
        rc = 1.0 / (2 * np.pi * self.cutoff)
        dt = 1.0 / audio.sample_rate
        alpha = dt / (rc + dt)
        
        if audio.channels == 1:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = output[i-1] + alpha * (audio.samples[i] - output[i-1])
        else:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = output[i-1] + alpha * (audio.samples[i] - output[i-1])
        
        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class HighPassFilter(AudioEffect):
    """Simple one-pole high-pass filter."""
    cutoff: float = 100.0  # Cutoff frequency in Hz
    
    def process(self, audio: AudioData) -> AudioData:
        rc = 1.0 / (2 * np.pi * self.cutoff)
        dt = 1.0 / audio.sample_rate
        alpha = rc / (rc + dt)
        
        if audio.channels == 1:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = alpha * (output[i-1] + audio.samples[i] - audio.samples[i-1])
        else:
            output = np.zeros_like(audio.samples)
            output[0] = audio.samples[0]
            for i in range(1, len(audio.samples)):
                output[i] = alpha * (output[i-1] + audio.samples[i] - audio.samples[i-1])
        
        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class Compressor(AudioEffect):
    """Dynamic range compressor."""
    threshold: float = -10.0  # dB
    ratio: float = 4.0        # Compression ratio
    attack: float = 0.01      # Attack time in seconds
    release: float = 0.1      # Release time in seconds
    makeup_gain: float = 0.0  # Makeup gain in dB
    
    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples.copy()
        sr = audio.sample_rate
        
        # Convert threshold to linear
        threshold_linear = 10 ** (self.threshold / 20)
        
        # Time constants
        attack_coef = np.exp(-1 / (self.attack * sr))
        release_coef = np.exp(-1 / (self.release * sr))
        
        # Envelope follower
        if audio.channels == 1:
            envelope = np.abs(samples)
        else:
            envelope = np.max(np.abs(samples), axis=1)
        
        # Smooth envelope
        smooth_env = np.zeros_like(envelope)
        smooth_env[0] = envelope[0]
        for i in range(1, len(envelope)):
            if envelope[i] > smooth_env[i-1]:
                smooth_env[i] = attack_coef * smooth_env[i-1] + (1 - attack_coef) * envelope[i]
            else:
                smooth_env[i] = release_coef * smooth_env[i-1] + (1 - release_coef) * envelope[i]
        
        # Calculate gain reduction
        gain = np.ones_like(smooth_env)
        above_threshold = smooth_env > threshold_linear
        gain[above_threshold] = (
            threshold_linear + 
            (smooth_env[above_threshold] - threshold_linear) / self.ratio
        ) / smooth_env[above_threshold]
        
        # Apply gain
        if audio.channels == 1:
            output = samples * gain
        else:
            output = samples * gain[:, np.newaxis]
        
        # Apply makeup gain
        makeup_linear = 10 ** (self.makeup_gain / 20)
        output *= makeup_linear
        
        return AudioData(output, audio.sample_rate, audio.channels)


@dataclass
class BitCrusher(AudioEffect):
    """Lo-fi bit depth reduction effect."""
    bit_depth: int = 8        # Target bit depth (1-16)
    sample_hold: int = 1      # Sample-and-hold factor for rate reduction
    
    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples.copy()
        
        # Bit reduction
        levels = 2 ** self.bit_depth
        samples = np.round(samples * levels) / levels
        
        # Sample rate reduction via sample-and-hold
        if self.sample_hold > 1:
            if audio.channels == 1:
                for i in range(len(samples)):
                    if i % self.sample_hold != 0:
                        samples[i] = samples[i - (i % self.sample_hold)]
            else:
                for i in range(len(samples)):
                    if i % self.sample_hold != 0:
                        samples[i] = samples[i - (i % self.sample_hold)]
        
        return AudioData(samples, audio.sample_rate, audio.channels)


@dataclass
class Chorus(AudioEffect):
    """Chorus effect using modulated delay lines."""
    rate: float = 1.5         # LFO rate in Hz
    depth: float = 0.002      # Modulation depth in seconds
    mix: float = 0.5          # Wet/dry mix
    voices: int = 2           # Number of chorus voices
    
    def process(self, audio: AudioData) -> AudioData:
        samples = audio.samples
        sr = audio.sample_rate
        length = len(samples)
        
        # Base delay
        base_delay = int(0.02 * sr)  # 20ms base delay
        max_mod = int(self.depth * sr)
        
        output = samples.copy()
        
        for voice in range(self.voices):
            # Each voice has different phase
            phase_offset = voice * 2 * np.pi / self.voices
            
            # Generate LFO
            t = np.arange(length) / sr
            lfo = np.sin(2 * np.pi * self.rate * t + phase_offset)
            delay_mod = base_delay + (lfo * max_mod).astype(int)
            
            # Apply modulated delay
            if audio.channels == 1:
                delayed = np.zeros_like(samples)
                for i in range(length):
                    idx = i - delay_mod[i]
                    if 0 <= idx < length:
                        delayed[i] = samples[idx]
            else:
                delayed = np.zeros_like(samples)
                for i in range(length):
                    idx = i - delay_mod[i]
                    if 0 <= idx < length:
                        delayed[i] = samples[idx]
            
            output = output + delayed * (self.mix / self.voices)
        
        # Normalize mix
        output = samples * (1 - self.mix) + output * self.mix
        
        return AudioData(output, audio.sample_rate, audio.channels)


class EffectChain:
    """Chain multiple effects together."""
    
    def __init__(self, *effects: AudioEffect):
        self.effects = list(effects)
    
    def add(self, effect: AudioEffect) -> 'EffectChain':
        """Add an effect to the chain."""
        self.effects.append(effect)
        return self
    
    def process(self, audio: AudioData) -> AudioData:
        """Process audio through all effects in order."""
        result = audio
        for effect in self.effects:
            result = effect.process(result)
        return result
    
    def __iter__(self):
        return iter(self.effects)
