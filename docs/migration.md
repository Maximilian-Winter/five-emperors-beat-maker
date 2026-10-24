# Moving to direct track access

Existing imports and callback chains remain supported. You can adopt direct
track access one track at a time, including inside sections.

## Configure a song in one call

```python
from beatmaker import create_song

# Existing style
old = create_song("Sketch").tempo(120).bars(2).sample_rate(44100)

# Equivalent configuration
project = create_song("Sketch", bpm=120, bars=2, sample_rate=44100)
```

Setters and constructor arguments now reject nonpositive settings; tempo also
rejects NaN and infinity, and bars/sample rate require integers.

## Keep track builders in variables

```python
from beatmaker import create_song

# Callback style remains valid.
old = (create_song("Old", bars=1)
    .add_drums(lambda drums: drums.four_on_floor().volume(0.7))
    .build())

# Direct style uses ordinary statements.
project = create_song("New", bars=1)
drums = project.drums()
drums.four_on_floor()
drums.volume(0.7)
song = project.build()
```

| Callback method | Direct equivalent |
| --- | --- |
| `add_drums(callback, name="Drums")` | `drums(name="Drums")` |
| `add_bass(callback, name="Bass")` | `bass(name="Bass")` |
| `add_melody(callback, name="Melody", synth_type="saw")` | `melody(name="Melody", synth_type="saw")` |
| `add_harmony(callback, name="Harmony", synth_type="saw")` | `harmony(name="Harmony", synth_type="saw")` |
| `add_keygroup(name, program, callback)` | `keygroup(name, program)` |
| `add_track(name, track_type, callback)` | `track(name, track_type)` |

Direct methods return track builders; callback methods return the parent builder.
Use a new statement to switch back to the parent. Save a track builder when you
want to edit it later; calling `project.drums()` again creates another drum track.

## Replace private-field workarounds

Old documentation suggested creating a `MelodyTrackBuilder` inside a generic
track callback using `t._track` and `t._song`. That bypasses melody finalization.
Use `melody()` or `add_melody()` instead. Use `.synth(...)` to select a sound;
melody builders have no `.waveform(...)` method.

```python
from beatmaker import create_song

project = create_song("Lead", bars=1)
project.melody(synth_type="sine").play("C4:1 E4:1 G4:2")
project.harmony(synth_type="warm_pad").key("C").progression("I - IV - V - I")
song = project.build()
```

For a raw track, use `track_builder.build()`; callers do not need `_track`.
Direct melody and harmony events are synthesized at build time. After further
edits, build again before using a previously returned Song or Track.

Repeated builds and calls to `render_melody()`/`render_harmony()` no longer
append duplicate generated notes. Melody/harmony humanization and groove now
run after synthesis, so they affect the composed notes. This can audibly change
compositions whose expression settings previously did nothing.

Keygroup builders now share the common track API, including `build`, `mute`,
`solo`, `add`, `sample`, and pan automation. Their existing volume automation
method retains its effect-based behavior.

## Imports and optional features

Prefer `beatmaker.synthesis` for synthesizers and `beatmaker.effects` for effects.
Root imports such as `from beatmaker import DrumSynth, Reverb` continue to work.
The `synth`, `synths`, and `sidechain` compatibility modules remain available.

SPC700 song helpers now import the separate `beatmaker_spc700` package correctly.
Install `beatmaker[spc700]` to use them. No SPC700 installation is required for
regular tracks.

See [song building](song_building.md) for timing rules, build ownership, and
complete examples.
