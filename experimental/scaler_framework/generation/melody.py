"""
Melody generator over chord progressions.

Four strategies:
- RULE_BASED: weighted random with chord/scale/proximity constraints
- MARKOV: interval Markov chain filtered by harmony
- CONTOUR: follow a melodic shape, snapped to chord/scale tones
- HYBRID: blends all three with motif repetition
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from scaler_framework.theory.chord import Chord, ChordProgression
from scaler_framework.theory.scale import Scale
from scaler_framework.theory.constants import pc_to_name
from scaler_framework.generation.rhythm import RHYTHM_PATTERNS, CONTOUR_SHAPES


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MelodyNote:
    pitch: int              # MIDI note number
    start_beat: float
    duration_beats: float
    velocity: int = 100

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats

    @property
    def name(self) -> str:
        return f"{pc_to_name(self.pitch % 12)}{self.pitch // 12 - 1}"


@dataclass
class Melody:
    notes: list[MelodyNote] = field(default_factory=list)
    bpm: float = 120.0

    def print_ascii(self, chord_prog: Optional[ChordProgression] = None):
        if not self.notes:
            print("(empty melody)")
            return

        min_pitch = min(n.pitch for n in self.notes)
        max_pitch = max(n.pitch for n in self.notes)
        total_beats = max(n.end_beat for n in self.notes)
        cols = int(total_beats * 4)

        print(f"\n{'=' * 60}")
        if chord_prog:
            chord_line = ""
            for chord in chord_prog.chords:
                label = chord.name
                width = int(chord.duration_beats * 4)
                chord_line += f"{label:<{width}}"
            print(f"  Chords: {chord_line}")
            print(f"{'_' * 60}")

        for pitch in range(max_pitch, min_pitch - 1, -1):
            note_name = f"{pc_to_name(pitch % 12)}{pitch // 12 - 1}"
            row = [' '] * cols
            for note in self.notes:
                if note.pitch == pitch:
                    start_col = int(note.start_beat * 4)
                    end_col = int(note.end_beat * 4)
                    for c in range(start_col, min(end_col, cols)):
                        row[c] = '#' if c == start_col else '='
            row_str = ''.join(row)
            if '#' in row_str or '=' in row_str:
                print(f"  {note_name:>4} |{row_str}|")

        beat_line = ""
        for b in range(int(total_beats)):
            beat_line += f"{b+1:<4}"
        print(f"       +{'-' * cols}+")
        print(f"  Beat: {beat_line}")
        print(f"{'=' * 60}\n")


# ---------------------------------------------------------------------------
# Interval Markov chain
# ---------------------------------------------------------------------------

class IntervalMarkov:
    """First-order Markov chain over melodic intervals."""

    def __init__(self):
        self.transitions: dict[int, dict[int, float]] = {}
        self._load_defaults()

    def _load_defaults(self):
        for prev_interval in range(-12, 13):
            weights = {}
            abs_prev = abs(prev_interval)
            for next_interval in range(-12, 13):
                abs_next = abs(next_interval)
                if abs_next == 0:
                    w = 3.0
                elif abs_next <= 2:
                    w = 10.0
                elif abs_next <= 4:
                    w = 5.0
                elif abs_next <= 5:
                    w = 3.0
                elif abs_next == 7:
                    w = 2.5
                elif abs_next <= 9:
                    w = 1.0
                elif abs_next <= 12:
                    w = 0.3
                else:
                    w = 0.05

                if abs_prev >= 5:
                    if next_interval * prev_interval < 0 and abs_next <= 2:
                        w *= 4.0
                    elif next_interval * prev_interval > 0 and abs_next >= 3:
                        w *= 0.2

                if next_interval > 0:
                    w *= 1.05

                weights[next_interval] = w
            self.transitions[prev_interval] = weights

    def next_interval(self, prev_interval: int, rng: random.Random) -> int:
        prev_interval = max(-12, min(12, prev_interval))
        weights = self.transitions.get(prev_interval, self.transitions[0])
        intervals = list(weights.keys())
        probs = list(weights.values())
        total = sum(probs)
        probs = [p / total for p in probs]
        return rng.choices(intervals, weights=probs, k=1)[0]


# ---------------------------------------------------------------------------
# Generation strategies & config
# ---------------------------------------------------------------------------

class GenerationStrategy(Enum):
    RULE_BASED = "rule_based"
    MARKOV = "markov"
    CONTOUR = "contour"
    HYBRID = "hybrid"


@dataclass
class GeneratorConfig:
    strategy: GenerationStrategy = GenerationStrategy.HYBRID
    pitch_range: tuple[int, int] = (60, 84)
    rhythm_pattern: str = "mixed_1"
    contour_shape: str = "arch"

    chord_tone_weight: float = 3.0
    scale_tone_weight: float = 1.5
    chromatic_weight: float = 0.1
    strong_beat_multiplier: float = 4.0
    motif_repetition_prob: float = 0.3
    rest_probability: float = 0.1

    velocity_base: int = 90
    velocity_variation: int = 25
    accent_strong_beats: bool = True
    humanize_timing: float = 0.02
    humanize_duration: float = 0.05

    repeats: int = 2
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class MelodyGenerator:
    """
    Generates melodies over chord progressions.

    Usage:
        prog = ChordProgression.from_string("Cmaj7 | Am7 | Dm7 | G7")
        gen = MelodyGenerator(prog, key_root=0, scale_type="major")
        melody = gen.generate()
        melody.print_ascii(prog)
    """

    def __init__(self, progression: ChordProgression, key_root: int = 0,
                 scale_type: str = "major", config: Optional[GeneratorConfig] = None):
        self.progression = progression
        self.scale = Scale(root=key_root, scale_type=scale_type)
        self.config = config or GeneratorConfig()
        self.rng = random.Random(self.config.seed)
        self.markov = IntervalMarkov()

    def generate(self) -> Melody:
        cfg = self.config
        melody = Melody(bpm=self.progression.bpm)
        total_beats = self.progression.total_beats * cfg.repeats

        rhythm = self._build_rhythm(total_beats)

        if cfg.strategy == GenerationStrategy.RULE_BASED:
            pitches = self._generate_rule_based(rhythm)
        elif cfg.strategy == GenerationStrategy.MARKOV:
            pitches = self._generate_markov(rhythm)
        elif cfg.strategy == GenerationStrategy.CONTOUR:
            pitches = self._generate_contour(rhythm)
        else:
            pitches = self._generate_hybrid(rhythm)

        for (beat, dur), pitch in zip(rhythm, pitches):
            if pitch is None:
                continue
            actual_beat = max(0, beat + self.rng.uniform(-cfg.humanize_timing, cfg.humanize_timing))
            actual_dur = max(0.1, dur + self.rng.uniform(-cfg.humanize_duration, cfg.humanize_duration))

            vel = cfg.velocity_base + self.rng.randint(-cfg.velocity_variation, cfg.velocity_variation)
            if cfg.accent_strong_beats and self._is_strong_beat(beat):
                vel += 15
            vel = max(1, min(127, vel))

            melody.notes.append(MelodyNote(
                pitch=pitch,
                start_beat=round(actual_beat, 4),
                duration_beats=round(actual_dur, 4),
                velocity=vel,
            ))

        return melody

    # --- Rhythm ---

    def _build_rhythm(self, total_beats: float) -> list[tuple[float, float]]:
        cfg = self.config
        rhythm = []
        beat = 0.0
        bar_beats = 4.0

        while beat < total_beats - 0.01:
            if cfg.rhythm_pattern == "random":
                pattern_key = self.rng.choice(list(RHYTHM_PATTERNS.keys()))
            else:
                pattern_key = cfg.rhythm_pattern
                if self.rng.random() < 0.2:
                    pattern_key = self.rng.choice(list(RHYTHM_PATTERNS.keys()))

            pattern = RHYTHM_PATTERNS.get(pattern_key, RHYTHM_PATTERNS["quarter_notes"])

            for offset, dur in pattern:
                note_beat = beat + offset
                if note_beat >= total_beats:
                    break
                actual_dur = min(dur, total_beats - note_beat)
                rhythm.append((note_beat, actual_dur))

            beat += bar_beats

        return rhythm

    def _is_strong_beat(self, beat: float) -> bool:
        pos_in_bar = beat % 4.0
        return pos_in_bar < 0.1 or abs(pos_in_bar - 2.0) < 0.1

    def _is_downbeat(self, beat: float) -> bool:
        return (beat % 4.0) < 0.1

    # --- Pitch helpers ---

    def _get_note_weights(self, beat: float, prev_pitch: Optional[int] = None) -> dict[int, float]:
        cfg = self.config
        lo, hi = cfg.pitch_range
        chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
        chord_pcs = chord.pitch_classes
        scale_pcs = set(self.scale.pitch_classes)
        is_strong = self._is_strong_beat(beat)

        weights = {}
        for pitch in range(lo, hi + 1):
            pc = pitch % 12
            w = cfg.chromatic_weight

            if pc in chord_pcs:
                w = cfg.chord_tone_weight
                if is_strong:
                    w *= cfg.strong_beat_multiplier
                if pc == chord.root and self._is_downbeat(beat):
                    w *= 1.5
            elif pc in scale_pcs:
                w = cfg.scale_tone_weight

            if prev_pitch is not None:
                dist = abs(pitch - prev_pitch)
                if dist == 0:
                    w *= 1.5
                elif dist <= 2:
                    w *= 3.0
                elif dist <= 4:
                    w *= 2.0
                elif dist <= 7:
                    w *= 1.0
                elif dist <= 12:
                    w *= 0.4
                else:
                    w *= 0.1

            weights[pitch] = max(w, 0.001)
        return weights

    def _pick_pitch(self, beat: float, prev_pitch: Optional[int] = None) -> Optional[int]:
        if self.rng.random() < self.config.rest_probability:
            return None
        weights = self._get_note_weights(beat, prev_pitch)
        pitches = list(weights.keys())
        probs = list(weights.values())
        return self.rng.choices(pitches, weights=probs, k=1)[0]

    # --- Strategies ---

    def _generate_rule_based(self, rhythm: list[tuple[float, float]]) -> list[Optional[int]]:
        pitches = []
        prev = None
        for beat, dur in rhythm:
            p = self._pick_pitch(beat, prev)
            pitches.append(p)
            if p is not None:
                prev = p
        return pitches

    def _generate_markov(self, rhythm: list[tuple[float, float]]) -> list[Optional[int]]:
        cfg = self.config
        pitches = []
        prev_pitch = self.rng.randint(cfg.pitch_range[0], cfg.pitch_range[1])
        prev_interval = 0

        for beat, dur in rhythm:
            if self.rng.random() < cfg.rest_probability:
                pitches.append(None)
                continue

            interval = self.markov.next_interval(prev_interval, self.rng)
            candidate = prev_pitch + interval
            candidate = max(cfg.pitch_range[0], min(cfg.pitch_range[1], candidate))

            if self._is_strong_beat(beat):
                chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
                if candidate % 12 not in chord.pitch_classes:
                    best, best_dist = candidate, 99
                    for offset in range(-4, 5):
                        test = candidate + offset
                        if (test % 12) in chord.pitch_classes and abs(offset) < best_dist:
                            if cfg.pitch_range[0] <= test <= cfg.pitch_range[1]:
                                best, best_dist = test, abs(offset)
                    candidate = best

            prev_interval = candidate - prev_pitch
            prev_pitch = candidate
            pitches.append(candidate)

        return pitches

    def _generate_contour(self, rhythm: list[tuple[float, float]]) -> list[Optional[int]]:
        cfg = self.config

        if cfg.contour_shape == "random":
            shape_key = self.rng.choice(list(CONTOUR_SHAPES.keys()))
        else:
            shape_key = cfg.contour_shape
        shape = CONTOUR_SHAPES.get(shape_key, CONTOUR_SHAPES["arch"])

        n = len(rhythm)
        if n == 0:
            return []

        interpolated = []
        for i in range(n):
            t = i / max(n - 1, 1) * (len(shape) - 1)
            idx = int(t)
            frac = t - idx
            if idx >= len(shape) - 1:
                val = shape[-1]
            else:
                val = shape[idx] * (1 - frac) + shape[idx + 1] * frac
            interpolated.append(val)

        mid_pitch = (cfg.pitch_range[0] + cfg.pitch_range[1]) // 2
        pitch_range_half = (cfg.pitch_range[1] - cfg.pitch_range[0]) // 2
        max_contour = max(abs(v) for v in interpolated) if interpolated else 1
        scale_factor = pitch_range_half / max(max_contour, 1)

        pitches = []
        for i, (beat, dur) in enumerate(rhythm):
            if self.rng.random() < cfg.rest_probability:
                pitches.append(None)
                continue

            raw_pitch = mid_pitch + int(interpolated[i] * scale_factor)
            raw_pitch = max(cfg.pitch_range[0], min(cfg.pitch_range[1], raw_pitch))
            snapped = self.scale.nearest_scale_tone(raw_pitch)

            if self._is_strong_beat(beat):
                chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
                if snapped % 12 not in chord.pitch_classes:
                    for offset in [0, 1, -1, 2, -2, 3, -3]:
                        test = snapped + offset
                        if (test % 12) in chord.pitch_classes:
                            if cfg.pitch_range[0] <= test <= cfg.pitch_range[1]:
                                snapped = test
                                break

            pitches.append(snapped)

        return pitches

    def _generate_hybrid(self, rhythm: list[tuple[float, float]]) -> list[Optional[int]]:
        cfg = self.config
        n = len(rhythm)
        if n == 0:
            return []

        contour_pitches = self._generate_contour(rhythm)

        pitches: list[Optional[int]] = []
        prev_pitch = None
        prev_interval = 0
        motif: list[Optional[int]] = []

        for i, (beat, dur) in enumerate(rhythm):
            # Motif repetition
            if (i > 0 and i % self.rng.randint(4, 8) == 0
                    and len(motif) >= 3
                    and self.rng.random() < cfg.motif_repetition_prob):
                chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
                transposition = 0
                if motif[0] is not None:
                    root_midi = chord.root + 60
                    transposition = root_midi - motif[0]
                    while abs(transposition) > 7:
                        transposition += 12 if transposition < 0 else -12

                for j, mp in enumerate(motif):
                    if i + j >= n:
                        break
                    if mp is not None:
                        transposed = max(cfg.pitch_range[0],
                                         min(cfg.pitch_range[1], mp + transposition))
                        pitches.append(transposed)
                        prev_pitch = transposed
                    else:
                        pitches.append(None)

                i_end = min(i + len(motif), n)
                while len(pitches) < i_end:
                    pitches.append(self._pick_pitch(rhythm[len(pitches)][0], prev_pitch))

                motif = []
                continue

            if len(pitches) > i:
                continue

            if self.rng.random() < cfg.rest_probability:
                pitches.append(None)
                motif.append(None)
                continue

            candidates = []

            if contour_pitches[i] is not None:
                candidates.append(('contour', contour_pitches[i], 0.4))

            if prev_pitch is not None:
                interval = self.markov.next_interval(prev_interval, self.rng)
                markov_pitch = max(cfg.pitch_range[0],
                                   min(cfg.pitch_range[1], prev_pitch + interval))
                candidates.append(('markov', markov_pitch, 0.3))

            wr_pitch = self._pick_pitch(beat, prev_pitch)
            if wr_pitch is not None:
                candidates.append(('weighted', wr_pitch, 0.3))

            if not candidates:
                pitches.append(None)
                motif.append(None)
                continue

            labels, cand_pitches, cand_weights = zip(*candidates)
            chosen_pitch = self.rng.choices(cand_pitches, weights=cand_weights, k=1)[0]

            if self._is_strong_beat(beat):
                chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
                if chosen_pitch % 12 not in chord.pitch_classes:
                    for offset in [0, 1, -1, 2, -2, 3, -3, 4, -4]:
                        test = chosen_pitch + offset
                        if ((test % 12) in chord.pitch_classes
                                and cfg.pitch_range[0] <= test <= cfg.pitch_range[1]):
                            chosen_pitch = test
                            break

            if chosen_pitch % 12 not in self.scale.pitch_classes:
                chord = self.progression.chord_at_beat(beat % self.progression.total_beats)
                if chosen_pitch % 12 not in chord.pitch_classes:
                    chosen_pitch = self.scale.nearest_scale_tone(chosen_pitch)

            pitches.append(chosen_pitch)
            motif.append(chosen_pitch)

            if prev_pitch is not None:
                prev_interval = chosen_pitch - prev_pitch
            prev_pitch = chosen_pitch

            if len(motif) > 8:
                motif = motif[-self.rng.randint(3, 6):]

        while len(pitches) < n:
            pitches.append(self._pick_pitch(rhythm[len(pitches)][0], prev_pitch))
        pitches = pitches[:n]

        return pitches
