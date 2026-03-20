# The Five Emperors Beat Maker

**v0.4.0** — A Python library for creating beats and songs with a fluent builder pattern.

```bash
pip install beatmaker
```

Dependencies: `numpy`, `tqdm`. Optional: `pydub` (for MP3/OGG/FLAC), `beatmaker-spc700` (SNES sound chip).

## Quick Start

```python
from beatmaker import create_song, Reverb, Compressor

song = (create_song("My Beat")
    .tempo(128)
    .bars(4)
    .add_drums(lambda d: d
        .four_on_floor()
        .backbeat()
        .eighth_hats()
        .volume(0.9)
        .effect(Compressor(threshold=-6, ratio=4))
    )
    .add_bass(lambda b: b
        .note('E2', beat=0, duration=1)
        .note('G2', beat=2, duration=1)
    )
    .master_effect(Reverb(room_size=0.2, mix=0.1))
    .master_limiter()
    .build()
)

song.export("my_beat.wav")
```

## Architecture

```
Song
 ├── Track (Drums)
 │    ├── SamplePlacements (kick at beat 0, snare at beat 1, ...)
 │    └── EffectChain (Compressor, EQ, ...)
 ├── Track (Bass)
 │    ├── SamplePlacements (synthesized notes)
 │    └── EffectChain
 ├── Track (Lead / Pad / FX / ...)
 └── Master Bus
      └── Master Effects (Reverb, Limiter)
```

Everything is built around `AudioData` (raw samples + sample rate) and `Sample` (named AudioData with metadata). Tracks hold `SamplePlacements` at specific times. Songs hold tracks and render them to a stereo mixdown.

## The Builder Pattern

The primary API is a fluent builder chain starting with `create_song()`:

```python
song = (create_song("Name")
    .tempo(120)                    # BPM
    .time_signature(4, 4)          # beats per bar, beat value
    .bars(4)                       # pattern length
    .samples(library)              # attach a SampleLibrary
    .add_drums(lambda d: ...)      # DrumTrackBuilder
    .add_bass(lambda b: ...)       # BassTrackBuilder
    .add_track("Lead", TrackType.LEAD, lambda t: ...)  # generic
    .master_effect(Reverb(...))    # master bus effect
    .master_limiter(0.95)          # final limiter
    .build()                       # returns Song
)
```

### Drum Track Builder

```python
.add_drums(lambda d: d
    .use_kit(kick=my_kick, snare=my_snare, hihat=my_hat)
    .kick(beats=[0, 2])
    .snare(beats=[1, 3])
    .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
    .four_on_floor()          # kick on every beat
    .backbeat()               # snare on 2 and 4
    .eighth_hats()            # 8th note hi-hats
    .sixteenth_hats()         # 16th note hi-hats
    .volume(0.9)
    .pan(-0.1)
    .effect(Compressor(...))
)
```

### Bass Track Builder

```python
.add_bass(lambda b: b
    .note('E2', beat=0, duration=1)
    .note('G2', beat=1, duration=0.5)
    .acid_note('E2', beat=2, duration=0.25)
    .line([('E2', 0, 1), ('G2', 1, 0.5), ('A2', 1.5, 0.5)])
    .octave_pattern('E2', beats=[0, 0.5, 1, 1.5])
    .effect(LowPassFilter(cutoff=400))
)
```

### Melody & Harmony Track Builders

```python
# Melody from Phrase notation
.add_track("Lead", TrackType.LEAD, lambda t:
    MelodyTrackBuilder(t._track, t._song)
        .phrase(Phrase.from_string("C4:1 E4:0.5 G4:0.5 R:1 C5:2"))
        .waveform('saw')
)

# Harmony from chord progressions
.add_track("Chords", TrackType.PAD, lambda t:
    HarmonyTrackBuilder(t._track, t._song)
        .progression(Key.major("C"), "I - IV - V - I")
)
```

## Synthesis

```python
from beatmaker import DrumSynth, BassSynth, PadSynth, LeadSynth, PluckSynth, FXSynth

# Drums
kick  = DrumSynth.kick(duration=0.5, pitch=60, punch=0.8)
snare = DrumSynth.snare(duration=0.3, noise_amount=0.6)
hihat = DrumSynth.hihat(duration=0.1, open_amount=0.0)
clap  = DrumSynth.clap(duration=0.2, spread=0.02)

# Bass
sub  = BassSynth.sub_bass(frequency=55, duration=1.0)
acid = BassSynth.acid_bass(frequency=110, duration=0.5)

# Pads, Leads, Plucks, FX
pad   = PadSynth.warm_pad(frequency=164.81, duration=8, num_voices=6)
lead  = LeadSynth.fm_lead(frequency=440, duration=0.5, mod_ratio=2.0)
pluck = PluckSynth.karplus_strong(frequency=392, duration=1, brightness=0.7)
riser = FXSynth.riser(duration=4, start_freq=100, end_freq=2000)

# Quick creation helpers
from beatmaker import create_pad, create_lead, create_pluck
pad   = create_pad('E3', duration=8, pad_type='warm')
lead  = create_lead('A4', duration=0.5, lead_type='saw')
pluck = create_pluck('G4', duration=1, pluck_type='karplus')

# Raw waveforms
from beatmaker import sine_wave, square_wave, sawtooth_wave, triangle_wave, white_noise
audio = sine_wave(440, duration=1.0)
audio = sawtooth_wave(110, duration=0.5)

# Oscillator with envelope
from beatmaker import Oscillator, ADSREnvelope, Waveform
osc = Oscillator(waveform=Waveform.SAWTOOTH, detune=5.0)
audio = osc.generate(440, duration=1.0)
env = ADSREnvelope(attack=0.01, decay=0.1, sustain=0.7, release=0.2)
audio = env.apply(audio)
```

