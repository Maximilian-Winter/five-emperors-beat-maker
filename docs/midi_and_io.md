# MIDI & I/O

This document covers audio file I/O, sample library management, MIDI data
types, MIDI file reading/writing, MIDI-to-beatmaker conversion, and audio
utility functions.

Source files:
`beatmaker/io.py`, `beatmaker/midi.py`, `beatmaker/utils.py`

---

## 1. Audio I/O

```python
from beatmaker.io import load_audio, save_audio
```

### `load_audio(path: Union[str, Path]) -> AudioData`

Loads audio from a file and returns an `AudioData` object with normalized
float samples in the range `[-1.0, 1.0]`.

| Parameter | Type                | Description           |
|-----------|---------------------|-----------------------|
| `path`    | `Union[str, Path]`  | Path to the audio file |

**WAV files** are loaded natively using Python's `wave` module (8-bit unsigned,
16-bit signed, and 32-bit signed are supported). **All other formats** (MP3,
OGG, FLAC, AIFF) require `pydub` to be installed; a `ValueError` is raised
with installation instructions if it is missing.

```python
audio = load_audio("drums/kick.wav")
audio = load_audio("vocals/lead.mp3")  # requires pydub
```

### `save_audio(audio, path, format=None) -> None`

Saves an `AudioData` object to a file.

| Parameter | Type                | Default | Description                                     |
|-----------|---------------------|---------|-------------------------------------------------|
| `audio`   | `AudioData`         | --      | Audio data to save                              |
| `path`    | `Union[str, Path]`  | --      | Output file path                                |
| `format`  | `Optional[str]`     | `None`  | Override format (e.g. `'wav'`, `'mp3'`). If `None`, inferred from file extension. |

WAV is written natively as 16-bit PCM. Other formats go through `pydub`.

```python
save_audio(audio, "output/mix.wav")
save_audio(audio, "output/mix.mp3")            # requires pydub
save_audio(audio, "output/mix", format='ogg')  # explicit format
```

---

## 2. SampleLibraryConfig

```python
from beatmaker.io import SampleLibraryConfig
```

A dataclass controlling how a `SampleLibrary` loads and processes samples.

| Field                | Type                     | Default                                    | Description                                                |
|----------------------|--------------------------|--------------------------------------------|------------------------------------------------------------|
| `extensions`         | `tuple[str, ...]`        | `('.wav', '.mp3', '.ogg', '.flac', '.aiff')` | File extensions to index                                  |
| `auto_tag`           | `bool`                   | `True`                                     | Automatically tag samples with their parent directory names |
| `lazy`               | `bool`                   | `False`                                    | Defer loading until first access                           |
| `normalize`          | `bool`                   | `False`                                    | Normalize sample amplitude on load                         |
| `normalize_peak`     | `float`                  | `0.95`                                     | Target peak amplitude when normalizing                     |
| `target_sample_rate` | `Optional[int]`          | `None`                                     | Resample all loaded audio to this rate (e.g. `44100`)       |
| `trim_silence`       | `bool`                   | `False`                                    | Trim leading/trailing silence on load                      |
| `trim_threshold`     | `float`                  | `0.001`                                    | Amplitude threshold below which audio is considered silence |
| `default_tags`       | `list[str]`              | `[]`                                       | Tags applied to every sample in the library                |

```python
config = SampleLibraryConfig(
    lazy=True,
    normalize=True,
    normalize_peak=0.9,
    target_sample_rate=44100,
    trim_silence=True,
    default_tags=["project_x"],
)
```

---

## 3. SampleLibrary

```python
from beatmaker.io import SampleLibrary
```

A managed collection of `Sample` objects organized by path-based keys, tags,
and user-defined aliases.

### Constructor

```python
lib = SampleLibrary(config: Optional[SampleLibraryConfig] = None)
```

| Parameter | Type                           | Default | Description              |
|-----------|--------------------------------|---------|--------------------------|
| `config`  | `Optional[SampleLibraryConfig]`| `None`  | Library configuration    |

### `from_directory(directory, config=None, *, extensions=None, auto_tag=None, lazy=None) -> SampleLibrary`

