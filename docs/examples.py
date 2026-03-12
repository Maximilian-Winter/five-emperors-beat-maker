"""
Example 1: Basic Four-on-the-Floor Beat (Hello World)
Demonstrates: SongBuilder, DrumTrackBuilder, synthesis, export
"""
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

"""
Example 2: Working with Samples & Drum Kits
Demonstrates: SampleLibrary, kit loading, velocity variations
"""
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
                   .kick(beats=[0, 1.5, 2, 3], velocity=1.0)  # Custom pattern
                   .snare(beats=[1, 3], velocity=0.9)
                   .hihat(
    beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
    open_beats=[1.5, 3.5],  # Open hat on off-beats
    velocity=0.7
)
                   .humanize(timing=0.008, velocity=0.1)  # Add groove
                   )
        .add_backing_track("loops/atmos_pad.wav", start_bar=0, volume=0.6)
        .master_compressor(threshold=-12.0, ratio=4.0)
        .build())

song.export("sample_beat.wav")

"""
Example 3: Melody & Harmony with Synthesis
Demonstrates: MelodyTrackBuilder, HarmonyTrackBuilder, ChordProgression
"""
from beatmaker import create_song, Key, ChordProgression

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
                     .voice_lead(enable=True, num_voices=4)  # Smooth voice leading
                     .synth('warm_pad')
                     .volume(0.6)
                     .effect(Reverb(room_size=0.7, mix=0.4))
                     , synth_type='warm_pad')
        .add_melody(lambda m: m
                    .synth('pluck')
                    .play("E4:0.5 G4:0.5 A4:0.5 G4:0.5", start_beat=8)  # Simple riff
                    .play("C5:1 G4:0.5 E4:0.5 D4:0.5 C4:1.5", start_beat=12)
                    .humanize(timing=0.01)
                    , synth_type='pluck')
        .build())

song.export("progression.wav")

"""
Example 4: Arpeggiators & Sequencers
Demonstrates: Arpeggiator, StepSequencer, Euclidean patterns
"""
from beatmaker import (
    create_song, Arpeggiator, ChordShape, Scale,
    StepSequencer, ClassicPatterns, EuclideanPattern
)
import numpy as np

