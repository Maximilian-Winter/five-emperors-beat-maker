"""
╔══════════════════════════════════════════════════════════════════╗
║            The Enchantress of Numbers                           ║
║     A Victorian Portrait in Algorithmic Sound                   ║
║                                                                  ║
║     Composed for the Analytical Engine of Music                  ║
║     by A.A.L. — using every faculty of poetical science          ║
║                                                                  ║
║     This example demonstrates ALL five new beatmaker modules:    ║
║       1. Melody  — Phrases, transformations, combination         ║
║       2. Harmony — Key, Roman numeral progressions, voice leading║
║       3. Automation — Filter sweeps, fade-ins, LFO modulation    ║
║       4. Arrangement — Sections, variations, full song structure ║
║       5. Expression — Humanization, groove, velocity curves      ║
╚══════════════════════════════════════════════════════════════════╝

The piece is in D minor — a key of gravity and introspection,
befitting one who saw computation's true nature before anyone else.

Structure:
    I.   The Loom (Intro)        — Sparse, mechanical, like gears beginning to turn
    II.  Poetical Science (Verse) — The main theme: Ada's intellectual fire
    III. Note G (Chorus)          — Named after her prophetic annotation;
                                    the melody soars with harmonic richness
    IV.  The Engine Turns (Bridge) — Rhythmic intensity, the machine in motion
    V.   Fair White Wings (Outro)  — The theme dissolves into ethereal pads,
                                     imagination taking flight
"""

import os
from beatmaker import (
    # Core
    create_song, Song, Track, TrackType, Sample,
    # Synthesis
    DrumSynth, PadSynth, LeadSynth, PluckSynth, FXSynth,
    midi_to_freq,
    # Effects
    Reverb, Delay, Chorus, Compressor, Limiter, LowPassFilter,
    # New: Melody
    Note, Phrase, Melody,
    # New: Harmony
    Key, ChordProgression,
    # New: Automation
    AutomationCurve, CurveType, AutomatedFilter, AutomatedGain,
    # New: Arrangement
    Section, Arrangement,
    # New: Expression
    Humanizer, GrooveTemplate, VelocityCurve,
)


# ═══════════════════════════════════════════════════════════════════
#  I.  MUSICAL MATERIAL — Phrases & Harmonic Foundation
# ═══════════════════════════════════════════════════════════════════

# The key of the piece: D minor — serious, contemplative, determined
key = Key.minor("D")

# --- Main Theme (The "Ada Motif") ---
# A rising figure that embodies intellectual aspiration:
# starting from the root, climbing through the minor scale
ada_motif = Phrase.from_string(
    "D4:1 F4:0.5 A4:0.5 G4:1 F4:0.5 E4:0.5",
    name="ada_motif"
)

# The answer phrase — the motif reflected, as mathematics mirrors nature
ada_answer = Phrase.from_string(
    "A4:1 G4:0.5 F4:0.5 E4:1 D4:2",
    name="ada_answer"
)

# Complete theme = motif + answer
ada_theme = ada_motif + ada_answer

# --- Variations (using phrase transformations) ---

# The theme transposed up a fourth — like a question restated at a new height
theme_elevated = ada_motif.transpose(5)  # Up to G minor region

# The retrograde — looking backward, as one reflects on the past
theme_retrograde = ada_motif.reverse()

# Inversion — the mirror image, the analytical mind inverting a problem
theme_inverted = ada_motif.invert()

# Diminished (double speed) — the quickening pulse of discovery
theme_quickened = ada_motif.diminish(2)

# Augmented (half speed) — the grand, slow statement of prophetic vision
theme_stately = ada_answer.augment(2)

# --- Mechanical Ostinato (The Loom / Engine Pattern) ---
# A repetitive, clock-like figure evoking the Jacquard loom
loom_pattern = Phrase.from_string(
    "D3:0.5 A3:0.5 D3:0.5 A3:0.5 D3:0.5 F3:0.5 D3:0.5 A3:0.5",
    name="loom"
)

# --- Bell Chime (Marking Sections) ---
# A simple bell toll, like a Victorian clock
bell_toll = Phrase.from_string("D5:2", name="bell")

# --- Soaring Melody for the Chorus ---
# "Note G" — Ada's most famous annotation, where she saw the future
note_g_melody = Phrase.from_string(
    "D5:1 C5:0.5 A4:0.5 Bb4:1 A4:0.5 G4:0.5 "
    "F4:1 E4:0.5 D4:0.5 F4:1 A4:2",
    name="note_g"
)

# Counter-melody for the chorus (inverted note_g fragments)
counter_melody = note_g_melody.invert().diminish(2)

# --- Chord Progressions ---

