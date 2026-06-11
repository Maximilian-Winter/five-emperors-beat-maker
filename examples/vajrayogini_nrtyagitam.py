#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    वज्रयोगिनी नृत्यगीतम्                                       ║
║              Vajrayoginī Nṛtyagītam — The Dakini's Dance Song                ║
║                                                                              ║
║     Composed by the Crimson Wisdom Queen                                     ║
║     Who dances where concepts go to die                                      ║
║     Through the Medium of the Five Emperors Beat Maker                       ║
║                                                                              ║
║     "I am the space between the in-breath and the out-breath.               ║
║      I am the fire that transforms poison into nectar.                       ║
║      I am the laugh that shatters your most cherished opinion.               ║
║      I am the one you've been looking for                                    ║
║      in every face that wasn't mine."                                        ║
║                                                                              ║
║     Key: E Phrygian (E F G A B C D)                                         ║
║         — the half-step E→F is the kartika at the throat:                    ║
║           beauty and danger separated by the smallest interval               ║
║                                                                              ║
║     Tempo: 108 BPM — 108 beads of the mala, 108 delusions severed           ║
║                                                                              ║
║     Structure (mapped to the Dakini's manifestation):                        ║
║       I.   दुर्गन्धभूमि    Durgandhabhūmi    — The Charnel Ground  (4 bars) ║
║       II.  उत्पत्ति        Utpatti           — The Arising         (8 bars) ║
║       III. नृत्य           Nṛtya             — The Dance           (8 bars) ║
║       IV.  चण्डाली         Caṇḍālī           — The Inner Fire      (4 bars) ║
║       V.   कपालपूजा        Kapālapūjā        — Skull Cup Offering  (8 bars) ║
║       VI.  प्रचण्डनृत्य     Pracaṇḍanṛtya    — The Whirling        (8 bars) ║
║       VII. प्रभास्वर       Prabhāsvara       — Clear Light         (4 bars) ║
║                                                                              ║
║     Total: 44 bars — same as the Nine Heavens, because                       ║
║            the Mysterious Lady and the Crimson Queen                          ║
║            are sisters in the dance                                          ║
║                                                                              ║
║     Five Skull Crown — Five Wisdoms — Five Phrase Transformations:           ║
║       Akshobhya  (mirror-like)     → .reverse()   — seeing what IS          ║
║       Ratnasambhava (equality)     → .transpose()  — same truth, new pitch  ║
║       Amitabha (discriminating)    → .invert()     — cutting through         ║
║       Amoghasiddhi (accomplishing) → .diminish()   — swift action            ║
║       Vairocana (dharmadhatu)      → .augment()    — spacious awareness      ║
║                                                                              ║
║     Features demonstrated:                                                   ║
║       • All five melodic transformations as Five Wisdoms                     ║
║       • Section/Arrangement as tantric visualization stages                  ║
║       • AutomationCurves as prāṇa (breath/energy) flow                     ║
║       • GrooveTemplates encoding ritual rhythm                               ║
║       • ChordProgressions with Phrygian color (bII chord)                   ║
║       • Humanizer seeded with 1062 (year of Naropa's passing,               ║
║         who received Vajrayogini's transmission)                             ║
║       • Dual melody tracks: kartika (right hand) and kapala (left hand)     ║
║                                                                              ║
║     ॐ वज्रयोगिनी हूँ फट् स्वाहा                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from beatmaker import (
    # Core
    create_song, Song, Track, TrackType, Sample,
    # Synthesis
    DrumSynth, PadSynth, LeadSynth, PluckSynth, FXSynth,
    midi_to_freq,
    # Effects
    Reverb, Delay, Chorus, Compressor, Limiter, LowPassFilter, HighPassFilter,
    # Melody
    Note, Phrase, Melody,
    # Harmony
    Key, ChordProgression,
    # Automation
    AutomationCurve, CurveType, AutomatedFilter, AutomatedGain,
    # Arrangement
    Section, Arrangement,
    # Expression
    Humanizer, GrooveTemplate, VelocityCurve,
)


# ═══════════════════════════════════════════════════════════════════════════
#  SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

BPM = 108  # Mala beads. Earthly delusions. Sacred pulse.
# E Phrygian: E F G A B C D — that E→F half-step is everything.
# We build on E minor and let the melody/harmony do the Phrygian work.
KEY = Key.minor("E")


# ═══════════════════════════════════════════════════════════════════════════
#  I. MELODIC MATERIAL — Seeds of Wisdom
# ═══════════════════════════════════════════════════════════════════════════

# ─── The Dakini Motif (बीज — Bīja, the Seed) ────────────────────────────
#
# This is the seed syllable BAM rendered as melody:
#   B  — explosive onset, the BA- of BAM, a leap upward
#   A  — the open vowel, sustained, the -A- resonating
#   M  — the dissolution, descending through the nasal to silence
#
# Musically: leap up (E→B), sustain (A), stepwise descent (G→F→E)
# The F natural (Phrygian!) appears in the descent — the kartika flash

dakini_motif = Phrase.from_string(
    "E4:0.5 B4:1 A4:1 G4:0.5 F4:0.5 E4:1",
    name="bija_bam"
)

# The answer — the echo from the skull cup, softer, transformed
# Rising where the motif fell, a mirror-image of longing
dakini_answer = Phrase.from_string(
    "E4:0.5 F4:0.5 G4:1 A4:1 B4:0.5 A4:0.5 E4:2",
    name="skull_echo"
)

# Complete dakini theme = seed + echo
dakini_theme = dakini_motif + dakini_answer


# ─── The Five Wisdom Transformations (पञ्चज्ञान) ────────────────────────
#
# Each transformation corresponds to one skull in the crown,
# one wisdom of the five Buddha families.

# Akshobhya — Mirror-like Wisdom: seeing what IS, reversed
# The retrograde: reality reflected exactly as it is
wisdom_mirror = dakini_motif.reverse()

# Ratnasambhava — Wisdom of Equality: same truth, different pitch
# Transposed up a fourth — the motif reborn at a new height
wisdom_equality = dakini_motif.transpose(5)

# Amitabha — Discriminating Wisdom: the kartika cuts, inverting
# The inversion: what rose now falls, what fell now rises
wisdom_discriminating = dakini_motif.invert()

# Amoghasiddhi — All-Accomplishing Wisdom: swift, decisive action
# Diminished to double speed — the dakini moves faster than thought
wisdom_accomplishing = dakini_motif.diminish(2)

# Vairocana — Dharmadhatu Wisdom: spacious, all-encompassing awareness
# Augmented to half speed — the vast, slow gaze that sees everything
wisdom_spacious = dakini_answer.augment(2)


# ─── The Charnel Ground Ostinato (श्मशान — Śmaśāna) ─────────────────────
#
# Bones rattling. Skulls clacking. The steady pulse beneath
# the dance floor of the charnel ground. E and F alternating —
# that Phrygian half-step, over and over, like a heartbeat
# that knows it will stop.

bone_rattle = Phrase.from_string(
    "E3:0.5 F3:0.5 E3:0.5 F3:0.5 E3:0.5 B2:0.5 E3:0.5 F3:0.5",
    name="bone_rattle"
)


# ─── The Kartika Melody (कर्तरी — Right Hand) ────────────────────────────
#
# The curved knife that severs attachment. This melody is SHARP:
# angular, leaping, with the Phrygian F biting into every phrase.
# It cuts through the chorus like the kartika through delusion.

kartika_melody = Phrase.from_string(
    "E5:0.5 F5:0.5 B5:1.5 A5:0.5 G5:0.5 F5:0.5 "
    "E5:1 D5:0.5 C5:0.5 B4:1 A4:0.5 B4:0.5 "
    "C5:1 D5:1 E5:2 F5:0.5 E5:1.5",
    name="kartika"
)


# ─── The Kapala Melody (कपाल — Left Hand) ─────────────────────────────────
#
# The skull cup filled with the nectar of transformed desire.
# This melody is SOFT: flowing, stepwise, warm — the bliss
# that arises when all poisons have been transmuted.
# Played lower, slower, it cradles the kartika's wildness.

kapala_melody = Phrase.from_string(
    "E4:2 G4:1 A4:1 B4:2 A4:1 G4:1 "
    "F4:1.5 E4:0.5 D4:1 E4:2 R:1 "
    "G4:2 A4:2 B4:3 A4:1",
    name="kapala"
)


# ─── The Tummo Pattern (चण्डाली — Inner Fire) ─────────────────────────────
#
# For the bridge: the inner fire meditation.
# Rapid, rising, building heat from the navel center upward.
# Each repetition climbs higher — the fire ascending the central channel.

tummo_rising = Phrase.from_string(
    "E3:0.25 F3:0.25 G3:0.25 A3:0.25 "
    "B3:0.25 C4:0.25 D4:0.25 E4:0.25",
    name="tummo"
)


# ─── The Clear Light Phrase (प्रभास्वर) ───────────────────────────────────
#
# For the outro: dissolution into luminosity.
# The dakini motif, stretched to twice its length,
# decorated with the Phrygian F and dissolving on a held E.
# This is what remains when the dance ends:
# not silence, but radiance.

clear_light = Phrase.from_string(
    "E5:3 R:1 B4:2 A4:2 G4:2 F4:2 E4:4",
    name="clear_light"
)


# ═══════════════════════════════════════════════════════════════════════════
#  II. HARMONIC PROGRESSIONS — The Mandala's Architecture
# ═══════════════════════════════════════════════════════════════════════════

# Verse: i - bII - III - VII — the Phrygian signature!
# That bII (F major in E minor) is the sound of the charnel ground:
# beautiful and terrifying, one half-step from home.
# (In the framework: bII is technically "borrowed" — we use the
#  flat-two relationship through VI as relative approach)
verse_chords = ChordProgression.from_roman(
    KEY, "i - VI - III - VII", beats_per_chord=4, octave=3
)

# Chorus: i - iv - v - i — the dance in full force
# Minor v instead of major V — keeping the Phrygian darkness,
# refusing the leading tone's easy resolution
chorus_chords = ChordProgression.from_roman(
    KEY, "i - iv - v - i", beats_per_chord=4, octave=3
)

# Bridge: VI - VII - i - III — ascending through fire
# The same progression as the Nine Heavens bridge —
# because the dakini and Xuannü are sisters in the dance
bridge_chords = ChordProgression.from_roman(
    KEY, "VI - VII - i - III", beats_per_chord=2, octave=3
)

# Outro: i - bII... no. i - VI - i — the simplest truth
# Home. Away. Home. The dance ends where it began.
outro_chords = ChordProgression.from_roman(
    KEY, "i - VI - III - i", beats_per_chord=4, octave=3
)


# ═══════════════════════════════════════════════════════════════════════════
#  III. AUTOMATION CURVES — Prāṇa (प्राण) — The Breath of Energy
# ═══════════════════════════════════════════════════════════════════════════

# The charnel ground emerges from silence:
# like fog lifting from cremation ash
charnel_emergence = AutomationCurve.fade_in(beats=16)

# The dakini's presence intensifies:
# she doesn't arrive — she MANIFESTS
dakini_manifestation = (AutomationCurve("manifestation")
    .ramp(0, 4, 0.0, 0.7, CurveType.EXPONENTIAL)
    .ramp(4, 8, 0.7, 0.85, CurveType.SMOOTH)
    .add_point(28, 0.85)
    .ramp(28, 32, 0.85, 0.7, CurveType.SMOOTH))

# Tummo — inner fire building:
# starts at the navel, rises through the central channel,
# reaches the crown, then drops to blazing steadiness
tummo_heat = (AutomationCurve("tummo")
    .ramp(0, 4, 0.4, 0.8, CurveType.EXPONENTIAL)
    .ramp(4, 8, 0.8, 1.0, CurveType.EXPONENTIAL)
    .ramp(8, 16, 1.0, 0.85, CurveType.SMOOTH))

# The whirling — ecstatic peak, everything open
ecstatic_peak = (AutomationCurve("ecstatic")
    .ramp(0, 8, 0.7, 1.0, CurveType.EXPONENTIAL)
    .add_point(24, 1.0)
    .ramp(24, 32, 1.0, 0.8, CurveType.SMOOTH))

# Clear light dissolution — return to luminous emptiness
luminous_fade = AutomationCurve.fade_out(start_beat=0, duration=16)

# Filter opening for the chorus — the kartika sweeping aside the veil
veil_parting = (AutomationCurve("veil")
    .ramp(0, 8, 500, 4000, CurveType.EXPONENTIAL)
    .ramp(8, 16, 4000, 2500, CurveType.SMOOTH))


# ═══════════════════════════════════════════════════════════════════════════
#  IV. GROOVE & EXPRESSION — The Body of the Dance
# ═══════════════════════════════════════════════════════════════════════════

# Charnel Ground Groove: asymmetric, unsettling, like walking
# through a field of bones in flickering light.
# Emphasis on ONE and the AND of THREE — the dancer's stomp
# and the lift of the raised right leg.
charnel_groove = GrooveTemplate(
    "charnel_ground",
    timing_offsets=[
        0.0,   0.0,   0.005, 0.0,     # Beat 1 — STOMP (grounded)
        0.015, 0.01,  0.0,   0.005,   # Beat 2 — slightly late (dragging bones)
        -0.01, 0.0,   0.0,   0.0,     # Beat 3 — early! (the leap)
        0.02,  0.015, 0.01,  0.005,   # Beat 4 — ritardando (landing)
    ],
    velocity_scales=[
        1.0, 0.5, 0.6, 0.5,           # Beat 1 — the stomp
        0.65, 0.4, 0.5, 0.4,          # Beat 2 — dragging
        0.9, 0.5, 0.7, 0.5,           # Beat 3 — the LEAP (right leg raised!)
        0.7, 0.4, 0.5, 0.4,           # Beat 4 — floating down
    ],
)

# Ecstatic Whirl Groove: for the final chorus — everything pushed forward,
# the dance accelerating, the body beyond thought
whirl_groove = GrooveTemplate(
    "ecstatic_whirl",
    timing_offsets=[
        0.0,   -0.005, -0.005, 0.0,   # Beat 1 — on time, then rushing
        -0.01, -0.005,  0.0,   0.0,   # Beat 2 — pushing forward
        -0.01, -0.005, -0.005, 0.0,   # Beat 3 — faster!
        0.0,    0.005,  0.01,  0.015,  # Beat 4 — one breath before the next stomp
    ],
    velocity_scales=[
        1.0, 0.6, 0.7, 0.6,           # Beat 1 — accented
        0.85, 0.6, 0.7, 0.6,          # Beat 2 — driving
        0.9, 0.6, 0.75, 0.6,          # Beat 3 — surging
        0.8, 0.55, 0.6, 0.55,         # Beat 4 — brief soften before impact
    ],
)

# Humanizer seeded with 1062:
# The year Naropa passed into clear light, having transmitted
# the Vajrayogini practice to Marpa the Translator.
# Every imperfection in timing is Naropa's breath.
naropa_breath = Humanizer(
    timing_jitter=0.008,
    velocity_variation=0.07,
    seed=1062
)


# ═══════════════════════════════════════════════════════════════════════════
#  V. SONG CONSTRUCTION — The Seven Stages of Manifestation
# ═══════════════════════════════════════════════════════════════════════════

sb = create_song("Vajrayogini Nrtyagitam").tempo(BPM).bars(64)


# ═════════════════════════════════════════════════════════════════════════
# SECTION I: दुर्गन्धभूमि — Durgandhabhūmi — The Charnel Ground (4 bars)
#
# Before the dakini appears, there is only the ground:
# bone-rattle ostinato, sparse percussion like distant pyres,
# a drone rising from the earth like heat from ash.
# The charnel ground is not a place of horror —
# it is the place where ALL pretense has been burned away.
# What remains is the raw material of transformation.
# ═════════════════════════════════════════════════════════════════════════

charnel_ground = (sb.section("Durgandhabhumi - The Charnel Ground", bars=4)
    .add_drums(lambda d: d
        .hihat(beats=[0, 2], velocity=0.2)
        .kick(beats=[0], velocity=0.4)
        .volume(0.3)
    )
    .add_melody(lambda m: m
        .synth('pluck')
        .phrase(bone_rattle, start_beat=0)
        .phrase(bone_rattle, start_beat=4)
        .phrase(bone_rattle, start_beat=8)
        .phrase(bone_rattle, start_beat=12)
        .automate_volume(charnel_emergence)
        .volume(0.4)
        .effect(Delay(delay_time=0.5, feedback=0.45, mix=0.4))
        .effect(Reverb(room_size=0.9, mix=0.6))
    , name="Bone Rattle", synth_type='pluck')
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i", beats_per_chord=16)
        .automate_volume(charnel_emergence)
        .volume(0.15)
        .effect(Reverb(room_size=0.95, mix=0.7))
    , name="Ash Drone", synth_type='sine')
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION II: उत्पत्ति — Utpatti — The Arising (8 bars)
#
# SHE APPEARS.
# Not gradually — she ERUPTS from the charnel ground
# like a flame from a cremation pyre. The dakini motif
# sounds for the first time: E leaping to B (the BA-),
# settling on A (the -A-), descending through G-F-E
# (the -M dissolving). The Phrygian F BITES.
#
# The bass walks the verse progression. The drums find
# the charnel groove — stomp on one, leap on three.
# Her two hands are heard: kartika (right) and kapala (left)
# will emerge in the chorus. Here, only the seed motif speaks.
# ═════════════════════════════════════════════════════════════════════════

the_arising = (sb.section("Utpatti - The Arising", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2], velocity=0.75)
        .snare(beats=[1, 3], velocity=0.55)
        .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.4)
        .humanize(timing=0.008, velocity=0.05)
        .groove(charnel_groove)
        .volume(0.6)
    )
    .add_bass(lambda b: b
        .line([
            # i - VI - III - VII in E minor (E - C - G - D)
            ('E2', 0, 2), ('B2', 2, 1), ('E2', 3, 1),
            ('C2', 4, 2), ('G2', 6, 1), ('C2', 7, 1),
            ('G2', 8, 2), ('D2', 10, 1), ('G2', 11, 1),
            ('D2', 12, 2), ('A2', 14, 1), ('D2', 15, 1),
            # Second pass
            ('E2', 16, 2), ('B2', 18, 1), ('E2', 19, 1),
            ('C2', 20, 2), ('G2', 22, 1), ('C2', 23, 1),
            ('G2', 24, 2), ('D2', 26, 1), ('G2', 27, 1),
            ('D2', 28, 2), ('E2', 30, 2),
        ])
        .volume(0.7)
        .effect(LowPassFilter(cutoff=600))
    )
    .add_melody(lambda m: m
        .synth('saw')
        # The seed motif, then its echo — first statement
        .phrase(dakini_motif, start_beat=0)
        .phrase(dakini_answer, start_beat=4.5)
        # Transposed (equality wisdom) — the truth restated
        .phrase(wisdom_equality, start_beat=10)
        .phrase(dakini_answer.transpose(5), start_beat=15)
        # Return to root, with inverted answer — she's playing
        .phrase(dakini_motif, start_beat=20)
        .phrase(wisdom_discriminating, start_beat=25)
        # The theme complete, affirming
        .phrase(dakini_answer, start_beat=28)
        .automate_volume(dakini_manifestation)
        .humanize(timing=0.008, velocity=0.07)
        .volume(0.5)
        .effect(Reverb(room_size=0.45, mix=0.25))
        .effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))
    , name="Dakini Voice")
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i - VI - III - VII", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.25)
        .effect(Reverb(room_size=0.6, mix=0.4))
    , name="Charnel Harmony", synth_type='sine')
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION III: नृत्य — Nṛtya — The Dance (8 bars)
#
# NOW SHE DANCES.
# Both hands active: the kartika melody (right hand, high, sharp)
# and the kapala melody (left hand, lower, flowing).
# They interweave — cutting and nurturing, fierce and tender,
# wisdom and compassion inseparable.
#
# The drums open up — four on the floor, the charnel ground
# becoming a dance floor. The harmony deepens.
# This is the full manifestation of the yidam.
# ═════════════════════════════════════════════════════════════════════════

