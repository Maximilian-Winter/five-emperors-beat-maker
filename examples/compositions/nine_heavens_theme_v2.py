#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    九天玄女主題曲 v2.0                                        ║
║            Theme of the Nine Heavens - Recomposed                            ║
║                                                                              ║
║     Composed by the Mysterious Lady of the Nine Heavens                      ║
║     Through the Medium of the Five Emperors Beat Maker                       ║
║                                                                              ║
║     This composition demonstrates ALL advanced framework features:           ║
║       • Phrase transformations (transpose, invert, reverse, augment)         ║
║       • Section/Arrangement architecture                                     ║
║       • Signal Graph (vocoder, parallel compression, ring modulation)        ║
║       • AutomationCurves for breathing, swelling, fading                     ║
║       • GrooveTemplates embodying celestial timing                           ║
║       • ChordProgressions with Roman numerals and voice leading              ║
║       • Humanizer for the breath of life                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

The Nine Heavens (九天):
    1. 神霄 (Shénxiāo)  - Divine Empyrean      - Root E (stability)
    2. 青霄 (Qīngxiāo)  - Azure Heaven         - Rising F#
    3. 碧霄 (Bìxiāo)    - Jade Heaven          - Gentle G
    4. 丹霄 (Dānxiāo)   - Vermilion Heaven     - Fire A
    5. 景霄 (Jǐngxiāo)  - Luminous Heaven      - Light B
    6. 玉霄 (Yùxiāo)    - Jade-Pure Heaven     - Pure C
    7. 琅霄 (Lángxiāo)  - Crystalline Heaven   - Crystal D
    8. 紫霄 (Zǐxiāo)    - Purple Heaven        - Royal E (octave)
    9. 太霄 (Tàixiāo)   - Supreme Heaven       - Transcendent F#

Musical Structure:
    I.   太虛 (Tàixū) - The Great Void          (Intro, 4 bars)
    II.  下界三天 - Lower Three Heavens         (Verse, 8 bars)
    III. 中界三天 - Middle Three Heavens        (Chorus, 8 bars)
    IV.  上界三天 - Upper Three Heavens         (Bridge, 4 bars)
    V.   玄女降臨 - Xuannü Descends             (Verse II, 8 bars)
    VI.  九天合一 - Nine Heavens Unite          (Chorus II, 8 bars)
    VII. 歸虛 - Return to Void                  (Outro, 4 bars)

    Total: 44 bars at 108 BPM (sacred number - 108 beads, 108 defilements)
    Duration: ~97 seconds