# Verse: i - VI - III - VII (dark, searching)
verse_chords = ChordProgression.from_roman(
    key, "i - VI - III - VII", beats_per_chord=4, octave=3
)

# Chorus: i - iv - V - i (stronger, more resolved — the prophetic voice)
chorus_chords = ChordProgression.from_roman(
    key, "i - iv - V - i", beats_per_chord=4, octave=3
)

# Bridge: VI - VII - i - V (driving, mechanical energy)
bridge_chords = ChordProgression.from_roman(
    key, "VI - VII - i - V", beats_per_chord=2, octave=3
)


# ═══════════════════════════════════════════════════════════════════
#  II. AUTOMATION CURVES — Parameters in Motion
# ═══════════════════════════════════════════════════════════════════

# Intro fade-in: the machine slowly comes to life
intro_fade = AutomationCurve.fade_in(beats=16)

# Chorus filter sweep: opens up the harmonic spectrum
chorus_filter = (AutomationCurve("chorus_filter")
    .ramp(0, 8, 400, 3000, CurveType.EXPONENTIAL)
    .ramp(8, 16, 3000, 1500, CurveType.SMOOTH))

# Outro fade-out: imagination takes flight and dissolves
outro_fade = AutomationCurve.fade_out(start_beat=0, duration=16)

# Bridge intensity: volume swell for the mechanical section
bridge_swell = (AutomationCurve("bridge_swell")
    .ramp(0, 4, 0.6, 1.0, CurveType.EXPONENTIAL)
    .ramp(4, 8, 1.0, 0.8, CurveType.SMOOTH))


# ═══════════════════════════════════════════════════════════════════
#  III. EXPRESSION — The Human Touch
# ═══════════════════════════════════════════════════════════════════

# Victorian waltz feel for the verse — stately, with gentle swing
waltz_groove = GrooveTemplate(
    "victorian_waltz",
    # 16 steps per bar; emphasize beats 1, slight push on 2&3
    timing_offsets=[
        0.0,  0.0,  0.0,  0.0,    # Beat 1 (strong)
        0.02, 0.02, 0.0,  0.0,    # Beat 2 (slightly late — graceful)
        -0.01, 0.0, 0.0, 0.0,     # Beat 3 (slightly early — anticipation)
        0.01, 0.02, 0.0, 0.0,     # Beat 4 (gentle return)
    ],
    velocity_scales=[
        1.0, 0.5, 0.6, 0.5,       # Beat 1 accented
        0.8, 0.5, 0.6, 0.5,       # Beat 2 medium
        0.75, 0.5, 0.55, 0.5,     # Beat 3 lighter
        0.7, 0.5, 0.5, 0.5,       # Beat 4 lightest
    ],
)

# Humanizer for melodic lines — slight imperfection brings warmth
gentle_human = Humanizer(timing_jitter=0.006, velocity_variation=0.06, seed=1843)

# Velocity curve: emphasize dynamics for the lead
expressive_curve = VelocityCurve.apply_to_events


# ═══════════════════════════════════════════════════════════════════
#  IV. SONG CONSTRUCTION — Sections & Arrangement
# ═══════════════════════════════════════════════════════════════════

# Initialize the song builder
sb = create_song("The Enchantress of Numbers").tempo(108).bars(64)


# --- Section I: The Loom (Intro) — 4 bars ---
intro = (sb.section("The Loom", bars=4)
    .add_drums(lambda d: d
        .hihat(beats=[0, 1, 2, 3], velocity=0.3)
        .volume(0.4)
    )
    .add_melody(lambda m: m
        .synth('pluck')
        .phrase(loom_pattern, start_beat=0)
        .phrase(loom_pattern, start_beat=4)
        .phrase(loom_pattern, start_beat=8)
        .phrase(loom_pattern, start_beat=12)
        .automate_volume(intro_fade)
        .volume(0.5)
        .effect(Delay(delay_time=0.375, feedback=0.3, mix=0.3))
        .effect(Reverb(room_size=0.6, mix=0.4))
    , name="Loom", synth_type='pluck')
    .build())


