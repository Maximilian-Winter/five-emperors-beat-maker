"""
Example: Songwriting Session
=============================
Walk through a typical Scaler-style workflow:
  1. Pick a key and explore its chords
  2. Build a progression using suggestions
  3. Try different voicings
  4. Generate a melody
  5. Export to MIDI

Run:
    python -m scaler_framework.examples.songwriting_session
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scaler_framework import (
    ScalerSession, GeneratorConfig, GenerationStrategy, VoicingStyle,
)
from scaler_framework.generation.progression import ProgressionEngine


def main():
    print("=" * 60)
    print("  Songwriting Session Example")
    print("=" * 60)

    # ── Step 1: Choose a key ──────────────────────────────────────

    session = ScalerSession()
    session.set_key(7, "major")  # G major

    print(f"\n  Key: {session.key.name}")
    print(f"  Scale notes: {', '.join(session.key.get_scale_notes())}")

    # ── Step 2: Explore chord suggestions ─────────────────────────

    engine = ProgressionEngine(root=7, scale="major")

    print("\n  Building a progression with suggestions...\n")

    progression = ["I"]
    for step in range(7):
        suggestions = engine.suggest_next(progression, top_n=3)
        chosen = suggestions[0]  # take the top suggestion each time
        progression.append(chosen.degree)

        print(f"  After {' -> '.join(progression[:-1])}")
        print(f"    Top pick: {chosen.degree} ({chosen.symbol}) "
              f"-- {chosen.reason}")

    print(f"\n  Final progression: {' -> '.join(progression)}")

    # Convert to actual chord names for the session
    chord_names = []
    for deg in progression:
        note, qual = engine.degree_to_note_name(deg)
        chord_names.append(f"{note}{qual}" if qual != "maj" else note)

    prog_string = " | ".join(chord_names)
    print(f"  As chords: {prog_string}")

    session.set_progression(prog_string)

    # ── Step 3: Compare voicings ──────────────────────────────────

    print(f"\n  Voicing comparison for this progression:")
    for style in [VoicingStyle.CLOSE, VoicingStyle.DROP_2,
                  VoicingStyle.SHELL, VoicingStyle.OPEN]:
        voiced = session.voice_progression(style=style, voice_lead=True)
        print(f"\n    {style.value}:")
        for vc in voiced:
            notes = ", ".join(vc.note_names)
            print(f"      {vc.chord.name:>6}: {notes}")

    # ── Step 4: Generate melodies with different strategies ───────

    strategies = [
        ("Rule-based", GenerationStrategy.RULE_BASED, "mixed_1", "arch"),
        ("Markov", GenerationStrategy.MARKOV, "syncopated_1", "arch"),
        ("Contour (wave)", GenerationStrategy.CONTOUR, "dotted", "wave"),
        ("Hybrid", GenerationStrategy.HYBRID, "mixed_2", "question"),
    ]

    for name, strat, rhythm, contour in strategies:
        print(f"\n  --- Melody: {name} ---")
        config = GeneratorConfig(
            strategy=strat,
            rhythm_pattern=rhythm,
            contour_shape=contour,
            pitch_range=(55, 79),  # fits G major nicely
            repeats=1,
            seed=42,
        )
        session.generate_melody(config=config)
        session.melody.print_ascii(session.progression)

    # ── Step 5: Export the last melody ────────────────────────────

    # Re-generate with hybrid for the final export
    config = GeneratorConfig(
        strategy=GenerationStrategy.HYBRID,
        rhythm_pattern="mixed_1",
        contour_shape="arch",
        pitch_range=(55, 79),
        repeats=2,
        seed=42,
    )
    session.generate_melody(config=config)

    output_dir = os.path.dirname(__file__)

    # Export with different voicings
    midi_close = os.path.join(output_dir, "session_close_voicing.mid")
    midi_drop2 = os.path.join(output_dir, "session_drop2_voicing.mid")
    midi_shell = os.path.join(output_dir, "session_shell_voicing.mid")

    session.export_midi(midi_close, voicing_style=VoicingStyle.CLOSE)
    session.export_midi(midi_drop2, voicing_style=VoicingStyle.DROP_2)
    session.export_midi(midi_shell, voicing_style=VoicingStyle.SHELL)

    print(f"\n  Exported:")
    print(f"    {midi_close}")
    print(f"    {midi_drop2}")
    print(f"    {midi_shell}")

    # ── Summary ───────────────────────────────────────────────────

    session.print_summary()


if __name__ == "__main__":
    main()
