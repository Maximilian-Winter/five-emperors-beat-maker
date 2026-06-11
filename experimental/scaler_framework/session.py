"""
ScalerSession — the orchestrator that ties detect, suggest, generate, export together.

Usage:
    session = ScalerSession()

    # DETECT from audio or MIDI
    session.detect_from_midi("song.mid")
    # or: session.detect_from_audio("song.wav")
    # or: session.set_key(0, "major")  # C major manually

    print(session.key)              # "C major (92%)"
    print(session.detected_chords)  # [Cmaj7, Am7, ...]

    # SUGGEST next chords
    suggestions = session.suggest_next_chord()

    # SET or GENERATE a progression
    session.set_progression("Cmaj7 | Am7 | Dm7 | G7")
    # or: session.generate_progression(length=8)

    # GENERATE melody
    session.generate_melody()
    session.melody.print_ascii(session.progression)

    # EXPORT
    session.export_midi("output.mid")

    # KEY GROUPS (MPC-style sample mapping)
    session.create_key_group("piano_c4.wav", output_dir=".")
    # or: session.load_key_group("piano_c4.keygroup")
    session.export_audio("rendered.wav")
"""

from __future__ import annotations

from typing import Optional

from scaler_framework.theory.chord import Chord, ChordProgression, DetectedChord
from scaler_framework.theory.scale import Scale, KeyEstimate
from scaler_framework.theory.constants import NOTE_NAMES
from scaler_framework.detection.key import KeyEstimator
from scaler_framework.generation.progression import ProgressionEngine, ChordSuggestion
from scaler_framework.generation.melody import (
    MelodyGenerator, GeneratorConfig, GenerationStrategy, Melody,
)
from scaler_framework.generation.voicing import VoicingEngine, VoicingStyle, VoicedChord
from scaler_framework.midi_io import export_midi


