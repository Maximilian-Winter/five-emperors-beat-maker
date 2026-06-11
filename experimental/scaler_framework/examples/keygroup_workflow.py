"""
Example: Key Group Workflow
============================
  1. Create a synthetic sample (sine wave)
  2. Build a key group from it (pitched across a scale)
  3. Save to disk, then reload
  4. Generate a progression and melody
  5. Render to WAV audio using the key group

Run:
    python -m scaler_framework.examples.keygroup_workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

from scaler_framework import (
    ScalerSession, GeneratorConfig, GenerationStrategy, VoicingStyle,
)
from scaler_framework.sampling.pitch import PitchDetector
from scaler_framework.sampling.keygroup import KeyGroup


def create_test_sample(output_dir, note_hz=261.63, note_name="C4"):
    """Create a richer test sample (sine + harmonics with envelope)."""
    sr = 22050
    duration = 1.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Fundamental + a few harmonics for a more musical tone
    y = (0.6 * np.sin(2 * np.pi * note_hz * t)           # fundamental
         + 0.25 * np.sin(2 * np.pi * note_hz * 2 * t)    # 2nd harmonic
         + 0.1 * np.sin(2 * np.pi * note_hz * 3 * t)     # 3rd harmonic
         + 0.05 * np.sin(2 * np.pi * note_hz * 4 * t))   # 4th harmonic

    # Simple ADSR-ish envelope
    attack = int(0.02 * sr)
    decay = int(0.1 * sr)
    release = int(0.3 * sr)
    envelope = np.ones_like(t)
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[attack:attack + decay] = np.linspace(1, 0.6, decay)
    envelope[-release:] = np.linspace(0.6, 0, release)
    y *= envelope

    path = os.path.join(output_dir, f"test_{note_name.replace('#', 's')}.wav")

    import soundfile as sf
    sf.write(path, y.astype(np.float32), sr)
    print(f"  Created test sample: {path} ({note_name} = {note_hz:.1f} Hz)")
    return path


def main():
    print("=" * 60)
    print("  Key Group Workflow Example")
    print("=" * 60)

    output_dir = os.path.dirname(__file__)

    # ── Step 1: Create a test sample ──────────────────────────────

    print("\n  Step 1: Creating a test sample...")
    sample_path = create_test_sample(output_dir, note_hz=261.63, note_name="C4")

    # Verify pitch detection
    detector = PitchDetector(sample_path)
    pitch = detector.detect()
    print(f"  Pitch detection: {pitch}")

    # ── Step 2: Build a key group ─────────────────────────────────

    print("\n  Step 2: Building key group (C major, octaves 3-5)...")
    session = ScalerSession()
    session.set_key(0, "major")
    session.create_key_group(
        sample_path,
        name="test_organ",
        octave_range=(3, 5),
        output_dir=output_dir,
    )

    kg = session.key_group
    print(f"\n  Key group created:")
    print(f"    Name: {kg.name}")
    print(f"    Scale: {kg.scale.name}")
    print(f"    Samples: {len(kg.mappings)}")
    print(f"    Range: MIDI {kg.note_range[0]} - {kg.note_range[1]}")
    print(f"    Notes: {[m.note_name for m in kg.mappings]}")

    # ── Step 3: Save and reload ───────────────────────────────────

    print(f"\n  Step 3: Saved to {kg.base_dir}")
    print("  Reloading from disk...")

    session2 = ScalerSession()
    session2.load_key_group(kg.base_dir)
    print(f"  Loaded: {session2.key_group}")
    print(f"  Session key auto-set to: {session2.key.name}")

    # ── Step 4: Generate music ────────────────────────────────────

    print("\n  Step 4: Generating progression and melody...")

    session2.set_progression("C | Am | F | G", bpm=110)
    config = GeneratorConfig(
        strategy=GenerationStrategy.HYBRID,
        contour_shape="arch",
        rhythm_pattern="mixed_1",
        pitch_range=session2.key_group.note_range,
        repeats=2,
        seed=42,
    )
    session2.generate_melody(config=config)
    session2.melody.print_ascii(session2.progression)

    # ── Step 5: Export ────────────────────────────────────────────

    print("  Step 5: Exporting...")

    # MIDI export
    midi_path = os.path.join(output_dir, "keygroup_demo.mid")
    session2.export_midi(midi_path, voicing_style=VoicingStyle.OPEN)
    print(f"    MIDI: {midi_path}")

    # Audio render via key group
    wav_path = os.path.join(output_dir, "keygroup_demo.wav")
    session2.export_audio(wav_path)
    print(f"    Audio: {wav_path}")

    # ── Summary ───────────────────────────────────────────────────

    session2.print_summary()

    # ── Cleanup hint ──────────────────────────────────────────────

    print(f"  Generated files:")
    print(f"    {kg.base_dir}/       (key group with {len(kg.mappings)} samples)")
    print(f"    {midi_path}")
    print(f"    {wav_path}")
    print(f"\n  Tip: Load the .keygroup in a new session with:")
    print(f"    session.load_key_group('{kg.base_dir}')")


if __name__ == "__main__":
    main()
