# Samples and keygroups

A keygroup turns a recorded or synthesized sample into a pitched instrument.
`KeygroupProgram` describes the sound and its root pitch. A keygroup track places
notes using that program. Song and section integration is built in.

## Create a playable instrument

This complete example uses a synthesized sample, so no sample files are needed.

```python
from beatmaker import create_song, KeygroupProgram, PluckSynth, note_to_freq

source = PluckSynth.karplus_strong(note_to_freq("C4"), duration=1.0)
program = KeygroupProgram.from_sample(source, root_note="C4")

project = create_song("Sampled instrument", bpm=100, bars=1)
keys = project.keygroup("Keys", program)
keys.note("C4", beat=0, duration=1)
keys.note("E4", beat=1, duration=1)
keys.chord(["C4", "E4", "G4"], beat=2, duration=2)
keys.volume(0.4)
song = project.master_limiter().build()
song.export("keygroup.wav")
```

For a recording, replace `source` with `load_audio("piano_C4.wav")`. Both
`AudioData` and `Sample` inputs are accepted. Set `root_note` to the sample's
original pitch. The program resamples it to produce other pitches, so pitch
changes also affect the source's playback speed and timbre.

## Place phrases and lines

```python
from beatmaker import create_song, KeygroupProgram, PluckSynth, Phrase, note_to_freq

program = KeygroupProgram.from_sample(
    PluckSynth.karplus_strong(note_to_freq("C4"), duration=1), root_note="C4"
)
project = create_song("Phrase", bpm=120)
keys = project.keygroup("Keys", program)
keys.phrase(Phrase.from_string("C4:1 E4:1 G4:2"), start_beat=0)
keys.line([("G4", 4, 1), ("E4", 5, 1), ("C4", 6, 2)])
song = project.master_limiter().build()
```

`note`, `chord`, and `line` positions and durations are in beats. Phrases use
`Phrase` notation. Keygroup notes are synthesized when placed; call
`.humanize(...)` or `.groove(...)` after adding them.

The common track controls are available: `.volume(...)`, `.pan(...)`,
`.effect(...)`, `.mute()`, `.solo()`, `.automate_volume(...)`, and
`.automate_pan(...)`. Use `.build()` to obtain the raw `Track`.

## Use sections or callbacks

```python
from beatmaker import create_song, Arrangement, KeygroupProgram, DrumSynth

program = KeygroupProgram.from_sample(DrumSynth.kick(), root_note="C2")
project = create_song("Sectioned sample", bpm=120)
verse = project.section("Verse", bars=1)
verse.keygroup("Low keys", program).note("C2", beat=0, duration=2)
song = (project.arrange(Arrangement().add(verse.build(), repeat=2))
    .master_limiter().build())
```

The callback equivalent is
`project.add_keygroup("Keys", program, lambda keys: keys.note("C4", 0, 1))`.
Both approaches work on `SectionBuilder` too.

## Multiple source samples

Pass `(sample, root_note)` pairs to `KeygroupProgram.from_multi_sample(...)`:

```python
from beatmaker import KeygroupProgram, PluckSynth, note_to_freq

program = KeygroupProgram.from_multi_sample([
    (PluckSynth.karplus_strong(note_to_freq("C3"), 1), "C3"),
    (PluckSynth.karplus_strong(note_to_freq("C4"), 1), "C4"),
])
```

Key ranges are split automatically between the root pitches. The program chooses
the zone covering the requested pitch. Use more source samples when wide pitch
shifts sound unnatural. Inspect the method's docstring for envelope options.

See [song building](song_building.md) for the shared track API and
[MIDI and I/O](midi_and_io.md) for loading audio and sample libraries.
