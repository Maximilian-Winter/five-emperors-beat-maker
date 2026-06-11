"""
Unified CLI entry point for the Scaler Framework.

Usage:
    python -m scaler_framework                          # interactive demo
    python -m scaler_framework detect song.mid          # detect key/chords from MIDI
    python -m scaler_framework detect song.wav          # detect from audio
    python -m scaler_framework generate --key C major   # generate progression + melody
    python -m scaler_framework demo                     # run full demo
"""

from __future__ import annotations

import sys
import json

from scaler_framework.session import ScalerSession
from scaler_framework.theory.constants import NOTE_NAMES, note_name_to_pc
from scaler_framework.generation.melody import GeneratorConfig, GenerationStrategy
from scaler_framework.generation.voicing import VoicingStyle


PRESET_PROGRESSIONS = {
    "pop_1":        "C | Am | F | G",
    "pop_2":        "G | Em | C | D",
    "jazz_ii_v_i":  "Dm7 | G7 | Cmaj7 | Cmaj7",
    "jazz_turnaround": "Cmaj7 | Am7 | Dm7 | G7",
    "blues_basic":  "C7 | C7 | F7 | C7",
    "sad":          "Am | F | C | G",
    "epic":         "Cm | Ab | Eb | Bb",
    "lofi":         "Cmaj7 | Am7 | Fmaj7 | G7",
    "bossa":        "Cmaj7 | Dm7 | Em7 | A7",
    "rnb":          "Fmaj7 | Em7 | Dm7 | Cmaj7",
    "anime":        "F | G | Am | Am",
}


def cmd_detect(args: list[str]):
    """Detect key and chords from a file."""
    if not args:
        print("Usage: detect <file.mid|file.wav> [--json]")
        return

    filepath = args[0]
    as_json = "--json" in args

    session = ScalerSession()

    if filepath.lower().endswith(('.mid', '.midi')):
        session.detect_from_midi(filepath)
    else:
        session.detect_from_audio(filepath)

    if as_json:
        print(json.dumps(session.summary(), indent=2))
    else:
        session.print_summary()


def cmd_generate(args: list[str]):
    """Generate a progression and melody."""
    # Parse args
    key_root = 0
    scale_type = "major"
    preset = None
    prog_str = None
    voicing = "close"
    output = None
    length = 8
    strategy = "hybrid"

    i = 0
    while i < len(args):
        if args[i] == "--key" and i + 1 < len(args):
            key_root = note_name_to_pc(args[i + 1])
            i += 2
        elif args[i] == "--scale" and i + 1 < len(args):
            scale_type = args[i + 1]
            i += 2
        elif args[i] == "--preset" and i + 1 < len(args):
            preset = args[i + 1]
            i += 2
        elif args[i] == "--progression" and i + 1 < len(args):
            prog_str = args[i + 1]
            i += 2
        elif args[i] == "--voicing" and i + 1 < len(args):
            voicing = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--length" and i + 1 < len(args):
            length = int(args[i + 1])
            i += 2
        elif args[i] == "--strategy" and i + 1 < len(args):
            strategy = args[i + 1]
            i += 2
        else:
            i += 1

    session = ScalerSession()
    session.set_key(key_root, scale_type)

    # Set progression
    if preset and preset in PRESET_PROGRESSIONS:
        session.set_progression(PRESET_PROGRESSIONS[preset])
        print(f"  Preset: {preset} -> {PRESET_PROGRESSIONS[preset]}")
    elif prog_str:
        session.set_progression(prog_str)
    else:
        session.generate_progression(length=length)

    print(f"  Key: {session.key.name}")
    print(f"  Progression: {session.progression}")

    # Generate melody
    strat = GenerationStrategy(strategy) if strategy in [s.value for s in GenerationStrategy] else GenerationStrategy.HYBRID
    config = GeneratorConfig(strategy=strat)
    session.generate_melody(config=config)
    session.melody.print_ascii(session.progression)

    # Export
    if output is None:
        output = "output.mid"

    vs = VoicingStyle(voicing) if voicing in [v.value for v in VoicingStyle] else VoicingStyle.CLOSE
    session.export_midi(output, voicing_style=vs)
    print(f"  Saved: {output}")


