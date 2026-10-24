# Beatmaker documentation

## Start here

1. Install the package and run the [first beat](../README.md#make-your-first-beat).
2. Read [song and track builders](song_building.md) to understand return values,
   timing, and when audio is synthesized.
3. Run [the small direct-API example](../examples/basics/02_direct_api.py), then
   change the notes or tempo.
4. Use sections to turn a pattern into a longer song.

## Choose a task

| I want to… | Read |
| --- | --- |
| Add drums, bass, melodies, or chords | [Song building](song_building.md) |
| Play my own samples at different pitches | [Samples and keygroups](keygroup_integration_guide.md) |
| Make a reusable verse or chorus | [Arrangement and expression](arrangement.md) |
| Create a sound from scratch | [Synthesis reference](synthesis.md) |
| Add reverb, filters, compression, or sidechain | [Effects reference](effects.md) |
| Use step patterns, Euclidean rhythms, or arpeggios | [Sequencing reference](sequencing.md) |
| Transform phrases or work with scales and chords | [Melody and harmony reference](melody_and_harmony.md) |
| Connect parallel audio processing paths | [Signal graph reference](signal_graph.md) |
| Load/export audio or MIDI, organize samples | [MIDI and I/O reference](midi_and_io.md) |
| Update existing builder code | [Migration guide](migration.md) |

## The objects you use

- **SongBuilder** configures a composition and owns its track builders.
- **TrackBuilder** places samples and controls volume, pan, effects, and expression.
  Specialized builders add drums, bass notes, phrases, chords, or keygroups.
- **Song** contains the finished tracks. Render it to `AudioData` or export it.
- **Track** holds sample placements in seconds. Use it directly when you need
  lower-level control.
- **Sample** is named audio plus metadata; **AudioData** contains a NumPy sample
  array and its sample rate. Synthesizers generally return `Sample`; raw waveform
  functions and effects return `AudioData`.

Most applications can import these objects from `beatmaker`. Feature modules
such as `beatmaker.synthesis`, `beatmaker.effects`, and `beatmaker.graph` are
also public. The old `beatmaker.synth`, `beatmaker.synths`, and
`beatmaker.sidechain` modules remain compatibility imports.

All examples assume the package has been installed in the Python environment
running the script. The experimental framework under `experimental/` is separate
from the main composition API.
