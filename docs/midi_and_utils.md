# API Reference: `beatmaker.midi` and `beatmaker.utils`

This document provides a comprehensive API reference for all public classes, methods, and functions in the `beatmaker.midi` and `beatmaker.utils` modules.

---

# Module: `beatmaker.midi`

MIDI reading, writing, and conversion utilities for the beatmaker system. Supports Standard MIDI Files (SMF) format 1.

---

## MIDINote

A dataclass representing a single MIDI note event.

### Constructor Parameters

- **pitch** (`int`): MIDI note number, range 0-127.
- **velocity** (`int`): Note velocity, range 0-127.
- **start_tick** (`int`): Start time of the note in ticks.
- **duration_ticks** (`int`): Duration of the note in ticks.
- **channel** (`int`): MIDI channel, range 0-15. Default: `0`.

### Properties

#### `end_tick`

```python
@property
def end_tick(self) -> int
```

Returns the tick at which the note ends (`start_tick + duration_ticks`).

**Returns**
`int`: The end tick of the note.

### Methods

#### `to_seconds()`

```python
def to_seconds(self, ticks_per_beat: int, bpm: float) -> Tuple[float, float]
```

Convert the note's timing to seconds.

**Parameters**
- **ticks_per_beat** (`int`): The MIDI file's PPQ (pulses per quarter note) resolution.
- **bpm** (`float`): Tempo in beats per minute.

**Returns**
`Tuple[float, float]`: A tuple of `(start_time, duration)` in seconds.

### Example

```python
note = MIDINote(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
start, dur = note.to_seconds(ticks_per_beat=480, bpm=120.0)
# start = 0.0, dur = 0.5
```

---

## MIDITrack

A dataclass representing a MIDI track containing notes and metadata.

### Constructor Parameters

- **name** (`str`): Name of the track. Default: `""`.
- **notes** (`List[MIDINote]`): List of MIDI notes in the track. Default: `[]` (empty list).
- **channel** (`int`): MIDI channel for new notes added via `add_note()`. Default: `0`.

### Properties

#### `duration_ticks`

```python
@property
def duration_ticks(self) -> int
```

Total duration of the track in ticks, determined by the latest-ending note.

**Returns**
`int`: Duration in ticks. Returns `0` if the track has no notes.

### Methods

#### `add_note()`

```python
def add_note(self, pitch: int, velocity: int, start_tick: int, duration_ticks: int) -> MIDITrack
```

Add a note to the track. The note inherits the track's `channel` attribute.

**Parameters**
- **pitch** (`int`): MIDI note number (0-127).
- **velocity** (`int`): Note velocity (0-127).
- **start_tick** (`int`): Start time in ticks.
- **duration_ticks** (`int`): Duration in ticks.

**Returns**
`MIDITrack`: Returns `self` for method chaining.

#### `get_notes_in_range()`

```python
def get_notes_in_range(self, start_tick: int, end_tick: int) -> List[MIDINote]
```

Retrieve all notes whose `start_tick` falls within the specified range (inclusive start, exclusive end).

**Parameters**
- **start_tick** (`int`): Start of the tick range (inclusive).
- **end_tick** (`int`): End of the tick range (exclusive).

**Returns**
`List[MIDINote]`: List of notes within the range.

### Example

```python
track = MIDITrack(name="Piano", channel=0)
track.add_note(60, 100, 0, 480).add_note(64, 80, 480, 480)
notes = track.get_notes_in_range(0, 480)  # returns the first note only
```

---

## MIDIFile

A dataclass representing a complete MIDI file. Supports reading and writing Standard MIDI Files (SMF) format 1, with a dedicated tempo track and one or more note tracks.

### Constructor Parameters

- **tracks** (`List[MIDITrack]`): List of tracks in the file. Default: `[]` (empty list).
- **ticks_per_beat** (`int`): PPQ resolution (pulses per quarter note). Default: `480`.
- **tempo** (`float`): Tempo in BPM. Default: `120.0`.
- **time_signature** (`Tuple[int, int]`): Time signature as `(numerator, denominator)`. Default: `(4, 4)`.

