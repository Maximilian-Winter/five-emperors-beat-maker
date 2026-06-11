"""
Audio-based chord and key detection using chromagram analysis.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from scaler_framework.theory.constants import NOTE_NAMES, CHORD_TEMPLATES
from scaler_framework.theory.chord import DetectedChord


class ChromagramExtractor:
    """
    Extracts a chromagram (12 x T pitch class energy matrix) from audio
    using librosa's CQT-based chromagram.
    """

    def __init__(self, filepath: str, sr: int = 22050):
        import librosa
        self.filepath = filepath
        self.sr = sr
        self.y, self.sr = librosa.load(filepath, sr=sr, mono=True)
        self.duration = len(self.y) / self.sr

    def extract(self, hop_length: int = 4096, norm: str = "max") -> np.ndarray:
        """
        Compute the chromagram.

        Args:
            hop_length: Samples between frames. 4096 @ 22050Hz ~ 0.19s/frame.
            norm: "max" normalizes each frame to [0,1].

        Returns:
            12 x T numpy array (rows = pitch classes C..B)
        """
        import librosa
        chroma = librosa.feature.chroma_cqt(
            y=self.y, sr=self.sr, hop_length=hop_length, norm=None,
        )
        if norm == "max":
            frame_max = chroma.max(axis=0, keepdims=True)
            frame_max[frame_max == 0] = 1
            chroma = chroma / frame_max
        return chroma

    def get_overall_histogram(self) -> np.ndarray:
        """Single 12-element pitch class histogram for the whole file."""
        chroma = self.extract()
        hist = chroma.mean(axis=1)
        total = hist.sum()
        if total > 0:
            hist /= total
        return hist

    def frame_to_time(self, frame: int, hop_length: int = 4096) -> float:
        return frame * hop_length / self.sr


class AudioChordDetector:
    """
    Detects chords from a chromagram by matching time windows
    against chord templates using cosine similarity.
    """

    def __init__(self, extractor: ChromagramExtractor):
        self.extractor = extractor
        self._build_template_matrix()

    def _build_template_matrix(self):
        self.templates = []
        for root in range(12):
            for name, intervals in CHORD_TEMPLATES.items():
                vec = np.zeros(12)
                for i in intervals:
                    vec[(root + i) % 12] = 1.0
                self.templates.append((root, name, vec))
        self.template_matrix = np.array([t[2] for t in self.templates])

    def detect(self, beat_duration: float = 0.5, min_energy: float = 0.05,
               smooth: bool = True) -> list[DetectedChord]:
        """
        Detect chords from audio.

        Args:
            beat_duration: Window size in seconds.
            min_energy: Minimum chroma energy to skip silence.
            smooth: Merge consecutive identical chords.

        Returns:
            List of DetectedChord with time-based positions.
        """
        hop_length = 4096
        chroma = self.extractor.extract(hop_length=hop_length)
        n_frames = chroma.shape[1]

        frame_duration = hop_length / self.extractor.sr
        frames_per_window = max(1, int(beat_duration / frame_duration))

        raw_chords = []

        for start_frame in range(0, n_frames, frames_per_window):
            end_frame = min(start_frame + frames_per_window, n_frames)
            window_chroma = chroma[:, start_frame:end_frame].mean(axis=1)

            if window_chroma.mean() < min_energy:
                raw_chords.append(None)
                continue

            chroma_norm = np.linalg.norm(window_chroma)
            if chroma_norm == 0:
                raw_chords.append(None)
                continue

            dots = self.template_matrix @ window_chroma
            template_norms = np.linalg.norm(self.template_matrix, axis=1)
            similarities = dots / (template_norms * chroma_norm + 1e-10)

            best_idx = int(np.argmax(similarities))
            best_sim = float(similarities[best_idx])
            root, chord_type, _ = self.templates[best_idx]

            time_start = self.extractor.frame_to_time(start_frame, hop_length)
            time_end = self.extractor.frame_to_time(end_frame, hop_length)

            # Store times as pseudo-ticks (time * 1000) for DetectedChord
            raw_chords.append(DetectedChord(
                root=root, quality=chord_type, duration_beats=time_end - time_start,
                start_tick=int(time_start * 1000),
                end_tick=int(time_end * 1000),
                confidence=round(best_sim, 3),
            ))

        results = [c for c in raw_chords if c is not None]

        if smooth:
            results = self._smooth_chords(results)

        return results

    def _smooth_chords(self, chords: list[DetectedChord],
                       min_duration: float = 0.3) -> list[DetectedChord]:
        if not chords:
            return []

        merged = [chords[0]]
        for ch in chords[1:]:
            prev = merged[-1]
            if ch.root == prev.root and ch.quality == prev.quality:
                prev.end_tick = ch.end_tick
                prev.duration_beats = (prev.end_tick - prev.start_tick) / 1000.0
                prev.confidence = round((prev.confidence + ch.confidence) / 2, 3)
            else:
                merged.append(ch)

        # Remove very short detections
        filtered = [
            ch for ch in merged
            if ch.duration_beats >= min_duration
        ]
        return filtered
