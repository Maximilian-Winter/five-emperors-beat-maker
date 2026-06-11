"""
Chord progression suggestion engine.

Three strategies:
1. Rule-based: functional harmony (common movements, circle of fifths)
2. Markov chain: trained on corpus of common progressions
3. Hybrid: combines both
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np

from scaler_framework.theory.constants import NOTE_NAMES
from scaler_framework.theory.roman import (
    MAJOR_DIATONIC, MINOR_DIATONIC, MAJOR_EXTENDED,
    MAJOR_MOVEMENTS, MINOR_MOVEMENTS,
    degree_to_note,
)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

MAJOR_CORPUS = [
    ["I", "V", "vi", "IV"],
    ["I", "IV", "V", "I"],
    ["I", "vi", "IV", "V"],
    ["I", "IV", "vi", "V"],
    ["vi", "IV", "I", "V"],
    ["I", "V", "vi", "iii", "IV"],
    ["I", "iii", "IV", "V"],
    ["I", "IV", "I", "V"],
    ["I", "IV", "V", "IV"],
    ["ii", "V", "I"],
    ["ii", "V", "I", "vi"],
    ["I", "vi", "ii", "V"],
    ["iii", "vi", "ii", "V"],
    ["I", "V", "IV", "I"],
    ["IV", "I", "V", "I"],
    ["I", "ii", "IV", "V"],
    ["vi", "IV", "V", "I"],
    ["I", "IV", "ii", "V"],
    ["I", "V", "IV", "V"],
    ["I", "iii", "vi", "IV"],
    ["IV", "V", "vi", "I"],
    ["vi", "V", "IV", "V"],
    ["I", "IV", "vi", "IV", "V"],
    ["I", "V", "vi", "IV", "I"],
    ["ii", "V", "I", "IV"],
    ["iii", "vi", "ii", "V", "I"],
    ["I", "vi", "ii", "V", "I"],
    ["I", "IV", "viio", "iii", "vi", "ii", "V", "I"],
    ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"],
]

MINOR_CORPUS = [
    ["i", "VII", "VI", "v"],
    ["i", "iv", "v", "i"],
    ["i", "VI", "III", "VII"],
    ["i", "iv", "VII", "III"],
    ["i", "VII", "VI", "VII"],
    ["i", "v", "VI", "VII"],
    ["i", "iio", "v", "i"],
    ["VI", "VII", "i", "i"],
    ["i", "iv", "i", "v"],
    ["i", "III", "VII", "iv"],
    ["i", "VI", "iv", "v"],
]


# ---------------------------------------------------------------------------
# Markov chain
# ---------------------------------------------------------------------------

class MarkovChain:
    """First-order Markov chain for chord progression modeling."""

    def __init__(self):
        self.transitions: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.totals: dict[str, float] = defaultdict(float)

    def train(self, corpus: list[list[str]]):
        for prog in corpus:
            for i in range(len(prog) - 1):
                current = prog[i]
                nxt = prog[i + 1]
                self.transitions[current][nxt] += 1.0
                self.totals[current] += 1.0

    def get_probabilities(self, current: str) -> dict[str, float]:
        if current not in self.transitions:
            return {}
        total = self.totals[current]
        return {nxt: count / total for nxt, count in self.transitions[current].items()}

    def sample_next(self, current: str) -> Optional[str]:
        probs = self.get_probabilities(current)
        if not probs:
            return None
        choices = list(probs.keys())
        weights = [probs[c] for c in choices]
        return random.choices(choices, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Suggestion
# ---------------------------------------------------------------------------

@dataclass
class ChordSuggestion:
    """A suggested next chord with scoring metadata."""
    degree: str
    root_note: str
    chord_quality: str
    score: float
    rule_score: float
    markov_score: float
    reason: str

    @property
    def symbol(self) -> str:
        return f"{self.root_note}{self.chord_quality}"

    def __repr__(self):
        return f"{self.degree:>5s} ({self.symbol:<6s})  score: {self.score:.2f}  -- {self.reason}"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ProgressionEngine:
    """
    Chord progression suggestion and generation engine.

    Usage:
        engine = ProgressionEngine(root=0, scale="major")
        suggestions = engine.suggest_next(["I", "V", "vi"])
        prog = engine.generate_progression(length=8)
    """

    def __init__(self, root: int = 0, scale: str = "major"):
        self.root = root
        self.scale = scale

        if scale in ("major", "lydian", "mixolydian"):
            self.diatonic = MAJOR_DIATONIC
            self.extended = MAJOR_EXTENDED
            self.movements = MAJOR_MOVEMENTS
            corpus = MAJOR_CORPUS
        else:
            self.diatonic = MINOR_DIATONIC
            self.extended = {}
            self.movements = MINOR_MOVEMENTS
            corpus = MINOR_CORPUS

        self.markov = MarkovChain()
        self.markov.train(corpus)

    def degree_to_note_name(self, deg: str) -> tuple[str, str]:
        return degree_to_note(deg, self.root, self.scale)

    def suggest_next(self, current_progression: list[str], top_n: int = 6,
                     rule_weight: float = 0.5,
                     markov_weight: float = 0.5) -> list[ChordSuggestion]:
        """Suggest the next chord given progression so far."""
        if not current_progression:
            tonic = "I" if self.scale == "major" else "i"
            note, qual = self.degree_to_note_name(tonic)
            return [ChordSuggestion(
                degree=tonic, root_note=note, chord_quality=qual,
                score=1.0, rule_score=1.0, markov_score=0.0,
                reason="Starting chord (tonic)",
            )]

        last_chord = current_progression[-1]
        candidates = {}

        # Rule-based scoring
        if last_chord in self.movements:
            max_rule_weight = max(w for _, w in self.movements[last_chord])
            for deg, weight in self.movements[last_chord]:
                norm_weight = weight / max_rule_weight
                reason = self._explain_movement(last_chord, deg)
                candidates[deg] = {"rule_score": norm_weight, "reason": reason}

        for deg in self.diatonic:
            if deg not in candidates:
                candidates[deg] = {"rule_score": 0.15, "reason": "Diatonic chord"}

        # Markov scoring
        markov_probs = self.markov.get_probabilities(last_chord)
        max_markov = max(markov_probs.values()) if markov_probs else 1.0

        for deg in candidates:
            mp = markov_probs.get(deg, 0.0) / max_markov if max_markov > 0 else 0
            candidates[deg]["markov_score"] = mp

        for deg, prob in markov_probs.items():
            if deg not in candidates:
                candidates[deg] = {
                    "rule_score": 0.1,
                    "markov_score": prob / max_markov if max_markov > 0 else 0,
                    "reason": "Common in progressions (corpus)",
                }

        # Combine and rank
        suggestions = []
        for deg, scores in candidates.items():
            rs = scores.get("rule_score", 0)
            ms = scores.get("markov_score", 0)
            combined = (rs * rule_weight) + (ms * markov_weight)

            note, qual = self.degree_to_note_name(deg)
            suggestions.append(ChordSuggestion(
                degree=deg, root_note=note, chord_quality=qual,
                score=round(combined, 3),
                rule_score=round(rs, 3), markov_score=round(ms, 3),
                reason=scores.get("reason", ""),
            ))

        suggestions.sort(key=lambda s: s.score, reverse=True)
        return suggestions[:top_n]

    def generate_progression(self, length: int = 8, start: Optional[str] = None,
                             temperature: float = 0.7) -> list[str]:
        """Generate a full chord progression as Roman numerals."""
        if start is None:
            start = "I" if self.scale == "major" else "i"

        progression = [start]

        for _ in range(length - 1):
            suggestions = self.suggest_next(progression, top_n=8)
            if not suggestions:
                break

            if temperature < 0.01:
                chosen = suggestions[0].degree
            else:
                scores = np.array([s.score for s in suggestions])
                scores = np.power(scores, 1.0 / temperature)
                total = scores.sum()
                probs = scores / total if total > 0 else np.ones(len(scores)) / len(scores)
                idx = np.random.choice(len(suggestions), p=probs)
                chosen = suggestions[idx].degree

            progression.append(chosen)

        return progression

    def _explain_movement(self, from_deg: str, to_deg: str) -> str:
        explanations = {
            ("V", "I"):    "Authentic cadence (strongest resolution)",
            ("IV", "I"):   "Plagal cadence (amen cadence)",
            ("V", "vi"):   "Deceptive cadence (surprise resolution)",
            ("ii", "V"):   "Pre-dominant to dominant (classic approach)",
            ("IV", "V"):   "Subdominant to dominant (building tension)",
            ("I", "IV"):   "Tonic to subdominant (opening up)",
            ("I", "V"):    "Tonic to dominant (creating expectation)",
            ("I", "vi"):   "Tonic to relative minor (emotional shift)",
            ("vi", "IV"):  "Common pop movement",
            ("vi", "ii"):  "Circle of fifths motion",
            ("iii", "vi"): "Circle of fifths motion (mediant to submediant)",
            ("I", "ii"):   "Stepwise bass motion",
            ("I", "iii"):  "Tonic to mediant",
        }
        return explanations.get((from_deg, to_deg), f"Common movement from {from_deg}")

    def print_suggestions(self, suggestions: list[ChordSuggestion]):
        print(f"\n  Suggestions (in {NOTE_NAMES[self.root]} {self.scale}):")
        print(f"  {'Rank':<5} {'Degree':<8} {'Chord':<8} {'Score':<7} "
              f"{'Rule':<6} {'Markov':<7} {'Reason'}")
        print(f"  {'-'*70}")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i:<5} {s.degree:<8} {s.symbol:<8} {s.score:<7.2f} "
                  f"{s.rule_score:<6.2f} {s.markov_score:<7.2f} {s.reason}")
        print()