Class method. Recursively scans `directory` for audio files and indexes them
using their path relative to the root (without extension, using forward
slashes).

| Parameter    | Type                            | Default | Description                             |
|--------------|---------------------------------|---------|-----------------------------------------|
| `directory`  | `Union[str, Path]`              | --      | Root folder to scan                     |
| `config`     | `Optional[SampleLibraryConfig]` | `None`  | Full configuration object               |
| `extensions` | `Optional[tuple[str, ...]]`     | `None`  | Override `config.extensions`            |
| `auto_tag`   | `Optional[bool]`                | `None`  | Override `config.auto_tag`              |
| `lazy`       | `Optional[bool]`                | `None`  | Override `config.lazy`                  |

Raises `FileNotFoundError` if the directory does not exist.

```python
lib = SampleLibrary.from_directory("./samples")
kick = lib["drums/kick"]          # from samples/drums/kick.wav
snare = lib["drums/snare_01"]     # from samples/drums/snare_01.wav
pad = lib["synths/pads/warm"]     # from samples/synths/pads/warm.wav
```

### `add(sample: Sample, key: Optional[str] = None) -> SampleLibrary`

Adds a sample to the library.

| Parameter | Type             | Default       | Description                           |
|-----------|------------------|---------------|---------------------------------------|
| `sample`  | `Sample`         | --            | Sample to add                         |
| `key`     | `Optional[str]`  | `sample.name` | Explicit key; defaults to sample name |

### `get(name: str) -> Optional[Sample]`

Returns the sample matching `name`, or `None`.

Resolution order:
1. Exact key match
2. Alias resolution, then key match

Lazy-loaded samples are materialized on first access.

### `__getitem__(name: str) -> Sample`

Same as `get`, but raises `KeyError` if not found. Also tries a stem-only
fallback (matching the last path component) before failing.

```python
kick = lib["kick"]            # alias, full key, or stem fallback
kick = lib["drums/808/kick"]  # full key
```

### `search(pattern: str) -> list[str]`

Returns all keys containing `pattern` as a case-insensitive substring.

| Parameter | Type  | Description            |
|-----------|-------|------------------------|
| `pattern` | `str` | Substring to search for |

```python
lib.search("kick")  # ['drums/kick', 'drums/kick_hard', 'perc/side_kick']
```

### `by_tag(tag: str) -> list[Sample]`

Returns all samples carrying the specified tag.

| Parameter | Type  | Description |
|-----------|-------|-------------|
| `tag`     | `str` | Tag to filter by |

```python
all_drums = lib.by_tag("drums")
```

### `keys() -> list[str]`

Returns a sorted list of all sample keys.

### `alias(short_name: str, target_key: str) -> SampleLibrary`

Registers a shorthand alias for a full key.

| Parameter    | Type  | Description                  |
|--------------|-------|------------------------------|
| `short_name` | `str` | Alias to register            |
| `target_key` | `str` | Full sample key it maps to   |

```python
lib.alias("kick", "drums/808/kick_hard")
kick = lib["kick"]  # resolves to drums/808/kick_hard
```

### `aliases(**mapping: str) -> SampleLibrary`

Registers multiple aliases at once.

```python
lib.aliases(
    kick="drums/808/kick_hard",
    snare="drums/acoustic/snare_02",
    pad="synths/pads/warm_analog",
)
```

### Additional Properties and Methods

| Member                      | Returns           | Description                                          |
|-----------------------------|-------------------|------------------------------------------------------|
| `names`                     | `list[str]`       | Sorted list of all sample keys                       |
| `tags`                      | `list[str]`       | Sorted list of all tags in the library               |
| `root`                      | `Optional[Path]`  | Root directory (if created via `from_directory`)      |
| `list(prefix: str = '')`   | `list[str]`       | Keys filtered by path prefix                         |
| `values()`                  | `list[Sample]`    | All samples (triggers lazy loading)                  |
| `items()`                   | `list[tuple]`     | All `(key, sample)` pairs                            |
| `__len__()`                 | `int`             | Number of samples                                    |
| `__contains__(name)`        | `bool`            | Check if key or alias exists                         |
| `__iter__()`                | iterator          | Yields `(key, sample)` pairs in sorted order         |