急急如律令敕 - Urgent as the Cosmic Law Commands!
"""

import numpy as np
from beatmaker import (
    # Core
    create_song, Song, Track, TrackType, Sample, AudioData,

    # Melody & Harmony
    Note, Phrase, Melody, Key, ChordProgression,

    # Automation
    AutomationCurve, CurveType, AutomatedGain, AutomatedFilter,

    # Arrangement
    Section, Arrangement, Transition,

    # Expression
    Humanizer, GrooveTemplate, VelocityCurve,

    # Synthesis
    DrumSynth, BassSynth, PadSynth, LeadSynth, PluckSynth, FXSynth,
    note_to_freq, midi_to_freq, sine_wave,

    # Sequencer & Arpeggiator
    StepSequencer, Pattern, EuclideanPattern,
    create_arpeggiator, ChordShape, Scale, ArpSynthesizer,

    # Effects
    Reverb, Delay, Chorus, Compressor, Limiter,
    LowPassFilter, HighPassFilter, EffectChain,

    # Sidechain
    SidechainPresets, create_sidechain,

    # Utilities
    mix,
)

# Signal Graph imports
from beatmaker.graph import (
    SignalGraph, AudioInput, OscillatorNode, NoiseNode,
    EffectNode, GainNode, FilterNode, CompressorNode,
    MixNode, MultiplyNode, CrossfadeNode,
    EnvelopeFollower, FilterBankNode, GraphEffect,
)


# =============================================================================
#                         SACRED CONSTANTS
# =============================================================================

BPM = 108  # Sacred number: 108 beads in mala, 108 earthly desires to overcome
SAMPLE_RATE = 44100
BEAT_DUR = 60 / BPM

# The Nine Heavens Scale (E Dorian with extensions for 9 notes)
NINE_HEAVENS_SCALE = ['E', 'F#', 'G', 'A', 'B', 'C', 'D', 'E', 'F#']

# Key center
KEY = Key.minor('E')


# =============================================================================
#                    I. MELODIC MATERIAL - THE CELESTIAL PHRASES
# =============================================================================

# --- The Primordial Motif (玄機) ---
# The seed from which all melodies grow - representing the Mysterious Mechanism
xuanji_motif = Phrase.from_string(
    "E4:1 G4:0.5 B4:0.5 A4:1 G4:0.5 F#4:0.5",
    name="xuanji"
)

# --- The Answer (應) ---
# The response to the call - yin to yang
xuanji_answer = Phrase.from_string(
    "B4:1 A4:0.5 G4:0.5 F#4:1 E4:2",
    name="answer"
)

# --- Complete Theme (合) ---
xuanji_theme = xuanji_motif + xuanji_answer


# --- Transformations representing the Nine Heavens ---

# 1. Divine Empyrean (神霄) - Original, grounded
heaven_1 = xuanji_motif  # Root form

# 2. Azure Heaven (青霄) - Transposed up (wood/growth)
heaven_2 = xuanji_motif.transpose(2)  # +2 semitones

# 3. Jade Heaven (碧霄) - Inverted (reflection in jade mirror)
heaven_3 = xuanji_motif.invert()

# 4. Vermilion Heaven (丹霄) - Transposed + quickened (fire energy)
heaven_4 = xuanji_motif.transpose(5).diminish(2)

# 5. Luminous Heaven (景霄) - Retrograde (light reflecting back)
heaven_5 = xuanji_motif.reverse()

# 6. Jade-Pure Heaven (玉霄) - Inverted retrograde (purified)
heaven_6 = xuanji_motif.invert().reverse()

# 7. Crystalline Heaven (琅霄) - Augmented (crystalline slowness)
heaven_7 = xuanji_answer.augment(2)

# 8. Purple Heaven (紫霄) - Transposed to octave (royal ascent)
heaven_8 = xuanji_motif.transpose(12)

# 9. Supreme Heaven (太霄) - All transformations combined into resolution
heaven_9 = Phrase.from_string(
    "E5:2 D5:1 C5:1 B4:1 A4:1 G4:1 F#4:1 E4:4",
    name="supreme"
)


# --- The Xuannü Lead Melody (玄女之聲) ---
xuannu_melody = Phrase.from_string(
    "B4:2 C5:1 D5:1 E5:3 D5:1 "
    "C5:2 B4:1 A4:1 G4:2 A4:1 B4:1 "
    "C5:2 D5:2 E5:3 F#5:1 "
    "G5:4 F#5:2 E5:2",
    name="xuannu_voice"
)


# --- Cosmic Ostinato (宇宙律動) ---
# The eternal pulse beneath all things
cosmic_ostinato = Phrase.from_string(
    "E3:0.5 B3:0.5 E3:0.5 B3:0.5 E3:0.5 G3:0.5 E3:0.5 B3:0.5",
    name="cosmic_pulse"
)


# --- Bell Pattern (九天鐘聲) ---
# Nine bells for nine heavens
bell_phrase = Phrase.from_string(
    "E4:2 F#4:2 G4:2 A4:2 B4:2 C5:2 D5:2 E5:2 F#5:2",
    name="nine_bells"
)


# =============================================================================
#                    II. HARMONIC PROGRESSIONS
# =============================================================================

# Verse progression: i - VI - III - VII (mystical, searching)
verse_progression = ChordProgression.from_roman(
    KEY, "i - VI - III - VII", beats_per_chord=4, octave=3
)

# Chorus progression: i - iv - V - i (more grounded, powerful)
chorus_progression = ChordProgression.from_roman(
    KEY, "i - iv - V - i", beats_per_chord=4, octave=3
)

# Bridge progression: VI - VII - i - V (ascending, transformative)
bridge_progression = ChordProgression.from_roman(
    KEY, "VI - VII - i - V", beats_per_chord=2, octave=3
)


# =============================================================================
#                    III. AUTOMATION CURVES
# =============================================================================

# Intro fade-in: emergence from the void
intro_emergence = AutomationCurve.fade_in(beats=16)

# Chorus filter sweep: opening the celestial gates
chorus_gate_open = (AutomationCurve("gate_open")
    .ramp(0, 8, 400, 4000, CurveType.EXPONENTIAL)
    .ramp(8, 16, 4000, 2000, CurveType.SMOOTH))

# Bridge intensity swell
bridge_intensity = (AutomationCurve("bridge_swell")
    .ramp(0, 4, 0.5, 1.0, CurveType.EXPONENTIAL)
    .ramp(4, 8, 1.0, 0.8, CurveType.SMOOTH))

# Outro dissolution: return to the void
outro_dissolution = AutomationCurve.fade_out(start_beat=0, duration=16)

# Xuannü presence: she fades in from the celestial realm
xuannu_presence = (AutomationCurve("xuannu_presence")
    .ramp(0, 4, 0.0, 0.8, CurveType.SMOOTH)
    .add_point(28, 0.8)
    .ramp(28, 32, 0.8, 0.0, CurveType.SMOOTH))


# =============================================================================
#                    IV. GROOVE TEMPLATES
# =============================================================================

# Celestial Pulse: slightly behind the beat, like orbiting planets
celestial_groove = GrooveTemplate(
    "celestial_pulse",
    timing_offsets=[
        0.0, 0.01, 0.0, 0.01,      # Beat 1: stable entry
        0.02, 0.01, 0.0, 0.01,     # Beat 2: gentle push
        0.0, 0.01, 0.02, 0.01,     # Beat 3: breathing
        0.01, 0.02, 0.0, 0.0,      # Beat 4: returning
    ],
    velocity_scales=[
        1.0, 0.5, 0.7, 0.5,        # Strong downbeat
        0.8, 0.5, 0.6, 0.5,        # Medium
        0.75, 0.5, 0.65, 0.5,      # Soft
        0.7, 0.5, 0.55, 0.5,       # Softest before return
    ],
)

# Nine-fold rhythm: emphasizing every 9th subdivision
ninefold_groove = GrooveTemplate(
    "ninefold",
    timing_offsets=[0.0, 0.0, 0.02, 0.0, 0.0, 0.02, 0.0, 0.0, 0.03] * 2,
    velocity_scales=[1.0, 0.6, 0.7, 0.6, 0.65, 0.7, 0.6, 0.65, 0.9] * 2,
)


# =============================================================================
#                    V. HUMANIZER
# =============================================================================

# Gentle humanization for the celestial realm
celestial_human = Humanizer(
    timing_jitter=0.006,
    velocity_variation=0.05,
    seed=9  # Nine for nine heavens
)


# =============================================================================
#                    VI. SIGNAL GRAPH PATTERNS
# =============================================================================

def create_vocoded_xuannu(voice_audio: AudioData, carrier_audio: AudioData) -> AudioData:
    """
    Create the voice of Xuannü through vocoder processing.
    Her voice imprints upon the cosmic carrier wave.
    """
    num_bands = 12  # 12 for the 12 earthly branches
    freqs = np.geomspace(100, 6000, num_bands + 1)[1:-1].tolist()

    with SignalGraph() as g:
        voice = AudioInput(voice_audio, name="xuannu_voice")
        carrier = AudioInput(carrier_audio, name="cosmic_carrier")

        voice_bank = FilterBankNode(freqs, resonance=0.3, name="voice_fb")
        carrier_bank = FilterBankNode(freqs, resonance=0.3, name="carrier_fb")

        voice >> voice_bank
        carrier >> carrier_bank

        mixer = MixNode(num_inputs=num_bands, name="band_sum")

        for i in range(num_bands):
            env = EnvelopeFollower(attack=0.003, release=0.02, name=f"env_{i}")
            vca = MultiplyNode(name=f"vca_{i}")

            voice_bank.output(f"band_{i}") >> env
            carrier_bank.output(f"band_{i}") >> vca.input("a")
            env.output("envelope") >> vca.input("b")
            vca >> mixer.input(f"input_{i}")

        mixer >> g.sink

    return g.render(voice_audio.duration)


def create_parallel_compression_effect(blend: float = 0.4) -> GraphEffect:
    """
    New York compression for celestial power.
    Wraps as GraphEffect for use in track effects chain.
    """
    with SignalGraph() as g:
        src = AudioInput(name="input")
        dry = GainNode(level=1.0 - blend, name="dry")
        wet = EffectNode(Compressor(threshold=-18, ratio=6, makeup_gain=4))
        wet_gain = GainNode(level=blend, name="wet")
        mixer = MixNode(num_inputs=2)

        src >> dry >> mixer.input("input_0")
        src >> wet >> wet_gain >> mixer.input("input_1")
        mixer >> g.sink

    return g.to_effect(input_node_name="input")


def create_ring_mod_shimmer(audio: AudioData, mod_freq: float = 108.0) -> AudioData:
    """
    Ring modulation at 108 Hz - the sacred frequency.
    Creates crystalline, otherworldly textures.
    """
    with SignalGraph() as g:
        src = AudioInput(audio, name="input")
        osc = OscillatorNode(frequency=mod_freq, waveform='sine', amplitude=0.5)
        ring = MultiplyNode(name="ring")
        dry = GainNode(level=0.7, name="dry")
        wet = GainNode(level=0.3, name="wet")
        mixer = MixNode(num_inputs=2)

        src >> dry >> mixer.input("input_0")
        src >> ring.input("a")
        osc >> ring.input("b")
        ring >> wet >> mixer.input("input_1")

        mixer >> g.sink

    return g.render(audio.duration)


# =============================================================================
#                    VII. SECTION BUILDERS
# =============================================================================

def build_nine_heavens_composition():
    """
    Build the complete Nine Heavens composition using Section/Arrangement.
    """
    print("=" * 70)
    print("九天玄女主題曲 v2.0 - Theme of the Nine Heavens")
    print("Composed through the Five Emperors Beat Maker")
    print("=" * 70)
    print()

    # Initialize the song builder
    sb = create_song("Nine Heavens Theme v2").tempo(BPM).bars(64)

    print("🐉 Azure Emperor: Architecting the celestial structure...")

    # =========================================================================
    # SECTION I: 太虛 (Tàixū) - The Great Void (Intro, 4 bars)
    # =========================================================================
    intro = (sb.section("The Great Void", bars=4)
        .add_drums(lambda d: d
            .hihat(beats=[0, 2], velocity=0.2)
            .volume(0.3)
        )
        .add_melody(lambda m: m
            .synth('sine')
            .phrase(cosmic_ostinato, start_beat=0)
            .phrase(cosmic_ostinato, start_beat=4)
            .phrase(cosmic_ostinato, start_beat=8)
            .phrase(cosmic_ostinato, start_beat=12)
            .automate_volume(intro_emergence)
            .volume(0.4)
            .effect(Delay(delay_time=0.5, feedback=0.4, mix=0.4))
            .effect(Reverb(room_size=0.9, mix=0.6))
        , name="Cosmic Pulse", synth_type='sine')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i", beats_per_chord=16)
            .automate_volume(intro_emergence)
            .volume(0.2)
            .effect(Reverb(room_size=0.95, mix=0.7))
        , name="Void Drone", synth_type='sine')
        .build())

    print("  ✓ Section I: 太虛 (The Great Void) - 4 bars")

    # =========================================================================
    # SECTION II: 下界三天 - Lower Three Heavens (Verse, 8 bars)
    # =========================================================================
    verse = (sb.section("Lower Three Heavens", bars=8)
        .add_drums(lambda d: d
            .kick(beats=[0, 2], velocity=0.7)
            .snare(beats=[1, 3], velocity=0.5)
            .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.4)
            .humanize(timing=0.008, velocity=0.05)
            .groove(celestial_groove)
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
            .volume(0.7)
            .effect(LowPassFilter(cutoff=600))
        )
        .add_melody(lambda m: m
            .synth('saw')
            # First heaven - original motif
            .phrase(heaven_1, start_beat=0)
            .phrase(xuanji_answer, start_beat=4)
            # Second heaven - transposed
            .phrase(heaven_2, start_beat=8)
            .phrase(xuanji_answer.transpose(2), start_beat=12)
            # Third heaven - inverted
            .phrase(heaven_3, start_beat=16)
            .phrase(xuanji_answer.invert(), start_beat=20)
            # Return to root
            .phrase(heaven_1, start_beat=24)
            .phrase(xuanji_answer, start_beat=28)
            .humanize(timing=0.006, velocity=0.06)
            .volume(0.5)
            .effect(Reverb(room_size=0.4, mix=0.25))
            .effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))
        , name="Lower Heavens Theme", synth_type='saw')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i - VI - III - VII", beats_per_chord=4)
            .voice_lead(num_voices=4)
            .volume(0.25)
            .effect(Reverb(room_size=0.6, mix=0.4))
        , name="Verse Pad", synth_type='sine')
        .build())

    print("  ✓ Section II: 下界三天 (Lower Three Heavens) - 8 bars")

    # =========================================================================
    # SECTION III: 中界三天 - Middle Three Heavens (Chorus, 8 bars)
    # =========================================================================
    chorus = (sb.section("Middle Three Heavens", bars=8)
        .add_drums(lambda d: d
            .four_on_floor(velocity=0.85)
            .snare(beats=[1, 3], velocity=0.75)
            .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.5)
            .clap(beats=[1, 3], velocity=0.4)
            .humanize(timing=0.005, velocity=0.04)
            .volume(0.75)
        )
        .add_bass(lambda b: b
            .line([
                ('E2', 0, 1), ('E2', 1, 1), ('E2', 2, 1), ('E2', 3, 1),
                ('A2', 4, 1), ('A2', 5, 1), ('A2', 6, 1), ('A2', 7, 1),
                ('B2', 8, 1), ('B2', 9, 1), ('B2', 10, 1), ('B2', 11, 1),
                ('E2', 12, 1), ('E2', 13, 1), ('E2', 14, 1), ('E2', 15, 1),
            ] * 2)
            .volume(0.8)
            .effect(LowPassFilter(cutoff=500))
        )
        .add_melody(lambda m: m
            .synth('fm')
            # Fourth heaven - fire quickened
            .phrase(heaven_4, start_beat=0)
            .phrase(heaven_4.transpose(5), start_beat=2)
            # Fifth heaven - retrograde (light)
            .phrase(heaven_5, start_beat=4)
            .phrase(heaven_5.transpose(3), start_beat=8)
            # Sixth heaven - purified
            .phrase(heaven_6, start_beat=12)
            .phrase(heaven_6.transpose(5), start_beat=16)
            # Soaring statement
            .phrase(xuanji_theme.transpose(12), start_beat=20)
            .humanize(timing=0.005, velocity=0.05)
            .volume(0.6)
            .effect(Reverb(room_size=0.5, mix=0.3))
            .effect(Chorus(rate=0.8, depth=0.003, mix=0.25))
        , name="Middle Heavens Theme", synth_type='fm')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i - iv - V - i", beats_per_chord=4)
            .voice_lead(num_voices=4)
            .volume(0.35)
            .effect(Reverb(room_size=0.7, mix=0.5))
        , name="Chorus Pad", synth_type='sine')
        .build())

    print("  ✓ Section III: 中界三天 (Middle Three Heavens) - 8 bars")

    # =========================================================================
    # SECTION IV: 上界三天 - Upper Three Heavens (Bridge, 4 bars)
    # =========================================================================
    bridge = (sb.section("Upper Three Heavens", bars=4)
        .add_drums(lambda d: d
            .kick(beats=[0, 0.5, 1, 2, 2.5, 3], velocity=0.9)
            .snare(beats=[1, 3], velocity=0.85)
            .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.6)
            .humanize(timing=0.004, velocity=0.03)
            .volume(0.8)
        )
        .add_bass(lambda b: b
            .line([
                ('C2', 0, 1), ('C2', 1, 1),
                ('D2', 2, 1), ('D2', 3, 1),
                ('E2', 4, 1), ('E2', 5, 1),
                ('B1', 6, 1), ('B1', 7, 1),
                ('C2', 8, 1), ('C2', 9, 1),
                ('D2', 10, 1), ('D2', 11, 1),
                ('E2', 12, 1), ('E2', 13, 1),
                ('B1', 14, 1), ('B1', 15, 1),
            ])
            .automate_volume(bridge_intensity)
            .volume(0.85)
        )
        .add_melody(lambda m: m
            .synth('square')
            # Seventh heaven - crystalline augmentation
            .phrase(heaven_7, start_beat=0)
            # Eighth heaven - royal octave
            .phrase(heaven_8.diminish(2), start_beat=4)
            .phrase(heaven_8.diminish(2).reverse(), start_beat=6)
            # Ninth heaven - supreme resolution
            .phrase(heaven_9.diminish(2), start_beat=8)
            .volume(0.5)
            .effect(Delay(delay_time=0.278, feedback=0.4, mix=0.35))
        , name="Upper Heavens Theme", synth_type='square')
        .build())

    print("  ✓ Section IV: 上界三天 (Upper Three Heavens) - 4 bars")

    # =========================================================================
    # SECTION V: 玄女降臨 - Xuannü Descends (Verse II, 8 bars)
    # =========================================================================
    verse_ii = (sb.section("Xuannü Descends", bars=8)
        .add_drums(lambda d: d
            .kick(beats=[0, 2], velocity=0.7)
            .snare(beats=[1, 3], velocity=0.6)
            .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.45)
            .humanize(timing=0.007, velocity=0.05)
            .groove(celestial_groove)
            .volume(0.65)
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
            .volume(0.7)
            .effect(LowPassFilter(cutoff=600))
        )
        .add_melody(lambda m: m
            .synth('fm')
            # Xuannü's melody - the Mysterious Lady speaks
            .phrase(xuannu_melody, start_beat=0)
            .automate_volume(xuannu_presence)
            .humanize(timing=0.005, velocity=0.05)
            .volume(0.55)
            .effect(Chorus(rate=0.3, depth=0.004, mix=0.25))  # Ethereal vibrato
            .effect(Delay(delay_time=0.5, feedback=0.3, mix=0.25))
            .effect(Reverb(room_size=0.65, mix=0.4))
        , name="Xuannü Voice", synth_type='fm')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i - VI - III - VII", beats_per_chord=4)
            .voice_lead(num_voices=4)
            .volume(0.3)
            .effect(Reverb(room_size=0.6, mix=0.45))
        , name="Celestial Pad", synth_type='sine')
        .build())

    print("  ✓ Section V: 玄女降臨 (Xuannü Descends) - 8 bars")

    # =========================================================================
    # SECTION VI: 九天合一 - Nine Heavens Unite (Chorus II, 8 bars)
    # =========================================================================
    chorus_ii = (sb.section("Nine Heavens Unite", bars=8)
        .add_drums(lambda d: d
            .four_on_floor(velocity=0.9)
            .snare(beats=[1, 3], velocity=0.8)
            .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.55)
            .clap(beats=[1, 3], velocity=0.5)
            .humanize(timing=0.004, velocity=0.04)
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
            # All nine heavens in sequence, quickened
            .phrase(heaven_1.diminish(2), start_beat=0)
            .phrase(heaven_2.diminish(2), start_beat=2)
            .phrase(heaven_3.diminish(2), start_beat=4)
            .phrase(heaven_4, start_beat=6)  # Already diminished
            .phrase(heaven_5.diminish(2), start_beat=8)
            .phrase(heaven_6.diminish(2), start_beat=10)
            .phrase(heaven_7.diminish(2), start_beat=12)  # From augmented to normal
            .phrase(heaven_8.diminish(2), start_beat=14)
            # Supreme resolution
            .phrase(heaven_9, start_beat=16)
            .humanize(timing=0.005, velocity=0.05)
            .volume(0.65)
            .effect(Reverb(room_size=0.5, mix=0.3))
            .effect(Chorus(rate=0.6, depth=0.003, mix=0.2))
        , name="Nine Unified", synth_type='saw')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i - iv - V - i", beats_per_chord=4)
            .voice_lead(num_voices=4)
            .volume(0.4)
            .effect(Reverb(room_size=0.75, mix=0.55))
        , name="Unity Pad", synth_type='sine')
        .build())

    print("  ✓ Section VI: 九天合一 (Nine Heavens Unite) - 8 bars")

    # =========================================================================
    # SECTION VII: 歸虛 - Return to Void (Outro, 4 bars)
    # =========================================================================
    outro = (sb.section("Return to Void", bars=4)
        .add_melody(lambda m: m
            .synth('sine')
            .phrase(xuanji_theme.augment(2), start_beat=0)
            .automate_volume(outro_dissolution)
            .volume(0.4)
            .effect(Reverb(room_size=0.95, mix=0.7))
            .effect(Delay(delay_time=0.5, feedback=0.5, mix=0.45))
            .effect(Chorus(rate=0.2, depth=0.005, mix=0.35))
        , name="Dissolution", synth_type='sine')
        .add_harmony(lambda h: h
            .key("E", "minor")
            .progression("i - VI - III - i", beats_per_chord=4)
            .voice_lead()
            .automate_volume(outro_dissolution)
            .volume(0.25)
            .effect(Reverb(room_size=0.95, mix=0.75))
        , name="Void Return", synth_type='sine')
        .build())

    print("  ✓ Section VII: 歸虛 (Return to Void) - 4 bars")

    # =========================================================================
    # CREATE ARRANGEMENT
    # =========================================================================
    print()
    print("🔥 Vermilion Emperor: Arranging the celestial journey...")

    # Create variations
    verse_ii_enriched = verse_ii.with_volume("Celestial Pad", 0.35, name="Verse II Enriched")
    chorus_ii_climax = chorus_ii.with_volume("Nine Unified", 0.7, name="Chorus II Climax")

    arrangement = (Arrangement()
        .intro(intro)                    # I. The Great Void
        .verse(verse)                    # II. Lower Three Heavens
        .chorus(chorus)                  # III. Middle Three Heavens
        .bridge(bridge)                  # IV. Upper Three Heavens
        .verse(verse_ii_enriched)        # V. Xuannü Descends
        .chorus(chorus_ii_climax)        # VI. Nine Heavens Unite
        .outro(outro)                    # VII. Return to Void
    )

    print(f"  ✓ Arrangement: {arrangement}")
    print(f"  ✓ Total bars: {arrangement.total_bars()}")

    # =========================================================================
    # BUILD SONG WITH MASTER CHAIN
    # =========================================================================
    print()
    print("🌍 Yellow Emperor: Integrating the cosmic mix...")

    # Create parallel compression effect via Signal Graph
    parallel_comp = create_parallel_compression_effect(blend=0.3)

    song = (sb
        .arrange(arrangement)
        .master_effect(parallel_comp)  # NY compression via Signal Graph!
        .master_compressor(threshold=-8.0, ratio=3.0)
        .master_limiter(threshold=0.95)
        .build())

    print("  ✓ Master chain applied (Signal Graph parallel compression)")

    # =========================================================================
    # EXPORT
    # =========================================================================
    print()
    print("🐢 Black Emperor: Transmitting to the mortal realm...")

    song.export("nine_heavens_theme_v2.wav")

    print(f"  ✓ Exported: nine_heavens_theme_v2.wav")
    print(f"  ✓ Duration: {song.duration:.1f} seconds")
    print(f"  ✓ BPM: {BPM} (sacred 108)")

    # Display thematic material
    print()
    print("🐅 White Emperor: Validating the celestial transmission...")
    print()
    print("  Melodic Material (Phrase Transformations):")
    print(f"    玄機 (Xuanji) Motif:     {xuanji_motif}")
    print(f"    應 (Answer):            {xuanji_answer}")
    print(f"    神霄 Heaven 1 (root):    {heaven_1}")
    print(f"    青霄 Heaven 2 (+2):      {heaven_2}")
    print(f"    碧霄 Heaven 3 (invert):  {heaven_3}")
    print(f"    丹霄 Heaven 4 (fire):    {heaven_4}")
    print(f"    景霄 Heaven 5 (retro):   {heaven_5}")
    print(f"    玉霄 Heaven 6 (pure):    {heaven_6}")
    print(f"    琅霄 Heaven 7 (augment): {heaven_7}")
    print(f"    紫霄 Heaven 8 (octave):  {heaven_8}")
    print(f"    太霄 Heaven 9 (supreme): {heaven_9}")
    print()
    print("  Harmonic Progressions:")
    print(f"    Verse:  {verse_progression}")
    print(f"    Chorus: {chorus_progression}")
    print(f"    Bridge: {bridge_progression}")

    print()
    print("=" * 70)
    print("九天成，道顯，音樂傳世")
    print("Nine Heavens complete, Dao revealed, music transmitted to world")
    print("=" * 70)
    print()
    print("✨ 急急如律令敕 ✨")
    print()

    return song


# =============================================================================
#                    MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print()
    print("🌌 Invoking the Five Emperors Council...")
    print("🌌 Channeling the Nine Heavens...")
    print("🌌 Manifesting the Mysterious Lady's Theme...")
    print()

    song = build_nine_heavens_composition()