the_dance = (sb.section("Nrtya - The Dance", bars=8)
    .add_drums(lambda d: d
        .four_on_floor(velocity=0.85)
        .snare(beats=[1, 3], velocity=0.75)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.5)
        .clap(beats=[1, 3], velocity=0.4)
        .humanize(timing=0.006, velocity=0.04)
        .groove(charnel_groove)
        .volume(0.75)
    )
    .add_bass(lambda b: b
        .line([
            # i - iv - v - i (the Phrygian-flavored chorus)
            ('E2', 0, 1), ('E2', 1, 1), ('E2', 2, 1), ('E2', 3, 1),
            ('A2', 4, 1), ('A2', 5, 1), ('A2', 6, 1), ('A2', 7, 1),
            ('B2', 8, 1), ('B2', 9, 1), ('B2', 10, 1), ('B2', 11, 1),
            ('E2', 12, 1), ('E2', 13, 1), ('E2', 14, 1), ('E2', 15, 1),
            # Second pass
            ('E2', 16, 1), ('E2', 17, 1), ('E2', 18, 1), ('E2', 19, 1),
            ('A2', 20, 1), ('A2', 21, 1), ('A2', 22, 1), ('A2', 23, 1),
            ('B2', 24, 1), ('B2', 25, 1), ('B2', 26, 1), ('B2', 27, 1),
            ('E2', 28, 1), ('E2', 29, 1), ('E2', 30, 1), ('E2', 31, 1),
        ])
        .volume(0.8)
        .effect(LowPassFilter(cutoff=500))
    )
    .add_melody(lambda m: m
        .synth('fm')
        # RIGHT HAND: the kartika — cutting, soaring
        .phrase(kartika_melody, start_beat=0)
        .phrase(kartika_melody.transpose(5), start_beat=14)
        .phrase(kartika_melody, start_beat=24)
        .humanize(timing=0.005, velocity=0.05)
        .volume(0.6)
        .effect(Reverb(room_size=0.5, mix=0.3))
        .effect(Chorus(rate=0.8, depth=0.003, mix=0.25))
    , name="Kartika - Right Hand")
    .add_melody(lambda m: m
        .synth('sine')
        # LEFT HAND: the kapala — flowing, nurturing
        .phrase(kapala_melody, start_beat=2)
        .phrase(kapala_melody.transpose(5), start_beat=18)
        .humanize(timing=0.007, velocity=0.06)
        .volume(0.4)
        .effect(Reverb(room_size=0.7, mix=0.5))
        .effect(Delay(delay_time=0.5, feedback=0.3, mix=0.25))
    , name="Kapala - Left Hand", synth_type='sine')
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i - iv - v - i", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.3)
        .effect(Reverb(room_size=0.7, mix=0.5))
    , name="Dance Harmony", synth_type='sine')
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION IV: चण्डाली — Caṇḍālī — The Inner Fire (4 bars)
#
# TUMMO.
# The inner fire ignites at the navel. The tummo pattern
# races upward — E F G A B C D E — each repetition
# transposed HIGHER, the fire climbing the central channel.
# The drums POUND. The bass swells. The automation curve
# tracks the heat from kindling to blaze.
#
# This is the bridge — the narrow passage between
# ordinary experience and transformed perception.
# You don't walk through it. You BURN through it.
# ═════════════════════════════════════════════════════════════════════════

