# Beatmaker

Compose beats and songs in Python using synthesized sounds or your own samples.
Build tracks, add effects, arrange sections, and export a stereo WAV file.

## Install

Requires Python 3.9 or newer.

```sh
pip install beatmaker
```

WAV support needs only the core dependencies (`numpy` and `tqdm`). For other
formats, install `beatmaker[audio]`; conversion uses pydub and may require FFmpeg.
SNES synthesis is available separately through `beatmaker[spc700]`.

To work from this checkout:

```sh
python -m pip install -e ".[dev]"
python -m pytest
```

## Make your first beat

```python
from beatmaker import create_song

project = create_song("My Beat", bpm=128, bars=2)
project.drums().four_on_floor().backbeat().eighth_hats().volume(0.7)
project.bass().line([
    ("E2", 0, 1), ("G2", 2, 1),
    ("E2", 4, 1), ("A2", 6, 1),
]).volume(0.5)
project.melody(synth_type="sine").play("E4:1 G4:1 B4:2").volume(0.3)
project.master_limiter()

song = project.build()
song.export("my_beat.wav")
```

`create_song()` returns a **song builder**. Its track methods return a **track
builder**, so you can save a track in a variable and edit it with ordinary Python.
`build()` finishes pending notes and returns a **Song**; `export()` renders audio
and writes the file.

Positions start at zero. At 128 BPM, each beat lasts `60 / 128` seconds.
`bars=2` repeats drum beat lists across two bars. Bass notes and melodies use
absolute beat positions and play once. See the [timing guide](docs/song_building.md#timing).

## Add chords and effects

```python
from beatmaker import create_song, Reverb

project = create_song("Chords", bpm=100)
chords = project.harmony("Pads", synth_type="warm_pad")
chords.key("C", "major").progression("I - V - vi - IV", beats_per_chord=4)
chords.voice_lead().volume(0.3).effect(Reverb(room_size=0.3, mix=0.2))
project.master_limiter()
song = project.build()
song.export("chords.wav")
```

The callback style is also supported:

```python
from beatmaker import create_song

song = (create_song("Callback style", bpm=128, bars=2)
    .add_drums(lambda drums: drums.four_on_floor().backbeat())
    .add_bass(lambda bass: bass.note("E2", beat=0, duration=4))
    .master_limiter()
    .build())
```

## Documentation

Start with the [documentation guide](docs/README.md).

- [Song and track builders](docs/song_building.md): configuration, timing, sounds, effects, and build behavior.
- [Sections and arrangements](docs/arrangement.md): reusable patterns and song structure.
- [Samples and keygroups](docs/keygroup_integration_guide.md): play an audio sample as a pitched instrument.
- [API migration](docs/migration.md): move existing code to direct track access.
- [Synthesis](docs/synthesis.md), [effects](docs/effects.md), [sequencing](docs/sequencing.md), [melody and harmony](docs/melody_and_harmony.md), [signal graphs](docs/signal_graph.md), and [MIDI and audio I/O](docs/midi_and_io.md).
- [Runnable examples](examples/README.md).
