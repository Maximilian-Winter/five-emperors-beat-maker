# Song and track builders

## Create a composition

```python
from beatmaker import create_song

project = create_song("Sketch", bpm=120, bars=2, sample_rate=44100)
```

These keyword arguments also work on `SongBuilder(...)`. Defaults are 120 BPM,
four bars, 44100 Hz, and 4/4 time. Tempo must be positive and finite; bars and
sample rate must be positive integers.

The chainable setters remain available: `.tempo(100)`, `.bars(8)`,
`.sample_rate(48000)`, and `.time_signature(3, 4)`. Set timing and attach a sample
library **before** creating tracks. Already placed samples keep their absolute
positions in seconds when settings change. `beat_value` records the time
signature denominator; beat-to-second conversion always uses `60 / bpm`.

## Create tracks directly

A direct track method creates a new track, attaches it immediately, and returns
its specialized builder. Keep the returned builder to edit that track later.
Calling the method again creates another track, even with the same name.

| Method | Default name | Main methods |
| --- | --- | --- |
| `project.drums(name="Drums")` | Drums | `kick`, `snare`, `hihat`, `clap`, `four_on_floor`, `backbeat`, `eighth_hats` |
| `project.bass(name="Bass")` | Bass | `note`, `acid_note`, `line`, `octave_pattern` |
| `project.melody(name="Melody", synth_type="saw")` | Melody | `play`, `phrase`, `synth` |
| `project.harmony(name="Harmony", synth_type="saw")` | Harmony | `key`, `progression`, `voice_lead`, `arpeggiate`, `synth` |
| `project.keygroup(name, program)` | required | `note`, `chord`, `line`, `phrase`, `melody`, `arp_events` |
| `project.track(name, track_type=TrackType.FX)` | required | `add`, `add_at_bar`, `sample` |

Each supports `volume(level)`, `pan(value)`, `effect(effect)`, `mute()`, `solo()`,
`humanize(...)`, `groove(template)`, `automate_volume(curve)`, and
`automate_pan(curve)`. These return the same track builder for chaining.
Use volume multipliers around 0–1 and pan from -1 (left) to +1 (right).

```python
from beatmaker import create_song, Delay

project = create_song("Lead", bpm=120, bars=2)
lead = project.melody("Hook", synth_type="sine")
lead.play("C4:1 E4:0.5 G4:0.5 R:1 C5:1")
lead.play("G4:2 E4:2", start_beat=4)
lead.volume(0.4).pan(0.1).effect(Delay(delay_time=0.25, mix=0.15))
song = project.master_limiter().build()
```

## Timing

All builder positions start at zero. At 120 BPM, beat 4 is 2 seconds into a song.
In 4/4, bar 1 starts at beat 4. In 3/4, bar 1 starts at beat 3.

| Input | Units and repetition |
| --- | --- |
| `drums.kick/snare/hihat/clap(beats=[...])` | Beats within a bar, repeated for the configured number of bars |
| `drums.kick/snare/hihat(pattern=[...])` | One boolean sequence; each step is 0.25 beats; it plays once |
| `four_on_floor`, `backbeat`, `eighth_hats`, `sixteenth_hats` | Presets for 4/4, repeated across the configured bars |
| `bass.note(note, beat, duration)` and keygroup notes | Absolute beat position and duration in beats; play once |
| `bass.line([(note, beat, duration), ...])` | Absolute beat positions; plays once |
| `melody.play(notation, start_beat=None)` | Note durations in beats; appends after the previous phrase unless positioned explicitly |
| `melody.phrase(phrase, start_beat=None)` | Same timing as `play`, accepting a `Phrase` object |
| `harmony.progression(numerals, beats_per_chord=4, octave=3)` | Chords start at beat 0 and play once |
| `track.add(sample, beat)` and `track.sample(key, beat)` | Absolute beat position |
| `track.add_at_bar(sample, bar)` | Absolute bar position |
| Low-level `Track.add(sample, time)` | Seconds |
| Synthesis duration and effect attack/release/delay | Seconds |

`bars` controls drum repetition. It does not pad, truncate, or loop the whole
song. Song duration follows the placed audio. Rendering adds a one-second tail;
long effect tails may need additional silence placed on the timeline.

For a different time signature, use explicit drum beat lists rather than the
4/4 presets. For longer structures, build and repeat sections.

## Bass, phrases, and chords

```python
from beatmaker import create_song, Phrase

project = create_song("Harmony study", bpm=100, bars=4)
project.bass().line([("C2", 0, 4), ("G2", 4, 4), ("A2", 8, 4), ("F2", 12, 4)])
motif = Phrase.from_string("C4:1 E4:1 G4:2")
lead = project.melody(synth_type="pluck")
lead.phrase(motif).phrase(motif.transpose(5))
project.harmony(synth_type="warm_pad").key("C", "major").progression(
    "I - V - vi - IV", beats_per_chord=4
).voice_lead().volume(0.25)
song = project.master_limiter().build()
```

