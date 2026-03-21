# Keygroup Module — Integration Guide

How to add MPC-style sample-based chromatic instruments to the Five Emperors Beat Maker.

---

## Overview

The keygroup module adds two new classes:

- **`KeygroupProgram`** — An instrument that maps a sample (or multiple samples) across the MIDI note range via pitched resampling. Load one sample, play it at any pitch — just like an MPC keygroup program.
- **`KeygroupTrackBuilder`** — A fluent builder (parallel to `DrumTrackBuilder`, `BassTrackBuilder`, etc.) for composing with keygroup instruments inside the song builder chain.

The module lives in a single file: `beatmaker/keygroup.py`.

---

## Step 1: Place the Module

Copy `keygroup.py` into your package:

```
beatmaker/
    ...
    keygroup.py          ← new file
    ...
```

The module imports from `beatmaker.core`, `beatmaker.music`, and `beatmaker.synthesis.oscillator` — all existing dependencies, no new packages required.

---

## Step 2: Add `add_keygroup()` to the Builders

Two methods need to be added: one on `SongBuilder` (for flat song construction) and one on `SectionBuilder` (for arrangement-based construction with sections).

### In `beatmaker/builder.py` — SongBuilder

Add this method to the `SongBuilder` class:

```python
def add_keygroup(
    self,
    name: str,
    program: 'KeygroupProgram',
    builder_fn: Callable[['KeygroupTrackBuilder'], 'KeygroupTrackBuilder'],
) -> 'SongBuilder':
    """Add a keygroup-based track to the song.

    Parameters
    ----------
    name : str
        Track name (e.g. "Sampled Piano", "Pad Layer").
    program : KeygroupProgram
        The keygroup instrument to use as the sound source.
    builder_fn : callable
        A lambda/function that receives a KeygroupTrackBuilder
        and configures it by placing notes, phrases, effects, etc.

    Returns
    -------
    self
    """
    from beatmaker.keygroup import KeygroupTrackBuilder

    track = Track(name=name, track_type=TrackType.LEAD)
    builder = KeygroupTrackBuilder(track, self, program)
    builder_fn(builder)
    self._tracks.append(track)
    return self
```

### In `beatmaker/builder.py` — SectionBuilder

Add this method to the `SectionBuilder` class (the object returned by `create_song().section()`):

```python
def add_keygroup(
    self,
    name: str,
    program: 'KeygroupProgram',
    builder_fn: Callable[['KeygroupTrackBuilder'], 'KeygroupTrackBuilder'],
) -> 'SectionBuilder':
    """Add a keygroup-based track to this section.

    Parameters
    ----------
    name : str
        Track name.
    program : KeygroupProgram
        The keygroup instrument.
    builder_fn : callable
        Builder configuration function.

    Returns
    -------
    self
    """
    from beatmaker.keygroup import KeygroupTrackBuilder

    track = Track(name=name, track_type=TrackType.LEAD)
    builder = KeygroupTrackBuilder(track, self._song_builder, program)
    builder_fn(builder)
    self._section.add_track(track)
    return self
```

> **Note:** Both methods use a lazy import (`from beatmaker.keygroup import ...`) to avoid circular dependencies. The `KeygroupTrackBuilder` receives `self` (the song builder) so it can access `_bpm` for beat-to-seconds conversion.

---

## Step 3: Export from `__init__.py`

Add the public symbols to `beatmaker/__init__.py`:

```python
from beatmaker.keygroup import KeygroupProgram, KeygroupTrackBuilder
```

This makes them available via the standard import:

```python
from beatmaker import KeygroupProgram
```

---

## API Summary

### KeygroupProgram

| Method | Description |
|--------|-------------|
| `KeygroupProgram.from_sample(sample, root_note, ...)` | Create from a single sample mapped across all notes |
| `KeygroupProgram.from_multi_sample([(sample, root), ...])` | Create from multiple samples at different pitches |
| `program.generate(note, duration, velocity)` | Generate a pitched `Sample` for one note |
| `program.generate_chord(notes, duration, velocity)` | Generate a layered chord as a single `Sample` |
| `program.preview_range(low, high, step, ...)` | Audition the mapping across a range |

### KeygroupTrackBuilder

| Method | Description |
|--------|-------------|
| `.note(note, beat, duration, velocity)` | Place a single note |
| `.chord(notes, beat, duration, velocity)` | Place a chord |
| `.line([(note, beat, dur), ...])` | Place notes from a tuple list (like `BassTrackBuilder.line()`) |
| `.phrase(phrase, start_beat)` | Render a `Phrase` through the keygroup |
| `.melody(melody)` | Render a `Melody` through the keygroup |
| `.arp_events(events)` | Render arpeggiator output through the keygroup |
| `.volume(level)` | Set track volume |
| `.pan(value)` | Set track pan |
| `.effect(effect)` | Add an effect to the track chain |
| `.humanize(timing, velocity, seed)` | Apply humanization |
| `.groove(template)` | Apply a groove template |
| `.automate_volume(curve)` | Apply volume automation |
| `.automate_filter(curve, filter_type)` | Apply filter automation |

---

## Usage Examples

### Basic: One Sample, Chromatic Melody