### Properties

#### `duration_ticks`

```python
@property
def duration_ticks(self) -> int
```

Total duration of the MIDI file in ticks, determined by the longest track.

**Returns**
`int`: Duration in ticks. Returns `0` if there are no tracks.

#### `duration_seconds`

```python
@property
def duration_seconds(self) -> float
```

Total duration of the MIDI file in seconds, derived from `duration_ticks` and the current tempo.

**Returns**
`float`: Duration in seconds.

### Methods

#### `add_track()`

```python
def add_track(self, name: str = "", channel: int = 0) -> MIDITrack
```

Create and add a new track to the MIDI file.

**Parameters**
- **name** (`str`): Name of the track. Default: `""`.
- **channel** (`int`): MIDI channel for the track. Default: `0`.

**Returns**
`MIDITrack`: The newly created track.

#### `beats_to_ticks()`

```python
def beats_to_ticks(self, beats: float) -> int
```

Convert a beat count to ticks.

**Parameters**
- **beats** (`float`): Number of beats.

**Returns**
`int`: Equivalent number of ticks.

#### `ticks_to_beats()`

```python
def ticks_to_beats(self, ticks: int) -> float
```

Convert ticks to a beat count.

**Parameters**
- **ticks** (`int`): Number of ticks.

**Returns**
`float`: Equivalent number of beats.

#### `ticks_to_seconds()`

```python
def ticks_to_seconds(self, ticks: int) -> float
```

Convert ticks to seconds based on the current tempo and PPQ.

**Parameters**
- **ticks** (`int`): Number of ticks.

**Returns**
`float`: Equivalent time in seconds.

#### `seconds_to_ticks()`

```python
def seconds_to_ticks(self, seconds: float) -> int
```

Convert seconds to ticks based on the current tempo and PPQ.

**Parameters**
- **seconds** (`float`): Time in seconds.

**Returns**
`int`: Equivalent number of ticks.

### Example

```python
midi = MIDIFile(tempo=140.0, ticks_per_beat=480, time_signature=(4, 4))
track = midi.add_track("Lead", channel=0)
track.add_note(60, 100, 0, midi.beats_to_ticks(1.0))
print(midi.duration_seconds)
```

---

## MIDIReader

Static class for reading Standard MIDI Files from disk.

### Methods

#### `read()`

```python
@staticmethod
def read(path: Union[str, Path]) -> MIDIFile
```

Read and parse a Standard MIDI File. Supports SMF format 0 and 1. Parses header, tempo, time signature, track names, and note on/off events. Only tracks that contain notes are included in the returned `MIDIFile`.

**Parameters**
- **path** (`Union[str, Path]`): Path to the `.mid` file.

**Returns**
`MIDIFile`: A fully populated `MIDIFile` instance.

**Raises**
- `ValueError`: If the file does not begin with a valid `MThd` header or contains an invalid track chunk.

### Example

```python
midi = MIDIReader.read("song.mid")
print(f"Tempo: {midi.tempo} BPM, Tracks: {len(midi.tracks)}")
```

---

## MIDIWriter

Static class for writing Standard MIDI Files to disk. Outputs SMF format 1 with a dedicated tempo track (track 0) followed by note tracks.

### Methods

#### `write()`

```python
@staticmethod
def write(midi_file: MIDIFile, path: Union[str, Path]) -> None
```

Write a `MIDIFile` to disk as a Standard MIDI File. The output file includes a tempo track (containing tempo and time signature meta events) followed by all note tracks.

**Parameters**
- **midi_file** (`MIDIFile`): The MIDI file to write.
- **path** (`Union[str, Path]`): Destination file path.

**Returns**
`None`

### Example

```python
midi = MIDIFile(tempo=120.0)
track = midi.add_track("Bass")
track.add_note(36, 100, 0, 480)
MIDIWriter.write(midi, "output.mid")
```

---

## `load_midi()`

```python
def load_midi(path: Union[str, Path]) -> MIDIFile
```