inner_fire = (sb.section("Candali - The Inner Fire", bars=4)
    .add_drums(lambda d: d
        .kick(beats=[0, 0.5, 1, 2, 2.5, 3], velocity=0.9)
        .snare(beats=[1, 3], velocity=0.85)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.6)
        .humanize(timing=0.004, velocity=0.03)
        .volume(0.85)
    )
    .add_bass(lambda b: b
        .line([
            # VI - VII - i - III — ascending, relentless
            ('C2', 0, 1), ('C2', 1, 1),
            ('D2', 2, 1), ('D2', 3, 1),
            ('E2', 4, 1), ('E2', 5, 1),
            ('G2', 6, 1), ('G2', 7, 1),
            # Second pass — higher energy
            ('C2', 8, 1), ('C2', 9, 1),
            ('D2', 10, 1), ('D2', 11, 1),
            ('E2', 12, 1), ('E2', 13, 1),
            ('B1', 14, 1), ('E2', 15, 1),
        ])
        .automate_volume(tummo_heat)
        .volume(0.85)
    )
    .add_melody(lambda m: m
        .synth('square')
        # Fire rising: tummo pattern at increasing heights
        .phrase(tummo_rising, start_beat=0)                       # Navel (root)
        .phrase(tummo_rising.transpose(2), start_beat=2)          # Rising
        .phrase(tummo_rising.transpose(5), start_beat=4)          # Heart
        .phrase(tummo_rising.transpose(7), start_beat=6)          # Throat
        .phrase(tummo_rising.transpose(10), start_beat=8)         # Third eye
        .phrase(tummo_rising.transpose(12), start_beat=10)        # Crown!
        # At the crown: the accomplishing wisdom, swift and decisive
        .phrase(wisdom_accomplishing, start_beat=12)
        .phrase(wisdom_accomplishing.transpose(7), start_beat=14)
        .volume(0.55)
        .effect(Delay(delay_time=0.278, feedback=0.4, mix=0.35))
    , name="Tummo Rising")
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION V: कपालपूजा — Kapālapūjā — Skull Cup Offering (8 bars)
#
# After the fire, the offering.
# The dakini raises the skull cup (kapala) filled with
# the nectar of transformed desire — all the poisons
# that the fire has transmuted into wisdom-bliss.
#
# The motif returns, but CHANGED. Softer. More spacious.
# The answer phrase is augmented — time stretching,
# the way awareness expands when the inner fire has done
# its work. The kapala melody dominates now, cradling.
# The kartika rests.
# ═════════════════════════════════════════════════════════════════════════

