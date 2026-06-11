"""
Scale and key estimation data structures.
"""

from __future__ import annotations

from dataclasses import dataclass

from scaler_framework.theory.constants import NOTE_NAMES, SCALE_TEMPLATES, pc_to_name


@dataclass
class Scale:
    """A musical scale defined by root pitch class and scale type."""
    root: int           # pitch class 0-11
    scale_type: str     # key into SCALE_TEMPLATES

    @property
    def intervals(self) -> tuple[int, ...]:
        return SCALE_TEMPLATES.get(self.scale_type, SCALE_TEMPLATES["major"])

    @property
    def pitch_classes(self) -> list[int]:
        return [(self.root + iv) % 12 for iv in self.intervals]

    @property
    def note_names(self) -> list[str]:
        return [pc_to_name(pc) for pc in self.pitch_classes]

    @property
    def name(self) -> str:
        return f"{pc_to_name(self.root)} {self.scale_type}"

    def contains(self, pc: int) -> bool:
        return (pc % 12) in self.pitch_classes

    def nearest_scale_tone(self, midi_note: int) -> int:
        """Snap a MIDI note to the nearest note in this scale."""
        pc = midi_note % 12
        octave = midi_note // 12
        pcs = self.pitch_classes

        if pc in pcs:
            return midi_note

        best_dist = 99
        best_pc = pc
        for spc in pcs:
            dist = min(abs(pc - spc), 12 - abs(pc - spc))
            if dist < best_dist:
                best_dist = dist
                best_pc = spc

        result = octave * 12 + best_pc
        if abs(result - midi_note) > 6:
            if result > midi_note:
                result -= 12
            else:
                result += 12
        return result

    def degree_name(self, degree: int) -> str:
        """Get the note name for a scale degree (0-indexed)."""
        pcs = self.pitch_classes
        if 0 <= degree < len(pcs):
            return pc_to_name(pcs[degree])
        return "?"


@dataclass
class KeyEstimate:
    """An estimated key/scale with confidence score."""
    root: int
    scale_type: str
    confidence: float

    @property
    def root_name(self) -> str:
        return NOTE_NAMES[self.root]

    @property
    def name(self) -> str:
        return f"{self.root_name} {self.scale_type}"

    def get_scale(self) -> Scale:
        return Scale(root=self.root, scale_type=self.scale_type)

    def get_scale_notes(self) -> list[str]:
        return self.get_scale().note_names

    def __repr__(self):
        return f"{self.name} ({self.confidence:.0%})"