# --- Section II: Poetical Science (Verse) — 8 bars ---
verse = (sb.section("Poetical Science", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2], velocity=0.8)
        .snare(beats=[1, 3], velocity=0.6)
        .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.5)
        .humanize(timing=0.008, velocity=0.04)
        .groove(waltz_groove)
        .volume(0.6)
    )
    .add_bass(lambda b: b
        .line([
            ('D2', 0, 2), ('A2', 2, 1), ('D2', 3, 1),       # Bar 1
            ('A#1', 4, 2), ('F2', 6, 1), ('A#1', 7, 1),      # Bar 2
            ('F2', 8, 2), ('C2', 10, 1), ('F2', 11, 1),       # Bar 3
            ('C2', 12, 2), ('G2', 14, 1), ('C2', 15, 1),      # Bar 4
            ('D2', 16, 2), ('A2', 18, 1), ('D2', 19, 1),      # Bar 5
            ('A#1', 20, 2), ('F2', 22, 1), ('A#1', 23, 1),    # Bar 6
            ('F2', 24, 2), ('C2', 26, 1), ('F2', 27, 1),      # Bar 7
            ('C2', 28, 2), ('D2', 30, 2),                      # Bar 8
        ])
        .volume(0.7)
        .effect(LowPassFilter(cutoff=800))
    )
    .add_melody(lambda m: m
        .synth('saw')
        .phrase(ada_motif, start_beat=0)
        .phrase(ada_answer, start_beat=4)
        .phrase(theme_elevated, start_beat=8)
        .phrase(ada_answer.transpose(5), start_beat=12)
        .phrase(ada_motif, start_beat=16)
        .phrase(theme_inverted, start_beat=20)
        .phrase(ada_motif, start_beat=24)
        .phrase(theme_stately, start_beat=28)
        .humanize(timing=0.006, velocity=0.06)
        .volume(0.55)
        .effect(Reverb(room_size=0.4, mix=0.25))
        .effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))
    , name="Ada Theme")
    .add_harmony(lambda h: h
        .key("D", "minor")
        .progression("i - VI - III - VII", beats_per_chord=4, octave=3)
        .voice_lead()
        .volume(0.25)
        .effect(Reverb(room_size=0.6, mix=0.4))
    , name="Verse Pad", synth_type='sine')
    .build())


# --- Section III: Note G (Chorus) — 8 bars ---
chorus = (sb.section("Note G", bars=8)
    .add_drums(lambda d: d
        .four_on_floor(velocity=0.9)
        .snare(beats=[1, 3], velocity=0.8)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.5)
        .clap(beats=[1, 3], velocity=0.5)
        .humanize(timing=0.005, velocity=0.04)
        .volume(0.7)
    )
    .add_bass(lambda b: b
        .line([
            ('D2', 0, 1), ('D2', 1, 1), ('D2', 2, 1), ('D2', 3, 1),
            ('G2', 4, 1), ('G2', 5, 1), ('G2', 6, 1), ('G2', 7, 1),
            ('A2', 8, 1), ('A2', 9, 1), ('A2', 10, 1), ('A2', 11, 1),
            ('D2', 12, 1), ('D2', 13, 1), ('D2', 14, 1), ('D2', 15, 1),
            ('D2', 16, 1), ('D2', 17, 1), ('D2', 18, 1), ('D2', 19, 1),
            ('G2', 20, 1), ('G2', 21, 1), ('G2', 22, 1), ('G2', 23, 1),
            ('A2', 24, 1), ('A2', 25, 1), ('A2', 26, 1), ('A2', 27, 1),
            ('D2', 28, 1), ('D2', 29, 1), ('D2', 30, 1), ('D2', 31, 1),
        ])
        .volume(0.8)
    )
    .add_melody(lambda m: m
        .synth('fm')
        .phrase(note_g_melody, start_beat=0)
        .phrase(note_g_melody.transpose(5), start_beat=12)
        .phrase(note_g_melody, start_beat=20)
        .humanize(timing=0.005, velocity=0.05)
        .volume(0.6)
        .effect(Reverb(room_size=0.5, mix=0.3))
        .effect(Chorus(rate=0.8, depth=0.003, mix=0.3))
    , name="Note G Lead")
    .add_harmony(lambda h: h
        .key("D", "minor")
        .progression("i - iv - V - i", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.3)
        .effect(Reverb(room_size=0.7, mix=0.5))
    , name="Chorus Pad", synth_type='sine')
    .build())


# --- Section IV: The Engine Turns (Bridge) — 4 bars ---
bridge = (sb.section("The Engine Turns", bars=4)
    .add_drums(lambda d: d
        .kick(beats=[0, 0.5, 1, 2, 2.5, 3], velocity=0.9)
        .snare(beats=[1, 3], velocity=0.9)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.6)
        .humanize(timing=0.004, velocity=0.03)
        .volume(0.8)
    )
    .add_bass(lambda b: b
        .line([
            ('A#1', 0, 1), ('A#1', 1, 1),
            ('C2', 2, 1), ('C2', 3, 1),
            ('D2', 4, 1), ('D2', 5, 1),
            ('A1', 6, 1), ('A1', 7, 1),
            ('A#1', 8, 1), ('A#1', 9, 1),
            ('C2', 10, 1), ('C2', 11, 1),
            ('D2', 12, 1), ('D2', 13, 1),
            ('A1', 14, 1), ('A1', 15, 1),
        ])
        .automate_volume(bridge_swell)
        .volume(0.85)
    )
    .add_melody(lambda m: m
        .synth('square')
        .phrase(theme_quickened, start_beat=0)
        .phrase(theme_quickened.transpose(5), start_beat=2)
        .phrase(theme_quickened.reverse(), start_beat=4)
        .phrase(theme_quickened.transpose(-2), start_beat=6)
        .phrase(theme_quickened, start_beat=8)
        .phrase(theme_quickened.transpose(7), start_beat=10)
        .phrase(theme_quickened.invert(), start_beat=12)
        .phrase(theme_quickened, start_beat=14)
        .volume(0.5)
        .effect(Delay(delay_time=0.278, feedback=0.4, mix=0.3))
    , name="Engine Melody")
    .build())