Melody synths: `saw`, `square`, `sine`, `triangle`, `fm`, `pluck`.
Harmony synths: `saw`, `square`, `sine`, `triangle`, `warm_pad` (or `pad`),
`string_pad`. Set the key before the progression. `play()` parses the same
notation as `Phrase.from_string()`: `C4:1` is a one-beat note and `R:1` is a
one-beat rest. See [melody and harmony](melody_and_harmony.md) for transformations.

## Samples and effects

```python
from beatmaker import create_song, DrumSynth, SampleLibrary, Reverb

library = SampleLibrary().add(DrumSynth.kick(), key="kick")
project = create_song("Sample sketch", bars=1).samples(library)
project.drums().use_sample("kick", "kick").four_on_floor()
project.track("Accent").sample("kick", beat=3.5).volume(0.4)
project.master_effect(Reverb(room_size=0.2, mix=0.1)).master_limiter()
song = project.build()
```

Attach libraries before creating the track or section. For files, use
`SampleLibrary.from_directory("samples")`, or wrap `load_audio("hit.wav")` in a
`Sample` and place it with `.add(...)`. Drum `.use_kit(...)` expects `Sample`
objects, such as the values returned by `DrumSynth`.

Track effects run in the order added, followed by master effects after mixing.
[Effects](effects.md) documents parameters and sidechain workflows.

## Build and export

`project.build()` synthesizes pending melody and harmony events and returns its
`Song`. `track_builder.build()` finishes just that track and returns its `Track`.
Repeated builds without edits reuse the generated samples and do not duplicate
notes or reapply expression. Adding a phrase or changing a synth or progression
regenerates that track's synthesized notes on the next build. Manually added
samples remain in place.

The song and tracks are mutable objects owned by the builder; `build()` does not
make a snapshot. After changing a melody or harmony builder, call `build()` again
before rendering or exporting the song.

Melody and harmony `.humanize(...)` and `.groove(...)` run on generated notes
after synthesis, in the order requested. They also apply to future phrases.
Other track builders apply these methods immediately to existing placements, so
call them after placing notes or samples.

```python
from beatmaker import create_song

project = create_song("Export", bars=1)
project.drums().four_on_floor()
song = project.master_limiter().build()
audio = song.render(channels=2)   # AudioData; use channels=1 for mono
song.export("export.wav")         # returns a pathlib.Path
```

WAV works without optional packages. Other formats use `beatmaker[audio]` and
may need FFmpeg. MIDI export is a separate operation; see its
[limitations](midi_and_io.md).

## Reusable sections

Sections expose the same direct track and callback methods as songs.
Build each section before adding it to an arrangement.

```python
from beatmaker import create_song, Arrangement

project = create_song("Arranged", bpm=120)
verse = project.section("Verse", bars=2)
verse.drums().four_on_floor().backbeat()
verse.bass().line([("C2", 0, 4), ("G2", 4, 4)])
verse.melody(synth_type="sine").play("C4:2 E4:2 G4:4")
section = verse.build()

structure = Arrangement().add(section, repeat=2)
song = project.arrange(structure).master_limiter().build()
```

Section positions are relative to its start. Arrangement offsets use the section's
bar count. Repeating a section copies its placements; audio extending beyond the
section boundary can overlap the next section. Tracks with matching names are
merged, so use distinct names for parts that need separate mixing settings.
`arrange()` immediately adds placements; calling it twice adds them twice.
See [arrangement and expression](arrangement.md) for variations and automation.

## Callback API

`add_drums`, `add_bass`, `add_melody`, `add_harmony`, `add_keygroup`, and
`add_track` return the parent song or section builder. Their callbacks receive
the same specialized track builders as the direct methods. A callback can return
the track builder or `None`. Melody and harmony callbacks synthesize their notes
before returning to the parent.

```python
from beatmaker import create_song


def configure_drums(drums):
    drums.four_on_floor()
    drums.backbeat()


song = (create_song("Callbacks", bars=1)
    .add_drums(configure_drums, name="Main drums")
    .add_melody(lambda lead: lead.play("C4:1 E4:1 G4:2"), synth_type="sine")
    .master_limiter()
    .build())
```

`add_track(name, track_type, builder)` keeps its historical default type:
`DRUMS` on songs and `FX` on sections. The direct `track(...)` method defaults
to `FX` on both. Pass a `TrackType` explicitly when classification matters.