Convenience wrapper around `MIDIReader.read()`. Loads a MIDI file from disk.

### Parameters

- **path** (`Union[str, Path]`): Path to the `.mid` file.

### Returns

`MIDIFile`: The parsed MIDI file.

### Example

```python
midi = load_midi("drums.mid")
```

---

## `save_midi()`

```python
def save_midi(midi_file: MIDIFile, path: Union[str, Path]) -> None
```

Convenience wrapper around `MIDIWriter.write()`. Saves a MIDI file to disk.

### Parameters

- **midi_file** (`MIDIFile`): The MIDI file to save.
- **path** (`Union[str, Path]`): Destination file path.

### Returns

`None`

### Example

```python
save_midi(midi, "output.mid")
```

---

## `create_midi()`

```python
def create_midi(bpm: float = 120.0, ticks_per_beat: int = 480) -> MIDIFile
```

Create a new empty MIDI file with the specified tempo and resolution.

### Parameters

- **bpm** (`float`): Tempo in beats per minute. Default: `120.0`.
- **ticks_per_beat** (`int`): PPQ resolution. Default: `480`.

### Returns

`MIDIFile`: A new empty `MIDIFile` instance.

### Example

```python
midi = create_midi(bpm=140.0, ticks_per_beat=960)
track = midi.add_track("Melody")
```

---

## `midi_to_beatmaker_events()`

```python
def midi_to_beatmaker_events(
    midi_file: MIDIFile,
    track_index: int = 0
) -> List[Tuple[float, int, float, float]]
```

Convert a single MIDI track into a list of beatmaker event tuples. Each event represents a note with its timing, pitch, normalized velocity, and duration, all expressed in seconds.

### Parameters

- **midi_file** (`MIDIFile`): The source MIDI file.
- **track_index** (`int`): Index of the track to convert. Default: `0`.

### Returns

`List[Tuple[float, int, float, float]]`: A list of tuples, each containing:
- `time_seconds` (`float`): Note start time in seconds.
- `midi_note` (`int`): MIDI note number (0-127).
- `velocity_normalized` (`float`): Velocity normalized to range 0.0-1.0.
- `duration_seconds` (`float`): Note duration in seconds.

The list is sorted by `time_seconds`.

Returns an empty list if `track_index` is out of range.

### Example

```python
midi = load_midi("beat.mid")
events = midi_to_beatmaker_events(midi, track_index=0)
for time, note, vel, dur in events:
    print(f"Note {note} at {time:.3f}s, vel={vel:.2f}, dur={dur:.3f}s")
```

---

## `beatmaker_events_to_midi()`

```python
def beatmaker_events_to_midi(
    events: List[Tuple[float, int, float, float]],
    bpm: float = 120.0,
    track_name: str = "Track 1"
) -> MIDIFile
```

Convert a list of beatmaker event tuples into a `MIDIFile`. This is the inverse of `midi_to_beatmaker_events()`.

### Parameters

- **events** (`List[Tuple[float, int, float, float]]`): List of event tuples, each containing `(time_seconds, midi_note, velocity_normalized, duration_seconds)`.
- **bpm** (`float`): Tempo for the resulting MIDI file. Default: `120.0`.
- **track_name** (`str`): Name assigned to the created track. Default: `"Track 1"`.

### Returns

`MIDIFile`: A new MIDI file containing a single track with the converted notes. Duration ticks are clamped to a minimum of 1.

### Example

```python
events = [
    (0.0, 36, 1.0, 0.25),   # Kick at beat 1
    (0.5, 38, 0.8, 0.25),   # Snare at beat 2
]
midi = beatmaker_events_to_midi(events, bpm=120.0, track_name="Drums")
save_midi(midi, "drums.mid")
```

---

## `song_to_midi()`

```python
def song_to_midi(song, include_drums: bool = True) -> MIDIFile
```

Convert a `Song` object (from `beatmaker.core`) to a `MIDIFile`. Performs a basic conversion where each track's sample placements become MIDI note triggers. Drum samples are mapped to General MIDI drum note numbers by name heuristics.