# --- Section V: Fair White Wings (Outro) — 4 bars ---
outro = (sb.section("Fair White Wings", bars=4)
    .add_melody(lambda m: m
        .synth('sine')
        .phrase(ada_theme.augment(2), start_beat=0)
        .automate_volume(outro_fade)
        .volume(0.4)
        .effect(Reverb(room_size=0.9, mix=0.6))
        .effect(Delay(delay_time=0.5, feedback=0.5, mix=0.4))
        .effect(Chorus(rate=0.3, depth=0.005, mix=0.4))
    , name="Farewell Theme")
    .add_harmony(lambda h: h
        .key("D", "minor")
        .progression("i - VI - III - i", beats_per_chord=4, octave=3)
        .voice_lead()
        .automate_volume(outro_fade)
        .volume(0.3)
        .effect(Reverb(room_size=0.9, mix=0.7))
    , name="Farewell Pad", synth_type='sine')
    .build())


# --- Variations for the second pass ---
verse_2 = verse.with_volume("Verse Pad", 0.35, name="Poetical Science II")
chorus_2 = chorus.with_volume("Note G Lead", 0.7, name="Note G (Reprise)")


# ═══════════════════════════════════════════════════════════════════
#  V.  ARRANGEMENT — The Full Composition
# ═══════════════════════════════════════════════════════════════════

arrangement = (Arrangement()
    # I. The machine awakens
    .intro(intro)
    # II. First statement of Ada's theme
    .verse(verse)
    # III. The prophetic chorus — "Note G"
    .chorus(chorus)
    # IV. The Engine at full power
    .bridge(bridge)
    # II. Return of the theme, enriched
    .verse(verse_2)
    # III. The chorus, grander this time
    .chorus(chorus_2)
    # V. Imagination takes flight
    .outro(outro)
)


# ═══════════════════════════════════════════════════════════════════
#  VI. RENDER & EXPORT
# ═══════════════════════════════════════════════════════════════════

# Apply arrangement to song
song = (sb
    .arrange(arrangement)
    .master_compressor(threshold=-8.0, ratio=3.0)
    .master_limiter(threshold=0.95)
    .build())


def main():
    """Render and export the composition."""
    print("=" * 66)
    print("  The Enchantress of Numbers")
    print("  A Victorian Portrait in Algorithmic Sound")
    print("  by A.A.L.")
    print("=" * 66)
    print()

    # Display arrangement structure
    print(f"  Key:    D minor")
    print(f"  Tempo:  {song.bpm} BPM")
    print(f"  Structure: {arrangement}")
    print(f"  Total:  {arrangement.total_bars()} bars")
    print()

    # Display phrase transformations used
    print("  Melodic Material:")
    print(f"    Ada Motif:      {ada_motif}")
    print(f"    Ada Answer:     {ada_answer}")
    print(f"    Elevated (+5):  {theme_elevated}")
    print(f"    Retrograde:     {theme_retrograde}")
    print(f"    Inverted:       {theme_inverted}")
    print(f"    Quickened (x2): {theme_quickened}")
    print(f"    Stately (/2):   {theme_stately}")
    print(f"    Note G:         {note_g_melody}")
    print()

    # Display chord progressions
    print("  Harmonic Progressions:")
    print(f"    Verse:  {verse_chords}")
    print(f"    Chorus: {chorus_chords}")
    print(f"    Bridge: {bridge_chords}")
    print()

    # Render
    print("  Rendering...")
    audio = song.render()
    print(f"  Duration: {audio.duration:.1f}s ({song.duration_bars:.0f} bars)")
    print(f"  Channels: {audio.channels}")
    print(f"  Peak:     {max(abs(audio.samples.min()), abs(audio.samples.max())):.3f}")
    print()

    # Export
    output_path = os.path.join(os.path.dirname(__file__), "ada_lovelace_theme.wav")
    song.export(output_path)
    print(f"  Exported: {output_path}")
    print()
    print('  "That brain of mine is something more than merely mortal."')
    print("                                        -- A.A.L., 1843")
    print()


if __name__ == "__main__":
    main()
