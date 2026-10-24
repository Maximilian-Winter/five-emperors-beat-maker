# Examples

Install the checkout into your active Python environment before running scripts:

```sh
python -m pip install -e .
python examples/basics/02_direct_api.py
```

Run from the repository root. Export paths are relative to your working
directory. The direct-API example creates `direct_api.wav` with synthesized
sounds and needs no sample files or optional audio packages.

## Start here

- [02_direct_api.py](basics/02_direct_api.py): a small complete song using direct
  track builders, phrases, humanization, a reusable section, and WAV export.
- [01_simple_beat.py](basics/01_simple_beat.py): five drum-and-bass recipes using
  the callback API: house, trap, lo-fi, techno, and drum and bass.

## Explore a feature

- [01_all_features.py](advanced/01_all_features.py): sequencers, Euclidean
  rhythms, arpeggios, sidechain, synthesis, and MIDI.
- [02_extended.py](advanced/02_extended.py): pentatonic melodies and loops.
- [03_full_example.py](advanced/03_full_example.py): phrase transformations,
  arrangement, automation, expression, and signal graphs.
- [04_signal_graph.py](advanced/04_signal_graph.py): ring modulation, parallel
  compression, auto-wah, and vocoder routing.
- [keygroup_demo.py](advanced/keygroup_demo.py): sampled instruments; check its
  source paths before running.

## Larger compositions

The [compositions](compositions/) directory contains longer pieces showing how
to combine these features. Some require external sample folders or the optional
`beatmaker-spc700` package. Read each script's imports and configuration first.
These are musical studies rather than the recommended starting point for the API.

See the [song-building guide](../docs/song_building.md) for timing rules and
[the migration guide](../docs/migration.md) to translate callback chains into
direct track access.