### Parameters

- **song** (`Song`): The song to convert. Must have `bpm` and `tracks` attributes.
- **include_drums** (`bool`): Whether to include drum tracks in the output. Default: `True`.

### Returns

`MIDIFile`: A MIDI file with one track per song track.

### Note Mapping

The function uses sample name heuristics:
- Names containing `"kick"` map to MIDI note `36`.
- Names containing `"snare"` map to MIDI note `38`.
- Names containing `"hihat"` or `"hat"` map to MIDI note `42`.
- Names containing `"clap"` map to MIDI note `39`.
- Other drum samples default to note `36`; bass tracks default to `36`; other tracks default to `60` (Middle C).

### Example

```python
from beatmaker.core import Song
song = Song(bpm=130)
# ... add tracks and placements ...
midi = song_to_midi(song, include_drums=True)
save_midi(midi, "song_export.mid")
```

---

# Module: `beatmaker.utils`

Audio analysis, manipulation, and export utilities. All functions operate on `AudioData` instances from `beatmaker.core`.

---

## `detect_bpm()`

```python
def detect_bpm(audio: AudioData, min_bpm: float = 60, max_bpm: float = 200) -> float
```

Estimate the tempo (BPM) of an audio signal using onset-based autocorrelation. Internally converts stereo to mono, computes short-window energy, derives spectral flux, and finds the dominant periodicity via autocorrelation.

### Parameters

- **audio** (`AudioData`): The audio signal to analyze.
- **min_bpm** (`float`): Lower bound of the BPM search range. Default: `60`.
- **max_bpm** (`float`): Upper bound of the BPM search range. Default: `200`.

### Returns

`float`: The estimated BPM, rounded to one decimal place. Returns `120.0` as a default if the autocorrelation search range is empty.

### Example

```python
from beatmaker.io import load_audio
audio = load_audio("loop.wav")
bpm = detect_bpm(audio, min_bpm=80, max_bpm=180)
print(f"Estimated BPM: {bpm}")
```

---

## `detect_onsets()`

```python
def detect_onsets(audio: AudioData, threshold: float = 0.1, min_interval: float = 0.05) -> List[float]
```

Detect onset (transient) times in an audio signal. Uses RMS envelope computation with peak-picking. Stereo audio is first converted to mono internally.

### Parameters

- **audio** (`AudioData`): The audio signal to analyze.
- **threshold** (`float`): Minimum normalized envelope amplitude for an onset to be registered. Range 0.0-1.0. Default: `0.1`.
- **min_interval** (`float`): Minimum time in seconds between consecutive onsets, preventing double-triggers. Default: `0.05`.

### Returns

`List[float]`: A list of onset times in seconds, sorted chronologically.

### Example

```python
audio = load_audio("drum_loop.wav")
onsets = detect_onsets(audio, threshold=0.15, min_interval=0.1)
print(f"Found {len(onsets)} onsets: {onsets}")
```

---

## `slice_at_onsets()`

```python
def slice_at_onsets(
    audio: AudioData,
    onsets: Optional[List[float]] = None,
    min_duration: float = 0.05
) -> List[AudioData]
```

Slice an audio signal at onset points, producing a list of individual audio segments. If no onsets are provided, they are detected automatically via `detect_onsets()`.

### Parameters

- **audio** (`AudioData`): The audio signal to slice.
- **onsets** (`Optional[List[float]]`): List of onset times in seconds. If `None`, onsets are detected automatically. Default: `None`.
- **min_duration** (`float`): Minimum duration in seconds for a slice to be included. Slices shorter than this are discarded. Default: `0.05`.

### Returns

`List[AudioData]`: A list of audio segments. Returns `[audio]` (the original, unsliced) if no onsets are detected.

### Example

```python
audio = load_audio("break.wav")
slices = slice_at_onsets(audio, min_duration=0.1)
print(f"Extracted {len(slices)} slices")
```

---

## `extract_samples_from_file()`

