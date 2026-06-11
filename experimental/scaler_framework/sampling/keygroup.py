"""
Key Group: maps a pitched audio sample across a musical scale.

Takes a single sample, detects its pitch, pitch-shifts it to every note
in a chosen scale across a range of octaves, and saves the result as a
directory of WAV files + JSON manifest.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from scaler_framework.theory.constants import NOTE_NAMES, pc_to_name
from scaler_framework.theory.scale import Scale
from scaler_framework.sampling.pitch import PitchDetector, PitchResult


MANIFEST_FILENAME = "manifest.json"
SAMPLES_DIR = "samples"
KEYGROUP_VERSION = 1


@dataclass
class KeyGroupMapping:
    """Maps a single MIDI note to a pitched sample file."""
    midi_note: int
    note_name: str
    semitone_shift: int     # shift from source sample
    file: str               # relative path within keygroup dir

    def to_dict(self) -> dict:
        return {
            "midi_note": self.midi_note,
            "note_name": self.note_name,
            "semitone_shift": self.semitone_shift,
            "file": self.file,
        }

    @classmethod
    def from_dict(cls, d: dict) -> KeyGroupMapping:
        return cls(
            midi_note=d["midi_note"],
            note_name=d["note_name"],
            semitone_shift=d["semitone_shift"],
            file=d["file"],
        )


@dataclass
class KeyGroup:
    """
    A set of pitch-shifted samples covering a musical scale.

    Create from an audio file:
        kg = KeyGroup.create("piano_c4.wav", name="my_piano",
                             scale_type="major", root=0, octave_range=(3, 5))
        kg.save()

    Load from disk:
        kg = KeyGroup.load("my_piano.keygroup")
        path = kg.get_sample_path(60)  # get the C4 sample
    """
    name: str
    source_file: str
    source_pitch: PitchResult
    scale: Scale
    octave_range: tuple[int, int]
    sample_rate: int
    mappings: list[KeyGroupMapping] = field(default_factory=list)
    base_dir: str = ""
    created: str = ""

    @classmethod
    def create(cls, audio_path: str, name: Optional[str] = None,
               scale_type: str = "major", root: Optional[int] = None,
               octave_range: tuple[int, int] = (3, 5),
               output_dir: str = ".",
               sr: int = 22050) -> KeyGroup:
        """
        Create a key group from an audio sample.

        Args:
            audio_path: Path to source audio file (wav, mp3, flac, etc.)
            name: Name for the key group. Defaults to filename stem.
            scale_type: Scale type (major, natural_minor, pentatonic_major, etc.)
            root: Scale root as pitch class (0=C). If None, uses detected pitch.
            octave_range: (lowest_octave, highest_octave) inclusive.
            output_dir: Parent directory for the keygroup folder.
            sr: Sample rate for processing and output.

        Returns:
            KeyGroup with all samples generated and saved to disk.
        """
        import librosa
        import soundfile as sf

        # Detect pitch
        detector = PitchDetector(audio_path, sr=sr)
        pitch = detector.detect()
        print(f"  Detected pitch: {pitch}")

        if pitch.confidence < 0.3:
            print(f"  Warning: low pitch confidence ({pitch.confidence:.0%}). "
                  "Results may be unreliable. Use a clear monophonic sample.")

        # Determine scale root
        if root is None:
            root = pitch.pitch_class
            print(f"  Using detected root: {NOTE_NAMES[root]}")

        scale = Scale(root=root, scale_type=scale_type)

        # Name and directory
        if name is None:
            name = Path(audio_path).stem
        dir_name = f"{name}.keygroup"
        base_dir = os.path.join(output_dir, dir_name)
        samples_dir = os.path.join(base_dir, SAMPLES_DIR)
        os.makedirs(samples_dir, exist_ok=True)

        # Load source audio
        y, _ = librosa.load(audio_path, sr=sr, mono=True)

        # Build mappings: every scale note in the octave range
        scale_pcs = set(scale.pitch_classes)
        mappings = []

        lo_oct, hi_oct = octave_range
        for octave in range(lo_oct, hi_oct + 1):
            for pc in sorted(scale_pcs):
                midi_note = (octave + 1) * 12 + pc
                note_name = f"{NOTE_NAMES[pc]}{octave}"
                semitone_shift = midi_note - pitch.midi_note

                # Warn on extreme shifts
                if abs(semitone_shift) > 18:
                    print(f"  Warning: large shift for {note_name} "
                          f"({semitone_shift:+d} semitones), quality may degrade.")

                # Pitch shift
                y_shifted = librosa.effects.pitch_shift(
                    y, sr=sr, n_steps=semitone_shift,
                )

                # Save WAV
                rel_path = f"{SAMPLES_DIR}/{note_name}.wav"
                abs_path = os.path.join(base_dir, rel_path)
                sf.write(abs_path, y_shifted, sr)

                mappings.append(KeyGroupMapping(
                    midi_note=midi_note,
                    note_name=note_name,
                    semitone_shift=semitone_shift,
                    file=rel_path,
                ))

        kg = cls(
            name=name,
            source_file=os.path.abspath(audio_path),
            source_pitch=pitch,
            scale=scale,
            octave_range=octave_range,
            sample_rate=sr,
            mappings=mappings,
            base_dir=os.path.abspath(base_dir),
            created=datetime.now(timezone.utc).isoformat(),
        )

        kg.save()
        print(f"  Key group saved: {base_dir}/ ({len(mappings)} samples)")
        return kg

    def save(self) -> str:
        """Save manifest to disk. Returns path to manifest file."""
        manifest = {
            "version": KEYGROUP_VERSION,
            "name": self.name,
            "source_file": self.source_file,
            "source_pitch": {
                "hz": self.source_pitch.hz,
                "midi_note": self.source_pitch.midi_note,
                "note_name": self.source_pitch.note_name,
                "confidence": self.source_pitch.confidence,
                "cents_offset": self.source_pitch.cents_offset,
            },
            "scale": {
                "root": self.scale.root,
                "scale_type": self.scale.scale_type,
            },
            "octave_range": list(self.octave_range),
            "sample_rate": self.sample_rate,
            "created": self.created,
            "mappings": [m.to_dict() for m in self.mappings],
        }

        manifest_path = os.path.join(self.base_dir, MANIFEST_FILENAME)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest_path

    @classmethod
    def load(cls, keygroup_path: str) -> KeyGroup:
        """
        Load a key group from a .keygroup directory.

        Args:
            keygroup_path: Path to the .keygroup directory.
        """
        base_dir = os.path.abspath(keygroup_path)
        manifest_path = os.path.join(base_dir, MANIFEST_FILENAME)

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        sp = manifest["source_pitch"]
        source_pitch = PitchResult(
            hz=sp["hz"],
            midi_note=sp["midi_note"],
            note_name=sp["note_name"],
            octave=(sp["midi_note"] // 12) - 1,
            pitch_class=sp["midi_note"] % 12,
            confidence=sp["confidence"],
            cents_offset=sp["cents_offset"],
        )

        sc = manifest["scale"]
        scale = Scale(root=sc["root"], scale_type=sc["scale_type"])

        mappings = [KeyGroupMapping.from_dict(m) for m in manifest["mappings"]]

        return cls(
            name=manifest["name"],
            source_file=manifest["source_file"],
            source_pitch=source_pitch,
            scale=scale,
            octave_range=tuple(manifest["octave_range"]),
            sample_rate=manifest["sample_rate"],
            mappings=mappings,
            base_dir=base_dir,
            created=manifest.get("created", ""),
        )

    # --- Query API ---

    @property
    def available_notes(self) -> list[int]:
        """Sorted list of available MIDI note numbers."""
        return sorted(m.midi_note for m in self.mappings)

    @property
    def note_range(self) -> tuple[int, int]:
        """Lowest and highest available MIDI notes."""
        notes = self.available_notes
        return (notes[0], notes[-1]) if notes else (0, 0)

    def get_sample_path(self, midi_note: int) -> Optional[str]:
        """Get absolute path to the sample for a MIDI note, or None."""
        for m in self.mappings:
            if m.midi_note == midi_note:
                return os.path.join(self.base_dir, m.file)
        return None

    def get_nearest_sample(self, midi_note: int) -> tuple[str, int]:
        """
        Get the closest available sample to a MIDI note.

        Returns:
            (absolute_path, actual_midi_note)
        """
        if not self.mappings:
            raise ValueError("Key group has no mappings.")

        best = min(self.mappings, key=lambda m: abs(m.midi_note - midi_note))
        return os.path.join(self.base_dir, best.file), best.midi_note

    def get_mapping(self, midi_note: int) -> Optional[KeyGroupMapping]:
        """Get the mapping for a specific MIDI note."""
        for m in self.mappings:
            if m.midi_note == midi_note:
                return m
        return None

    def info(self) -> str:
        """Human-readable summary."""
        lo, hi = self.note_range
        lo_name = f"{NOTE_NAMES[lo % 12]}{lo // 12 - 1}" if self.mappings else "?"
        hi_name = f"{NOTE_NAMES[hi % 12]}{hi // 12 - 1}" if self.mappings else "?"
        return (
            f"KeyGroup: {self.name}\n"
            f"  Source: {self.source_file}\n"
            f"  Detected pitch: {self.source_pitch}\n"
            f"  Scale: {self.scale.name}\n"
            f"  Range: {lo_name} - {hi_name} ({len(self.mappings)} samples)\n"
            f"  Path: {self.base_dir}"
        )

    def __repr__(self):
        return f"KeyGroup({self.name}, {self.scale.name}, {len(self.mappings)} samples)"