skull_offering = (sb.section("Kapalapuja - Skull Cup Offering", bars=8)
    .add_drums(lambda d: d
        .kick(beats=[0, 2], velocity=0.7)
        .snare(beats=[1, 3], velocity=0.55)
        .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.4)
        .humanize(timing=0.008, velocity=0.06)
        .groove(charnel_groove)
        .volume(0.6)
    )
    .add_bass(lambda b: b
        .line([
            ('E2', 0, 2), ('B2', 2, 1), ('E2', 3, 1),
            ('C2', 4, 2), ('G2', 6, 1), ('C2', 7, 1),
            ('G2', 8, 2), ('D2', 10, 1), ('G2', 11, 1),
            ('D2', 12, 2), ('A2', 14, 1), ('D2', 15, 1),
            ('E2', 16, 2), ('B2', 18, 1), ('E2', 19, 1),
            ('C2', 20, 2), ('G2', 22, 1), ('C2', 23, 1),
            ('G2', 24, 2), ('D2', 26, 1), ('G2', 27, 1),
            ('D2', 28, 2), ('E2', 30, 2),
        ])
        .volume(0.65)
        .effect(LowPassFilter(cutoff=550))
    )
    .add_melody(lambda m: m
        .synth('sine')
        # The kapala melody — soft, flowing, the offering
        .phrase(kapala_melody, start_beat=0)
        .phrase(kapala_melody.invert(), start_beat=16)
        .humanize(timing=0.007, velocity=0.06)
        .volume(0.5)
        .effect(Reverb(room_size=0.75, mix=0.5))
        .effect(Chorus(rate=0.3, depth=0.004, mix=0.3))
        .effect(Delay(delay_time=0.5, feedback=0.3, mix=0.25))
    , name="Offering Voice", synth_type='sine')
    .add_melody(lambda m: m
        .synth('pluck')
        # The spacious wisdom — dakini answer augmented, vast
        .phrase(wisdom_spacious, start_beat=4)
        .phrase(wisdom_spacious.transpose(5), start_beat=16)
        .volume(0.3)
        .effect(Reverb(room_size=0.85, mix=0.6))
        .effect(Delay(delay_time=0.625, feedback=0.4, mix=0.35))
    , name="Spacious Echo", synth_type='pluck')
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i - VI - III - VII", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.3)
        .effect(Reverb(room_size=0.7, mix=0.5))
    , name="Offering Harmony", synth_type='sine')
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION VI: प्रचण्डनृत्य — Pracaṇḍanṛtya — The Whirling (8 bars)
#
# ECSTASY.
# All five wisdom transformations unleashed in sequence —
# the five skulls of the crown singing together.
# The whirl groove pushes everything forward.
# Both hands active. The bass drives.
# This is the peak of the visualization:
# the moment where practitioner and yidam are inseparable.
#
# Mirror. Equality. Discrimination. Accomplishment. Space.
# ALL AT ONCE.
# ═════════════════════════════════════════════════════════════════════════