---

## 4. MIDI Types

```python
from beatmaker.midi import MIDINote, MIDITrack, MIDIFile
```

### MIDINote

A single MIDI note event.

| Field            | Type  | Default | Description                    |
|------------------|-------|---------|--------------------------------|
| `pitch`          | `int` | --      | MIDI note number (0-127)       |
| `velocity`       | `int` | --      | Velocity (0-127)               |
| `start_tick`     | `int` | --      | Start time in ticks            |
| `duration_ticks` | `int` | --      | Duration in ticks              |
| `channel`        | `int` | `0`     | MIDI channel (0-15)            |

#### Properties

- **`end_tick -> int`**: `start_tick + duration_ticks`

#### `to_seconds(ticks_per_beat: int, bpm: float) -> Tuple[float, float]`

Converts to `(start_time, duration)` in seconds.

| Parameter        | Type    | Description                     |
|------------------|---------|---------------------------------|
| `ticks_per_beat` | `int`   | PPQ resolution of the MIDI file |
| `bpm`            | `float` | Tempo in beats per minute       |

```python
note = MIDINote(pitch=60, velocity=100, start_tick=480, duration_ticks=240)
start, dur = note.to_seconds(ticks_per_beat=480, bpm=120.0)
# start = 0.5s, dur = 0.25s
```

### MIDITrack

A track containing notes and metadata.

| Field     | Type              | Default | Description              |
|-----------|-------------------|---------|--------------------------|
| `name`    | `str`             | `""`    | Track name               |
| `notes`   | `List[MIDINote]`  | `[]`    | Notes in this track      |
| `channel` | `int`             | `0`     | Default MIDI channel     |

#### `add_note(pitch, velocity, start_tick, duration_ticks) -> MIDITrack`

Adds a note to the track using the track's channel. Returns `self` for
chaining.

| Parameter        | Type  | Description               |
|------------------|-------|---------------------------|
| `pitch`          | `int` | MIDI note number (0-127)  |
| `velocity`       | `int` | Velocity (0-127)          |
| `start_tick`     | `int` | Start time in ticks       |
| `duration_ticks` | `int` | Duration in ticks         |

#### `get_notes_in_range(start_tick: int, end_tick: int) -> List[MIDINote]`

Returns all notes whose `start_tick` falls within `[start_tick, end_tick)`.

| Parameter    | Type  | Description           |
|--------------|-------|-----------------------|
| `start_tick` | `int` | Range start (inclusive) |
| `end_tick`   | `int` | Range end (exclusive)   |

#### Properties

- **`duration_ticks -> int`**: The `end_tick` of the latest note (0 if empty).

### MIDIFile

A complete MIDI file representation.

| Field            | Type              | Default   | Description                        |
|------------------|-------------------|-----------|------------------------------------|
| `tracks`         | `List[MIDITrack]` | `[]`      | All tracks                         |
| `ticks_per_beat` | `int`             | `480`     | PPQ (pulses per quarter note)      |
| `tempo`          | `float`           | `120.0`   | Tempo in BPM                       |
| `time_signature` | `Tuple[int, int]` | `(4, 4)`  | Time signature (numerator, denominator) |

#### Methods

| Method                                  | Returns   | Description                         |
|-----------------------------------------|-----------|-------------------------------------|
| `add_track(name="", channel=0)`         | `MIDITrack` | Creates and appends a new track   |
| `beats_to_ticks(beats: float)`          | `int`     | Convert beats to ticks              |
| `ticks_to_beats(ticks: int)`            | `float`   | Convert ticks to beats              |
| `ticks_to_seconds(ticks: int)`          | `float`   | Convert ticks to seconds            |
| `seconds_to_ticks(seconds: float)`      | `int`     | Convert seconds to ticks            |

#### Properties

- **`duration_ticks -> int`**: Maximum `duration_ticks` across all tracks.
- **`duration_seconds -> float`**: Total duration in seconds.

