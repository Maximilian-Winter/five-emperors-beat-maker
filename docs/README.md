# Beatmaker API Reference

**The Numinous Treasure Five Emperors Beat Maker** — a Python library for creating beats and songs with a fluent builder pattern.

> *Version 0.3.0*

---

## Quick Start

```python
from beatmaker import create_song, DrumSynth

song = (create_song("My Beat")
    .tempo(128)
    .bars(4)
    .add_drums(lambda d: d
        .four_on_floor()
        .backbeat()
        .eighth_hats()
    )
    .build())

song.export("my_beat.wav")
```

---

## Module Reference

The library is organized into the following modules, each documented in detail:

| Document | Modules | Description |
|----------|---------|-------------|
| [Core & I/O](core_and_io.md) | `core`, `io` | Foundational types (`AudioData`, `Sample`, `Track`, `TrackType`, `TimeSignature`, `NoteValue`), audio loading/saving, and `SampleLibrary` with aliases & configuration |
| [Builder](builder.md) | `builder` | Fluent builder pattern — `create_song()`, `SongBuilder`, `DrumTrackBuilder`, `BassTrackBuilder`, `MelodyTrackBuilder`, `HarmonyTrackBuilder`, `SectionBuilder`, and `Song` |
| [Synthesis](synthesis.md) | `synth`, `synths` | Waveform generators, `Oscillator`, `ADSREnvelope`, `DrumSynth`, `BassSynth`, `PadSynth`, `LeadSynth`, `PluckSynth`, `FXSynth`, `LFO`, `Filter` |
| [Effects](effects.md) | `effects`, `sidechain` | Audio effects (`Gain`, `Limiter`, `Delay`, `Reverb`, `Compressor`, `Chorus`, `BitCrusher`, etc.), `EffectChain`, sidechain compression & `PumpingBass` |
| [Sequencer & Arpeggiator](sequencer_and_arpeggiator.md) | `sequencer`, `arpeggiator` | `StepSequencer`, `Pattern`, `ClassicPatterns`, `EuclideanPattern`, `PolyrhythmGenerator`, `Arpeggiator`, `Scale`, `ChordShape` |
| [Melody, Harmony & Automation](melody_harmony_automation.md) | `melody`, `harmony`, `automation` | `Note`, `Phrase`, `Melody`, `Key`, `ChordProgression` (with Roman numerals & presets), `AutomationCurve`, `AutomatedGain`, `AutomatedFilter` |
| [Arrangement & Expression](arrangement_and_expression.md) | `arrangement`, `expression` | `Section`, `Arrangement`, `Transition`, `Vibrato`, `PitchBend`, `Portamento`, `Humanizer`, `GrooveTemplate`, `VelocityCurve` |
| [MIDI & Utilities](midi_and_utils.md) | `midi`, `utils` | MIDI read/write (`MIDIFile`, `MIDIReader`, `MIDIWriter`), MIDI-beatmaker conversion, BPM detection, onset detection, time stretch, pitch shift, and audio utilities |

---

## Architecture Overview

```
                    ┌──────────────┐
                    │  create_song │  Entry point
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  SongBuilder │  Fluent configuration
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──┐  ┌─────▼─────┐  ┌──▼────────┐
     │DrumTrack  │  │ BassTrack │  │MelodyTrack│  Track builders
     │Builder    │  │ Builder   │  │Builder    │
     └────────┬──┘  └─────┬─────┘  └──┬────────┘
              │            │            │
              │     ┌──────▼──────┐     │
              │     │   Synths    │     │
              ├────►│ DrumSynth   │◄────┤  Sound generation
              │     │ BassSynth   │     │
              │     │ PadSynth    │     │
              │     └─────────────┘     │
              │                         │
     ┌────────▼─────────────────────────▼──────┐
     │              Song (built)               │
     │  tracks[], bpm, bars, time_signature    │
     └─────────────────┬───────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
   ┌──────▼─────┐ ┌───▼────┐ ┌───▼──────┐
   │  Effects   │ │Arrange-│ │Expression│  Post-processing
   │  Chain     │ │ment    │ │Humanizer │
   └──────┬─────┘ └───┬────┘ └───┬──────┘
          │            │          │
          └────────────┼──────────┘
                       │
               ┌───────▼───────┐
               │   .export()   │  Output
               │   .to_midi()  │
               └───────────────┘
```

---

## Key Concepts

### The Builder Pattern

Everything flows through a fluent API:

```python
song = (create_song("Track")
    .tempo(140)
    .bars(8)
    .time_signature(4, 4)
    .add_drums(lambda d: d.four_on_floor().backbeat())
    .add_bass(lambda b: b.note("C2", beat=0).note("G2", beat=2))
    .build())
```

### Sample Library Integration

Load samples from disk and use them throughout the builder:

```python
from beatmaker import SampleLibrary, SampleLibraryConfig

lib = SampleLibrary.from_directory("./samples",
    config=SampleLibraryConfig(normalize=True, lazy=True))
lib.alias("kick", "drums/808/kick_hard")

song = (create_song("Sample Track")
    .tempo(128)
    .samples(lib)
    .add_drums(lambda d: d
        .use_kit_from("drums/808")
        .kick(beats=[0, 2])
    )
    .build())
```