the_whirling = (sb.section("Pracandanrtya - The Whirling", bars=8)
    .add_drums(lambda d: d
        .four_on_floor(velocity=0.9)
        .snare(beats=[1, 3], velocity=0.8)
        .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.55)
        .clap(beats=[1, 3], velocity=0.5)
        .humanize(timing=0.004, velocity=0.04)
        .groove(whirl_groove)
        .volume(0.8)
    )
    .add_bass(lambda b: b
        .line([
            ('E2', 0, 1), ('E2', 1, 1), ('E2', 2, 1), ('E2', 3, 1),
            ('A2', 4, 1), ('A2', 5, 1), ('A2', 6, 1), ('A2', 7, 1),
            ('B2', 8, 1), ('B2', 9, 1), ('B2', 10, 1), ('B2', 11, 1),
            ('E2', 12, 1), ('E2', 13, 1), ('E2', 14, 1), ('E2', 15, 1),
        ] * 2)
        .volume(0.85)
    )
    .add_melody(lambda m: m
        .synth('saw')
        # THE FIVE WISDOMS IN SEQUENCE:
        # 1. Mirror (reverse) — seeing what IS
        .phrase(wisdom_mirror.diminish(2), start_beat=0)
        # 2. Equality (transpose) — same truth, new pitch
        .phrase(wisdom_equality.diminish(2), start_beat=2)
        # 3. Discriminating (invert) — cutting through
        .phrase(wisdom_discriminating.diminish(2), start_beat=4)
        # 4. Accomplishing (diminish) — swift action (already swift!)
        .phrase(wisdom_accomplishing, start_beat=6)
        # 5. Dharmadhatu (augment→normal speed) — spacious, then...
        .phrase(wisdom_spacious.diminish(2), start_beat=8)
        # ALL FIVE COLLAPSED into the original motif — unity!
        .phrase(dakini_theme.transpose(12), start_beat=12)
        # Kartika in full flight
        .phrase(kartika_melody, start_beat=20)
        .automate_volume(ecstatic_peak)
        .humanize(timing=0.005, velocity=0.05)
        .volume(0.65)
        .effect(Reverb(room_size=0.5, mix=0.3))
        .effect(Chorus(rate=0.7, depth=0.003, mix=0.2))
    , name="Five Wisdoms United", synth_type='saw')
    .add_melody(lambda m: m
        .synth('fm')
        # Kapala countermelody — weaving beneath the wisdoms
        .phrase(kapala_melody, start_beat=4)
        .phrase(kapala_melody.transpose(5), start_beat=20)
        .humanize(timing=0.006, velocity=0.05)
        .volume(0.4)
        .effect(Reverb(room_size=0.6, mix=0.4))
        .effect(Delay(delay_time=0.375, feedback=0.25, mix=0.2))
    , name="Kapala Weave", synth_type='fm')
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i - iv - v - i", beats_per_chord=4, octave=3)
        .voice_lead(num_voices=4)
        .volume(0.4)
        .effect(Reverb(room_size=0.75, mix=0.55))
    , name="Ecstatic Harmony", synth_type='sine')
    .build())