```python
midi = MIDIFile(tempo=140, ticks_per_beat=480, time_signature=(4, 4))
track = midi.add_track("Lead", channel=0)
track.add_note(60, 100, 0, 480)       # C4, quarter note at beat 0
track.add_note(64, 90, 480, 480)      # E4, quarter note at beat 1
track.add_note(67, 80, 960, 960)      # G4, half note at beat 2
```

---

## 5. MIDI I/O

```python
from beatmaker.midi import load_midi, save_midi, create_midi
```

### `load_midi(path: Union[str, Path]) -> MIDIFile`

Reads a Standard MIDI File (SMF format 0 or 1). Parses header, tempo, time
signature, track names, and note on/off events. Running status is supported.
Only tracks containing at least one note are included.

| Parameter | Type                | Description        |
|-----------|---------------------|--------------------|
| `path`    | `Union[str, Path]`  | Path to .mid file  |

```python
midi = load_midi("song.mid")
print(f"Tempo: {midi.tempo} BPM, Tracks: {len(midi.tracks)}")
```

### `save_midi(midi_file: MIDIFile, path: Union[str, Path]) -> None`

Writes a MIDI file to disk as SMF format 1 (multiple tracks). A dedicated
tempo track is written as track 0, containing tempo and time signature meta
events.

| Parameter   | Type                | Description          |
|-------------|---------------------|----------------------|
| `midi_file` | `MIDIFile`          | MIDI data to write   |
| `path`      | `Union[str, Path]`  | Output file path     |

```python
save_midi(midi, "output.mid")
```

### `create_midi(bpm: float = 120.0, ticks_per_beat: int = 480) -> MIDIFile`

Creates a new empty MIDI file with the specified tempo and resolution.

| Parameter        | Type    | Default | Description                   |
|------------------|---------|---------|-------------------------------|
| `bpm`            | `float` | `120.0` | Tempo in BPM                  |
| `ticks_per_beat` | `int`   | `480`   | PPQ resolution                |

```python
midi = create_midi(bpm=140, ticks_per_beat=960)
track = midi.add_track("Melody")
```

---

## 6. MIDI Conversion

```python
from beatmaker.midi import midi_to_beatmaker_events, beatmaker_events_to_midi, song_to_midi
```

### `midi_to_beatmaker_events(midi_file, track_index=0) -> List[Tuple[float, int, float, float]]`

Converts a MIDI track to beatmaker's event format.

| Parameter     | Type       | Default | Description                        |
|---------------|------------|---------|------------------------------------|
| `midi_file`   | `MIDIFile` | --      | Source MIDI file                   |
| `track_index` | `int`      | `0`     | Index of the track to convert      |

Returns a list of `(time_seconds, midi_note, velocity_normalized, duration_seconds)`
tuples, sorted by time. Velocity is normalized from 0-127 to 0.0-1.0.

```python
events = midi_to_beatmaker_events(midi, track_index=0)
for time, note, vel, dur in events:
    print(f"Note {note} at {time:.2f}s, vel={vel:.2f}, dur={dur:.2f}s")
```

### `beatmaker_events_to_midi(events, bpm=120.0, track_name="Track 1") -> MIDIFile`

Converts beatmaker event tuples back to a MIDI file.

| Parameter    | Type                                          | Default      | Description              |
|--------------|-----------------------------------------------|--------------|--------------------------|
| `events`     | `List[Tuple[float, int, float, float]]`       | --           | `(time_s, note, vel, dur_s)` |
| `bpm`        | `float`                                       | `120.0`      | Tempo for the MIDI file  |
| `track_name` | `str`                                         | `"Track 1"`  | Name for the MIDI track  |

Velocity is scaled from 0.0-1.0 back to 0-127. Duration ticks are clamped to
a minimum of 1.

```python
midi = beatmaker_events_to_midi(events, bpm=128, track_name="Synth Lead")
save_midi(midi, "lead.mid")
```

### `song_to_midi(song, include_drums: bool = True) -> MIDIFile`

Converts a full `Song` object to a MIDI file. Each track becomes a MIDI track
assigned to a sequential channel (0-15). Sample names are pattern-matched to
GM drum map notes: `"kick"` -> 36, `"snare"` -> 38, `"hihat"` / `"hat"` -> 42,
`"clap"` -> 39. Other samples use a base note determined by track type (drums:
36, bass: 36, other: 60).

