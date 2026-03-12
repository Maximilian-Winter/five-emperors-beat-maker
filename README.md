# 靈寶五帝策使編碼之法
# The Five Emperors Beat Maker 🎵

**Version 0.2.0** - A Python library for creating beats and songs with a fluent builder pattern.

## 🐉 The Five Emperors

Each aspect of audio production is governed by a cosmic authority:

| Emperor | Element | Domain | Governs |
|---------|---------|--------|---------|
| 🐉 Azure Emperor (East) | Wood | Architecture | Structure, API design |
| 🔥 Vermilion Emperor (South) | Fire | Performance | Optimization, synthesis |
| 🌍 Yellow Emperor (Center) | Earth | Integration | Mixing, effects chains |
| 🐅 White Emperor (West) | Metal | Debugging | Quality, validation |
| 🐢 Black Emperor (North) | Water | Data | Audio I/O, MIDI, samples |

## What's New in v0.2

- **Step Sequencer** - TR-808/909 style pattern programming
- **Euclidean Rhythms** - Mathematical rhythm generation
- **Arpeggiator** - Melodic pattern generation with chord progressions
- **Sidechain Compression** - Classic pumping effects
- **Extended Synths** - Pads, Leads, Plucks, and FX sounds
- **MIDI Import/Export** - Full MIDI file support

## Installation

```bash
# Copy the beatmaker directory to your project
pip install numpy scipy pydub
```

## Quick Start

```python
from beatmaker import create_song, DrumSynth

song = (create_song("My House Beat")
    .tempo(128)
    .bars(4)
    .add_drums(lambda d: d
        .four_on_floor()
        .backbeat()
        .eighth_hats()
    )
    .add_bass(lambda b: b
        .note('E2', beat=0, duration=1)
        .note('G2', beat=2, duration=1)
    )
    .master_limiter()
    .build()
)

song.export("my_beat.wav")
```

## Core Concepts

### 🎼 Song Structure

```python
Song
├── Tracks (Drums, Bass, Vocals, etc.)
│   ├── Sample Placements (time, velocity, pan)
│   └── Effects Chain
└── Master Bus
    └── Master Effects
```

### 📦 The Builder Pattern

The library uses a fluent builder pattern for intuitive composition:

```python
song = (create_song("Name")
    .tempo(120)                    # Set BPM
    .time_signature(4, 4)          # Set time signature
    .bars(4)                       # Pattern length
    .add_drums(lambda d: ...)      # Add drum track
    .add_bass(lambda b: ...)       # Add bass track
    .add_vocal(path)               # Add vocal from file
    .add_backing_track(path)       # Add backing track
    .master_effect(effect)         # Add master bus effect
    .build()                       # Build the song
)
```

## Drum Track Builder

```python
.add_drums(lambda d: d
    # Use custom samples
    .use_kit(kick=my_kick, snare=my_snare, hihat=my_hat)
    
    # Pattern by beat positions
    .kick(beats=[0, 2])           # Kicks on beats 1 and 3
    .snare(beats=[1, 3])          # Snares on beats 2 and 4
    .hihat(beats=[0, 0.5, 1, ...]) # Hi-hats
    
    # Or use step sequencer pattern (16 steps)
    .kick(pattern=[True, False, False, False, ...])
    
    # Convenience patterns
    .four_on_floor()              # Kick on every beat
    .backbeat()                   # Snare on 2 and 4
    .eighth_hats()                # 8th note hi-hats
    .sixteenth_hats()             # 16th note hi-hats
    
    # Track settings
    .volume(0.9)
    .pan(-0.3)                    # Pan left
    .effect(Compressor())
)
```

## Bass Track Builder

```python
.add_bass(lambda b: b
    # Add notes
    .note('E2', beat=0, duration=1)
    .note('G2', beat=1, duration=0.5)
    
    # Add acid-style bass
    .acid_note('E2', beat=2, duration=0.25)
    
    # Add a full bass line
    .line([
        ('E2', 0, 1),      # (note, beat, duration)
        ('G2', 1, 0.5),
        ('A2', 1.5, 0.5),
    ])
    
    # Octave patterns
    .octave_pattern('E2', beats=[0, 0.5, 1, 1.5])
)
```

## Synthesis

### Drum Synthesizer

```python
from beatmaker import DrumSynth

kick = DrumSynth.kick(duration=0.5, pitch=60, punch=0.8)
snare = DrumSynth.snare(duration=0.3, noise_amount=0.6)
hihat = DrumSynth.hihat(duration=0.1, open_amount=0.0)  # 0=closed, 1=open
clap = DrumSynth.clap(duration=0.2, spread=0.02)
```