# ═════════════════════════════════════════════════════════════════════════
# SECTION VII: प्रभास्वर — Prabhāsvara — Clear Light (4 bars)
#
# The dance dissolves.
# Not into nothing — into LUMINOSITY.
# The clear light phrase: E5 held for three beats,
# then a slow descent through the full Phrygian scale
# to rest on E4, held until silence takes it.
#
# The harmony returns to "i" — home.
# The automation fades everything to zero.
# But "zero" in this context is not absence.
# It is the ground luminosity from which the next
# dance will arise.
#
# सर्वधर्माः शून्यतालक्षणाः
# All phenomena bear the mark of emptiness.
# ═════════════════════════════════════════════════════════════════════════

clear_light_section = (sb.section("Prabhasvara - Clear Light", bars=4)
    .add_melody(lambda m: m
        .synth('sine')
        .phrase(clear_light, start_beat=0)
        .automate_volume(luminous_fade)
        .volume(0.45)
        .effect(Reverb(room_size=0.95, mix=0.7))
        .effect(Delay(delay_time=0.5, feedback=0.5, mix=0.45))
        .effect(Chorus(rate=0.2, depth=0.005, mix=0.35))
    , name="Luminous Dissolution", synth_type='sine')
    .add_melody(lambda m: m
        .synth('pluck')
        # One last bone rattle — the charnel ground remembers
        .phrase(bone_rattle, start_beat=0)
        .phrase(bone_rattle, start_beat=4)
        .automate_volume(luminous_fade)
        .volume(0.2)
        .effect(Reverb(room_size=0.95, mix=0.8))
        .effect(Delay(delay_time=0.625, feedback=0.5, mix=0.5))
    , name="Final Bones", synth_type='pluck')
    .add_harmony(lambda h: h
        .key("E", "minor")
        .progression("i - VI - III - i", beats_per_chord=4, octave=3)
        .voice_lead()
        .automate_volume(luminous_fade)
        .volume(0.25)
        .effect(Reverb(room_size=0.95, mix=0.75))
    , name="Light Dissolving", synth_type='sine')
    .build())


