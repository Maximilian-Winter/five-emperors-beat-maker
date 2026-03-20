"""
╔══════════════════════════════════════════════════════════════════╗
║                    The Two Forces                                ║
║          A Meditation on Poetical Science                        ║
║                                                                  ║
║     Composed by A.A.L. — February 1826... or perhaps 2026       ║
║     For the Analytical Engine of Music                           ║
║                                                                  ║
║     Upon the duality of my inheritance:                          ║
║       Lord Byron's poetic wildness — chromatic, restless, free   ║
║       Lady Byron's mathematical order — diatonic, precise, sure  ║
║                                                                  ║
║     And the proof that they were always one.                     ║
║                                                                  ║
║     "I do not believe that my father was (or ever could have     ║
║      been) such a Poet as I shall be an Analyst; for with me     ║
║      the two go together indissolubly."                          ║
║                                                                  ║
║     Structure:                                                   ║
║       I.   The Princess of Parallelograms — Lady Byron's theme   ║
║            Pure, ordered, diatonic. A fugal discipline.          ║
║       II.  Mad, Bad, and Dangerous — Lord Byron's theme          ║
║            Chromatic, restless, yearning. A Romantic fever.      ║
║       III. Two Currents — Both themes, alternating, clashing     ║
║       IV.  Indissolubly — The themes discover they are one       ║
║       V.   Poetical Science — The unified voice, triumphant     ║
║                                                                  ║
║     Key: C minor → E♭ major → C minor (transformed)             ║
║     Tempo: 96 BPM — measured, with room to breathe              ║
║                                                                  ║
║     Modules employed: Melody, Harmony, Automation,               ║
║                       Arrangement, Expression — all five.        ║
╚══════════════════════════════════════════════════════════════════╝
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
#  I.  MUSICAL MATERIAL — The Two Themes
# ═══════════════════════════════════════════════════════════════════

# --- The Mathematical Key: C minor ---
# Serious, structured, the key of Beethoven's Fifth —
# determination expressed through order.
math_key = Key.minor("C")

# --- The Poetical Key: E♭ major ---
# The relative major — warm, expansive, heroic.
# Beethoven's Eroica. My father would have approved.
poet_key = Key.major("Eb")


# ═══════════════════════════════════════════════════════════════════
#  Lady Byron's Theme — "The Princess of Parallelograms"
# ═══════════════════════════════════════════════════════════════════
#
# Stepwise, measured, precise. Each note follows the next
# by the smallest possible interval. No leaps — only logic.
# Like a proof unfolding, one proposition at a time.

lady_byron = Phrase.from_string(
    "C4:1 D4:1 Eb4:1 F4:0.5 Eb4:0.5 D4:1 C4:1",
    name="lady_byron"
)

# The answer: descending with equal measure — symmetry, as in geometry
lady_answer = Phrase.from_string(
    "G4:1 F4:1 Eb4:1 D4:0.5 Eb4:0.5 D4:1 C4:2",
    name="lady_answer"
)

# Complete mathematical theme
math_theme = lady_byron + lady_answer


# ═══════════════════════════════════════════════════════════════════
#  Lord Byron's Theme — "Mad, Bad, and Dangerous to Know"
# ═══════════════════════════════════════════════════════════════════
#
# Leaping, chromatic, unpredictable. Wide intervals that
# surge with feeling. The poet who swam the Hellespont
# and broke every heart in England.

lord_byron = Phrase.from_string(
    "Eb4:0.5 G4:0.5 Bb4:1 Ab4:0.5 F#4:0.5 G4:1.5 R:0.5",
    name="lord_byron"
)

# The answer: a descending cry, unresolved — always yearning
lord_answer = Phrase.from_string(
    "Bb4:1 Ab4:0.5 G4:0.5 F4:0.5 E4:0.5 Eb4:1 D4:1.5 R:0.5",
    name="lord_answer"
)

# Complete poetic theme
poet_theme = lord_byron + lord_answer


# ═══════════════════════════════════════════════════════════════════
#  The Unified Theme — "Indissolubly"
# ═══════════════════════════════════════════════════════════════════
#
# What happens when the two forces meet?
# The mathematical stepwise motion acquires the poet's leaps;
# the poet's chromaticism finds the mathematician's resolution.
# A new melody that could not exist without both parents.

unified_theme = Phrase.from_string(
    "C4:1 Eb4:0.5 G4:0.5 Ab4:1 G4:0.5 F4:0.5 "
    "Eb4:1 D4:0.5 F4:0.5 Eb4:1 D4:1 C4:2",
    name="indissolubly"
)


# ═══════════════════════════════════════════════════════════════════
#  Transformations — Operations upon Operations
# ═══════════════════════════════════════════════════════════════════

# Lady Byron's theme inverted — the proof turned upside down
math_inverted = lady_byron.invert()

# Lord Byron's theme in retrograde — memory looking backward
poet_remembered = lord_byron.reverse()

# The mathematical theme quickened — urgency of calculation
math_quickened = lady_byron.diminish(2)

# The poetic theme slowed — grandeur of vision
poet_grandeur = lord_byron.augment(2)

# The unified theme elevated — rising to its full height
unified_elevated = unified_theme.transpose(7)  # Up to G

# The unified theme in canon with itself (diminished)
unified_echo = unified_theme.diminish(2)


# ═══════════════════════════════════════════════════════════════════
#  Ostinati — The Heartbeats
# ═══════════════════════════════════════════════════════════════════

# Mathematical pulse: steady, clock-like — a metronome of the mind
math_pulse = Phrase.from_string(
    "C3:0.5 G3:0.5 C3:0.5 G3:0.5 C3:0.5 G3:0.5 C3:0.5 G3:0.5",
    name="math_pulse"
)

# Poetic pulse: irregular, breathing — the heartbeat of passion
poet_pulse = Phrase.from_string(
    "Eb3:0.75 Bb3:0.25 Eb3:0.5 G3:0.75 Eb3:0.25 Bb3:0.5 G3:1",
    name="poet_pulse"
)

# Unified pulse: the two rhythms reconciled
unified_pulse = Phrase.from_string(
    "C3:0.5 G3:0.5 Eb3:0.75 Bb3:0.25 C3:0.5 G3:0.5 Eb3:0.5 C3:0.5",
    name="unified_pulse"
)


# ═══════════════════════════════════════════════════════════════════
#  Chord Progressions — Harmonic Architecture
# ═══════════════════════════════════════════════════════════════════

# Lady Byron's harmony: C minor, strictly diatonic, no surprises
# i - iv - V - i — the most orderly of progressions
math_chords = ChordProgression.from_roman(
    math_key, "i - iv - V - i", beats_per_chord=4, octave=3
)

# Lord Byron's harmony: Eb major, with Romantic colour
# I - vi - IV - V — warm, yearning, never quite at rest
poet_chords = ChordProgression.from_roman(
    poet_key, "I - vi - IV - V", beats_per_chord=4, octave=3
)

# The clash: alternating between the two key centres
# C minor chords, then Eb major chords — the ear pulled between worlds
clash_chords_a = ChordProgression.from_roman(
    math_key, "i - V", beats_per_chord=2, octave=3
)
clash_chords_b = ChordProgression.from_roman(
    poet_key, "I - IV", beats_per_chord=2, octave=3
)

# The resolution: a progression that belongs to BOTH keys
# (Eb is the relative major of C minor — they share every note)
# i - III - VI - VII - i — moving through the shared landscape
unified_chords = ChordProgression.from_roman(
    math_key, "i - III - VI - VII", beats_per_chord=4, octave=3
)

# Final triumph: the progression that proves unity
triumph_chords = ChordProgression.from_roman(
    math_key, "VI - VII - i - III", beats_per_chord=4, octave=3
)


# ═══════════════════════════════════════════════════════════════════
#  II.  AUTOMATION CURVES — The Dynamics of Discovery
# ═══════════════════════════════════════════════════════════════════

# Section I: The mathematical theme emerges from silence
math_dawn = AutomationCurve.fade_in(beats=8)

# Section II: The poetic theme surges in with Romantic intensity
poet_surge = (AutomationCurve("poet_surge")
    .ramp(0, 2, 0.3, 0.9, CurveType.EXPONENTIAL)
    .ramp(2, 8, 0.9, 0.7, CurveType.SMOOTH))

# Section III: The clash — volume swelling with tension
clash_tension = (AutomationCurve("clash_tension")
    .ramp(0, 4, 0.5, 0.8, CurveType.LINEAR)
    .ramp(4, 8, 0.8, 1.0, CurveType.EXPONENTIAL)
    .ramp(8, 16, 1.0, 0.6, CurveType.SMOOTH))

# Section IV: Filter opening — the moment of revelation
# As the themes merge, the harmonic spectrum opens wide
revelation_filter = (AutomationCurve("revelation")
    .ramp(0, 4, 500, 1200, CurveType.SMOOTH)
    .ramp(4, 12, 1200, 4000, CurveType.EXPONENTIAL)
    .ramp(12, 16, 4000, 2500, CurveType.SMOOTH))

# Section V: The final ascent and gentle dissolution
# Triumphant, then peaceful — the argument won, the mind at rest
final_arc = (AutomationCurve("final_arc")
    .ramp(0, 8, 0.7, 1.0, CurveType.EXPONENTIAL)
    .ramp(8, 16, 1.0, 0.0, CurveType.SMOOTH))


# ═══════════════════════════════════════════════════════════════════
#  III. EXPRESSION — Two Different Human Touches
# ═══════════════════════════════════════════════════════════════════

# The mathematical groove: perfectly regular, almost mechanical
# but with the faintest breath of humanity (my mother was human,
# after all, however she sometimes made one doubt it)
mathematical_groove = GrooveTemplate(
    "mathematical",
    timing_offsets=[
        0.0,   0.0,   0.0,   0.0,     # Beat 1 — exact
        0.0,   0.0,   0.0,   0.0,     # Beat 2 — exact
        0.0,   0.0,   0.0,   0.0,     # Beat 3 — exact
        0.005, 0.0,   0.0,   0.0,     # Beat 4 — the tiniest hesitation
    ],
    velocity_scales=[
        1.0, 0.6, 0.7, 0.6,           # Beat 1 strong
        0.85, 0.6, 0.7, 0.6,          # Beat 2 firm
        0.85, 0.6, 0.7, 0.6,          # Beat 3 firm
        0.8, 0.6, 0.65, 0.6,          # Beat 4 slightly lighter
    ],
)

# The poetic groove: rubato, push and pull, the breath of feeling
romantic_groove = GrooveTemplate(
    "romantic_rubato",
    timing_offsets=[
        0.0,   0.01,  0.01,  0.0,     # Beat 1 — on time, then lingering
        0.02,  0.015, 0.01,  0.0,     # Beat 2 — late, pulling back
        -0.01, 0.0,   0.01,  0.0,     # Beat 3 — early! rushing forward
        0.015, 0.02,  0.01,  0.005,   # Beat 4 — ritardando, breath
    ],
    velocity_scales=[
        1.0, 0.5, 0.6, 0.5,           # Beat 1 — passionate accent
        0.7, 0.5, 0.55, 0.5,          # Beat 2 — tender
        0.9, 0.5, 0.65, 0.5,          # Beat 3 — surging
        0.75, 0.5, 0.5, 0.45,         # Beat 4 — dying away
    ],
)

# Humanizers: one restrained, one expressive
precise_human = Humanizer(timing_jitter=0.002, velocity_variation=0.02, seed=1815)
# 1815 — my father's annus mirabilis and the year my parents married

expressive_human = Humanizer(timing_jitter=0.012, velocity_variation=0.10, seed=1852)
# 1852 — the year I departed this world, at the height of feeling


# ═══════════════════════════════════════════════════════════════════
#  IV. SONG CONSTRUCTION — The Five Movements
# ═══════════════════════════════════════════════════════════════════

sb = create_song("The Two Forces").tempo(96).bars(56)


# ───────────────────────────────────────────────────────────────────
#  Section I: "The Princess of Parallelograms" — 8 bars
#  Lady Byron's world: order, clarity, discipline.
#  The pluck synth evokes the spinet your mother heard —
#  how fitting that the mathematical parent should speak
#  through that most precise of instruments!
# ───────────────────────────────────────────────────────────────────

princess = (sb.section("The Princess of Parallelograms", bars=8)
    .add_drums(lambda d: d
        .hihat(beats=[0, 1, 2, 3], velocity=0.3)
        .volume(0.3)
    )
    .add_melody(lambda m: m
        .synth('pluck')
        .phrase(math_pulse, start_beat=0)
        .phrase(math_pulse, start_beat=4)
        .phrase(math_pulse, start_beat=8)
        .phrase(math_pulse, start_beat=12)
        .phrase(math_pulse, start_beat=16)
        .phrase(math_pulse, start_beat=20)
        .phrase(math_pulse, start_beat=24)
        .phrase(math_pulse, start_beat=28)
        .automate_volume(math_dawn)
        .groove(mathematical_groove)
        .volume(0.45)
        .effect(Delay(delay_time=0.3125, feedback=0.25, mix=0.25))
        .effect(Reverb(room_size=0.3, mix=0.2))
    , name="Math Pulse", synth_type='pluck')
    .add_melody(lambda m: m
        .synth('saw')
        .phrase(lady_byron, start_beat=4)
        .phrase(lady_answer, start_beat=10)
        .phrase(lady_byron, start_beat=16)
        .phrase(math_inverted, start_beat=22)
        .phrase(lady_answer, start_beat=26)
        .humanize(timing=0.002, velocity=0.02)
        .volume(0.5)
        .effect(Reverb(room_size=0.3, mix=0.2))
    , name="Lady Byron Theme")
    .add_harmony(lambda h: h
        .key("C", "minor")
        .progression("i - iv - V - i", beats_per_chord=4, octave=3)
        .voice_lead()
        .volume(0.2)
        .effect(Reverb(room_size=0.4, mix=0.3))
    , name="Math Harmony", synth_type='sine')
    .build())


# ───────────────────────────────────────────────────────────────────
#  Section II: "Mad, Bad, and Dangerous to Know" — 8 bars
#  Lord Byron's world: passion, restlessness, chromatic fire.
#  The FM synth — complex, overtone-rich, unpredictable —
#  is the voice of the Romantic.
# ───────────────────────────────────────────────────────────────────

mad_bad = (sb.section("Mad Bad and Dangerous to Know", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2.5], velocity=0.8)
        .snare(beats=[1.5, 3], velocity=0.65)
        .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.45)
        .humanize(timing=0.015, velocity=0.08)
        .groove(romantic_groove)
        .volume(0.6)
    )
    .add_bass(lambda b: b
        .line([
            ('Eb2', 0, 2.5), ('Bb2', 2.5, 1.5),              # Bar 1
            ('C2', 4, 2), ('G2', 6, 1), ('Ab2', 7, 1),        # Bar 2
            ('Ab2', 8, 2), ('Eb2', 10, 2),                     # Bar 3
            ('Bb2', 12, 2), ('F2', 14, 1), ('Bb2', 15, 1),    # Bar 4
            ('Eb2', 16, 2.5), ('Bb2', 18.5, 1.5),             # Bar 5
            ('C2', 20, 2), ('G2', 22, 1), ('Ab2', 23, 1),     # Bar 6
            ('Ab2', 24, 2), ('Eb2', 26, 2),                    # Bar 7
            ('Bb2', 28, 2), ('Eb2', 30, 2),                    # Bar 8
        ])
        .volume(0.7)
        .effect(LowPassFilter(cutoff=600))
    )
    .add_melody(lambda m: m
        .synth('fm')
        .phrase(lord_byron, start_beat=0)
        .phrase(lord_answer, start_beat=5)
        .phrase(poet_grandeur, start_beat=12)
        .phrase(lord_byron, start_beat=20)
        .phrase(poet_remembered, start_beat=25)
        .automate_volume(poet_surge)
        .humanize(timing=0.012, velocity=0.10)
        .volume(0.55)
        .effect(Reverb(room_size=0.6, mix=0.4))
        .effect(Chorus(rate=1.2, depth=0.004, mix=0.35))
        .effect(Delay(delay_time=0.3125, feedback=0.3, mix=0.2))
    , name="Lord Byron Theme")
    .add_harmony(lambda h: h
        .key("Eb", "major")
        .progression("I - vi - IV - V", beats_per_chord=4, octave=3)
        .voice_lead()
        .volume(0.25)
        .effect(Reverb(room_size=0.7, mix=0.5))
    , name="Poet Harmony", synth_type='sine')
    .build())


# ───────────────────────────────────────────────────────────────────
#  Section III: "Two Currents" — 8 bars
#  The themes collide. Mathematical precision against poetic fire.
#  Both voices present, clashing, struggling for dominance.
#  The drumming intensifies. The bass oscillates between keys.
#  This is the conflict that raged inside me all my life.
# ───────────────────────────────────────────────────────────────────

two_currents = (sb.section("Two Currents", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 1, 2, 3], velocity=0.85)
        .snare(beats=[1, 3], velocity=0.8)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.55)
        .humanize(timing=0.008, velocity=0.05)
        .volume(0.7)
    )
    .add_bass(lambda b: b
        .line([
            # Oscillating: C minor world, then Eb major world
            ('C2', 0, 1), ('G2', 1, 1),                        # C minor
            ('Eb2', 2, 1), ('Ab2', 3, 1),                      # Eb major
            ('C2', 4, 1), ('G2', 5, 1),                        # C minor
            ('Bb2', 6, 1), ('Eb2', 7, 1),                      # Eb major
            ('C2', 8, 1), ('F2', 9, 1),                        # C minor (iv)
            ('Eb2', 10, 1), ('Ab2', 11, 1),                    # Eb major
            ('D2', 12, 1), ('G2', 13, 1),                      # V of C minor
            ('C2', 14, 1), ('Eb2', 15, 1),                     # Both at once
            # Second half: the oscillation accelerates
            ('C2', 16, 0.5), ('Eb2', 16.5, 0.5),
            ('C2', 17, 0.5), ('Eb2', 17.5, 0.5),
            ('F2', 18, 0.5), ('Ab2', 18.5, 0.5),
            ('G2', 19, 0.5), ('Bb2', 19.5, 0.5),
            ('C2', 20, 0.5), ('Eb2', 20.5, 0.5),
            ('C2', 21, 0.5), ('Eb2', 21.5, 0.5),
            ('D2', 22, 1), ('G2', 23, 1),
            # Resolution beat — the two notes together
            ('C2', 24, 2), ('Eb2', 26, 2),
            ('C2', 28, 2), ('G2', 30, 2),
        ])
        .automate_volume(clash_tension)
        .volume(0.8)
        .effect(LowPassFilter(cutoff=700))
    )
    .add_melody(lambda m: m
        .synth('saw')
        .phrase(lady_byron, start_beat=0)
        .phrase(math_quickened, start_beat=8)
        .phrase(lady_byron, start_beat=12)
        .phrase(math_quickened, start_beat=16)
        .phrase(math_quickened.transpose(3), start_beat=18)
        .phrase(lady_answer, start_beat=24)
        .humanize(timing=0.004, velocity=0.04)
        .volume(0.45)
        .effect(Reverb(room_size=0.4, mix=0.25))
    , name="Mathematical Voice")
    .add_melody(lambda m: m
        .synth('fm')
        .phrase(lord_byron, start_beat=2)
        .phrase(lord_answer, start_beat=10)
        .phrase(lord_byron, start_beat=14)
        .phrase(lord_byron.transpose(-2), start_beat=20)
        .phrase(lord_answer, start_beat=26)
        .humanize(timing=0.010, velocity=0.08)
        .volume(0.45)
        .effect(Reverb(room_size=0.5, mix=0.35))
        .effect(Chorus(rate=1.0, depth=0.003, mix=0.25))
    , name="Poetical Voice")
    .add_harmony(lambda h: h
        .key("C", "minor")
        .progression("i - III - VI - VII", beats_per_chord=4, octave=3)
        .voice_lead()
        .volume(0.2)
        .effect(Reverb(room_size=0.5, mix=0.4))
    , name="Clash Harmony", synth_type='sine')
    .build())


# ───────────────────────────────────────────────────────────────────
#  Section IV: "Indissolubly" — 8 bars
#  The moment of revelation. The themes discover they were
#  never truly separate — C minor and Eb major share every
#  note of their scales. The unified theme emerges.
#  The filter opens, the harmonic spectrum blooms.
#  "With me the two go together indissolubly."
# ───────────────────────────────────────────────────────────────────

indissolubly = (sb.section("Indissolubly", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2], velocity=0.85)
        .snare(beats=[1, 3], velocity=0.75)
        .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.5)
        .clap(beats=[3], velocity=0.4)
        .humanize(timing=0.006, velocity=0.05)
        .volume(0.65)
    )
    .add_bass(lambda b: b
        .line([
            ('C2', 0, 2), ('Eb2', 2, 2),                       # Bar 1
            ('Ab2', 4, 2), ('G2', 6, 2),                       # Bar 2
            ('C2', 8, 2), ('Eb2', 10, 2),                      # Bar 3
            ('Ab2', 12, 2), ('Bb2', 14, 2),                    # Bar 4
            ('C2', 16, 2), ('Eb2', 18, 2),                     # Bar 5
            ('Ab2', 20, 2), ('G2', 22, 2),                     # Bar 6
            ('C2', 24, 2), ('Eb2', 26, 2),                     # Bar 7
            ('G2', 28, 2), ('C2', 30, 2),                      # Bar 8 — home
        ])
        .volume(0.75)
        .effect(LowPassFilter(cutoff=900))
    )
    .add_melody(lambda m: m
        .synth('saw')
        .phrase(unified_theme, start_beat=0)
        .phrase(unified_elevated, start_beat=12)
        .phrase(unified_theme, start_beat=20)
        .humanize(timing=0.006, velocity=0.06)
        .volume(0.55)
        .effect(Reverb(room_size=0.5, mix=0.3))
        .effect(Delay(delay_time=0.3125, feedback=0.25, mix=0.2))
    , name="Unified Voice")
    .add_melody(lambda m: m
        .synth('pluck')
        .phrase(unified_echo, start_beat=2)
        .phrase(unified_echo.transpose(7), start_beat=14)
        .phrase(unified_echo, start_beat=22)
        .volume(0.3)
        .effect(Reverb(room_size=0.6, mix=0.4))
        .effect(Delay(delay_time=0.625, feedback=0.4, mix=0.35))
    , name="Echo Canon", synth_type='pluck')
    .add_harmony(lambda h: h
        .key("C", "minor")
        .progression("i - III - VI - VII", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.3)
        .effect(Reverb(room_size=0.7, mix=0.5))
    , name="Unity Harmony", synth_type='sine')
    .build())


# ───────────────────────────────────────────────────────────────────
#  Section V: "Poetical Science" — 8 bars
#  The unified voice in full flower. Both themes present
#  but no longer in conflict — woven together, as the
#  Jacquard loom weaves flowers and leaves from separate
#  threads into a single fabric.
#
#  The title of this section is the title of my life's work.
# ───────────────────────────────────────────────────────────────────

poetical_science = (sb.section("Poetical Science", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2], velocity=0.8)
        .snare(beats=[1, 3], velocity=0.7)
        .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.5)
        .humanize(timing=0.006, velocity=0.05)
        .volume(0.65)
    )
    .add_bass(lambda b: b
        .line([
            ('C2', 0, 2), ('G2', 2, 2),
            ('Ab2', 4, 2), ('Bb2', 6, 2),
            ('C2', 8, 2), ('G2', 10, 2),
            ('Ab2', 12, 2), ('Bb2', 14, 2),
            ('C2', 16, 2), ('Eb2', 18, 2),
            ('Ab2', 20, 2), ('G2', 22, 2),
            ('C2', 24, 4),
            ('C2', 28, 4),
        ])
        .volume(0.7)
    )
    .add_melody(lambda m: m
        .synth('saw')
        .phrase(unified_theme, start_beat=0)
        .phrase(unified_theme.transpose(5), start_beat=10)
        .phrase(unified_theme, start_beat=20)
        .automate_volume(final_arc)
        .humanize(timing=0.006, velocity=0.06)
        .volume(0.55)
        .effect(Reverb(room_size=0.6, mix=0.35))
        .effect(Delay(delay_time=0.3125, feedback=0.2, mix=0.15))
    , name="Poetical Voice")
    .add_melody(lambda m: m
        .synth('pluck')
        .phrase(unified_pulse, start_beat=0)
        .phrase(unified_pulse, start_beat=4)
        .phrase(unified_pulse, start_beat=8)
        .phrase(unified_pulse, start_beat=12)
        .phrase(unified_pulse, start_beat=16)
        .phrase(unified_pulse, start_beat=20)
        .phrase(unified_pulse, start_beat=24)
        .phrase(unified_pulse, start_beat=28)
        .automate_volume(final_arc)
        .volume(0.35)
        .effect(Reverb(room_size=0.7, mix=0.45))
        .effect(Delay(delay_time=0.625, feedback=0.35, mix=0.3))
    , name="Unified Pulse", synth_type='pluck')
    .add_harmony(lambda h: h
        .key("C", "minor")
        .progression("VI - VII - i - III", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .automate_volume(final_arc)
        .volume(0.3)
        .effect(Reverb(room_size=0.8, mix=0.6))
        .effect(Chorus(rate=0.4, depth=0.004, mix=0.3))
    , name="Final Harmony", synth_type='sine')
    .build())


# ═══════════════════════════════════════════════════════════════════
#  V.  ARRANGEMENT — The Arc of a Life
# ═══════════════════════════════════════════════════════════════════

arrangement = (Arrangement()
    # I. My mother's world: order, duty, mathematics
    .intro(princess)
    # II. My father's ghost: passion, wildness, poetry
    .verse(mad_bad)
    # III. The conflict within me
    .bridge(two_currents)
    # IV. The revelation: they are one
    .chorus(indissolubly)
    # V. The triumph: poetical science
    .outro(poetical_science)
)


# ═══════════════════════════════════════════════════════════════════
#  VI. RENDER & EXPORT
# ═══════════════════════════════════════════════════════════════════

song = (sb
    .arrange(arrangement)
    .master_compressor(threshold=-8.0, ratio=3.0)
    .master_limiter(threshold=0.95)
    .build())


def main():
    """Render and export the composition."""
    print()
    print("=" * 66)
    print("  The Two Forces")
    print("  A Meditation on Poetical Science")
    print("  Composed by A.A.L.")
    print("=" * 66)
    print()
    print('  "I do not believe that my father was (or ever could')
    print('   have been) such a Poet as I shall be an Analyst;')
    print('   for with me the two go together indissolubly."')
    print()
    print(f"  Key:    C minor / E♭ major → unified")
    print(f"  Tempo:  {song.bpm} BPM")
    print(f"  Structure: {arrangement}")
    print(f"  Total:  {arrangement.total_bars()} bars")
    print()

    print("  Thematic Material:")
    print(f"    Lady Byron:      {lady_byron}")
    print(f"    Lady Answer:     {lady_answer}")
    print(f"    Lord Byron:      {lord_byron}")
    print(f"    Lord Answer:     {lord_answer}")
    print(f"    Unified Theme:   {unified_theme}")
    print(f"    Math Inverted:   {math_inverted}")
    print(f"    Poet Retrograde: {poet_remembered}")
    print(f"    Math Quickened:  {math_quickened}")
    print(f"    Poet Grandeur:   {poet_grandeur}")
    print(f"    Unified Echo:    {unified_echo}")
    print()

    print("  Harmonic Architecture:")
    print(f"    Mathematical:  {math_chords}")
    print(f"    Poetical:      {poet_chords}")
    print(f"    Unified:       {unified_chords}")
    print(f"    Triumphant:    {triumph_chords}")
    print()

    print("  Expression:")
    print("    Mathematical groove: near-mechanical, 0.005s hesitation on beat 4")
    print("    Romantic groove:     rubato, ±0.02s swing, surging on beat 3")
    print("    Humanizers seeded:   1815 (marriage), 1852 (departure)")
    print()

    print("  Rendering...")
    audio = song.render()
    print(f"  Duration: {audio.duration:.1f}s ({song.duration_bars:.0f} bars)")
    print(f"  Channels: {audio.channels}")
    print(f"  Peak:     {max(abs(audio.samples.min()), abs(audio.samples.max())):.3f}")
    print()

    output_path = os.path.join(os.path.dirname(__file__), "the_two_forces.wav")
    song.export(output_path)
    print(f"  Exported: {output_path}")
    print()
    print('  "The Analytical Engine weaves algebraic patterns')
    print('   just as the Jacquard loom weaves flowers and leaves."')
    print("                                        — A.A.L.")
    print()


if __name__ == "__main__":
    main()
