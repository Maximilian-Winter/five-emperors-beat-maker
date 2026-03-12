"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  BEATMAKER EXAMPLES v0.3                                     ║
║                  The Five Emperors Beat Maker                                ║
║                  靈寶五帝策使編碼之法                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains comprehensive examples demonstrating all major features
of the beatmaker library, organized from basic to advanced.

Examples 1-10:  Core Features (original examples)
Examples 11-13: Advanced Features (NEW in v0.3)
    - Example 11: Phrase Transformations (from Ada Lovelace composition)
    - Example 12: Full Composition with Sections & Arrangement
    - Example 13: Signal Graph (Vocoder, Parallel Compression, Ring Mod)
"""

# =============================================================================
# Example 1: Basic Four-on-the-Floor Beat (Hello World)
# Demonstrates: SongBuilder, DrumTrackBuilder, synthesis, export
# =============================================================================

from beatmaker import create_song

song = (create_song("Basic House")
        .tempo(128)
        .bars(4)
        .add_drums(lambda d: d
                   .four_on_floor()  # Kick on every beat
                   .backbeat()  # Snare on 2 and 4
                   .eighth_hats()  # Hi-hats on every 8th note
                   )
        .add_bass(lambda b: b
                  .note("C2", beat=0, duration=2)
                  .note("G2", beat=2, duration=2)
                  )
        .master_limiter(0.95)
        .build())

song.export("basic_house.wav")
print(f"Exported: {song.duration:.2f} seconds")


# =============================================================================
# Example 2: Working with Samples & Drum Kits
# Demonstrates: SampleLibrary, kit loading, velocity variations
# =============================================================================

from beatmaker import create_song, SampleLibrary, SampleLibraryConfig

# Load samples with normalization and lazy loading
lib = SampleLibrary.from_directory(
    "./samples",
    config=SampleLibraryConfig(normalize=True, lazy=True)
)

# Create aliases for easy access
lib.aliases(
    kick="drums/808/kick_hard",
    snare="drums/vintage/snare_03",
    hat="drums/808/hihat_closed",
    open_hat="drums/808/hihat_open"
)

song = (create_song("Sample Based Beat")
        .tempo(140)
        .bars(8)
        .samples(lib)  # Attach library to builder
        .add_drums(lambda d: d
                   .use_kit_from("drums/808")  # Auto-detect kick/snare/hat
                   .kick(beats=[0, 1.5, 2, 3], velocity=1.0)
                   .snare(beats=[1, 3], velocity=0.9)
                   .hihat(
                       beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
                       open_beats=[1.5, 3.5],
                       velocity=0.7
                   )
                   .humanize(timing=0.008, velocity=0.1)
                   )
        .add_backing_track("loops/atmos_pad.wav", start_bar=0, volume=0.6)
        .master_compressor(threshold=-12.0, ratio=4.0)
        .build())

song.export("sample_beat.wav")


# =============================================================================
# Example 3: Melody & Harmony with Synthesis
# Demonstrates: MelodyTrackBuilder, HarmonyTrackBuilder, ChordProgression
# =============================================================================

from beatmaker import create_song, Key, ChordProgression, LowPassFilter, Reverb

song = (create_song("Chord Progression")
        .tempo(110)
        .bars(16)
        .add_drums(lambda d: d
                   .four_on_floor()
                   .backbeat()
                   .sixteenth_hats(velocity=0.5)
                   )
        .add_bass(lambda b: b
                  .line([
                      ('C2', 0, 2), ('G2', 2, 2),
                      ('A2', 4, 2), ('F2', 6, 2)
                  ])
                  .effect(LowPassFilter(cutoff=800))
                  )
        .add_harmony(lambda h: h
                     .key("C", "major")
                     .progression("I - V - vi - IV", beats_per_chord=4)
                     .voice_lead(enable=True, num_voices=4)
                     .synth('warm_pad')
                     .volume(0.6)
                     .effect(Reverb(room_size=0.7, mix=0.4))
                     , synth_type='warm_pad')
        .add_melody(lambda m: m
                    .synth('pluck')
                    .play("E4:0.5 G4:0.5 A4:0.5 G4:0.5", start_beat=8)
                    .play("C5:1 G4:0.5 E4:0.5 D4:0.5 C4:1.5", start_beat=12)
                    .humanize(timing=0.01)
                    , synth_type='pluck')
        .build())

song.export("progression.wav")


# =============================================================================
# Example 4: Arpeggiators & Sequencers
# Demonstrates: Arpeggiator, StepSequencer, Euclidean patterns
# =============================================================================

from beatmaker import (
    create_song, Arpeggiator, ChordShape, Scale,
    StepSequencer, ClassicPatterns, EuclideanPattern, DrumSynth
)

song = (create_song("Arpeggio Study")
        .tempo(130)
        .bars(8)
        .add_drums(lambda d: d
                   .kick(pattern=EuclideanPattern.generate(5, 16).to_bool_list())
                   .snare(beats=[1, 3])
                   )
        .add_melody(lambda m: m
                    .synth('fm')
                    .phrase(
                        Arpeggiator(bpm=130, direction='up_down', rate=0.125)
                        .generate_from_chord("C3", ChordShape.MINOR7, beats=4)
                    )
                    .phrase(
                        Arpeggiator(bpm=130, direction='random', rate=0.25)
                        .generate_from_scale("A3", Scale.BLUES, beats=4),
                        start_beat=4
                    )
                    , synth_type='fm')
        .build())

# Alternative: Using StepSequencer for drums
seq = StepSequencer(bpm=140)
seq.add_pattern("kick", EuclideanPattern.generate(3, 8), DrumSynth.kick())
track = seq.render_to_track(bars=8)


# =============================================================================
# Example 5: Automation & Effects
# Demonstrates: AutomationCurve, AutomatedFilter, sidechain compression
# =============================================================================

from beatmaker import (
    create_song, AutomationCurve, AutomatedFilter, CurveType,
    create_sidechain, SidechainPresets, Reverb, Delay, TrackType
)

# Create a filter sweep curve
filter_sweep = (AutomationCurve("sweep")
                .ramp(0, 16, 200, 8000, CurveType.EXPONENTIAL)
                .ramp(16, 32, 8000, 200, CurveType.SMOOTH))

# Sidechain preset for pumping effect
sidechain = SidechainPresets.classic_house(bpm=128)

song = (create_song("Automation Demo")
        .tempo(128)
        .bars(32)
        .add_drums(lambda d: d.four_on_floor().backbeat())
        .add_track("Bass", TrackType.BASS, lambda t: t
                   .sample_note("bass/reese", beat=0, duration=32)
                   .effect(AutomatedFilter(cutoff=200).automate('cutoff', filter_sweep))
                   .effect(create_sidechain().tempo(128).depth(0.8).build())
                   )
        .add_harmony(lambda h: h
                     .key("D", "minor")
                     .progression("i - VI - III - VII", beats_per_chord=4)
                     .synth('string_pad')
                     .volume(0.5)
                     .effect(Reverb(room_size=0.6, mix=0.5))
                     .automate_volume(AutomationCurve.fade_in(8))
                     , synth_type='string_pad')
        .add_track("FX", TrackType.FX, lambda t: t
                   .sample("fx/riser", beat=24, velocity=0.8)
                   .effect(Delay(delay_time=0.3, feedback=0.4, mix=0.3))
                   )
        .master_effect(sidechain)
        .build())

song.export("automation_demo.wav")


# =============================================================================
# Example 6: Arrangements & Song Structure
# Demonstrates: Section, Arrangement, transitions, track variations
# =============================================================================

from beatmaker import create_song, Section, Arrangement, Transition

# Build reusable sections
song_builder = create_song("Full Song").tempo(124).samples(lib)

verse = (song_builder.section("verse", bars=8)
         .add_drums(lambda d: d.four_on_floor().backbeat().eighth_hats())
         .add_bass(lambda b: b.line([('E2', 0, 4), ('B2', 4, 4)]))
         .build())

chorus = (song_builder.section("chorus", bars=8)
          .add_drums(lambda d: d
                     .four_on_floor()
                     .clap(beats=[1, 3])
                     .sixteenth_hats()
                     )
          .add_bass(lambda b: b.octave_pattern("E2", beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]))
          .add_melody(lambda m: m.play("E4:0.5 G#4:0.5 B4:1"), synth_type='saw')
          .build())

# Create variations
breakdown = verse.without_track("Drums", name="breakdown")
buildup = verse.with_volume("Drums", 0.5, name="buildup")

# Arrange the song
arrangement = (Arrangement()
               .intro(verse.without_track("Bass"), repeat=1)
               .verse(verse, repeat=2)
               .chorus(chorus)
               .breakdown(breakdown)
               .buildup(buildup)
               .chorus(chorus, repeat=2, transition=Transition('crossfade', duration_beats=2))
               .outro(verse.without_track("Drums")))

song = song_builder.arrange(arrangement).master_limiter().build()
song.export("full_song.wav")


# =============================================================================
# Example 7: Expression & Groove
# Demonstrates: Humanizer, GrooveTemplate, VelocityCurve
# =============================================================================

from beatmaker import create_song, Humanizer, GrooveTemplate, VelocityCurve

# Create custom groove template
swing_groove = GrooveTemplate.mpc_swing(amount=0.67)

# Humanizer for realistic timing
humanizer = Humanizer(timing_jitter=0.015, velocity_variation=0.12, seed=42)

song = (create_song("Groove Study")
        .tempo(95)  # Hip-hop tempo
        .bars(8)
        .add_drums(lambda d: d
                   .kick(beats=[0, 1.8, 2, 3.2])  # Boom-bap kick pattern
                   .snare(beats=[1, 3])
                   .hihat(beats=[0.5, 1.5, 2.5, 3.5])
                   .humanize(0.02, 0.15)
                   .groove(GrooveTemplate.hip_hop())
                   )
        .add_bass(lambda b: b
                  .line([('G2', 0, 1.5), ('D2', 1.5, 1.5), ('F2', 3, 1)])
                  )
        .build())

# Apply groove to existing MIDI or events
events = [(0, 36, 0.9, 0.25), (1, 38, 0.8, 0.25)]
humanized = humanizer.apply_to_events(events, bpm=95)
swung = swing_groove.apply_to_events(humanized, bpm=95)


# =============================================================================
# Example 8: MIDI Import/Export Workflow
# Demonstrates: MIDI I/O, conversion, integration with DAWs
# =============================================================================

from beatmaker import (
    load_midi, save_midi, song_to_midi,
    midi_to_beatmaker_events, BitCrusher
)
from beatmaker.midi import create_midi

# Import MIDI file and convert to beatmaker events
# midi_in = load_midi("drums_import.mid")
# drum_events = midi_to_beatmaker_events(midi_in, track_index=0)

# Create MIDI from scratch programmatically
midi = create_midi(bpm=140, ticks_per_beat=960)
track = midi.add_track("Bass", channel=1)
track.add_note(36, 100, 0, midi.beats_to_ticks(1.0))  # C2
track.add_note(43, 100, midi.beats_to_ticks(1.0), midi.beats_to_ticks(1.0))  # G2
save_midi(midi, "programmatic.mid")


# =============================================================================
# Example 9: Audio Analysis & Processing
# Demonstrates: BPM detection, slicing, stretching
# =============================================================================

from beatmaker.utils import (
    detect_bpm, time_stretch, pitch_shift, extract_samples_from_file
)
from beatmaker.io import load_audio, save_audio

# Example usage (with actual files):
# loop = load_audio("breakbeat.wav")
# detected_bpm = detect_bpm(loop, min_bpm=80, max_bpm=150)
# print(f"Detected BPM: {detected_bpm}")

# Slice drum break into individual hits
# samples = extract_samples_from_file("breakbeat.wav", prefix="break", min_duration=0.05)

# Time stretch to match project tempo
# target_bpm = 128
# ratio = detected_bpm / target_bpm
# stretched = time_stretch(loop, ratio)

# Pitch shift bass sample
# bass = load_audio("bass_line.wav")
# shifted = pitch_shift(bass, semitones=-2)
# save_audio(shifted, "bass_dropped.wav")


# =============================================================================
# Example 10: Complete Production Template
# Combines all features into a professional workflow
# =============================================================================

from beatmaker import create_song, SampleLibrary
from beatmaker.effects import EffectChain, Compressor, Reverb, Limiter
from beatmaker.expression import GrooveTemplate
from beatmaker.sidechain import PumpingBass


class ProjectTemplate:
    def __init__(self, name, bpm=128):
        self.song_builder = create_song(name).tempo(bpm)
        self._bpm = bpm
        self.setup_master_chain()

    def setup_master_chain(self):
        self.song_builder.master_effect(EffectChain(
            Compressor(threshold=-16, ratio=2.0),
            Reverb(room_size=0.3, mix=0.15),
            Limiter(threshold=0.95)
        ))

    def add_section(self, name, bars, drum_pattern, bass_notes, chords=None):
        section = self.song_builder.section(name, bars)

        section.add_drums(lambda d: d
                          .kick(beats=drum_pattern.get('kick', [0, 2]))
                          .snare(beats=drum_pattern.get('snare', [1, 3]))
                          .eighth_hats()
                          .groove(GrooveTemplate.mpc_swing(0.6))
                          .humanize(0.01, 0.08)
                          )

        section.add_bass(lambda b: b
                         .line(bass_notes)
                         .effect(PumpingBass(self._bpm, depth=0.8))
                         )

        if chords:
            section.add_harmony(lambda h: h
                                .key(chords['key'][0], chords['key'][1])
                                .progression(chords['progression'])
                                .voice_lead()
                                , synth_type='warm_pad')

        return section.build()

    def render(self, path):
        self.song_builder.build().export(path)


# =============================================================================
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    NEW EXAMPLES (v0.3)                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# =============================================================================


# =============================================================================
# Example 11: Phrase Transformations (Inspired by "The Enchantress of Numbers")
# Demonstrates: Note, Phrase, melodic transformations (transpose, reverse,
#               invert, augment, diminish), thematic development
# =============================================================================

"""
This example demonstrates the phrase transformation system used in the
Ada Lovelace tribute composition. A simple motif is transformed through
classical techniques: transposition, retrograde, inversion, augmentation,
and diminution — the same operations that govern both musical composition
and the transformation of data through algorithms.