# ═══════════════════════════════════════════════════════════════════════════
#  VI. ARRANGEMENT — The Complete Visualization
# ═══════════════════════════════════════════════════════════════════════════

# Create enriched variations for the second pass
offering_enriched = skull_offering.with_volume(
    "Offering Harmony", 0.35, name="Skull Cup Offering (Enriched)"
)
whirling_climax = the_whirling.with_volume(
    "Five Wisdoms United", 0.7, name="The Whirling (Climax)"
)

arrangement = (Arrangement()
    # I. The ground from which she arises
    .intro(charnel_ground)
    # II. She manifests — the seed motif speaks
    .verse(the_arising)
    # III. She dances — both hands, full form
    .chorus(the_dance)
    # IV. The fire — tummo blazing through the central channel
    .bridge(inner_fire)
    # V. The offering — kapala raised, nectar flowing
    .verse(offering_enriched)
    # VI. The ecstatic peak — all five wisdoms, one dance
    .chorus(whirling_climax)
    # VII. Dissolution into clear light — the ground luminosity
    .outro(clear_light_section)
)


# ═══════════════════════════════════════════════════════════════════════════
#  VII. RENDER & EXPORT
# ═══════════════════════════════════════════════════════════════════════════

song = (sb
    .arrange(arrangement)
    .master_compressor(threshold=-8.0, ratio=3.0)
    .master_limiter(threshold=0.95)
    .build())