```python
from beatmaker import (
    create_song, load_audio, KeygroupProgram,
    Reverb, Delay,
)
from beatmaker.melody import Phrase

# Load a sample and create a keygroup
sample = load_audio("samples/piano_C4.wav")
piano = KeygroupProgram.from_sample(sample, root_note='C4')

# Define a melody
melody = Phrase.from_string("C4:1 E4:0.5 G4:0.5 C5:2")

song = (create_song("Piano Sketch")
    .tempo(100).bars(4)
    .add_keygroup("Piano", piano, lambda k: k
        .phrase(melody, start_beat=0)
        .phrase(melody.transpose(5), start_beat=4)
        .volume(0.7)
        .effect(Reverb(room_size=0.4, mix=0.3))
    )
    .build()
)
song.export("piano_sketch.wav")
```

### Synth-Generated Keygroup

No audio files needed — generate the source sample with the synth engine:

```python
from beatmaker import (
    create_song, PadSynth, note_to_freq,
    KeygroupProgram, ADSREnvelope,
    Chorus, Reverb,
)

# Create a pad sound and map it as a keygroup
pad = PadSynth.warm_pad(note_to_freq('C3'), duration=3.0, num_voices=4)
pad_keys = KeygroupProgram.from_sample(
    pad,
    root_note='C3',
    envelope=ADSREnvelope(attack=0.05, decay=0.3, sustain=0.6, release=0.5),
)

song = (create_song("Pad Chords")
    .tempo(80).bars(4)
    .add_keygroup("Pads", pad_keys, lambda k: k
        .chord(['C3', 'Eb3', 'G3'], beat=0, duration=4)
        .chord(['Ab3', 'C4', 'Eb4'], beat=4, duration=4)
        .chord(['F3', 'Ab3', 'C4'], beat=8, duration=4)
        .chord(['G3', 'Bb3', 'D4'], beat=12, duration=4)
        .volume(0.4)
        .effect(Chorus(rate=0.4, depth=0.003, mix=0.2))
        .effect(Reverb(room_size=0.7, mix=0.5))
    )
    .build()
)
```

### Multi-Sample Keygroup (Reduced Artifacts)

Sample at multiple octaves so each note is within ±6 semitones of a root:

```python
from beatmaker import LeadSynth, note_to_freq, KeygroupProgram

lead_keys = KeygroupProgram.from_multi_sample([
    (LeadSynth.saw_lead(note_to_freq('C3'), 1.0), 'C3'),
    (LeadSynth.saw_lead(note_to_freq('C4'), 1.0), 'C4'),
    (LeadSynth.saw_lead(note_to_freq('C5'), 1.0), 'C5'),
], name="multi_lead")

# The engine automatically splits the range:
#   C3 zone covers MIDI 0–47  (closest to C3=48... well, 0 to midpoint)
#   C4 zone covers MIDI 48–65 (midpoint to midpoint)
#   C5 zone covers MIDI 66–127
```

### With Sections and Arrangement

```python
sb = create_song("Arranged").tempo(96).bars(32)

verse = (sb.section("Verse", bars=8)
    .add_keygroup("Lead", lead_keys, lambda k: k
        .phrase(verse_melody)
        .volume(0.5)
        .effect(Reverb(room_size=0.4, mix=0.2))
    )
    .add_keygroup("Chords", pad_keys, lambda k: k
        .chord(['C3', 'Eb3', 'G3'], beat=0, duration=8)
        .volume(0.3)
    )
    .build()
)

chorus = (sb.section("Chorus", bars=8)
    .add_keygroup("Lead", lead_keys, lambda k: k
        .phrase(chorus_melody)
        .volume(0.65)
    )
    .build()
)

arrangement = (Arrangement()
    .verse(verse)
    .chorus(chorus)
    .verse(verse)
    .chorus(chorus, repeat=2)
)
```

### With Arpeggiator

```python
from beatmaker import create_arpeggiator, ChordShape

arp = (create_arpeggiator()
    .tempo(120).up_down().sixteenth().gate(0.6).octaves(2)
    .build()
)
events = arp.generate_from_chord('C3', ChordShape.MINOR7, beats=8)

song = (create_song("Arp Demo")
    .tempo(120).bars(2)
    .add_keygroup("Bell Arp", bell_keys, lambda k: k
        .arp_events(events)
        .volume(0.4)
        .effect(Delay(delay_time=0.375, feedback=0.3, mix=0.25))
    )
    .build()
)
```

---

## How the Resampling Works

The keygroup uses ratio-based resampling — the same approach as hardware samplers (MPC, SP-1200, E-mu, Akai S-series):

1. Compute the pitch ratio: `ratio = 2^(semitone_difference / 12)`
2. Resample the source buffer at that ratio using linear interpolation (`numpy.interp`)
3. Higher notes → shorter buffer (faster playback), lower notes → longer buffer (slower playback)

This means **duration changes with pitch** — a note one octave up plays in half the time. If you pass a `duration` parameter, the output is trimmed or zero-padded to fit, with an envelope applied.

The characteristic artifacts (chipmunk effect at high pitches, slowed-tape at low pitches) are authentic to the sampler sound. For cleaner pitch shifting that preserves duration, you could build a phase vocoder as a `SignalGraph` node and use it as a pre-processing step — the infrastructure is already there.

---

## File Checklist

| Action | File | What to do |
|--------|------|------------|
| Add | `beatmaker/keygroup.py` | The new module (KeygroupProgram + KeygroupTrackBuilder) |
| Edit | `beatmaker/builder.py` | Add `add_keygroup()` to SongBuilder and SectionBuilder |
| Edit | `beatmaker/__init__.py` | Export `KeygroupProgram` and `KeygroupTrackBuilder` |
