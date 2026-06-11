"""
Pitch detection for audio samples using librosa's pyin (probabilistic YIN).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scaler_framework.theory.constants import NOTE_NAMES


@dataclass
class PitchResult:
    """Result of pitch detection on an audio sample."""
    hz: float               # detected fundamental frequency
    midi_note: int           # nearest MIDI note number
    note_name: str           # e.g. "A4"
    octave: int
    pitch_class: int         # 0-11
    confidence: float        # 0-1, fraction of voiced frames
    cents_offset: float      # deviation from nearest semitone (-50 to +50)

    def __repr__(self):
        sign = "+" if self.cents_offset >= 0 else ""
        return f"{self.note_name} ({self.hz:.1f} Hz, {sign}{self.cents_offset:.0f}c, conf: {self.confidence:.0%})"


class PitchDetector:
    """
    Detects the fundamental pitch of a monophonic audio sample.

    Usage:
        detector = PitchDetector("piano_c4.wav")
        result = detector.detect()
        print(result)  # "C4 (261.6 Hz, +2c, conf: 94%)"
    """

    def __init__(self, filepath: str, sr: int = 22050):
        import librosa
        self.filepath = filepath
        self.sr = sr
        self.y, self.sr = librosa.load(filepath, sr=sr, mono=True)
        self.duration = len(self.y) / self.sr

    def detect(self, fmin: str = "C2", fmax: str = "C7") -> PitchResult:
        """
        Detect the dominant pitch in the sample.

        Args:
            fmin: Lowest expected pitch as note name.
            fmax: Highest expected pitch as note name.

        Returns:
            PitchResult with detected frequency, MIDI note, confidence, etc.

        Raises:
            ValueError: If no pitched content is detected.
        """
        import librosa

        fmin_hz = librosa.note_to_hz(fmin)
        fmax_hz = librosa.note_to_hz(fmax)

        f0, voiced_flag, voiced_prob = librosa.pyin(
            self.y, sr=self.sr,
            fmin=fmin_hz, fmax=fmax_hz,
            frame_length=2048,
        )

        # Filter to voiced frames only
        voiced_f0 = f0[~np.isnan(f0)]

        if len(voiced_f0) == 0:
            raise ValueError(
                f"No pitched content detected in '{self.filepath}'. "
                "Ensure the sample contains a clear monophonic tone."
            )

        # Use median for stability (robust to onset/release noise)
        median_f0 = float(np.median(voiced_f0))
        confidence = float(np.sum(~np.isnan(f0)) / len(f0))

        # Convert to MIDI
        midi_float = librosa.hz_to_midi(median_f0)
        midi_note = int(round(midi_float))
        cents_offset = (midi_float - midi_note) * 100

        # Note name
        pitch_class = midi_note % 12
        octave = (midi_note // 12) - 1
        note_name = f"{NOTE_NAMES[pitch_class]}{octave}"

        return PitchResult(
            hz=round(median_f0, 2),
            midi_note=midi_note,
            note_name=note_name,
            octave=octave,
            pitch_class=pitch_class,
            confidence=round(confidence, 3),
            cents_offset=round(cents_offset, 1),
        )

    def detect_safe(self, fmin: str = "C2", fmax: str = "C7") -> PitchResult | None:
        """Like detect(), but returns None instead of raising on failure."""
        try:
            return self.detect(fmin=fmin, fmax=fmax)
        except ValueError:
            return None