## Effects

```python
from beatmaker import (
    Gain, Limiter, SoftClipper, Delay, Reverb, Chorus,
    LowPassFilter, HighPassFilter, Compressor, BitCrusher, EffectChain
)

# Apply to tracks
track.effect(Gain(level=0.8))
track.effect(Gain.from_db(-3))
track.effect(Delay(delay_time=0.25, feedback=0.3, mix=0.5))
track.effect(Reverb(room_size=0.6, damping=0.5, mix=0.3))
track.effect(LowPassFilter(cutoff=1000))
track.effect(Compressor(threshold=-10, ratio=4, attack=0.01, release=0.1))
track.effect(BitCrusher(bit_depth=8, sample_hold=2))

# Chain multiple effects
chain = EffectChain(HighPassFilter(80), Compressor(threshold=-8, ratio=3), Reverb(room_size=0.3, mix=0.2))
track.effect(chain)
```

### Sidechain Compression

```python
from beatmaker import SidechainPresets, SidechainCompressor, create_sidechain

# Presets
pump = SidechainPresets.classic_house(bpm=128)
pumped_pad = pump.process(pad_audio)

# Custom
sidechain = (create_sidechain()
    .tempo(128).depth(0.7).quarter_notes().release(0.3).shape_exp()
    .build())

# True sidechain from trigger signal
sc = SidechainCompressor(threshold=-20, ratio=8, release=0.15)
sc.set_trigger(kick_audio)
ducked = sc.process(bass_audio)
```

## Step Sequencer

```python
from beatmaker import StepSequencer, Pattern, ClassicPatterns, EuclideanPattern, DrumSynth

seq = StepSequencer(bpm=128, steps_per_beat=4, swing=0.1)

# String notation: x=hit, X=accent, o=ghost, r=roll, .=rest
seq.add_pattern('kick',  Pattern.from_string("x...x...x...x.x."), DrumSynth.kick())
seq.add_pattern('snare', Pattern.from_string("....X.......X..."), DrumSynth.snare())
seq.add_pattern('hihat', Pattern.from_string("x.x.x.x.x.x.x.x."), DrumSynth.hihat())

drum_track = seq.render_to_track(bars=4, name="Drums")

# Pattern operations
rotated  = pattern.rotate(2)
reversed = pattern.reverse()
combined = p1.combine(p2, mode='or')

# Euclidean rhythms: distribute hits evenly across steps
tresillo = EuclideanPattern.generate(3, 8)    # Cuban tresillo
cinquillo = EuclideanPattern.generate(5, 8)   # Cuban cinquillo
```

## Arpeggiator

```python
from beatmaker import create_arpeggiator, ChordShape, Scale, ArpSynthesizer

arp = (create_arpeggiator()
    .tempo(130).up_down().sixteenth().gate(0.7).octaves(2)
    .build())

events = arp.generate_from_chord('A2', ChordShape.MINOR, beats=4)
events = arp.generate_from_scale('C3', Scale.MINOR_PENTATONIC, beats=4)
events = arp.generate_from_progression([
    ('A2', ChordShape.MINOR), ('F2', ChordShape.MAJOR),
    ('C3', ChordShape.MAJOR), ('G2', ChordShape.MAJOR),
], beats_per_chord=4)

audio = ArpSynthesizer(waveform='saw').render_events(events)
```

## Melody & Harmony

```python
from beatmaker import Note, Phrase, Melody, Key, ChordProgression

# Build melodies from concise notation
phrase = Phrase.from_string("C4:1 E4:0.5 G4:0.5 R:1 C5:2")
phrase2 = phrase.transpose(5).reverse().augment(2.0)
melody = Melody("lead").add(phrase).add(phrase2)
events = melody.to_events()  # [(beat, midi, velocity, duration), ...]

# Harmony
key = Key.major("C")
prog = ChordProgression.from_roman(key, "I - IV - V - vi")
```

## Arrangement & Automation