def cmd_demo():
    """Run a full demo showing all capabilities."""
    print("=" * 60)
    print("  Scaler Framework Demo")
    print("=" * 60)

    session = ScalerSession()

    # --- Demo 1: Pop progression ---
    print("\n--- Demo 1: Pop (C major) ---")
    session.set_key(0, "major")
    session.set_progression("C | Am | F | G")
    config = GeneratorConfig(
        strategy=GenerationStrategy.HYBRID,
        rhythm_pattern="mixed_1",
        contour_shape="arch",
        pitch_range=(60, 79),
        repeats=2,
        seed=42,
    )
    session.generate_melody(config=config)
    session.melody.print_ascii(session.progression)
    session.export_midi("demo_pop.mid", voicing_style=VoicingStyle.OPEN)
    print("  -> demo_pop.mid")

    # --- Demo 2: Jazz with shell voicings ---
    print("\n--- Demo 2: Jazz (C major, shell voicings) ---")
    session.set_progression("Cmaj7 | Am7 | Dm7 | G7")
    config2 = GeneratorConfig(
        strategy=GenerationStrategy.MARKOV,
        rhythm_pattern="syncopated_1",
        pitch_range=(60, 84),
        repeats=2,
        rest_probability=0.15,
        seed=123,
    )
    session.generate_melody(config=config2)
    session.melody.print_ascii(session.progression)
    session.export_midi("demo_jazz.mid", voicing_style=VoicingStyle.SHELL)
    print("  -> demo_jazz.mid")

    # --- Demo 3: Auto-generated progression ---
    print("\n--- Demo 3: Auto-generated progression ---")
    session.set_key(7, "major")  # G major
    session.generate_progression(length=8, temperature=0.5)
    print(f"  Generated: {session.progression}")
    config3 = GeneratorConfig(
        strategy=GenerationStrategy.CONTOUR,
        contour_shape="question",
        rhythm_pattern="dotted",
        pitch_range=(62, 79),
        repeats=2,
        seed=777,
    )
    session.generate_melody(config=config3)
    session.melody.print_ascii(session.progression)
    session.export_midi("demo_auto.mid", voicing_style=VoicingStyle.DROP_2)
    print("  -> demo_auto.mid")

    # --- Voicing showcase ---
    print("\n--- Voicing Styles ---")
    from scaler_framework.theory.chord import Chord
    from scaler_framework.generation.voicing import VoicingEngine
    engine = VoicingEngine()
    chord = Chord.from_string("Cmaj7")
    for style in VoicingStyle:
        vc = engine.voice(chord, style=style, octave=4)
        print(f"  {style.value:<12s}: {', '.join(vc.note_names)}")

    # --- Suggestion demo ---
    print("\n--- Chord Suggestions after I -> V -> vi ---")
    from scaler_framework.generation.progression import ProgressionEngine
    pe = ProgressionEngine(root=0, scale="major")
    suggestions = pe.suggest_next(["I", "V", "vi"])
    pe.print_suggestions(suggestions)

    print("\n  Presets:")
    for name, prog in PRESET_PROGRESSIONS.items():
        print(f"    {name:20s} -> {prog}")

    print(f"\n{'=' * 60}")
    print("  Done! Check the generated .mid files.")
    print(f"{'=' * 60}\n")


