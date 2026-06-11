"""
Audio renderer: turns a Melody + KeyGroup into a WAV file.

Loads key group samples, places them on a timeline according to
melody note positions and BPM, mixes overlapping notes, and
applies simple envelope shaping to avoid clicks.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from scaler_framework.generation.melody import Melody
from scaler_framework.sampling.keygroup import KeyGroup


class KeyGroupRenderer:
    """
    Renders a Melody to audio using samples from a KeyGroup.

    Usage:
        renderer = KeyGroupRenderer(key_group)
        audio = renderer.render(melody, bpm=120)
        renderer.render_to_file(melody, bpm=120, output_path="output.wav")
    """

    def __init__(self, key_group: KeyGroup):
        self.key_group = key_group
        self._sample_cache: dict[int, np.ndarray] = {}

    def _load_sample(self, midi_note: int) -> Optional[np.ndarray]:
        """Load and cache a sample for a MIDI note."""
        if midi_note in self._sample_cache:
            return self._sample_cache[midi_note]

        path = self.key_group.get_sample_path(midi_note)
        if path is None:
            # Snap to nearest available note
            path, actual_note = self.key_group.get_nearest_sample(midi_note)
            midi_note = actual_note
            if midi_note in self._sample_cache:
                return self._sample_cache[midi_note]

        import soundfile as sf
        try:
            data, sr = sf.read(path, dtype='float32')
            if data.ndim > 1:
                data = data.mean(axis=1)  # mono mixdown
            self._sample_cache[midi_note] = data
            return data
        except Exception:
            return None

    def render(self, melody: Melody, bpm: Optional[float] = None,
               tail_seconds: float = 1.0,
               attack_ms: float = 5.0,
               release_ms: float = 30.0) -> np.ndarray:
        """
        Render a melody to a numpy audio array.

        Args:
            melody: The melody to render.
            bpm: Tempo. Defaults to melody.bpm.
            tail_seconds: Extra silence at the end for sample tails.
            attack_ms: Attack time in ms (fade in to avoid click).
            release_ms: Release time in ms (fade out).

        Returns:
            1-D float32 numpy array of audio samples.
        """
        actual_bpm = bpm or melody.bpm
        sr = self.key_group.sample_rate
        beats_to_seconds = 60.0 / actual_bpm

        if not melody.notes:
            return np.zeros(int(sr * tail_seconds), dtype=np.float32)

        # Total duration
        last_note = max(melody.notes, key=lambda n: n.end_beat)
        total_seconds = last_note.end_beat * beats_to_seconds + tail_seconds
        total_frames = int(total_seconds * sr)

        output = np.zeros(total_frames, dtype=np.float64)

        attack_frames = int(attack_ms / 1000.0 * sr)
        release_frames = int(release_ms / 1000.0 * sr)

        for note in melody.notes:
            sample = self._load_sample(note.pitch)
            if sample is None:
                continue

            # Position on timeline
            start_frame = int(note.start_beat * beats_to_seconds * sr)
            duration_frames = int(note.duration_beats * beats_to_seconds * sr)

            # Trim or pad the sample to the note duration
            if len(sample) > duration_frames:
                chunk = sample[:duration_frames].copy()
            else:
                chunk = np.zeros(duration_frames, dtype=np.float64)
                chunk[:len(sample)] = sample

            # Apply velocity scaling (MIDI velocity 0-127 -> amplitude 0-1)
            velocity_scale = note.velocity / 127.0
            chunk *= velocity_scale

            # Apply attack envelope
            if attack_frames > 0 and len(chunk) > attack_frames:
                attack_env = np.linspace(0, 1, attack_frames)
                chunk[:attack_frames] *= attack_env

            # Apply release envelope
            if release_frames > 0 and len(chunk) > release_frames:
                release_env = np.linspace(1, 0, release_frames)
                chunk[-release_frames:] *= release_env

            # Mix into output
            end_frame = start_frame + len(chunk)
            if end_frame > total_frames:
                chunk = chunk[:total_frames - start_frame]
                end_frame = total_frames

            if start_frame < total_frames:
                output[start_frame:end_frame] += chunk

        # Normalize to prevent clipping
        peak = np.max(np.abs(output))
        if peak > 0:
            output = output / peak * 0.9

        return output.astype(np.float32)

    def render_to_file(self, melody: Melody, output_path: str,
                       bpm: Optional[float] = None,
                       tail_seconds: float = 1.0) -> str:
        """
        Render melody to a WAV file.

        Returns:
            The output file path.
        """
        import soundfile as sf

        audio = self.render(melody, bpm=bpm, tail_seconds=tail_seconds)
        sf.write(output_path, audio, self.key_group.sample_rate)
        print(f"  Rendered: {output_path} ({len(audio) / self.key_group.sample_rate:.1f}s)")
        return output_path