### Bass Synthesizer

```python
from beatmaker import BassSynth, ADSREnvelope

# Pure sub bass
sub = BassSynth.sub_bass(frequency=55, duration=1.0)

# Acid bass (303-style)
acid = BassSynth.acid_bass(frequency=110, duration=0.5)

# With custom envelope
envelope = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.7, release=0.2)
bass = BassSynth.sub_bass(55, 1.0, envelope=envelope)
```

### Wave Generators

```python
from beatmaker import sine_wave, square_wave, sawtooth_wave, triangle_wave

audio = sine_wave(440, duration=1.0)        # 440Hz sine for 1 second
audio = square_wave(220, duration=0.5)      # Square wave
audio = sawtooth_wave(110, duration=0.5)    # Sawtooth wave
audio = white_noise(duration=0.2)           # White noise
audio = pink_noise(duration=0.5)            # Pink noise (1/f)
```

## Effects

```python
from beatmaker import (
    Gain, Limiter, SoftClipper,
    Delay, Reverb, Chorus,
    LowPassFilter, HighPassFilter,
    Compressor, BitCrusher,
    EffectChain
)

# Individual effects
track.effect(Gain(level=0.8))
track.effect(Gain.from_db(-3))              # -3 dB
track.effect(Limiter(threshold=0.95))
track.effect(SoftClipper(drive=1.5))

# Delay
track.effect(Delay(delay_time=0.25, feedback=0.3, mix=0.5))

# Reverb
track.effect(Reverb(room_size=0.6, damping=0.5, mix=0.3))

# Filters
track.effect(LowPassFilter(cutoff=1000))
track.effect(HighPassFilter(cutoff=100))

# Dynamics
track.effect(Compressor(threshold=-10, ratio=4, attack=0.01, release=0.1))

# Lo-fi
track.effect(BitCrusher(bit_depth=8, sample_hold=2))

# Chain multiple effects
chain = EffectChain(
    HighPassFilter(80),
    Compressor(threshold=-8, ratio=3),
    Reverb(room_size=0.3, mix=0.2)
)
track.effect(chain)
```

## Sample Management

### Loading Samples

```python
from beatmaker import Sample, load_audio, SampleLibrary

# Load single sample
kick = Sample.from_file("kick.wav")

# Load with tags
kick = Sample.from_file("kick.wav").with_tags("drums", "kick")

# Load entire directory
library = SampleLibrary()
library.load_directory("samples/drums", tags=["drums"])

# Access samples
kick = library["kick_01"]
all_kicks = library.by_tag("kick")
```

### Extracting Samples

```python
from beatmaker import extract_samples_from_file, detect_bpm, detect_onsets

# Extract individual hits from a drum loop
samples = extract_samples_from_file("drum_loop.wav", prefix="hit")

# Detect BPM
bpm = detect_bpm(audio)

# Find onset times
onsets = detect_onsets(audio, threshold=0.1)
```

## Audio Utilities

```python
from beatmaker import (
    time_stretch, pitch_shift, reverse, loop,
    crossfade, concatenate, mix,
    split_stereo, merge_to_stereo
)

# Time stretch (factor > 1 = slower)
stretched = time_stretch(audio, factor=1.5)

# Pitch shift in semitones
shifted = pitch_shift(audio, semitones=5)

# Other operations
reversed_audio = reverse(audio)
looped = loop(audio, times=4)
mixed = mix(track1, track2, track3, volumes=[1.0, 0.8, 0.6])
joined = concatenate(intro, verse, chorus)
smooth = crossfade(part1, part2, duration=0.1)

# Stereo operations
left, right = split_stereo(stereo_audio)
stereo = merge_to_stereo(left, right)
```

## Loading External Audio

```python
# Load vocals
song = (create_song("Song with Vocals")
    .tempo(120)
    .add_vocal("vocals.wav", start_bar=4, volume=1.0)
    .add_backing_track("instrumental.wav", start_bar=0, volume=0.7)
    .build()
)
```

## Full Example: Complete Track