def cmd_keygroup(args: list[str]):
    """Key group creation, loading, and rendering."""
    if not args:
        print("Usage:")
        print("  keygroup create <audio.wav> [options]    Create a key group from a sample")
        print("  keygroup info <path.keygroup>            Show key group info")
        print("  keygroup render <path.keygroup> [opts]   Render a melody using the key group")
        print()
        print("Create options:")
        print("  --name <name>                Name for the key group")
        print("  --scale <type>               Scale type (default: major)")
        print("  --root <note>                Scale root (default: auto-detect from sample)")
        print("  --octaves <lo>-<hi>          Octave range (default: 3-5)")
        print("  --output <dir>               Output directory (default: .)")
        return

    subcmd = args[0]

    if subcmd == "create":
        if len(args) < 2:
            print("Usage: keygroup create <audio.wav> [options]")
            return

        audio_path = args[1]
        name = None
        scale_type = "major"
        root = None
        octave_range = (3, 5)
        output_dir = "."

        i = 2
        while i < len(args):
            if args[i] == "--name" and i + 1 < len(args):
                name = args[i + 1]
                i += 2
            elif args[i] == "--scale" and i + 1 < len(args):
                scale_type = args[i + 1]
                i += 2
            elif args[i] == "--root" and i + 1 < len(args):
                root = note_name_to_pc(args[i + 1])
                i += 2
            elif args[i] == "--octaves" and i + 1 < len(args):
                lo, hi = args[i + 1].split("-")
                octave_range = (int(lo), int(hi))
                i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output_dir = args[i + 1]
                i += 2
            else:
                i += 1

        session = ScalerSession()
        session.create_key_group(
            audio_path, name=name, scale_type=scale_type,
            root=root, octave_range=octave_range, output_dir=output_dir,
        )
        print(f"\n{session.key_group.info()}")

    elif subcmd == "info":
        if len(args) < 2:
            print("Usage: keygroup info <path.keygroup>")
            return
        from scaler_framework.sampling.keygroup import KeyGroup
        kg = KeyGroup.load(args[1])
        print(f"\n{kg.info()}")
        print(f"\n  Notes:")
        for m in kg.mappings:
            print(f"    {m.note_name:>4s}  (MIDI {m.midi_note:>3d}, shift {m.semitone_shift:>+3d})")

    elif subcmd == "render":
        if len(args) < 2:
            print("Usage: keygroup render <path.keygroup> [--progression 'C Am F G'] "
                  "[--output file.wav] [--strategy hybrid]")
            return

        kg_path = args[1]
        prog_str = "C | Am | F | G"
        output = "rendered.wav"
        strategy = "hybrid"

        i = 2
        while i < len(args):
            if args[i] == "--progression" and i + 1 < len(args):
                prog_str = args[i + 1]
                i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            elif args[i] == "--strategy" and i + 1 < len(args):
                strategy = args[i + 1]
                i += 2
            else:
                i += 1

        session = ScalerSession()
        session.load_key_group(kg_path)
        session.set_progression(prog_str)
        print(f"  Key: {session.key.name}")
        print(f"  Progression: {session.progression}")

        strat = GenerationStrategy(strategy) if strategy in [s.value for s in GenerationStrategy] else GenerationStrategy.HYBRID
        config = GeneratorConfig(
            strategy=strat,
            pitch_range=session.key_group.note_range,
        )
        session.generate_melody(config=config)
        session.melody.print_ascii(session.progression)
        session.export_audio(output)

    else:
        print(f"Unknown keygroup subcommand: {subcmd}")
        print("Use: keygroup create | info | render")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "demo":
        cmd_demo()
    elif args[0] == "detect":
        cmd_detect(args[1:])
    elif args[0] == "generate":
        cmd_generate(args[1:])
    elif args[0] == "keygroup":
        cmd_keygroup(args[1:])
    else:
        print("Scaler Framework")
        print()
        print("Commands:")
        print("  demo                         Run full demo")
        print("  detect <file>                Detect key/chords from MIDI or audio")
        print("  generate [options]           Generate progression + melody")
        print("  keygroup <subcmd> [options]   MPC-style key group tools")
        print()
        print("Generate options:")
        print("  --key <note>                 Root note (C, D, F#, etc.)")
        print("  --scale <type>               Scale type (major, natural_minor, dorian, etc.)")
        print("  --preset <name>              Use a preset progression")
        print("  --progression <string>       Custom progression ('Cmaj7 | Am7 | Dm7 | G7')")
        print("  --voicing <style>            Voicing style (close, open, drop_2, shell, etc.)")
        print("  --strategy <type>            Melody strategy (hybrid, rule_based, markov, contour)")
        print("  --output <file.mid>          Output file (default: output.mid)")
        print()
        print("Keygroup subcommands:")
        print("  keygroup create <audio.wav>  Create key group from sample")
        print("  keygroup info <path>         Show key group details")
        print("  keygroup render <path>       Render melody using key group samples")
        print()
        print("Presets:", ", ".join(PRESET_PROGRESSIONS.keys()))


if __name__ == "__main__":
    main()