song = (create_song("Arpeggio Study")
        .tempo(130)
        .bars(8)
        .add_drums(lambda d: d
                   .use_kit_from("drums/808")
                   .kick(pattern=EuclideanPattern.generate(5, 16).to_bool_list())
                   .snare(beats=[1, 3])
                   )
        .add_melody(lambda m: m
                    .synth('fm')
                    .phrase(
    # Create arpeggio from chord
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
seq.load_kit(ClassicPatterns.trap_kit())
seq.add_pattern("kick", EuclideanPattern.generate(3, 8), kick_sample)

track = seq.render_to_track(bars=8)

"""
Example 5: Automation & Effects
Demonstrates: AutomationCurve, AutomatedFilter, sidechain compression
"""
from beatmaker import (
    create_song, AutomationCurve, AutomatedFilter,
    create_sidechain, SidechainPresets, Reverb, Delay
)

# Create a filter sweep curve
filter_sweep = (AutomationCurve("sweep")
                .ramp(0, 16, 200, 8000, curve_type='exponential')
                .ramp(16, 32, 8000, 200))

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
                     .key("Dm")
                     .progression("i - VI - III - VII")
                     .synth('string_pad')
                     .volume(0.5)
                     .effect(Reverb(decay=2.0, mix=0.5))
                     .automate_volume(AutomationCurve.fade_in(8))
                     , synth_type='string_pad')
        .add_track("FX", TrackType.FX, lambda t: t
                   .sample("fx/riser", beat=24, velocity=0.8)
                   .effect(Delay(delay_time=0.3, feedback=0.4, mix=0.3))
                   )
        .master_effect(sidechain)  # Master sidechain for whole mix
        .build())

song.export("automation_demo.wav")

"""
Example 6: Arrangements & Song Structure
Demonstrates: Section, Arrangement, transitions, track variations
"""
from beatmaker import create_song, Section, Arrangement, Transition

# Build reusable sections
song_builder = create_song("Full Song").tempo(124).samples(lib)

verse = (song_builder.section("verse", bars=8)
         .add_drums(lambda d: d.four_on_floor().backbeat().eighth_hats())
         .add_bass(lambda b: b.line([('E2', 0, 8), ('B2', 0, 8)]))
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

"""
Example 7: Expression & Groove
Demonstrates: Humanizer, GrooveTemplate, VelocityCurve
"""
from beatmaker import (
    create_song, Humanizer, GrooveTemplate, VelocityCurve
)

# Create custom groove template
swing_groove = GrooveTemplate.mpc_swing(amount=0.67)

# Humanizer for realistic timing
humanizer = Humanizer(timing_jitter=0.015, velocity_variation=0.12, seed=42)

song = (create_song("Groove Study")
        .tempo(95)  # Hip-hop tempo
        .bars(8)
        .add_drums(lambda d: d
                   .use_kit_from("drums/boom_bap")
                   .kick(beats=[0, 1.8, 2, 3.2])  # Boom-bap kick pattern
                   .snare(beats=[1, 3])
                   .hihat(beats=[0.5, 1.5, 2.5, 3.5])
                   .humanize(0.02, 0.15)  # Micro-timing shifts
                   .groove(GrooveTemplate.hip_hop())  # Apply hip-hop groove
                   )
        .add_bass(lambda b: b
                  .line([('G2', 0, 1.5), ('D2', 1.5, 1.5), ('F2', 3, 1)])
                  # Apply velocity shaping
                  .apply_velocity_curve(VelocityCurve.exponential)
                  )
        .build())

# Apply groove to existing MIDI or events
events = [(0, 36, 0.9, 0.25), (1, 38, 0.8, 0.25)]
humanized = humanizer.apply_to_events(events, bpm=95)
swung = swing_groove.apply_to_events(humanized, bpm=95)

"""
Example 8: MIDI Import/Export Workflow
Demonstrates: MIDI I/O, conversion, integration with DAWs
"""
from beatmaker import (
    load_midi, save_midi, song_to_midi,
    midi_to_beatmaker_events, beatmaker_events_to_midi
)
from beatmaker.midi import create_midi, MIDIFile

# Import MIDI file and convert to beatmaker events
midi_in = load_midi("drums_import.mid")
drum_events = midi_to_beatmaker_events(midi_in, track_index=0)

# Create song from imported MIDI
song = (create_song("MIDI Remixed")
        .tempo(midi_in.tempo)
        .add_drums(lambda d: d
                   # Use events from MIDI but replace samples
                   .use_kit_from("drums/modern")
                   .from_events(drum_events)  # Assuming this method exists
                   .effect(BitCrusher(bit_depth=8))  # Lo-fi effect
                   )
        .add_harmony(lambda h: h
                     .key("Am")
                     .progression("i - VII - VI - V")
                     , synth_type='warm_pad')
        .build())

# Export back to MIDI for DAW editing
midi_out = song_to_midi(song, include_drums=True)
save_midi(midi_out, "export_for_daw.mid")

# Create MIDI from scratch programmatically
midi = create_midi(bpm=140, ticks_per_beat=960)
track = midi.add_track("Bass", channel=1)
track.add_note(36, 100, 0, midi.beats_to_ticks(1.0))  # C2
track.add_note(43, 100, midi.beats_to_ticks(1.0), midi.beats_to_ticks(1.0))  # G2
save_midi(midi, "programmatic.mid")

"""
Example 9: Audio Analysis & Processing
Demonstrates: BPM detection, slicing, stretching
"""
from beatmaker.utils import (
    load_audio, detect_bpm, slice_at_onsets,
    time_stretch, pitch_shift, extract_samples_from_file
)
from beatmaker.io import save_audio

# Analyze loop
loop = load_audio("breakbeat.wav")
detected_bpm = detect_bpm(loop, min_bpm=80, max_bpm=150)
print(f"Detected BPM: {detected_bpm}")

# Slice drum break into individual hits
samples = extract_samples_from_file("breakbeat.wav", prefix="break", min_duration=0.05)

# Time stretch to match project tempo
target_bpm = 128
ratio = detected_bpm / target_bpm
stretched = time_stretch(loop, ratio)

# Pitch shift bass sample
bass = load_audio("bass_line.wav")
shifted = pitch_shift(bass, semitones=-2)  # Drop 2 semitones
save_audio(shifted, "bass_dropped.wav")

"""
Example 10: Complete Production Template
Combines all features into a professional workflow
"""
from beatmaker import create_song, SampleLibrary
from beatmaker.effects import EffectChain, Compressor, Reverb, Limiter
from beatmaker.expression import GrooveTemplate
from beatmaker.sidechain import PumpingBass


class ProjectTemplate:
    def __init__(self, name, bpm=128):
        self.song = create_song(name).tempo(bpm)
        self.lib = SampleLibrary.from_directory("./samples")
        self.setup_master_chain()

    def setup_master_chain(self):
        self.song.master_effect(EffectChain(
            Compressor(threshold=-16, ratio=2.0),  # Glue compression
            Reverb(room_size=0.3, mix=0.15),  # Subtle room
            Limiter(threshold=0.95)  # Safety limiter
        ))

    def add_section(self, name, bars, drum_pattern, bass_notes, chords=None):
        section = self.song.section(name, bars)

        # Drums with groove
        section.add_drums(lambda d: d
                          .use_kit_from("drums/pro")
                          .apply_pattern(drum_pattern)
                          .groove(GrooveTemplate.mpc_swing(0.6))
                          .humanize(0.01, 0.08)
                          )

        # Bass with sidechain
        section.add_bass(lambda b: b
                         .line(bass_notes)
                         .effect(PumpingBass(self.song._bpm, depth=0.8))
                         )

        if chords:
            section.add_harmony(lambda h: h
                                .key(*chords['key'])
                                .progression(chords['progression'])
                                .voice_lead()
                                , synth_type='warm_pad')

        return section.build()

    def render(self, path):
        self.song.build().export(path)


# Usage
project = ProjectTemplate("My Track", bpm=130)
verse = project.add_section(
    "verse", 16,
    drum_pattern={'kick': [0, 2], 'snare': [1, 3], 'hat': 'eighths'},
    bass_notes=[('C2', 0, 4), ('G2', 4, 4)],
    chords={'key': ('C', 'major'), 'progression': 'I - V - vi - IV'}
)
# ... build arrangement with sections ...
project.render("final_mix.wav")