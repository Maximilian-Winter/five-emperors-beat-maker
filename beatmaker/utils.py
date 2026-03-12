"""
靈寶五帝策使編碼之法 - Utilities Module
Tools for extracting, analyzing, and manipulating audio.

The Five Emperors provide these utilities:
- Azure Emperor: Structure analysis
- Vermilion Emperor: Performance optimization  
- Yellow Emperor: Format conversion
- White Tiger: Quality validation
- Dark Turtle: Data extraction
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np

from .core import AudioData, Sample
from .io import load_audio, save_audio


def detect_bpm(audio: AudioData, min_bpm: float = 60, 
               max_bpm: float = 200) -> float:
    """
    Estimate the BPM of an audio file using onset detection.
    
    This is a simplified implementation - for production use,
    consider using librosa or madmom.
    """
    # Convert to mono
    if audio.channels > 1:
        samples = np.mean(audio.samples, axis=1)
    else:
        samples = audio.samples
    
    # Compute energy in short windows
    window_size = int(0.01 * audio.sample_rate)  # 10ms windows
    hop_size = window_size // 2
    
    num_windows = (len(samples) - window_size) // hop_size
    energy = np.zeros(num_windows)
    
    for i in range(num_windows):
        start = i * hop_size
        window = samples[start:start + window_size]
        energy[i] = np.sum(window ** 2)
    
    # Compute spectral flux (difference in energy)
    flux = np.diff(energy)
    flux = np.maximum(flux, 0)  # Only positive changes (onsets)
    
    # Autocorrelation to find periodicity
    autocorr = np.correlate(flux, flux, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    
    # Convert BPM range to lag range
    window_rate = audio.sample_rate / hop_size
    min_lag = int(60 * window_rate / max_bpm)
    max_lag = int(60 * window_rate / min_bpm)
    
    # Find peak in valid range
    if max_lag > len(autocorr):
        max_lag = len(autocorr) - 1
    
    search_range = autocorr[min_lag:max_lag]
    if len(search_range) == 0:
        return 120.0  # Default
    
    peak_idx = np.argmax(search_range) + min_lag
    
    # Convert lag to BPM
    bpm = 60 * window_rate / peak_idx
    
    return round(bpm, 1)


def detect_onsets(audio: AudioData, threshold: float = 0.1,
                  min_interval: float = 0.05) -> List[float]:
    """
    Detect onset times in audio.
    
    Returns a list of onset times in seconds.
    """
    if audio.channels > 1:
        samples = np.mean(audio.samples, axis=1)
    else:
        samples = audio.samples
    
    # Compute envelope using RMS
    window_size = int(0.01 * audio.sample_rate)
    hop_size = window_size // 4
    
    num_windows = (len(samples) - window_size) // hop_size
    envelope = np.zeros(num_windows)
    
    for i in range(num_windows):
        start = i * hop_size
        window = samples[start:start + window_size]
        envelope[i] = np.sqrt(np.mean(window ** 2))
    
    # Normalize
    if np.max(envelope) > 0:
        envelope = envelope / np.max(envelope)
    
    # Find peaks above threshold
    diff = np.diff(envelope)
    onsets = []
    min_samples = int(min_interval * audio.sample_rate / hop_size)
    last_onset = -min_samples
    
    for i in range(1, len(diff) - 1):
        if envelope[i] > threshold:
            if diff[i-1] > 0 and diff[i] <= 0:  # Peak
                if i - last_onset >= min_samples:
                    time = i * hop_size / audio.sample_rate
                    onsets.append(time)
                    last_onset = i
    
    return onsets


def slice_at_onsets(audio: AudioData, onsets: Optional[List[float]] = None,
                    min_duration: float = 0.05) -> List[AudioData]:
    """
    Slice audio at onset points.
    
    If onsets not provided, detects them automatically.
    """
    if onsets is None:
        onsets = detect_onsets(audio)
    
    if not onsets:
        return [audio]
    
    slices = []
    
    # Add end time
    times = onsets + [audio.duration]
    
    for i, start in enumerate(onsets):
        end = times[i + 1]
        
        if end - start >= min_duration:
            slice_audio = audio.slice(start, end)
            slices.append(slice_audio)
    
    return slices


def extract_samples_from_file(path: Union[str, Path],
                              prefix: str = "sample",
                              min_duration: float = 0.05) -> List[Sample]:
    """
    Load an audio file and extract individual samples at onset points.
    
    Useful for extracting individual drum hits from a loop.
    """
    audio = load_audio(Path(path))
    slices = slice_at_onsets(audio, min_duration=min_duration)
    
    samples = []
    for i, slice_audio in enumerate(slices):
        sample = Sample(
            name=f"{prefix}_{i:03d}",
            audio=slice_audio.normalize()
        )
        samples.append(sample)
    
    return samples


def split_stereo(audio: AudioData) -> Tuple[AudioData, AudioData]:
    """Split stereo audio into left and right channels."""
    if audio.channels != 2:
        raise ValueError("Audio must be stereo")
    
    left = AudioData(audio.samples[:, 0].copy(), audio.sample_rate, 1)
    right = AudioData(audio.samples[:, 1].copy(), audio.sample_rate, 1)
    
    return left, right


def merge_to_stereo(left: AudioData, right: AudioData) -> AudioData:
    """Merge two mono audio streams to stereo."""
    if left.channels != 1 or right.channels != 1:
        raise ValueError("Both inputs must be mono")
    
    # Ensure same length and sample rate
    if left.sample_rate != right.sample_rate:
        right = right.resample(left.sample_rate)
    
    max_len = max(len(left.samples), len(right.samples))
    
    left_padded = np.zeros(max_len)
    right_padded = np.zeros(max_len)
    
    left_padded[:len(left.samples)] = left.samples
    right_padded[:len(right.samples)] = right.samples
    
    stereo = np.column_stack([left_padded, right_padded])
    
    return AudioData(stereo, left.sample_rate, 2)


def time_stretch(audio: AudioData, factor: float) -> AudioData:
    """
    Time stretch audio without changing pitch.
    
    factor > 1.0 = slower
    factor < 1.0 = faster
    
    This is a simple implementation using overlap-add.
    For better quality, use librosa or rubberband.
    """
    if factor == 1.0:
        return audio
    
    samples = audio.samples
    if audio.channels > 1:
        # Process each channel
        stretched_channels = []
        for ch in range(audio.channels):
            mono = AudioData(samples[:, ch], audio.sample_rate, 1)
            stretched = time_stretch(mono, factor)
            stretched_channels.append(stretched.samples)
        
        result = np.column_stack(stretched_channels)
        return AudioData(result, audio.sample_rate, audio.channels)
    
    # Simple OLA time stretching
    window_size = 2048
    hop_in = window_size // 4
    hop_out = int(hop_in * factor)
    
    # Create Hann window
    window = np.hanning(window_size)
    
    # Output buffer
    output_length = int(len(samples) * factor)
    output = np.zeros(output_length + window_size)
    
    pos_in = 0
    pos_out = 0
    
    while pos_in + window_size < len(samples):
        # Extract and window
        frame = samples[pos_in:pos_in + window_size] * window
        
        # Overlap-add
        output[pos_out:pos_out + window_size] += frame
        
        pos_in += hop_in
        pos_out += hop_out
    
    # Normalize for overlap
    output = output[:output_length] / (window_size / hop_out / 2)
    
    return AudioData(output, audio.sample_rate, 1)


def pitch_shift(audio: AudioData, semitones: float) -> AudioData:
    """
    Pitch shift audio by resampling.
    
    Note: This changes duration. For constant duration pitch shift,
    combine with time_stretch.
    """
    ratio = 2 ** (semitones / 12)
    
    # Resample to change pitch
    new_length = int(len(audio.samples) / ratio)
    
    if audio.channels == 1:
        shifted = np.interp(
            np.linspace(0, len(audio.samples) - 1, new_length),
            np.arange(len(audio.samples)),
            audio.samples
        )
    else:
        shifted = np.zeros((new_length, audio.channels))
        for ch in range(audio.channels):
            shifted[:, ch] = np.interp(
                np.linspace(0, len(audio.samples) - 1, new_length),
                np.arange(len(audio.samples)),
                audio.samples[:, ch]
            )
    
    return AudioData(shifted, audio.sample_rate, audio.channels)


def reverse(audio: AudioData) -> AudioData:
    """Reverse audio."""
    return AudioData(audio.samples[::-1].copy(), audio.sample_rate, audio.channels)


def loop(audio: AudioData, times: int) -> AudioData:
    """Loop audio a specified number of times."""
    if times <= 1:
        return audio
    
    if audio.channels == 1:
        looped = np.tile(audio.samples, times)
    else:
        looped = np.tile(audio.samples, (times, 1))
    
    return AudioData(looped, audio.sample_rate, audio.channels)


def crossfade(audio1: AudioData, audio2: AudioData, 
              duration: float = 0.1) -> AudioData:
    """Crossfade between two audio segments."""
    # Ensure same format
    if audio1.sample_rate != audio2.sample_rate:
        audio2 = audio2.resample(audio1.sample_rate)
    
    if audio1.channels != audio2.channels:
        if audio1.channels == 1:
            audio1 = audio1.to_stereo()
        else:
            audio2 = audio2.to_stereo()
    
    sr = audio1.sample_rate
    channels = audio1.channels
    fade_samples = int(duration * sr)
    
    # Ensure crossfade isn't longer than either audio
    fade_samples = min(fade_samples, len(audio1.samples), len(audio2.samples))
    
    total_length = len(audio1.samples) + len(audio2.samples) - fade_samples
    
    if channels == 1:
        output = np.zeros(total_length)
    else:
        output = np.zeros((total_length, channels))
    
    # Copy audio1
    output[:len(audio1.samples)] = audio1.samples
    
    # Create crossfade
    fade_out = np.linspace(1, 0, fade_samples)
    fade_in = np.linspace(0, 1, fade_samples)
    
    fade_start = len(audio1.samples) - fade_samples
    
    if channels == 1:
        output[fade_start:fade_start + fade_samples] *= fade_out
        output[fade_start:fade_start + fade_samples] += audio2.samples[:fade_samples] * fade_in
        output[fade_start + fade_samples:] = audio2.samples[fade_samples:]
    else:
        output[fade_start:fade_start + fade_samples] *= fade_out[:, np.newaxis]
        output[fade_start:fade_start + fade_samples] += audio2.samples[:fade_samples] * fade_in[:, np.newaxis]
        output[fade_start + fade_samples:] = audio2.samples[fade_samples:]
    
    return AudioData(output, sr, channels)


def concatenate(*audios: AudioData) -> AudioData:
    """Concatenate multiple audio segments."""
    if not audios:
        return AudioData.silence(0.0)
    
    # Use first audio's properties as reference
    sr = audios[0].sample_rate
    channels = audios[0].channels
    
    # Convert all to same format
    converted = []
    for audio in audios:
        if audio.sample_rate != sr:
            audio = audio.resample(sr)
        if audio.channels != channels:
            if channels == 2:
                audio = audio.to_stereo()
            else:
                audio = audio.to_mono()
        converted.append(audio.samples)
    
    if channels == 1:
        result = np.concatenate(converted)
    else:
        result = np.vstack(converted)
    
    return AudioData(result, sr, channels)


def mix(*audios: AudioData, volumes: Optional[List[float]] = None) -> AudioData:
    """Mix multiple audio streams together."""
    if not audios:
        return AudioData.silence(0.0)
    
    if volumes is None:
        volumes = [1.0] * len(audios)
    
    # Use first audio's properties as reference
    sr = audios[0].sample_rate
    channels = max(a.channels for a in audios)
    max_length = max(len(a.samples) for a in audios)
    
    if channels == 1:
        output = np.zeros(max_length)
    else:
        output = np.zeros((max_length, channels))
    
    for audio, vol in zip(audios, volumes):
        # Convert format
        if audio.sample_rate != sr:
            audio = audio.resample(sr)
        if audio.channels != channels:
            if channels == 2:
                audio = audio.to_stereo()
            else:
                audio = audio.to_mono()
        
        # Mix
        output[:len(audio.samples)] += audio.samples * vol
    
    return AudioData(output, sr, channels)


def export_samples(samples: List[Sample], directory: Union[str, Path],
                   format: str = 'wav') -> List[Path]:
    """Export a list of samples to individual files."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    
    paths = []
    for sample in samples:
        path = directory / f"{sample.name}.{format}"
        save_audio(sample.audio, path)
        paths.append(path)
    
    return paths