```python
from beatmaker import Section, Arrangement, AutomationCurve, CurveType

# Build song structure from sections
verse = Section("verse", bars=8)
verse.add_track(drum_track)
verse.add_track(bass_track)

chorus = Section("chorus", bars=8)
chorus.add_track(drum_track)
chorus.add_track(bass_track)
chorus.add_track(lead_track)

arr = Arrangement()
arr.intro(intro_section).verse(verse).chorus(chorus).verse(verse).chorus(chorus).outro(outro_section)

# Section variations
verse2 = verse.without_track("lead").with_volume("bass", 0.7)

# Automation
vol = AutomationCurve("volume").ramp(0, 8, 0.0, 1.0)  # fade in over 8 beats
filter_sweep = AutomationCurve("cutoff").ramp(0, 16, 200, 8000, CurveType.EXPONENTIAL)
```

## Expression

```python
from beatmaker import Vibrato, PitchBend, Humanizer, GrooveTemplate

vibrato = Vibrato(rate=5.0, depth=0.5, delay=0.1)
audio = vibrato.apply(audio, base_freq=440)

humanizer = Humanizer(timing_jitter=0.01, velocity_variation=0.1)
humanized = humanizer.apply_to_events(events, bpm=120)
```

## Signal Graph

Node-based audio routing for complex signal flows:

```python
from beatmaker import SignalGraph, AudioInput, GainNode, FilterNode, MixNode, GraphEffect

graph = SignalGraph(sample_rate=44100, duration=2.0)
with graph.context():
    src = AudioInput(audio_data)
    gain = GainNode(level=0.8)
    filt = FilterNode(cutoff=1000, filter_type='lowpass')
    src >> gain >> filt

output = graph.render()

# Use a graph as an effect
effect = GraphEffect(graph)
processed = effect.process(audio)
```

## MIDI

```python
from beatmaker import load_midi, save_midi, create_midi, song_to_midi

# Load and inspect
midi = load_midi("song.mid")

# Create programmatically
midi = create_midi(bpm=120)
track = midi.add_track("Lead")
track.add_note(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
save_midi(midi, "output.mid")

# Convert Song to MIDI
midi = song_to_midi(song)
save_midi(midi, "my_song.mid")
```

## Audio I/O & Utilities

```python
from beatmaker import (
    load_audio, save_audio, SampleLibrary, Sample,
    detect_bpm, time_stretch, pitch_shift, reverse, loop, mix, concatenate
)

# File I/O
audio = load_audio("sample.wav")
save_audio(audio, "output.wav")

# Sample library
library = SampleLibrary.from_directory("./samples")
kick = library["kick_01"]
drums = library.by_tag("drums")

# Utilities
bpm = detect_bpm(audio)
stretched = time_stretch(audio, factor=1.5)
shifted = pitch_shift(audio, semitones=5)
reversed_audio = reverse(audio)
looped = loop(audio, times=4)
mixed = mix(track1, track2, volumes=[1.0, 0.8])
```

## Package Structure

```
beatmaker/
    core.py              # AudioData, Sample, Track, Song fundamentals
    music.py             # Note/MIDI/frequency conversion, Scale, ChordShape
    builder.py           # SongBuilder, DrumTrackBuilder, BassTrackBuilder, ...
    synthesis/           # Waveforms, oscillators, DrumSynth, BassSynth, PadSynth, ...
    effects/             # Gain, Reverb, Delay, Compressor, sidechain, ...
    sequencer.py         # StepSequencer, Pattern, EuclideanPattern
    arpeggiator.py       # Arpeggiator, ArpeggiatorBuilder
    melody.py            # Note, Phrase, Melody
    harmony.py           # Key, ChordProgression
    automation.py        # AutomationCurve, AutomatedGain, AutomatedFilter
    arrangement.py       # Section, Arrangement
    expression.py        # Vibrato, PitchBend, Humanizer, GrooveTemplate
    graph/               # SignalGraph, node-based audio routing
    midi.py              # MIDI file I/O
    io.py                # Audio file I/O, SampleLibrary
    utils.py             # BPM detection, time stretch, pitch shift, ...
```

## Documentation

Detailed API reference for each module: [docs/](docs/)

- [Synthesis](docs/synthesis.md) — Waveforms, oscillators, drum/bass/pad/lead/pluck/FX synths
- [Effects](docs/effects.md) — Audio effects, sidechain compression, effect chains
- [Sequencing & Rhythm](docs/sequencing.md) — Step sequencer, patterns, euclidean rhythms, arpeggiator
- [Melody & Harmony](docs/melody_and_harmony.md) — Notes, phrases, melodies, keys, chord progressions
- [Arrangement & Expression](docs/arrangement.md) — Sections, song structure, automation, humanization
- [Signal Graph](docs/signal_graph.md) — Node-based audio routing
- [MIDI & I/O](docs/midi_and_io.md) — MIDI files, audio I/O, sample library, utilities
