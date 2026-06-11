"""
Scaler Framework — Detect, Suggest, Generate, Export
=====================================================
A music theory toolkit inspired by Scaler 2/3.

Quick start:
    from scaler_framework import ScalerSession

    session = ScalerSession()
    session.detect_from_midi("song.mid")
    print(session.key)

    session.set_progression("Cmaj7 | Am7 | Dm7 | G7")
    session.generate_melody()
    session.export_midi("output.mid")
"""

from scaler_framework.session import ScalerSession
from scaler_framework.theory.chord import Chord, ChordProgression
from scaler_framework.theory.scale import Scale, KeyEstimate
from scaler_framework.theory.constants import NOTE_NAMES
from scaler_framework.generation.melody import MelodyGenerator, GeneratorConfig, GenerationStrategy
from scaler_framework.generation.progression import ProgressionEngine
from scaler_framework.generation.voicing import VoicingEngine, VoicingStyle
from scaler_framework.sampling.keygroup import KeyGroup
from scaler_framework.sampling.pitch import PitchDetector, PitchResult
from scaler_framework.sampling.renderer import KeyGroupRenderer

__all__ = [
    "ScalerSession",
    "Chord", "ChordProgression",
    "Scale", "KeyEstimate",
    "NOTE_NAMES",
    "MelodyGenerator", "GeneratorConfig", "GenerationStrategy",
    "ProgressionEngine",
    "VoicingEngine", "VoicingStyle",
    "KeyGroup", "PitchDetector", "PitchResult", "KeyGroupRenderer",
]