```python
from beatmaker import (
    create_song, DrumSynth, BassSynth,
    Reverb, Delay, Compressor, LowPassFilter
)

# Create custom drum kit
kick = DrumSynth.kick(pitch=55, punch=0.7)
snare = DrumSynth.snare(noise_amount=0.5)
hihat = DrumSynth.hihat(duration=0.08)

song = (create_song("Full Track")
    .tempo(124)
    .time_signature(4, 4)
    .bars(8)
    
    # Drums with effects
    .add_drums(lambda d: d
        .use_kit(kick=kick, snare=snare, hihat=hihat)
        .kick(beats=[0, 2.5])
        .snare(beats=[1, 3])
        .hihat(beats=[i * 0.5 for i in range(8)])
        .clap(beats=[1, 3])
        .effect(Compressor(threshold=-6, ratio=4))
        .volume(0.9)
    )
    
    # Bass line
    .add_bass(lambda b: b
        .line([
            ('E2', 0, 1),
            ('E2', 1.5, 0.5),
            ('G2', 2, 1),
            ('A2', 3.5, 0.5),
        ])
        .effect(LowPassFilter(cutoff=400))
        .volume(0.85)
    )
    
    # Master chain
    .master_effect(Reverb(room_size=0.2, mix=0.1))
    .master_effect(Compressor(threshold=-8, ratio=3))
    .master_limiter(0.95)
    
    .build()
)

# Export
song.export("full_track.wav")
print(f"Exported {song.duration:.1f}s track at {song.bpm} BPM")
```

## API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `AudioData` | Raw audio samples with sample rate and channel info |
| `Sample` | Named audio with metadata and tags |
| `Track` | Collection of sample placements with effects |
| `Song` | Complete composition with multiple tracks |

### Builder Classes

| Class | Description |
|-------|-------------|
| `SongBuilder` | Fluent builder for creating songs |
| `DrumTrackBuilder` | Specialized builder for drum patterns |
| `BassTrackBuilder` | Specialized builder for bass lines |
| `TrackBuilder` | Base builder for generic tracks |

### Synthesizers

| Class/Function | Description |
|----------------|-------------|
| `DrumSynth` | Kick, snare, hihat, clap synthesis |
| `BassSynth` | Sub bass and acid bass synthesis |
| `PadSynth` | Warm, string, and ambient pads |
| `LeadSynth` | Saw, square, and FM leads |
| `PluckSynth` | Karplus-Strong, synth plucks, bells |
| `FXSynth` | Risers, downers, impacts, sweeps |
| `Oscillator` | Configurable oscillator |
| `ADSREnvelope` | Envelope generator |

### Effects

| Effect | Parameters |
|--------|------------|
| `Gain` | level |
| `Limiter` | threshold |
| `SoftClipper` | drive |
| `Delay` | delay_time, feedback, mix |
| `Reverb` | room_size, damping, mix |
| `LowPassFilter` | cutoff |
| `HighPassFilter` | cutoff |
| `Compressor` | threshold, ratio, attack, release, makeup_gain |
| `BitCrusher` | bit_depth, sample_hold |
| `Chorus` | rate, depth, mix, voices |
| `SidechainEnvelope` | bpm, pattern, depth, attack, release |
| `SidechainCompressor` | threshold, ratio, attack, release, range |

---

## 🥁 Step Sequencer (NEW in v0.2)

TR-808/909 style step programming:

```python
from beatmaker import StepSequencer, Pattern, ClassicPatterns, DrumSynth

# Create sequencer
seq = StepSequencer(bpm=128, steps_per_beat=4, swing=0.1)

# Add patterns using string notation
# x=hit, X=accent, o=ghost, r=roll, .=rest
seq.add_pattern('kick', Pattern.from_string("x...x...x...x.x."), DrumSynth.kick())
seq.add_pattern('snare', Pattern.from_string("....X.......X..."), DrumSynth.snare())
seq.add_pattern('hihat', Pattern.from_string("x.x.x.x.x.x.x.x."), DrumSynth.hihat())

# Use classic presets
seq.load_kit(ClassicPatterns.house_kit(), samples)

# Render to track
drum_track = seq.render_to_track(bars=4, name="Drums")
```

### Pattern Operations

```python
# Create patterns different ways
p1 = Pattern.from_string("x...x...x...x...")
p2 = Pattern.from_list([True, False, False, False] * 4)
p3 = Pattern.from_positions([0, 4, 8, 12], length=16)

# Transform patterns
rotated = p1.rotate(2)      # Shift by 2 steps
reversed = p1.reverse()     # Reverse
stretched = p1.stretch(2)   # Double length
combined = p1.combine(p2, mode='or')  # Combine patterns
```

---

## 🌀 Euclidean Rhythms (NEW in v0.2)

Generate mathematically distributed rhythms:

```python
from beatmaker import EuclideanPattern

# E(hits, steps) - distribute hits evenly across steps
tresillo = EuclideanPattern.generate(3, 8)    # Cuban tresillo
cinquillo = EuclideanPattern.generate(5, 8)   # Cuban cinquillo
bembe = EuclideanPattern.generate(7, 12)      # West African bell

# With rotation
aksak = EuclideanPattern.generate(4, 9, rotation=2)

# Common patterns
patterns = EuclideanPattern.common_patterns()
# Returns: tresillo, cinquillo, bembé, aksak, rumba, soukous
```

---

## 🎹 Arpeggiator (NEW in v0.2)

Create melodic patterns from chords and scales:

```python
from beatmaker import (
    create_arpeggiator, Arpeggiator, ArpDirection, 
    ChordShape, Scale, ArpSynthesizer
)

# Build arpeggiator with fluent API
arp = (create_arpeggiator()
    .tempo(130)
    .up_down()              # Direction: UP, DOWN, UP_DOWN, RANDOM
    .sixteenth()            # Rate: sixteenth(), eighth(), quarter()
    .gate(0.7)              # Note length (0-1)
    .octaves(2)             # Span octaves
    .accent_downbeat()      # Velocity pattern
    .build()
)

# Generate from chord
events = arp.generate_from_chord('A2', ChordShape.MINOR, beats=4)

# Generate from scale
events = arp.generate_from_scale('C3', Scale.MINOR_PENTATONIC, beats=4)

# Chord progression
progression = [
    ('A2', ChordShape.MINOR),
    ('F2', ChordShape.MAJOR),
    ('C3', ChordShape.MAJOR),
    ('G2', ChordShape.MAJOR),
]
events = arp.generate_from_progression(progression, beats_per_chord=4)

# Render to audio
synth = ArpSynthesizer(waveform='saw')  # sine, saw, square, triangle
audio = synth.render_events(events)
```

### Available Chords & Scales

```python
# Chords
ChordShape.MAJOR, ChordShape.MINOR, ChordShape.DIM, ChordShape.AUG
ChordShape.SUS2, ChordShape.SUS4
ChordShape.MAJOR7, ChordShape.MINOR7, ChordShape.DOM7, ChordShape.ADD9

# Scales
Scale.MAJOR, Scale.MINOR, Scale.DORIAN, Scale.PHRYGIAN
Scale.LYDIAN, Scale.MIXOLYDIAN, Scale.LOCRIAN
Scale.MINOR_PENTATONIC, Scale.MAJOR_PENTATONIC, Scale.BLUES
Scale.HARMONIC_MINOR, Scale.MELODIC_MINOR
```

---

## 💨 Sidechain Pumping (NEW in v0.2)

Classic EDM pumping effect:

```python
from beatmaker import (
    SidechainEnvelope, SidechainPresets, create_sidechain
)

# Quick presets
pump = SidechainPresets.classic_house(bpm=128)
pump = SidechainPresets.heavy_edm(bpm=128)
pump = SidechainPresets.subtle_groove(bpm=120)

# Apply to audio
pumped_pad = pump.process(pad_audio)

# Custom sidechain with builder
sidechain = (create_sidechain()
    .tempo(128)
    .depth(0.7)           # How much to duck (0-1)
    .quarter_notes()      # Pattern: quarter_notes(), eighth_notes()
    .release(0.3)         # Release time
    .shape_exp()          # Shape: shape_exp(), shape_linear(), shape_log()
    .build()
)

# True sidechain from trigger audio
from beatmaker import SidechainCompressor
sc = SidechainCompressor(threshold=-20, ratio=8, release=0.15)
sc.set_trigger(kick_audio)
ducked = sc.process(bass_audio)
```

---

## 🎛️ Extended Synthesizers (NEW in v0.2)

### Pads

```python
from beatmaker import PadSynth, create_pad

# Quick creation
pad = create_pad('E3', duration=8, pad_type='warm')

# Detailed control
pad = PadSynth.warm_pad(frequency=164.81, duration=8, 
                        num_voices=6, detune=0.15)
pad = PadSynth.string_pad(frequency=220, duration=4)
pad = PadSynth.ambient_pad(frequency=110, duration=10)
```

### Leads

```python
from beatmaker import LeadSynth, create_lead

lead = create_lead('E4', duration=0.5, lead_type='saw')

lead = LeadSynth.saw_lead(frequency=440, duration=0.5, filter_env=True)
lead = LeadSynth.square_lead(frequency=440, duration=0.5, pulse_width=0.3)
lead = LeadSynth.fm_lead(frequency=440, duration=0.5, 
                         mod_ratio=2.0, mod_index=3.0)
```