### Sections & Arrangement

Build reusable sections and arrange them into full songs:

```python
from beatmaker import Section, Arrangement

verse = Section("verse", bars=8)
chorus = Section("chorus", bars=8)

arrangement = (Arrangement()
    .intro(verse.without_track("Bass"))
    .verse(verse, repeat=2)
    .chorus(chorus)
    .verse(verse)
    .chorus(chorus, repeat=2)
    .outro(chorus.with_volume("Drums", 0.5)))
```

### Chord Progressions & Melody

Compose with music theory:

```python
from beatmaker import Key, ChordProgression, Phrase, Melody

key = Key.major('C')
prog = ChordProgression.from_roman(key, "I - V - vi - IV")

melody = Melody("lead")
melody.add(Phrase.from_string("C4:1 E4:1 G4:2 A4:1 G4:1 E4:2"))
```

### Automation

Animate any parameter over time:

```python
from beatmaker import AutomationCurve, AutomatedFilter, CurveType

sweep = AutomationCurve.filter_sweep(0, 32, 200, 8000)
filt = AutomatedFilter(cutoff=200)
filt.automate('cutoff', sweep)
```

### Expression & Groove

Make it feel human:

```python
from beatmaker import Humanizer, GrooveTemplate

humanizer = Humanizer(timing_jitter=0.015, velocity_variation=0.1)
groove = GrooveTemplate.mpc_swing(amount=0.67)
```

### MIDI Import/Export

Bridge to DAWs and external tools:

```python
from beatmaker import load_midi, save_midi, song_to_midi

midi = load_midi("input.mid")
midi_out = song_to_midi(song)
save_midi(midi_out, "output.mid")
```

---

## All Exported Symbols

The complete public API, importable from `beatmaker`:

**Core:** `AudioData`, `Sample`, `Track`, `TrackType`, `TimeSignature`, `SamplePlacement`, `NoteValue`, `AudioEffect`

**Building:** `Song`, `SongBuilder`, `TrackBuilder`, `DrumTrackBuilder`, `BassTrackBuilder`, `MelodyTrackBuilder`, `HarmonyTrackBuilder`, `SectionBuilder`, `create_song`

**Synthesis:** `Waveform`, `Oscillator`, `ADSREnvelope`, `sine_wave`, `square_wave`, `sawtooth_wave`, `triangle_wave`, `white_noise`, `pink_noise`, `DrumSynth`, `BassSynth`, `midi_to_freq`, `freq_to_midi`, `note_to_freq`, `LFO`, `Filter`, `PadSynth`, `LeadSynth`, `PluckSynth`, `FXSynth`, `create_pad`, `create_lead`, `create_pluck`

**Effects:** `Gain`, `Limiter`, `SoftClipper`, `Delay`, `Reverb`, `LowPassFilter`, `HighPassFilter`, `Compressor`, `BitCrusher`, `Chorus`, `EffectChain`

**Sidechain:** `SidechainCompressor`, `SidechainEnvelope`, `PumpingBass`, `SidechainBuilder`, `SidechainPresets`, `create_sidechain`

**Sequencer:** `Step`, `Pattern`, `StepSequencer`, `ClassicPatterns`, `EuclideanPattern`, `PolyrhythmGenerator`, `StepValue`

**Arpeggiator:** `Arpeggiator`, `ArpeggiatorBuilder`, `ArpDirection`, `ArpMode`, `ChordShape`, `Scale`, `ArpSynthesizer`, `create_arpeggiator`, `arp_chord`, `arp_scale`, `note_name_to_midi`

**Melody:** `Note`, `Phrase`, `Melody`, `midi_to_note_name`

**Harmony:** `Key`, `ChordProgression`, `ChordEntry`

**Automation:** `AutomationCurve`, `AutomationPoint`, `CurveType`, `AutomatableEffect`, `AutomatedGain`, `AutomatedFilter`

**Arrangement:** `Section`, `Arrangement`, `ArrangementEntry`, `Transition`

**Expression:** `Vibrato`, `PitchBend`, `Portamento`, `NoteExpression`, `Humanizer`, `GrooveTemplate`, `VelocityCurve`

**MIDI:** `MIDIFile`, `MIDITrack`, `MIDINote`, `MIDIReader`, `MIDIWriter`, `load_midi`, `save_midi`, `create_midi`, `midi_to_beatmaker_events`, `beatmaker_events_to_midi`, `song_to_midi`

**I/O:** `load_audio`, `save_audio`, `load_samples_from_directory`, `SampleLibrary`, `SampleLibraryConfig`

**Utilities:** `detect_bpm`, `detect_onsets`, `slice_at_onsets`, `extract_samples_from_file`, `split_stereo`, `merge_to_stereo`, `time_stretch`, `pitch_shift`, `reverse`, `loop`, `crossfade`, `concatenate`, `mix`, `export_samples`