| Parameter      | Type   | Default | Description                  |
|----------------|--------|---------|------------------------------|
| `song`         | `Song` | --      | Song to convert              |
| `include_drums`| `bool` | `True`  | Whether to include drum tracks |

```python
midi = song_to_midi(my_song, include_drums=True)
save_midi(midi, "full_song.mid")
```

---

## 7. Utilities

```python
from beatmaker.utils import (
    detect_bpm, detect_onsets, slice_at_onsets, extract_samples_from_file,
    split_stereo, merge_to_stereo, time_stretch, pitch_shift,
    reverse, loop, crossfade, concatenate, mix, export_samples,
)
```

### `detect_bpm(audio, min_bpm=60, max_bpm=200) -> float`

Estimates the BPM of an audio signal using onset-based autocorrelation.

| Parameter | Type        | Default | Description                    |
|-----------|-------------|---------|--------------------------------|
| `audio`   | `AudioData` | --      | Input audio                    |
| `min_bpm` | `float`     | `60`    | Lower bound for BPM search    |
| `max_bpm` | `float`     | `200`   | Upper bound for BPM search    |

Returns the estimated BPM as a `float`, rounded to one decimal place.
Returns `120.0` if detection fails.

```python
bpm = detect_bpm(load_audio("loop.wav"))
```

### `detect_onsets(audio, threshold=0.1, min_interval=0.05) -> List[float]`

Detects onset times in audio using RMS envelope peak-picking.

| Parameter      | Type        | Default | Description                                    |
|----------------|-------------|---------|------------------------------------------------|
| `audio`        | `AudioData` | --      | Input audio                                    |
| `threshold`    | `float`     | `0.1`   | Minimum normalized envelope level for an onset |
| `min_interval` | `float`     | `0.05`  | Minimum time in seconds between onsets         |

Returns a list of onset times in seconds.

```python
onsets = detect_onsets(drum_loop, threshold=0.15)
```

### `slice_at_onsets(audio, onsets=None, min_duration=0.05) -> List[AudioData]`

Slices audio at onset points into individual segments.

| Parameter      | Type                   | Default | Description                                |
|----------------|------------------------|---------|--------------------------------------------|
| `audio`        | `AudioData`            | --      | Audio to slice                             |
| `onsets`       | `Optional[List[float]]`| `None`  | Onset times in seconds; auto-detected if `None` |
| `min_duration` | `float`                | `0.05`  | Minimum slice duration in seconds          |

Returns a list of `AudioData` slices.

```python
slices = slice_at_onsets(drum_loop)
```

### `extract_samples_from_file(path, prefix="sample", min_duration=0.05) -> List[Sample]`

Loads an audio file, detects onsets, slices, normalizes each slice, and
returns a list of `Sample` objects.

| Parameter      | Type                | Default    | Description                        |
|----------------|---------------------|------------|------------------------------------|
| `path`         | `Union[str, Path]`  | --         | Path to the audio file             |
| `prefix`       | `str`               | `"sample"` | Name prefix for extracted samples  |
| `min_duration` | `float`             | `0.05`     | Minimum slice duration in seconds  |

Samples are named `"{prefix}_000"`, `"{prefix}_001"`, etc.

```python
hits = extract_samples_from_file("breaks/amen.wav", prefix="amen")
```

### `split_stereo(audio) -> Tuple[AudioData, AudioData]`

Splits stereo audio into separate left and right mono `AudioData` objects.
Raises `ValueError` if the input is not stereo.

| Parameter | Type        | Description         |
|-----------|-------------|---------------------|
| `audio`   | `AudioData` | Stereo audio input  |

```python
left, right = split_stereo(stereo_audio)
```

### `merge_to_stereo(left, right) -> AudioData`

Merges two mono `AudioData` objects into a stereo `AudioData`.  Resamples
the right channel if sample rates differ. Zero-pads the shorter signal.
Raises `ValueError` if either input is not mono.

| Parameter | Type        | Description       |
|-----------|-------------|-------------------|
| `left`    | `AudioData` | Left channel      |
| `right`   | `AudioData` | Right channel     |