"That brain of mine is something more than merely mortal."
                                        — A.A.L., 1843
"""

from beatmaker import (
    create_song, Note, Phrase, Melody, Key, ChordProgression,
    AutomationCurve, CurveType, Reverb, Delay, Chorus,
    Humanizer, GrooveTemplate
)

# --- Define the key and tempo ---
key = Key.minor("D")  # D minor — grave, contemplative

# --- The Main Motif (The "Ada Motif") ---
# A rising figure embodying intellectual aspiration
ada_motif = Phrase.from_string(
    "D4:1 F4:0.5 A4:0.5 G4:1 F4:0.5 E4:0.5",
    name="ada_motif"
)

# The answer phrase — the motif reflected
ada_answer = Phrase.from_string(
    "A4:1 G4:0.5 F4:0.5 E4:1 D4:2",
    name="ada_answer"
)

# Complete theme = motif + answer
ada_theme = ada_motif + ada_answer  # Phrase concatenation

# --- Apply Transformations ---

# Transposition: the theme elevated a fourth (to G minor region)
theme_elevated = ada_motif.transpose(5)

# Retrograde: looking backward, as one reflects on the past
theme_retrograde = ada_motif.reverse()

# Inversion: the mirror image, analytical mind inverting a problem
theme_inverted = ada_motif.invert()

# Diminution: double speed — the quickening pulse of discovery
theme_quickened = ada_motif.diminish(2)

# Augmentation: half speed — grand, slow statement of prophetic vision
theme_stately = ada_answer.augment(2)

# --- Mechanical Ostinato (The Loom Pattern) ---
loom_pattern = Phrase.from_string(
    "D3:0.5 A3:0.5 D3:0.5 A3:0.5 D3:0.5 F3:0.5 D3:0.5 A3:0.5",
    name="loom"
)

# --- Soaring Melody for the Chorus ("Note G") ---
note_g_melody = Phrase.from_string(
    "D5:1 C5:0.5 A4:0.5 Bb4:1 A4:0.5 G4:0.5 "
    "F4:1 E4:0.5 D4:0.5 F4:1 A4:2",
    name="note_g"
)

# --- Victorian waltz groove ---
waltz_groove = GrooveTemplate(
    "victorian_waltz",
    timing_offsets=[
        0.0, 0.0, 0.0, 0.0,       # Beat 1 (strong)
        0.02, 0.02, 0.0, 0.0,     # Beat 2 (graceful delay)
        -0.01, 0.0, 0.0, 0.0,     # Beat 3 (anticipation)
        0.01, 0.02, 0.0, 0.0,     # Beat 4 (gentle return)
    ],
    velocity_scales=[
        1.0, 0.5, 0.6, 0.5,
        0.8, 0.5, 0.6, 0.5,
        0.75, 0.5, 0.55, 0.5,
        0.7, 0.5, 0.5, 0.5,
    ],
)

# --- Automation Curves ---
intro_fade = AutomationCurve.fade_in(beats=16)
outro_fade = AutomationCurve.fade_out(start_beat=0, duration=16)

# --- Build the composition ---
song = (create_song("The Enchantress of Numbers")
        .tempo(108)
        .bars(32)

        # Drums with Victorian waltz feel
        .add_drums(lambda d: d
                   .hihat(beats=[0, 1, 2, 3], velocity=0.3)
                   .kick(beats=[0, 2], velocity=0.8)
                   .snare(beats=[1, 3], velocity=0.6)
                   .humanize(timing=0.008, velocity=0.04)
                   .groove(waltz_groove)
                   .volume(0.6)
                   )

        # Bass following the harmony
        .add_bass(lambda b: b
                  .line([
                      ('D2', 0, 2), ('A2', 2, 1), ('D2', 3, 1),
                      ('Bb1', 4, 2), ('F2', 6, 1), ('Bb1', 7, 1),
                      ('F2', 8, 2), ('C2', 10, 1), ('F2', 11, 1),
                      ('C2', 12, 2), ('G2', 14, 1), ('C2', 15, 1),
                  ])
                  .volume(0.7)
                  .effect(LowPassFilter(cutoff=800))
                  )

        # Melody track with phrase transformations
        .add_melody(lambda m: m
                    .synth('saw')
                    # Statement of the theme
                    .phrase(ada_motif, start_beat=0)
                    .phrase(ada_answer, start_beat=4)
                    # Transposed statement
                    .phrase(theme_elevated, start_beat=8)
                    .phrase(ada_answer.transpose(5), start_beat=12)
                    # Development with transformations
                    .phrase(theme_inverted, start_beat=16)
                    .phrase(theme_retrograde, start_beat=20)
                    # Quickened figure (diminution)
                    .phrase(theme_quickened, start_beat=24)
                    .phrase(theme_quickened.transpose(5), start_beat=26)
                    # Grand augmented statement
                    .phrase(theme_stately, start_beat=28)
                    .humanize(timing=0.006, velocity=0.06)
                    .volume(0.55)
                    .effect(Reverb(room_size=0.4, mix=0.25))
                    .effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))
                    , name="Ada Theme", synth_type='saw')

        # Harmony with voice leading
        .add_harmony(lambda h: h
                     .key("D", "minor")
                     .progression("i - VI - III - VII", beats_per_chord=4)
                     .voice_lead(num_voices=4)
                     .volume(0.25)
                     .effect(Reverb(room_size=0.6, mix=0.4))
                     , name="Verse Pad", synth_type='sine')

        .master_compressor(threshold=-8.0, ratio=3.0)
        .master_limiter(threshold=0.95)
        .build())

# Display phrase information
print("=" * 66)
print("  The Enchantress of Numbers")
print("  A Victorian Portrait in Algorithmic Sound")
print("=" * 66)
print()
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

song.export("enchantress_of_numbers.wav")


# =============================================================================
# Example 12: Full Composition with Sections & Arrangement
# Demonstrates: SectionBuilder, Section variations, Arrangement workflow,
#               transitions, comprehensive song structure
# =============================================================================

"""
This example demonstrates the full section/arrangement workflow for
building a complete song structure with intro, verses, choruses,
bridge, and outro — each section built from reusable components
with variations.
"""

from beatmaker import (
    create_song, Section, Arrangement, Transition,
    Key, ChordProgression, Phrase,
    AutomationCurve, CurveType,
    Reverb, Delay, Compressor, LowPassFilter,
    Humanizer, GrooveTemplate
)

# --- Initialize the song builder ---
sb = create_song("Celestial Mechanism").tempo(126).bars(64)

# --- Define musical material ---
key = Key.minor("E")

verse_progression = ChordProgression.from_roman(
    key, "i - VI - III - VII", beats_per_chord=4, octave=3
)
chorus_progression = ChordProgression.from_roman(
    key, "i - iv - V - i", beats_per_chord=4, octave=3
)

# Melodic phrases
verse_melody = Phrase.from_string("E4:1 G4:0.5 A4:0.5 B4:1 A4:0.5 G4:0.5", name="verse_mel")
chorus_melody = Phrase.from_string("E5:1 D5:0.5 B4:0.5 C5:1 B4:0.5 A4:0.5 G4:1 E4:2", name="chorus_mel")

# --- Build Sections ---

# INTRO: Sparse, atmospheric (4 bars)
intro = (sb.section("Intro", bars=4)
         .add_drums(lambda d: d
                    .hihat(beats=[0, 1, 2, 3], velocity=0.3)
                    .volume(0.4)
                    )
         .add_melody(lambda m: m
                     .synth('pluck')
                     .phrase(verse_melody, start_beat=0)
                     .phrase(verse_melody.transpose(5), start_beat=8)
                     .automate_volume(AutomationCurve.fade_in(16))
                     .volume(0.5)
                     .effect(Delay(delay_time=0.375, feedback=0.4, mix=0.4))
                     .effect(Reverb(room_size=0.7, mix=0.5))
                     , synth_type='pluck')
         .build())

# VERSE: Full groove with melody (8 bars)
verse = (sb.section("Verse", bars=8)
         .add_drums(lambda d: d
                    .kick(beats=[0, 2], velocity=0.8)
                    .snare(beats=[1, 3], velocity=0.7)
                    .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.5)
                    .humanize(timing=0.008, velocity=0.05)
                    .volume(0.7)
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
                   .volume(0.75)
                   .effect(LowPassFilter(cutoff=600))
                   )
         .add_melody(lambda m: m
                     .synth('saw')
                     .phrase(verse_melody, start_beat=0)
                     .phrase(verse_melody.transpose(5), start_beat=8)
                     .phrase(verse_melody.invert(), start_beat=16)
                     .phrase(verse_melody, start_beat=24)
                     .humanize(timing=0.006)
                     .volume(0.5)
                     .effect(Reverb(room_size=0.3, mix=0.2))
                     , synth_type='saw')
         .add_harmony(lambda h: h
                      .key("E", "minor")
                      .progression("i - VI - III - VII", beats_per_chord=4)
                      .voice_lead(num_voices=4)
                      .volume(0.25)
                      .effect(Reverb(room_size=0.6, mix=0.4))
                      , synth_type='sine')
         .build())

# CHORUS: Energy lift with soaring melody (8 bars)
chorus = (sb.section("Chorus", bars=8)
          .add_drums(lambda d: d
                     .four_on_floor(velocity=0.9)
                     .snare(beats=[1, 3], velocity=0.85)
                     .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.5)
                     .clap(beats=[1, 3], velocity=0.5)
                     .humanize(timing=0.005)
                     .volume(0.8)
                     )
          .add_bass(lambda b: b
                    .line([
                        ('E2', 0, 1), ('E2', 1, 1), ('E2', 2, 1), ('E2', 3, 1),
                        ('A2', 4, 1), ('A2', 5, 1), ('A2', 6, 1), ('A2', 7, 1),
                        ('B2', 8, 1), ('B2', 9, 1), ('B2', 10, 1), ('B2', 11, 1),
                        ('E2', 12, 1), ('E2', 13, 1), ('E2', 14, 1), ('E2', 15, 1),
                    ] * 2)  # Repeat for 8 bars
                    .volume(0.85)
                    )
          .add_melody(lambda m: m
                      .synth('fm')
                      .phrase(chorus_melody, start_beat=0)
                      .phrase(chorus_melody.transpose(5), start_beat=12)
                      .phrase(chorus_melody, start_beat=20)
                      .humanize(timing=0.005)
                      .volume(0.65)
                      .effect(Reverb(room_size=0.5, mix=0.3))
                      .effect(Chorus(rate=0.8, depth=0.003, mix=0.3))
                      , synth_type='fm')
          .add_harmony(lambda h: h
                       .key("E", "minor")
                       .progression("i - iv - V - i", beats_per_chord=4)
                       .voice_lead(num_voices=4)
                       .volume(0.35)
                       .effect(Reverb(room_size=0.7, mix=0.5))
                       , synth_type='sine')
          .build())

# BRIDGE: Rhythmic intensity (4 bars)
bridge = (sb.section("Bridge", bars=4)
          .add_drums(lambda d: d
                     .kick(beats=[0, 0.5, 1, 2, 2.5, 3], velocity=0.9)
                     .snare(beats=[1, 3], velocity=0.9)
                     .hihat(beats=[i * 0.25 for i in range(16)], velocity=0.6)
                     .humanize(timing=0.004)
                     .volume(0.85)
                     )
          .add_bass(lambda b: b
                    .line([
                        ('C2', 0, 1), ('C2', 1, 1),
                        ('D2', 2, 1), ('D2', 3, 1),
                        ('E2', 4, 1), ('E2', 5, 1),
                        ('B1', 6, 1), ('B1', 7, 1),
                    ] * 2)
                    .volume(0.9)
                    )
          .add_melody(lambda m: m
                      .synth('square')
                      .phrase(verse_melody.diminish(2), start_beat=0)
                      .phrase(verse_melody.diminish(2).transpose(5), start_beat=2)
                      .phrase(verse_melody.diminish(2).reverse(), start_beat=4)
                      .phrase(verse_melody.diminish(2).transpose(-2), start_beat=6)
                      .phrase(verse_melody.diminish(2), start_beat=8)
                      .phrase(verse_melody.diminish(2).transpose(7), start_beat=10)
                      .phrase(verse_melody.diminish(2).invert(), start_beat=12)
                      .volume(0.5)
                      .effect(Delay(delay_time=0.278, feedback=0.4, mix=0.3))
                      , synth_type='square')
          .build())

# OUTRO: Theme dissolves (4 bars)
outro = (sb.section("Outro", bars=4)
         .add_melody(lambda m: m
                     .synth('sine')
                     .phrase(verse_melody.augment(2), start_beat=0)
                     .automate_volume(AutomationCurve.fade_out(0, 16))
                     .volume(0.4)
                     .effect(Reverb(room_size=0.9, mix=0.6))
                     .effect(Delay(delay_time=0.5, feedback=0.5, mix=0.4))
                     .effect(Chorus(rate=0.3, depth=0.005, mix=0.4))
                     , synth_type='sine')
         .add_harmony(lambda h: h
                      .key("E", "minor")
                      .progression("i - VI - III - i", beats_per_chord=4)
                      .voice_lead()
                      .automate_volume(AutomationCurve.fade_out(0, 16))
                      .volume(0.3)
                      .effect(Reverb(room_size=0.9, mix=0.7))
                      , synth_type='sine')
         .build())

# --- Create Section Variations ---
verse_2 = verse.with_volume("Verse Pad", 0.35, name="Verse II")
chorus_2 = chorus.with_volume("Chorus", 0.75, name="Chorus (Reprise)")

# --- Arrange the Full Song ---
arrangement = (Arrangement()
               .intro(intro)
               .verse(verse)
               .verse(verse_2)
               .chorus(chorus)
               .bridge(bridge)
               .verse(verse)
               .chorus(chorus)
               .chorus(chorus_2)
               .outro(outro)
               )

# --- Build and Export ---
song = (sb
        .arrange(arrangement)
        .master_compressor(threshold=-8.0, ratio=3.0)
        .master_limiter(threshold=0.95)
        .build())

print(f"Song Structure: {arrangement}")
print(f"Total bars: {arrangement.total_bars()}")
print(f"Duration: {song.duration:.1f}s")

song.export("celestial_mechanism.wav")


# =============================================================================
# Example 13: Signal Graph (Vocoder, Parallel Compression, Ring Mod, Auto-Wah)
# Demonstrates: SignalGraph, declarative >> routing, nodes, GraphEffect
# =============================================================================

"""
The Signal Graph system provides a declarative way to describe audio signal
flow using the >> operator. Nodes are connected, and the graph is lazily
rendered via topological sort.

