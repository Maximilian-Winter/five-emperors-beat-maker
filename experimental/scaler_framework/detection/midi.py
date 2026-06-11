"""
MIDI parsing and chord detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from scaler_framework.theory.constants import NOTE_NAMES, CHORD_TEMPLATES
from scaler_framework.theory.chord import Chord, DetectedChord


@dataclass
class NoteEvent:
    """A single note on/off event extracted from MIDI."""
    pitch: int
    velocity: int
    start_tick: int
    end_tick: int
    channel: int = 0
    track: int = 0

    @property
    def pitch_class(self) -> int:
        return self.pitch % 12

    @property
    def note_name(self) -> str:
        return NOTE_NAMES[self.pitch_class]

    @property
    def octave(self) -> int:
        return (self.pitch // 12) - 1

    @property
    def full_name(self) -> str:
        return f"{self.note_name}{self.octave}"

    @property
    def duration_ticks(self) -> int:
        return self.end_tick - self.start_tick


class MidiParser:
    """Extracts NoteEvents from a MIDI file using mido."""

    def __init__(self, filepath: str):
        import mido
        self.filepath = filepath
        self.midi = mido.MidiFile(filepath)
        self.ticks_per_beat = self.midi.ticks_per_beat
        self.notes: list[NoteEvent] = []
        self._parse()

    def _parse(self):
        for track_idx, track in enumerate(self.midi.tracks):
            active_notes = {}
            abs_tick = 0

            for msg in track:
                abs_tick += msg.time

                if msg.type == "note_on" and msg.velocity > 0:
                    key = (msg.note, msg.channel)
                    active_notes[key] = (abs_tick, msg.velocity)

                elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                    key = (msg.note, msg.channel)
                    if key in active_notes:
                        start, vel = active_notes.pop(key)
                        self.notes.append(NoteEvent(
                            pitch=msg.note, velocity=vel,
                            start_tick=start, end_tick=abs_tick,
                            channel=msg.channel, track=track_idx,
                        ))

        self.notes.sort(key=lambda n: (n.start_tick, n.pitch))

    def tick_to_beat(self, tick: int) -> float:
        return tick / self.ticks_per_beat

    def get_pitch_class_histogram(self) -> np.ndarray:
        """Duration-weighted histogram of pitch classes."""
        hist = np.zeros(12)
        for n in self.notes:
            hist[n.pitch_class] += n.duration_ticks
        total = hist.sum()
        if total > 0:
            hist /= total
        return hist


class MidiChordDetector:
    """
    Detects chords by segmenting MIDI notes into time slices
    and matching against chord templates.
    """

    def __init__(self, notes: list[NoteEvent], ticks_per_beat: int = 480):
        self.notes = notes
        self.ticks_per_beat = ticks_per_beat

    def detect(self, quantize_div: float = 1.0, min_notes: int = 3,
               merge_same: bool = True) -> list[DetectedChord]:
        """
        Args:
            quantize_div: Beat subdivision for time slices (1.0 = quarter note).
            min_notes: Minimum distinct pitch classes to attempt match.
            merge_same: Merge consecutive identical chords.
        """
        slices = self._quantize_to_slices(quantize_div)
        chords = []

        for start_tick, end_tick, slice_notes in slices:
            pitch_classes = set(n.pitch_class for n in slice_notes)
            if len(pitch_classes) < min_notes:
                continue

            best = self._match_chord(pitch_classes, slice_notes)
            if best:
                best.start_tick = start_tick
                best.end_tick = end_tick
                chords.append(best)

        if merge_same:
            chords = self._merge_consecutive(chords)

        return chords

    def _quantize_to_slices(self, div: float) -> list[tuple]:
        if not self.notes:
            return []

        window = int(self.ticks_per_beat * div)
        max_tick = max(n.end_tick for n in self.notes)
        slices = []

        for win_start in range(0, max_tick, window):
            win_end = win_start + window
            sounding = [
                n for n in self.notes
                if n.start_tick < win_end and n.end_tick > win_start
            ]
            if sounding:
                slices.append((win_start, win_end, sounding))

        return slices

    def _match_chord(self, pitch_classes: set,
                     notes: list[NoteEvent]) -> Optional[DetectedChord]:
        pc_set = frozenset(pitch_classes)
        best_score = -1
        best_result = None

        for root in range(12):
            for chord_name, intervals in CHORD_TEMPLATES.items():
                template_pcs = frozenset((root + i) % 12 for i in intervals)

                matched = len(template_pcs & pc_set)
                extras = len(pc_set - template_pcs)
                total_template = len(template_pcs)

                if matched < total_template:
                    continue

                score = matched - (extras * 0.3) + (total_template * 0.1)

                if score > best_score:
                    best_score = score
                    lowest_note = min(notes, key=lambda n: n.pitch)
                    lowest_pc = lowest_note.pitch_class
                    interval_list = sorted(intervals)
                    bass_interval = (lowest_pc - root) % 12
                    inversion = interval_list.index(bass_interval) if bass_interval in interval_list else 0

                    confidence = matched / (matched + extras) if (matched + extras) > 0 else 0

                    best_result = DetectedChord(
                        root=root, quality=chord_name,
                        duration_beats=0, start_tick=0, end_tick=0,
                        confidence=confidence, inversion=inversion,
                        source_notes=list(notes),
                    )

        return best_result

    def _merge_consecutive(self, chords: list[DetectedChord]) -> list[DetectedChord]:
        if not chords:
            return []
        merged = [chords[0]]
        for ch in chords[1:]:
            prev = merged[-1]
            if ch.root == prev.root and ch.quality == prev.quality:
                prev.end_tick = ch.end_tick
                prev.source_notes.extend(ch.source_notes)
            else:
                merged.append(ch)
        return merged