```python
def extract_samples_from_file(
    path: Union[str, Path],
    prefix: str = "sample",
    min_duration: float = 0.05
) -> List[Sample]
```

Load an audio file, detect onsets, slice at those onsets, and return each slice as a normalized `Sample`. Useful for extracting individual drum hits from a loop or break.

### Parameters

- **path** (`Union[str, Path]`): Path to the audio file.
- **prefix** (`str`): Naming prefix for extracted samples. Samples are named `"{prefix}_000"`, `"{prefix}_001"`, etc. Default: `"sample"`.
- **min_duration** (`float`): Minimum duration in seconds for a slice to be kept. Default: `0.05`.

### Returns

`List[Sample]`: A list of `Sample` objects, each with normalized audio data.

### Example

```python
samples = extract_samples_from_file("amen_break.wav", prefix="amen")
print(f"Extracted {len(samples)} samples")
# samples[0].name == "amen_000"
```

---

## `split_stereo()`

```python
def split_stereo(audio: AudioData) -> Tuple[AudioData, AudioData]
```

Split a stereo audio signal into its left and right channels as two separate mono `AudioData` instances.

### Parameters

- **audio** (`AudioData`): A stereo audio signal. Must have exactly 2 channels.

### Returns

`Tuple[AudioData, AudioData]`: A tuple of `(left, right)` mono `AudioData` instances.

### Raises

- `ValueError`: If the input audio is not stereo (does not have exactly 2 channels).

### Example

```python
stereo = load_audio("stereo_file.wav")
left, right = split_stereo(stereo)
```

---

## `merge_to_stereo()`

```python
def merge_to_stereo(left: AudioData, right: AudioData) -> AudioData
```

Merge two mono audio signals into a single stereo `AudioData`. If the signals have different lengths, the shorter one is zero-padded. If sample rates differ, the right channel is resampled to match the left.

### Parameters

- **left** (`AudioData`): The left channel. Must be mono (1 channel).
- **right** (`AudioData`): The right channel. Must be mono (1 channel).

### Returns

`AudioData`: A stereo `AudioData` with 2 channels, using the left channel's sample rate.

### Raises

- `ValueError`: If either input is not mono.

### Example

```python
left, right = split_stereo(stereo_audio)
# Process channels independently...
merged = merge_to_stereo(left, right)
```

---

## `time_stretch()`

```python
def time_stretch(audio: AudioData, factor: float) -> AudioData
```

Time-stretch audio without changing its pitch using a simplified overlap-add (OLA) algorithm. For multi-channel audio, each channel is processed independently via recursion.

### Parameters

- **audio** (`AudioData`): The audio signal to stretch.
- **factor** (`float`): The stretch factor.
  - `factor > 1.0`: Audio becomes slower (longer).
  - `factor < 1.0`: Audio becomes faster (shorter).
  - `factor == 1.0`: Returns the original audio unchanged.

### Returns

`AudioData`: The time-stretched audio. Multi-channel input produces multi-channel output; mono input produces mono output.

### Example

```python
audio = load_audio("loop.wav")
slower = time_stretch(audio, 1.5)   # 50% slower
faster = time_stretch(audio, 0.75)  # 25% faster
```

---

## `pitch_shift()`

```python
def pitch_shift(audio: AudioData, semitones: float) -> AudioData
```

Shift the pitch of audio by a given number of semitones using resampling (linear interpolation). Note: this also changes the duration. To pitch-shift without changing duration, combine with `time_stretch()`.

### Parameters

- **audio** (`AudioData`): The audio signal to pitch-shift.
- **semitones** (`float`): Number of semitones to shift. Positive values shift up, negative values shift down. Fractional values are supported.

### Returns

`AudioData`: The pitch-shifted audio. The duration changes by a factor of `2^(-semitones/12)`.

### Example

```python
audio = load_audio("vocal.wav")
up = pitch_shift(audio, 5)     # Up 5 semitones
down = pitch_shift(audio, -3)  # Down 3 semitones

# Pitch shift without duration change:
shifted = pitch_shift(audio, 2)
corrected = time_stretch(shifted, 2 ** (2 / 12))
```

