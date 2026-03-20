# Quickstart Guide

Get up and running with **beatmaker** in minutes.

---

## Installation

```bash
# Core package
pip install beatmaker

# With SPC700 support (optional, separate package)
pip install beatmaker[spc700]
```

---

## Hello World: Your First Beat

```python
from beatmaker import create_song

song = (create_song("My First Beat")
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

That's it -- 10 lines to a four-bar house beat with kick, snare, and hi-hats.

---

## Adding a Bass Line

```python
song = (create_song("Bass Beat")
    .tempo(128)
    .bars(4)
    .add_drums(lambda d: d
        .four_on_floor()
        .backbeat()
    )
    .add_bass(lambda b: b
        .note("C2", beat=0)
        .note("C2", beat=1)
        .note("G2", beat=2)
        .note("Eb2", beat=3)
    )
    .build())

song.export("bass_beat.wav")
```

---

## Adding a Melody

```python
from beatmaker import create_song, Key, ChordProgression, Phrase, Melody

key = Key.major('C')
prog = ChordProgression.from_roman(key, "I - V - vi - IV")

song = (create_song("Melodic Beat")
    .tempo(120)
    .bars(4)
    .add_drums(lambda d: d.four_on_floor().backbeat().eighth_hats())
    .add_bass(lambda b: b.note("C2", beat=0).note("G2", beat=2))
    .add_melody(lambda m: m
        .phrase("C4:1 E4:1 G4:2 A4:1 G4:1 E4:2")
    )
    .build())

song.export("melodic_beat.wav")
```

---

## Import Paths

With the v0.4 restructure, you can import from either the top-level package or the specific subpackages:

```python
# Top-level import (simple, recommended for most users)
from beatmaker import DrumSynth, BassSynth, Reverb, Delay

# Subpackage import (precise, useful for larger projects)
from beatmaker.synthesis import DrumSynth, BassSynth
from beatmaker.synthesis.waveforms import sine_wave, sawtooth_wave
from beatmaker.effects import Reverb, Delay
from beatmaker.effects.sidechain import PumpingBass
from beatmaker.graph import SignalGraph, AudioInput

# Music theory utilities
from beatmaker.music import note_name_to_midi, Scale, ChordShape, midi_to_freq
```

The old import paths (`from beatmaker.synth import ...`, `from beatmaker.synths import ...`, `from beatmaker.sidechain import ...`) continue to work via backward-compatibility stubs but are deprecated. See the [Migration Guide](migration_v0.3_to_v0.4.md) for details.

---

## Common Patterns

### Apply Effects

```python
from beatmaker import create_song, Reverb, Delay, Compressor, EffectChain

song = (create_song("FX Demo")
    .tempo(128)
    .bars(4)
    .add_drums(lambda d: d.four_on_floor().backbeat())
    .master_effects([Compressor(threshold=-12), Reverb(room_size=0.6), Delay(time=0.375)])
    .build())
```

### Use the Signal Graph

```python
from beatmaker.graph import SignalGraph, AudioInput, GainNode, FilterNode

with SignalGraph() as g:
    source = AudioInput(my_audio, name="input")
    filt = FilterNode(cutoff=800, resonance=0.5)
    gain = GainNode(level=0.8)
    source >> filt >> gain >> g.sink

result = g.render(duration=2.0)
```

### Sections and Arrangement

```python
from beatmaker import Section, Arrangement

verse = Section("verse", bars=8)
chorus = Section("chorus", bars=8)

arrangement = (Arrangement()
    .intro(verse.without_track("Bass"))
    .verse(verse, repeat=2)
    .chorus(chorus)
    .outro(chorus.with_volume("Drums", 0.5)))
```

---

## Next Steps

- [API Reference (README)](README.md) -- Full module index and architecture overview
- [Synthesis](synthesis.md) -- Oscillators, drum machines, pad/lead/pluck synths
- [Effects](effects.md) -- Gain, reverb, delay, compression, sidechain
- [Signal Graph](signal_graph.md) -- Declarative audio routing
- [Builder](builder.md) -- Fluent song construction API
- [Sequencer & Arpeggiator](sequencer_and_arpeggiator.md) -- Step sequencing and arpeggiation
- [Melody, Harmony & Automation](melody_harmony_automation.md) -- Music theory, chords, automation
- [Migration Guide (v0.3 to v0.4)](migration_v0.3_to_v0.4.md) -- Upgrading from v0.3