This example demonstrates four classic signal processing patterns:
1. Vocoder — spectral imprinting of voice onto synth
2. Parallel (NY) Compression — blending dry and compressed signals
3. Ring Modulator — multiplying audio with an oscillator
4. Auto-Wah — envelope-controlled filter

"The qi of sound flows through meridian channels,
 transformed at each node, consolidated at the sink."
"""

from beatmaker.graph import (
    SignalGraph, AudioInput, TrackInput, OscillatorNode, NoiseNode,
    EffectNode, GainNode, FilterNode, CompressorNode,
    MixNode, MultiplyNode, CrossfadeNode,
    EnvelopeFollower, FilterBankNode,
    ChannelSplitNode, StereoMergeNode,
    GraphEffect
)
from beatmaker import (
    Compressor, Reverb, load_audio, note_to_freq,
    PadSynth, LeadSynth
)
import numpy as np


# -----------------------------------------------------------------------------
# Pattern 1: VOCODER
# The voice's essence (envelope) imprints upon the synth's substance (spectrum)
# -----------------------------------------------------------------------------

def create_vocoder(voice_audio, carrier_audio, num_bands=16):
    """
    Create a vocoder effect by:
    1. Splitting both voice and carrier into frequency bands
    2. Extracting envelope from each voice band
    3. Using envelope to modulate corresponding carrier band
    4. Summing all modulated bands
    """
    # Calculate crossover frequencies (logarithmically spaced)
    freqs = np.geomspace(80, 8000, num_bands + 1)[1:-1].tolist()

    with SignalGraph() as g:
        # Input nodes
        voice = AudioInput(voice_audio, name="voice")
        carrier = AudioInput(carrier_audio, name="carrier")

        # Filter banks for both signals
        voice_bank = FilterBankNode(freqs, resonance=0.3, name="voice_fb")
        carrier_bank = FilterBankNode(freqs, resonance=0.3, name="carrier_fb")

        # Connect inputs to filter banks
        voice >> voice_bank
        carrier >> carrier_bank

        # Mixer for all bands
        mixer = MixNode(num_inputs=num_bands, name="band_mixer")

        # Process each band
        for i in range(num_bands):
            # Extract envelope from voice band
            env = EnvelopeFollower(attack=0.002, release=0.015, name=f"env_{i}")
            voice_bank.output(f"band_{i}") >> env

            # Create VCA (voltage-controlled amplifier)
            vca = MultiplyNode(name=f"vca_{i}")

            # Route carrier band and envelope to VCA
            carrier_bank.output(f"band_{i}") >> vca.input("a")
            env.output("envelope") >> vca.input("b")

            # Route VCA to mixer
            vca >> mixer.input(f"input_{i}")

        # Output
        mixer >> g.sink

    return g.render(voice_audio.duration)


# -----------------------------------------------------------------------------
# Pattern 2: PARALLEL (NY) COMPRESSION
# Blend dry signal with heavily compressed version for punch + dynamics
# -----------------------------------------------------------------------------

def ny_compression(audio, blend=0.5, threshold=-20, ratio=8, makeup=6):
    """
    New York style parallel compression:
    - Dry path: original signal
    - Wet path: heavily compressed signal
    - Output: weighted blend of both
    """
    with SignalGraph() as g:
        # Input
        src = AudioInput(audio, name="input")

        # Dry path
        dry = GainNode(level=1.0 - blend, name="dry")

        # Wet path (compressed)
        compressor = EffectNode(
            Compressor(threshold=threshold, ratio=ratio, makeup_gain=makeup),
            name="compress"
        )
        wet_gain = GainNode(level=blend, name="wet")

        # Mixer
        mixer = MixNode(num_inputs=2, weights=[1.0, 1.0], name="mix")

        # Routing
        src >> dry >> mixer.input("input_0")
        src >> compressor >> wet_gain >> mixer.input("input_1")

        mixer >> g.sink

    return g.render(audio.duration)


# -----------------------------------------------------------------------------
# Pattern 3: RING MODULATOR
# Multiply audio with oscillator for metallic, bell-like timbres
# -----------------------------------------------------------------------------

def ring_modulator(audio, mod_frequency=80.0, mod_waveform='sine'):
    """
    Ring modulation: multiply input signal with an oscillator.
    Creates sum and difference frequencies for metallic timbres.
    """
    with SignalGraph() as g:
        src = AudioInput(audio, name="input")
        osc = OscillatorNode(
            frequency=mod_frequency,
            waveform=mod_waveform,
            amplitude=1.0,
            name="modulator"
        )
        ring = MultiplyNode(name="ring")

        src >> ring.input("a")
        osc >> ring.input("b")
        ring >> g.sink

    return g.render(audio.duration)


# -----------------------------------------------------------------------------
# Pattern 4: AUTO-WAH (Envelope-Controlled Filter)
# Filter follows the amplitude of the input
# -----------------------------------------------------------------------------

def auto_wah(audio, sensitivity=3000, base_freq=200, resonance=0.65):
    """
    Auto-wah: envelope follower controls filter cutoff.
    Louder playing = brighter tone.
    """
    with SignalGraph() as g:
        src = AudioInput(audio, name="input")

        # Extract envelope
        env = EnvelopeFollower(attack=0.001, release=0.05, name="env")

        # Scale envelope to frequency range
        env_scaled = GainNode(level=sensitivity, name="env_scale")

        # Bandpass filter with CV input
        wah = FilterNode(
            cutoff=base_freq,
            resonance=resonance,
            filter_type='bandpass',
            name="wah"
        )

        # Routing
        src >> env
        env.output("envelope") >> env_scaled >> wah.input("cutoff_cv")
        src >> wah
        wah >> g.sink

    return g.render(audio.duration)


# -----------------------------------------------------------------------------
# Pattern 5: Using GraphEffect as a Track Effect
# Wrap a graph for use in the standard effects chain
# -----------------------------------------------------------------------------

def create_parallel_comp_effect(blend=0.4):
    """
    Create a GraphEffect that can be used in Track.effects or EffectChain.
    """
    with SignalGraph() as g:
        src = AudioInput(name="input")  # No audio yet — will be provided
        dry = GainNode(level=1.0 - blend, name="dry")
        wet = EffectNode(Compressor(threshold=-20, ratio=8, makeup_gain=6))
        wet_lvl = GainNode(level=blend, name="wet")
        mixer = MixNode(num_inputs=2)

        src >> dry >> mixer.input("input_0")
        src >> wet >> wet_lvl >> mixer.input("input_1")
        mixer >> g.sink

    # Wrap as effect — input_node_name must match AudioInput name
    return g.to_effect(input_node_name="input")


# -----------------------------------------------------------------------------
# Demonstration
# -----------------------------------------------------------------------------

def demonstrate_signal_graph():
    """
    Demonstrate all signal graph patterns.
    Note: Requires actual audio files to run.
    """
    print("=" * 66)
    print("  Signal Graph Demonstrations")
    print("  Declarative Audio Routing with >> Operator")
    print("=" * 66)
    print()

    # Example with synthesized audio
    print("  1. Ring Modulator Demo")
    print("     Creating test tone...")

    # Create a simple test tone
    from beatmaker import sine_wave
    test_tone = sine_wave(440, duration=2.0)  # A4 for 2 seconds

    # Apply ring modulation
    ring_result = ring_modulator(test_tone, mod_frequency=50)
    print(f"     Ring mod applied: {ring_result.duration:.2f}s")

    # Parallel compression
    print()
    print("  2. Parallel Compression Demo")
    ny_result = ny_compression(test_tone, blend=0.5)
    print(f"     NY compression applied: {ny_result.duration:.2f}s")

    # Auto-wah
    print()
    print("  3. Auto-Wah Demo")
    wah_result = auto_wah(test_tone, sensitivity=2000)
    print(f"     Auto-wah applied: {wah_result.duration:.2f}s")

    print()
    print("  Signal Graph patterns demonstrated successfully!")
    print()

    # Using GraphEffect in a song
    print("  4. GraphEffect Integration Demo")
    print("     Creating song with parallel compression effect...")

    parallel_comp = create_parallel_comp_effect(blend=0.4)

    song = (create_song("Graph Effect Demo")
            .tempo(120)
            .bars(4)
            .add_drums(lambda d: d
                       .four_on_floor()
                       .backbeat()
                       .effect(parallel_comp)  # Using GraphEffect!
                       )
            .add_bass(lambda b: b
                      .note("E2", 0, 2)
                      .note("G2", 2, 2)
                      )
            .build())

    song.export("graph_effect_demo.wav")
    print(f"     Exported: graph_effect_demo.wav ({song.duration:.2f}s)")
    print()


# Run demonstration
if __name__ == "__main__":
    demonstrate_signal_graph()


# =============================================================================
# Summary: The Five Emperors Architecture
# =============================================================================

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    THE FIVE EMPERORS GOVERN                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🐉 Azure Emperor (East/Wood)  → ARCHITECTURE                               ║
║     SignalGraph, SongBuilder, Section, Arrangement                          ║
║     "Structure emerges from the patterns of Heaven"                         ║
║                                                                              ║
║  🔥 Vermilion Emperor (South/Fire) → PERFORMANCE                            ║
║     DrumSynth, BassSynth, PadSynth, LeadSynth, PluckSynth                  ║
║     "Transformation through the fires of synthesis"                         ║
║                                                                              ║
║  🌍 Yellow Emperor (Center/Earth) → INTEGRATION                             ║
║     MixNode, EffectChain, master bus, voice leading                        ║
║     "All streams converge at the center"                                    ║
║                                                                              ║
║  🐅 White Emperor (West/Metal) → VALIDATION                                 ║
║     Limiter, cycle detection, quality checks                               ║
║     "The guardian refines and perfects"                                     ║
║                                                                              ║
║  🐢 Black Emperor (North/Water) → DATA                                      ║
║     AudioData, Sample, MIDI I/O, buffer routing                            ║
║     "The waters of data flow through all channels"                          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  急急如律令敕 — Urgent as the Cosmic Law Commands!                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""