class ScalerSession:
    """
    Main orchestrator for the Scaler workflow:
    Detect -> Suggest -> Generate -> Export

    Maintains state across the pipeline so each step can
    build on the previous one.
    """

    def __init__(self):
        self.key: Optional[KeyEstimate] = None
        self.key_alternatives: list[KeyEstimate] = []
        self.scale: Optional[Scale] = None
        self.detected_chords: list[DetectedChord] = []
        self.progression: Optional[ChordProgression] = None
        self.melody: Optional[Melody] = None

        # Sub-engines
        self._key_estimator = KeyEstimator()
        self._progression_engine: Optional[ProgressionEngine] = None
        self._voicing_engine = VoicingEngine()

        # Key group (MPC-style sample mapping)
        self.key_group = None  # Optional[KeyGroup]

        # Detection source metadata
        self._source_file: Optional[str] = None
        self._source_type: Optional[str] = None  # "midi" or "audio"

    # ------------------------------------------------------------------
    # DETECT
    # ------------------------------------------------------------------

    def detect_from_midi(self, filepath: str, quantize_div: float = 1.0) -> "ScalerSession":
        """
        Detect key and chords from a MIDI file.
        Sets self.key, self.scale, self.detected_chords.
        """
        from scaler_framework.detection.midi import MidiParser, MidiChordDetector

        self._source_file = filepath
        self._source_type = "midi"

        parser = MidiParser(filepath)

        # Key estimation
        hist = parser.get_pitch_class_histogram()
        keys = self._key_estimator.estimate(hist, top_n=5)
        self.key = keys[0] if keys else None
        self.key_alternatives = keys
        self.scale = self.key.get_scale() if self.key else None

        # Chord detection
        detector = MidiChordDetector(parser.notes, parser.ticks_per_beat)
        self.detected_chords = detector.detect(quantize_div=quantize_div)

        # Auto-build progression from detected chords
        if self.detected_chords:
            self.progression = ChordProgression.from_detected(
                self.detected_chords, parser.ticks_per_beat
            )

        self._init_progression_engine()
        return self

    def detect_from_audio(self, filepath: str, beat_duration: float = 0.5) -> "ScalerSession":
        """
        Detect key and chords from an audio file.
        Sets self.key, self.scale, self.detected_chords.
        """
        from scaler_framework.detection.audio import ChromagramExtractor, AudioChordDetector

        self._source_file = filepath
        self._source_type = "audio"

        extractor = ChromagramExtractor(filepath)

        # Key estimation
        hist = extractor.get_overall_histogram()
        keys = self._key_estimator.estimate(hist, top_n=5)
        self.key = keys[0] if keys else None
        self.key_alternatives = keys
        self.scale = self.key.get_scale() if self.key else None

        # Chord detection
        detector = AudioChordDetector(extractor)
        self.detected_chords = detector.detect(beat_duration=beat_duration)

        self._init_progression_engine()
        return self

    def set_key(self, root: int, scale_type: str = "major") -> "ScalerSession":
        """Manually set the key."""
        self.key = KeyEstimate(root=root, scale_type=scale_type, confidence=1.0)
        self.key_alternatives = [self.key]
        self.scale = self.key.get_scale()
        self._init_progression_engine()
        return self

    # ------------------------------------------------------------------
    # SUGGEST
    # ------------------------------------------------------------------

    def suggest_next_chord(self, current: Optional[list[str]] = None,
                           top_n: int = 6) -> list[ChordSuggestion]:
        """
        Suggest next chords.

        Args:
            current: Roman numeral progression so far. If None, uses
                     detected chords converted to degrees (or empty).
            top_n: Number of suggestions.
        """
        self._ensure_progression_engine()
        if current is None:
            current = []
        return self._progression_engine.suggest_next(current, top_n=top_n)

    def generate_progression(self, length: int = 8, start: Optional[str] = None,
                             temperature: float = 0.7,
                             beats_per_chord: float = 4.0) -> "ScalerSession":
        """Generate a chord progression and set it as the active progression."""
        self._ensure_progression_engine()
        degrees = self._progression_engine.generate_progression(
            length=length, start=start, temperature=temperature
        )
        # Convert degrees to Chord objects
        chords = []
        for deg in degrees:
            note, qual = self._progression_engine.degree_to_note_name(deg)
            chords.append(Chord.from_string(f"{note}{qual}", duration_beats=beats_per_chord))
        self.progression = ChordProgression(chords=chords, bpm=120.0)
        return self

    # ------------------------------------------------------------------
    # SET PROGRESSION
    # ------------------------------------------------------------------

    def set_progression(self, prog: str | ChordProgression,
                        beats_per_chord: float = 4.0,
                        bpm: float = 120.0) -> "ScalerSession":
        """Set the active chord progression from a string or object."""
        if isinstance(prog, str):
            self.progression = ChordProgression.from_string(
                prog, beats_per_chord=beats_per_chord, bpm=bpm
            )
        else:
            self.progression = prog
        return self

    # ------------------------------------------------------------------
    # GENERATE MELODY
    # ------------------------------------------------------------------

    def generate_melody(self, config: Optional[GeneratorConfig] = None) -> "ScalerSession":
        """Generate a melody over the active progression."""
        if self.progression is None:
            raise ValueError("No progression set. Use set_progression() or generate_progression() first.")

        key_root = self.key.root if self.key else 0
        scale_type = self.key.scale_type if self.key else "major"

        gen = MelodyGenerator(
            self.progression,
            key_root=key_root,
            scale_type=scale_type,
            config=config,
        )
        self.melody = gen.generate()
        return self

    # ------------------------------------------------------------------
    # VOICING
    # ------------------------------------------------------------------

    def voice_progression(self, style: VoicingStyle = VoicingStyle.CLOSE,
                          octave: int = 4,
                          voice_lead: bool = True) -> list[VoicedChord]:
        """Voice the active progression with a specific voicing style."""
        if self.progression is None:
            raise ValueError("No progression set.")
        return self._voicing_engine.voice_progression(
            self.progression.chords, style=style, octave=octave, voice_lead=voice_lead
        )

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def export_midi(self, filename: str,
                    include_melody: bool = True,
                    include_chords: bool = True,
                    voicing_style: VoicingStyle = VoicingStyle.CLOSE,
                    voicing_octave: int = 3) -> str:
        """
        Export the current session to a MIDI file.

        Returns:
            The output filename.
        """
        mel = self.melody if include_melody else None
        prog = self.progression if include_chords else None
        bpm = self.progression.bpm if self.progression else 120.0

        return export_midi(
            filename,
            melody=mel,
            chord_prog=prog,
            voicing_style=voicing_style,
            voicing_octave=voicing_octave,
            bpm=bpm,
        )

    # ------------------------------------------------------------------
    # KEY GROUPS
    # ------------------------------------------------------------------

    def create_key_group(self, audio_path: str, name: str | None = None,
                         scale_type: str | None = None,
                         root: int | None = None,
                         octave_range: tuple[int, int] = (3, 5),
                         output_dir: str = ".") -> "ScalerSession":
        """
        Create a key group from an audio sample.

        Detects pitch, pitch-shifts across the scale, saves to disk.
        If scale_type is None, auto-detects from the session key or the audio.

        Args:
            audio_path: Path to the source audio sample.
            name: Name for the key group. Defaults to filename stem.
            scale_type: Scale type. None = use session key or auto-detect.
            root: Scale root pitch class. None = use detected pitch.
            octave_range: (lowest, highest) octave inclusive.
            output_dir: Parent directory for the .keygroup folder.
        """
        from scaler_framework.sampling.keygroup import KeyGroup

        # Use session key if available and no override given
        if scale_type is None and self.key:
            scale_type = self.key.scale_type
            if root is None:
                root = self.key.root
        if scale_type is None:
            scale_type = "major"

        self.key_group = KeyGroup.create(
            audio_path, name=name,
            scale_type=scale_type, root=root,
            octave_range=octave_range,
            output_dir=output_dir,
        )

        # Sync session key/scale to key group
        self.scale = self.key_group.scale
        if self.key is None:
            self.set_key(self.key_group.scale.root, self.key_group.scale.scale_type)

        return self

    def load_key_group(self, keygroup_path: str) -> "ScalerSession":
        """
        Load a key group from a .keygroup directory.
        Sets the session key and scale from the key group.
        """
        from scaler_framework.sampling.keygroup import KeyGroup

        self.key_group = KeyGroup.load(keygroup_path)
        self.scale = self.key_group.scale
        self.set_key(self.key_group.scale.root, self.key_group.scale.scale_type)
        return self

    def export_audio(self, filename: str, bpm: float | None = None,
                     tail_seconds: float = 1.0) -> str:
        """
        Render the current melody to audio using the loaded key group.

        Requires both a melody and a key group to be set.

        Returns:
            The output file path.
        """
        from scaler_framework.sampling.renderer import KeyGroupRenderer

        if self.key_group is None:
            raise ValueError("No key group loaded. Use create_key_group() or load_key_group() first.")
        if self.melody is None:
            raise ValueError("No melody generated. Use generate_melody() first.")

        actual_bpm = bpm or (self.progression.bpm if self.progression else 120.0)
        renderer = KeyGroupRenderer(self.key_group)
        return renderer.render_to_file(
            self.melody, output_path=filename,
            bpm=actual_bpm, tail_seconds=tail_seconds,
        )

    # ------------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """Return a full session summary as a dict."""
        result = {}

        if self._source_file:
            result["source"] = {"file": self._source_file, "type": self._source_type}

        if self.key:
            result["key"] = {
                "name": self.key.name,
                "confidence": round(self.key.confidence, 3),
                "scale_notes": self.key.get_scale_notes(),
            }
            result["key_alternatives"] = [
                {"name": k.name, "confidence": round(k.confidence, 3)}
                for k in self.key_alternatives[:5]
            ]

        if self.detected_chords:
            result["detected_chords"] = [
                {"chord": c.symbol, "confidence": round(c.confidence, 3)}
                for c in self.detected_chords
            ]

        if self.progression:
            result["progression"] = str(self.progression)

        if self.melody:
            result["melody_notes"] = len(self.melody.notes)

        if self.key_group is not None:
            result["key_group"] = {
                "name": self.key_group.name,
                "scale": self.key_group.scale.name,
                "samples": len(self.key_group.mappings),
                "range": list(self.key_group.note_range),
            }

        return result

    def print_summary(self):
        """Pretty-print the session state."""
        print(f"\n{'=' * 60}")
        print(f"  Scaler Session")
        print(f"{'=' * 60}")

        if self._source_file:
            print(f"  Source: {self._source_file} ({self._source_type})")

        if self.key:
            print(f"\n  Key: {self.key.name} ({self.key.confidence:.0%})")
            print(f"  Scale: {', '.join(self.key.get_scale_notes())}")
            if len(self.key_alternatives) > 1:
                print(f"  Alternatives:")
                for k in self.key_alternatives[1:4]:
                    print(f"    {k.name} ({k.confidence:.0%})")

        if self.detected_chords:
            print(f"\n  Detected Chords ({len(self.detected_chords)}):")
            for c in self.detected_chords[:16]:
                print(f"    {c.symbol:<10s} {c.confidence:.0%}")

        if self.progression:
            print(f"\n  Progression: {self.progression}")

        if self.melody:
            print(f"\n  Melody: {len(self.melody.notes)} notes")

        if self.key_group is not None:
            print(f"\n  Key Group: {self.key_group.name}")
            print(f"    {len(self.key_group.mappings)} samples, "
                  f"range: {self.key_group.note_range}")

        print(f"{'=' * 60}\n")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _init_progression_engine(self):
        if self.key:
            scale = "major" if self.key.scale_type in ("major", "lydian", "mixolydian") else "minor"
            self._progression_engine = ProgressionEngine(
                root=self.key.root, scale=scale
            )

    def _ensure_progression_engine(self):
        if self._progression_engine is None:
            self._progression_engine = ProgressionEngine(root=0, scale="major")