```python
stereo = merge_to_stereo(left_audio, right_audio)
```

### `time_stretch(audio, factor) -> AudioData`

Time-stretches audio without changing pitch using overlap-add (OLA).

| Parameter | Type        | Description                                    |
|-----------|-------------|------------------------------------------------|
| `audio`   | `AudioData` | Input audio                                    |
| `factor`  | `float`     | Stretch factor. `> 1.0` = slower, `< 1.0` = faster |

Returns unchanged audio if `factor == 1.0`. Multichannel audio is processed
per-channel.

```python
slower = time_stretch(audio, 1.5)   # 50% slower
faster = time_stretch(audio, 0.75)  # 25% faster
```

### `pitch_shift(audio, semitones) -> AudioData`

Shifts pitch by resampling. **This changes duration.** For constant-duration
pitch shifting, combine with `time_stretch`.

| Parameter   | Type        | Description                         |
|-------------|-------------|-------------------------------------|
| `audio`     | `AudioData` | Input audio                         |
| `semitones` | `float`     | Pitch shift amount (+/- semitones)  |

```python
higher = pitch_shift(audio, 7)     # up a fifth
lower = pitch_shift(audio, -12)    # down an octave
```

### `reverse(audio) -> AudioData`

Returns a reversed copy of the audio.

| Parameter | Type        | Description   |
|-----------|-------------|---------------|
| `audio`   | `AudioData` | Input audio   |

```python
rev = reverse(cymbal)
```

### `loop(audio, times) -> AudioData`

Repeats audio the specified number of times. Returns the original if
`times <= 1`.

| Parameter | Type        | Description                |
|-----------|-------------|----------------------------|
| `audio`   | `AudioData` | Input audio                |
| `times`   | `int`       | Number of repetitions      |

```python
looped = loop(one_bar, 8)
```

### `crossfade(audio1, audio2, duration=0.1) -> AudioData`

Concatenates two audio segments with a crossfade overlap. Automatically
handles sample rate and channel count mismatches.

| Parameter  | Type        | Default | Description                          |
|------------|-------------|---------|--------------------------------------|
| `audio1`   | `AudioData` | --      | First audio segment                  |
| `audio2`   | `AudioData` | --      | Second audio segment                 |
| `duration` | `float`     | `0.1`   | Crossfade duration in seconds        |

The crossfade duration is clamped to the shorter of the two inputs.

```python
joined = crossfade(verse_audio, chorus_audio, duration=0.5)
```

### `concatenate(*audios) -> AudioData`

Concatenates multiple audio segments end-to-end.  Automatically resamples
and converts channels to match the first segment.

| Parameter | Type           | Description                     |
|-----------|----------------|---------------------------------|
| `*audios` | `AudioData...` | Audio segments to concatenate   |

```python
full = concatenate(intro, verse, chorus, outro)
```

### `mix(*audios, volumes=None) -> AudioData`

Mixes (sums) multiple audio streams together with optional per-stream
volume control.

| Parameter | Type                    | Default           | Description                    |
|-----------|-------------------------|--------------------|-------------------------------|
| `*audios` | `AudioData...`          | --                | Audio streams to mix           |
| `volumes` | `Optional[List[float]]` | `[1.0, 1.0, ...]` | Per-stream volume multipliers  |

Output length and channel count match the longest / widest input.

```python
mixed = mix(drums, bass, synth, volumes=[1.0, 0.8, 0.6])
```

### `export_samples(samples, directory, format='wav') -> List[Path]`

Exports a list of `Sample` objects to individual files, creating the
directory if needed.

| Parameter   | Type                | Default | Description                    |
|-------------|---------------------|---------|--------------------------------|
| `samples`   | `List[Sample]`      | --      | Samples to export              |
| `directory` | `Union[str, Path]`  | --      | Output directory               |
| `format`    | `str`               | `'wav'` | Audio format for output files  |

Returns a list of `Path` objects for the created files.  Each file is named
`"{sample.name}.{format}"`.

```python
hits = extract_samples_from_file("breaks/amen.wav", prefix="amen")
paths = export_samples(hits, "./extracted/amen/", format='wav')
```