---

## `reverse()`

```python
def reverse(audio: AudioData) -> AudioData
```

Reverse the audio signal.

### Parameters

- **audio** (`AudioData`): The audio signal to reverse.

### Returns

`AudioData`: A new `AudioData` with the samples in reverse order. Sample rate and channel count are preserved.

### Example

```python
reversed_audio = reverse(audio)
```

---

## `loop()`

```python
def loop(audio: AudioData, times: int) -> AudioData
```

Repeat (tile) an audio signal a specified number of times.

### Parameters

- **audio** (`AudioData`): The audio signal to loop.
- **times** (`int`): Number of times to repeat the audio. If `<= 1`, the original audio is returned unchanged.

### Returns

`AudioData`: The looped audio. Total duration is `audio.duration * times`.

### Example

```python
one_bar = load_audio("bar.wav")
four_bars = loop(one_bar, 4)
```

---

## `crossfade()`

```python
def crossfade(audio1: AudioData, audio2: AudioData, duration: float = 0.1) -> AudioData
```

Join two audio segments with a crossfade transition. The end of `audio1` fades out while the beginning of `audio2` fades in over the specified duration. Automatically handles sample rate and channel count mismatches by resampling/converting as needed.

### Parameters

- **audio1** (`AudioData`): The first audio segment.
- **audio2** (`AudioData`): The second audio segment.
- **duration** (`float`): Crossfade duration in seconds. Clamped to be no longer than either input. Default: `0.1`.

### Returns

`AudioData`: The joined audio. Total length is `len(audio1) + len(audio2) - crossfade_samples`.

### Example

```python
intro = load_audio("intro.wav")
verse = load_audio("verse.wav")
joined = crossfade(intro, verse, duration=0.5)
```

---

## `concatenate()`

```python
def concatenate(*audios: AudioData) -> AudioData
```

Concatenate multiple audio segments end-to-end. All inputs are converted to match the sample rate and channel count of the first argument.

### Parameters

- **\*audios** (`AudioData`): Variable number of audio segments to concatenate.

### Returns

`AudioData`: A single `AudioData` containing all segments in order. Returns `AudioData.silence(0.0)` if no arguments are provided.

### Example

```python
full = concatenate(intro, verse, chorus, outro)
```

---

## `mix()`

```python
def mix(*audios: AudioData, volumes: Optional[List[float]] = None) -> AudioData
```

Mix (sum) multiple audio streams together. Shorter signals are zero-padded to match the longest. All inputs are converted to match the sample rate of the first argument and the highest channel count among all inputs.

### Parameters

- **\*audios** (`AudioData`): Variable number of audio signals to mix.
- **volumes** (`Optional[List[float]]`): Per-stream volume multipliers. Must have the same length as `audios` if provided. Default: `None` (all volumes set to `1.0`).

### Returns

`AudioData`: The mixed audio signal. Returns `AudioData.silence(0.0)` if no arguments are provided.

### Example

```python
drums = load_audio("drums.wav")
bass = load_audio("bass.wav")
keys = load_audio("keys.wav")
mixed = mix(drums, bass, keys, volumes=[1.0, 0.8, 0.6])
```

---

## `export_samples()`

```python
def export_samples(
    samples: List[Sample],
    directory: Union[str, Path],
    format: str = 'wav'
) -> List[Path]
```

Export a list of `Sample` objects to individual audio files in a directory. The directory is created if it does not exist (including parent directories).

### Parameters

- **samples** (`List[Sample]`): List of samples to export.
- **directory** (`Union[str, Path]`): Output directory path.
- **format** (`str`): Audio file format extension (e.g., `'wav'`, `'flac'`). Default: `'wav'`.

### Returns

`List[Path]`: List of `Path` objects pointing to the exported files. Each file is named `"{sample.name}.{format}"`.

### Example

```python
samples = extract_samples_from_file("break.wav", prefix="hit")
paths = export_samples(samples, "output/samples", format="wav")
for p in paths:
    print(f"Exported: {p}")
```