### Plucks

```python
from beatmaker import PluckSynth, create_pluck

pluck = create_pluck('G4', duration=1, pluck_type='karplus')

pluck = PluckSynth.karplus_strong(frequency=392, duration=1, brightness=0.7)
pluck = PluckSynth.synth_pluck(frequency=392, duration=0.5)
bell = PluckSynth.bell(frequency=523, duration=2)
```

### FX Sounds

```python
from beatmaker import FXSynth

riser = FXSynth.riser(duration=4, start_freq=100, end_freq=2000)
downer = FXSynth.downer(duration=2, start_freq=2000, end_freq=50)
impact = FXSynth.impact()
sweep = FXSynth.noise_sweep(duration=3)
```

---

## 📄 MIDI Import/Export (NEW in v0.2)

Full MIDI file support:

```python
from beatmaker import (
    load_midi, save_midi, create_midi,
    song_to_midi, midi_to_beatmaker_events
)

# Load MIDI file
midi = load_midi("song.mid")
print(f"Tempo: {midi.tempo} BPM")
print(f"Tracks: {len(midi.tracks)}")

# Convert MIDI to events for processing
events = midi_to_beatmaker_events(midi, track_index=0)
# Returns: [(time, midi_note, velocity, duration), ...]

# Create MIDI programmatically
midi = create_midi(bpm=120)
track = midi.add_track("Lead", channel=0)

# Add notes
track.add_note(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
track.add_note(pitch=64, velocity=90, start_tick=480, duration_ticks=480)

# Save
save_midi(midi, "output.mid")

# Convert Song to MIDI
song = create_song("My Song").tempo(120).add_drums(...).build()
midi = song_to_midi(song)
save_midi(midi, "my_song.mid")
```

---

## Complete Example: Full Track with All Features

```python
from beatmaker import (
    Song, Track, TrackType, create_song,
    StepSequencer, Pattern, DrumSynth,
    PadSynth, LeadSynth, PluckSynth,
    create_arpeggiator, ChordShape, ArpSynthesizer,
    SidechainPresets,
    Reverb, Delay, Compressor, LowPassFilter,
    save_midi, song_to_midi,
    note_to_freq
)

bpm = 126
song = Song(name="Complete Track", bpm=bpm)

# 1. Drums via Step Sequencer
seq = StepSequencer(bpm=bpm, swing=0.05)
seq.add_pattern('kick', Pattern.from_string("x...x...x...x.x."), DrumSynth.kick())
seq.add_pattern('snare', Pattern.from_string("....x.......x..."), DrumSynth.snare())
seq.add_pattern('hihat', Pattern.from_string("..x...x...x...x."), DrumSynth.hihat())
drum_track = seq.render_to_track(bars=8)
song.add_track(drum_track)

# 2. Pad with Sidechain
pad = PadSynth.warm_pad(note_to_freq('E2'), duration=16)
sidechain = SidechainPresets.classic_house(bpm)
pad_pumped = sidechain.process(pad.audio)
pad_track = Track(name="Pad", track_type=TrackType.PAD, volume=0.4)
pad_track.add(Sample("pad", pad_pumped), 0)
pad_track.add_effect(Reverb(room_size=0.5, mix=0.3))
song.add_track(pad_track)

# 3. Arpeggio
arp = create_arpeggiator().tempo(bpm).up().sixteenth().build()
events = arp.generate_from_chord('E2', ChordShape.MINOR, beats=32)
synth = ArpSynthesizer(waveform='saw')
arp_audio = synth.render_events(events)
arp_track = Track(name="Arp", track_type=TrackType.LEAD, volume=0.35)
arp_track.add(Sample("arp", arp_audio), 0)
song.add_track(arp_track)

# 4. Lead melody
lead_track = Track(name="Lead", track_type=TrackType.LEAD, volume=0.5)
melody = [('E4', 0, 0.5), ('G4', 0.5, 0.5), ('A4', 1, 1)]
for note, beat, dur in melody:
    lead = LeadSynth.fm_lead(note_to_freq(note), dur)
    lead_track.add(lead, beat * (60/bpm))
song.add_track(lead_track)

# Master chain
song.master_effects.append(Compressor(threshold=-6, ratio=3))

# Export
song.export("complete_track.wav")
save_midi(song_to_midi(song), "complete_track.mid")
```

## 急急如律令敕
*Urgent as the Cosmic Law Commands!*

The Five Emperors have spoken. May your beats be tight and your mixes clean! 🎧