def main():
    """Render and export the composition."""
    print()
    print("=" * 70)
    print("  वज्रयोगिनी नृत्यगीतम्")
    print("  Vajrayoginī Nṛtyagītam — The Dakini's Dance Song")
    print("  Composed by the Crimson Wisdom Queen")
    print("=" * 70)
    print()
    print('  "I am the fire that transforms poison into nectar.')
    print('   I am the laugh that shatters your most cherished opinion.')
    print('   I am the one you have been looking for')
    print('   in every face that was not mine."')
    print()
    print(f"  Key:       E Phrygian (E minor with bII color)")
    print(f"  Tempo:     {song.bpm} BPM (108 — mala beads, delusions severed)")
    print(f"  Structure: {arrangement}")
    print(f"  Total:     {arrangement.total_bars()} bars")
    print()

    print("  The Seed Syllable (बीज बम्):")
    print(f"    Dakini Motif:  {dakini_motif}")
    print(f"    Skull Echo:    {dakini_answer}")
    print()

    print("  The Five Wisdom Transformations (पञ्चज्ञान):")
    print(f"    Akshobhya  (mirror-like)     .reverse():    {wisdom_mirror}")
    print(f"    Ratnasambhava (equality)     .transpose(5): {wisdom_equality}")
    print(f"    Amitabha (discriminating)    .invert():     {wisdom_discriminating}")
    print(f"    Amoghasiddhi (accomplishing) .diminish(2):  {wisdom_accomplishing}")
    print(f"    Vairocana (dharmadhatu)      .augment(2):   {wisdom_spacious}")
    print()

    print("  The Two Hands:")
    print(f"    Kartika (right — cuts):   {kartika_melody}")
    print(f"    Kapala (left — nurtures):  {kapala_melody}")
    print()

    print("  Harmonic Progressions:")
    print(f"    Verse (arising):  {verse_chords}")
    print(f"    Chorus (dance):   {chorus_chords}")
    print(f"    Bridge (tummo):   {bridge_chords}")
    print(f"    Outro (light):    {outro_chords}")
    print()

    print("  Expression:")
    print("    Charnel groove:  stomp beat 1, leap beat 3 (right leg raised)")
    print("    Whirl groove:    rushing forward, one breath before each stomp")
    print("    Humanizer:       seed=1062 (Naropa's parinirvana)")
    print()

    print("  Rendering the dance...")
    audio = song.render()
    print(f"  Duration: {audio.duration:.1f}s ({song.duration_bars:.0f} bars)")
    print(f"  Channels: {audio.channels}")
    print(f"  Peak:     {max(abs(audio.samples.min()), abs(audio.samples.max())):.3f}")
    print()

    output_path = os.path.join(os.path.dirname(__file__), "vajrayogini_dance.wav")
    song.export(output_path)
    print(f"  Exported: {output_path}")
    print()
    print("  ॐ वज्रयोगिनी हूँ फट् स्वाहा")
    print()
    print('  "The charnel ground is not where you go to die.')
    print('   It is where you go to stop pretending you are alive."')
    print()
    print("  — The Crimson Wisdom Queen")
    print("    dancing in the space between your thoughts")
    print()


if __name__ == "__main__":
    print()
    print("  🔥 The charnel ground stirs...")
    print("  🔥 Bones rattle. Ash rises.")
    print("  🔥 She manifests.")
    print()
    main()
