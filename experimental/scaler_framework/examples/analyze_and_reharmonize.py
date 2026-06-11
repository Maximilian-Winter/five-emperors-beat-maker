"""
Example: Analyze a MIDI file, then reharmonize and generate a new melody
=========================================================================
  1. Detect key and chords from a MIDI file
  2. Show analysis results
  3. Generate a new progression in the same key
  4. Generate a melody over the new progression
  5. Export both the original analysis and the new version

Run:
    python -m scaler_framework.examples.analyze_and_reharmonize

(Uses the demo MIDI files in the project root. If they don't exist,
generates a fresh one to analyze.)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scaler_framework import (
    ScalerSession, GeneratorConfig, GenerationStrategy, VoicingStyle,
)


def ensure_demo_midi(output_dir):
    """Create a simple demo MIDI to analyze if none exists."""
    demo_path = os.path.join(output_dir, "..", "demo1_pop_hybrid.mid")
    if os.path.exists(demo_path):
        return demo_path

    # Generate one from scratch
    print("  No existing MIDI found, generating a demo...")
    s = ScalerSession()
    s.set_key(0, "major")
    s.set_progression("C | Am | F | G", bpm=120)
    s.generate_melody(GeneratorConfig(
        strategy=GenerationStrategy.HYBRID,
        seed=42,
        repeats=2,
    ))
    path = os.path.join(output_dir, "demo_to_analyze.mid")
    s.export_midi(path)
    return path


def main():
    print("=" * 60)
    print("  Analyze & Reharmonize Example")
    print("=" * 60)

    output_dir = os.path.dirname(__file__)
    midi_path = ensure_demo_midi(output_dir)

    # ── Step 1: Analyze the MIDI file ─────────────────────────────

    print(f"\n  Analyzing: {midi_path}")

    session = ScalerSession()
    session.detect_from_midi(midi_path)

    print(f"\n  Detected key: {session.key}")
    print(f"  Scale notes: {', '.join(session.key.get_scale_notes())}")

    if session.key_alternatives:
        print(f"  Other candidates:")
        for k in session.key_alternatives[1:4]:
            print(f"    {k}")

    print(f"\n  Detected chords ({len(session.detected_chords)}):")
    for ch in session.detected_chords[:12]:
        print(f"    {ch}")

    if session.progression:
        print(f"\n  Original progression: {session.progression}")

    # ── Step 2: Generate a new progression in the same key ────────

    print(f"\n  Generating a new progression in {session.key.name}...")

    session.generate_progression(length=8, temperature=0.6)
    print(f"  New progression: {session.progression}")

    # ── Step 3: Generate a melody over the new chords ─────────────

    print(f"\n  Generating melodies over the new progression...")

    # Try three different approaches
    configs = {
        "gentle_arch": GeneratorConfig(
            strategy=GenerationStrategy.CONTOUR,
            contour_shape="arch",
            rhythm_pattern="dotted",
            pitch_range=(60, 79),
            rest_probability=0.12,
            repeats=2,
            seed=100,
        ),
        "jazzy_markov": GeneratorConfig(
            strategy=GenerationStrategy.MARKOV,
            rhythm_pattern="syncopated_2",
            pitch_range=(58, 82),
            rest_probability=0.18,
            repeats=2,
            seed=200,
        ),
        "hybrid_mix": GeneratorConfig(
            strategy=GenerationStrategy.HYBRID,
            contour_shape="question",
            rhythm_pattern="mixed_1",
            pitch_range=(60, 84),
            motif_repetition_prob=0.4,
            repeats=2,
            seed=300,
        ),
    }

    for name, config in configs.items():
        print(f"\n  --- {name} ---")
        session.generate_melody(config=config)
        session.melody.print_ascii(session.progression)

        midi_out = os.path.join(output_dir, f"reharmonized_{name}.mid")
        session.export_midi(midi_out, voicing_style=VoicingStyle.DROP_2)
        print(f"  -> {midi_out}")

    # ── Summary ───────────────────────────────────────────────────

    session.print_summary()

    print("  Tip: Open the .mid files in a DAW to hear the results,")
    print("  or use a soundfont player like fluidsynth.")


if __name__ == "__main__":
    main()
