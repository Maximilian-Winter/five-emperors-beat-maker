# API Reference: `beatmaker.core` and `beatmaker.io`

This document provides a comprehensive reference for all public classes, methods, properties, and functions exported by the `core` and `io` modules of the beatmaker package.

---

## NoteValue

**Module:** `beatmaker.core`

An enumeration of musical note durations expressed as fractions of a whole note.

### Members

| Member              | Value       | Description                              |
|---------------------|-------------|------------------------------------------|
| `WHOLE`             | `1.0`       | Whole note                               |
| `HALF`              | `0.5`       | Half note                                |
| `QUARTER`           | `0.25`      | Quarter note                             |
| `EIGHTH`            | `0.125`     | Eighth note                              |
| `SIXTEENTH`         | `0.0625`    | Sixteenth note                           |
| `THIRTY_SECOND`     | `0.03125`   | Thirty-second note                       |
| `DOTTED_HALF`       | `0.75`      | Dotted half note (half + quarter)        |
| `DOTTED_QUARTER`    | `0.375`     | Dotted quarter note (quarter + eighth)   |
| `DOTTED_EIGHTH`     | `0.1875`    | Dotted eighth note (eighth + sixteenth)  |
| `TRIPLET_QUARTER`   | `1/6`       | Quarter-note triplet                     |
| `TRIPLET_EIGHTH`    | `1/12`      | Eighth-note triplet                      |

**Usage:**

```python
from beatmaker.core import NoteValue

dur = NoteValue.QUARTER.value  # 0.25
```

---

## TrackType

**Module:** `beatmaker.core`

An enumeration classifying the purpose of a track.

### Members

| Member    | Description                             |
|-----------|-----------------------------------------|
| `DRUMS`   | Percussive / drum track                 |
| `BASS`    | Bass line track                         |
| `LEAD`    | Lead melody track                       |
| `PAD`     | Sustained pad / chord track             |
| `VOCAL`   | Vocal track                             |
| `FX`      | Sound effects track                     |
| `BACKING` | Backing / accompaniment track           |

**Usage:**

```python
from beatmaker.core import TrackType

t = TrackType.DRUMS
```

---

## TimeSignature

**Module:** `beatmaker.core`

A dataclass representing a musical time signature, with utility methods for converting between beats, bars, and seconds.

### Constructor

```python
TimeSignature(beats_per_bar: int = 4, beat_value: int = 4)
```

- **beats_per_bar** (`int`): Number of beats in one bar. Default: `4`.
- **beat_value** (`int`): The note value that receives one beat (4 = quarter note, 8 = eighth note, etc.). Default: `4`.

### Methods

#### `.beats_to_seconds(beats: float, bpm: float) -> float`

Convert a number of beats to seconds at the given tempo.

- **beats** (`float`): Number of beats.
- **bpm** (`float`): Tempo in beats per minute.
- **Returns:** Duration in seconds.

```python
ts = TimeSignature(4, 4)
ts.beats_to_seconds(4, 120.0)  # 2.0 seconds
```

#### `.bars_to_seconds(bars: float, bpm: float) -> float`

Convert a number of bars to seconds at the given tempo.

- **bars** (`float`): Number of bars.
- **bpm** (`float`): Tempo in beats per minute.
- **Returns:** Duration in seconds.

```python
ts = TimeSignature(4, 4)
ts.bars_to_seconds(2, 120.0)  # 4.0 seconds
```

---

## AudioData

**Module:** `beatmaker.core`

A dataclass representing raw audio data -- the atomic unit of sound in the system. Wraps a NumPy array of audio samples together with sample rate and channel count metadata.

### Constructor

```python
AudioData(samples: np.ndarray, sample_rate: int = 44100, channels: int = 1)
```

- **samples** (`np.ndarray`): NumPy array of audio sample values. 1-D for mono, 2-D `(num_samples, channels)` for multi-channel.
- **sample_rate** (`int`): Number of samples per second. Default: `44100`.
- **channels** (`int`): Number of audio channels. Default: `1`. **Note:** This field is automatically corrected in `__post_init__` based on the dimensionality of `samples`. A 1-D array forces `channels = 1`; a 2-D array sets `channels` to the size of the second axis.

### Properties

- **duration** (`float`): Duration of the audio in seconds. Computed as `len(samples) / sample_rate`.
- **num_samples** (`int`): Total number of sample frames (i.e., `len(samples)`).

### Methods

#### `.to_mono() -> AudioData`

Convert stereo (or multi-channel) audio to mono by averaging all channels. Returns `self` unchanged if already mono.

- **Returns:** A new `AudioData` with 1 channel.

```python
mono = audio.to_mono()
```

#### `.to_stereo() -> AudioData`

Convert mono audio to stereo by duplicating the single channel. Returns `self` unchanged if already stereo.

- **Returns:** A new `AudioData` with 2 channels.

```python
stereo = audio.to_stereo()
```

#### `.normalize(peak: float = 0.95) -> AudioData`

Normalize the audio so that its peak absolute value equals `peak`. If the audio is completely silent (max amplitude is 0), returns `self` unchanged.

- **peak** (`float`): Target peak amplitude. Default: `0.95`.
- **Returns:** A new normalized `AudioData`.

```python
loud = audio.normalize(0.9)
```

#### `.resample(target_rate: int) -> AudioData`

Resample the audio to a different sample rate using linear interpolation. Returns `self` unchanged if the rate already matches.

- **target_rate** (`int`): Desired sample rate.
- **Returns:** A new `AudioData` at the target sample rate.

```python
audio_48k = audio.resample(48000)
```

#### `.slice(start_sec: float, end_sec: float) -> AudioData`

Extract a time-range slice from the audio.

- **start_sec** (`float`): Start time in seconds (inclusive).
- **end_sec** (`float`): End time in seconds (exclusive).
- **Returns:** A new `AudioData` containing only the specified range.

```python
clip = audio.slice(0.5, 1.5)  # 1-second clip starting at 0.5s
```

#### `.fade_in(duration: float) -> AudioData`

Apply a linear fade-in from silence to full volume over the specified duration. If `duration` exceeds the audio length, the fade spans the entire audio.

- **duration** (`float`): Fade duration in seconds.
- **Returns:** A new `AudioData` with the fade applied.

```python
faded = audio.fade_in(0.1)
```

#### `.fade_out(duration: float) -> AudioData`

Apply a linear fade-out from full volume to silence over the specified duration at the end of the audio.

- **duration** (`float`): Fade duration in seconds.
- **Returns:** A new `AudioData` with the fade applied.

```python
faded = audio.fade_out(0.2)
```

### Class Methods

#### `AudioData.silence(duration: float, sample_rate: int = 44100, channels: int = 1) -> AudioData`

Create an `AudioData` instance filled with silence (all zeros).

- **duration** (`float`): Duration in seconds.
- **sample_rate** (`int`): Sample rate. Default: `44100`.
- **channels** (`int`): Number of channels. Default: `1`.
- **Returns:** A silent `AudioData`.

```python
gap = AudioData.silence(2.0, sample_rate=44100, channels=2)
```

#### `AudioData.from_generator(generator: Callable[[np.ndarray], np.ndarray], duration: float, sample_rate: int = 44100) -> AudioData`

Create mono audio by passing a time-value array through a generator function.

- **generator** (`Callable[[np.ndarray], np.ndarray]`): A function that receives a 1-D array of time values (in seconds) and returns a 1-D array of sample values.
- **duration** (`float`): Duration in seconds.
- **sample_rate** (`int`): Sample rate. Default: `44100`.
- **Returns:** A mono `AudioData`.

```python
import numpy as np
sine = AudioData.from_generator(lambda t: np.sin(2 * np.pi * 440 * t), 1.0)
```

---

## Sample

**Module:** `beatmaker.core`

A dataclass representing a named audio sample with optional metadata. Samples are the primary building blocks that get placed onto tracks.

### Constructor

```python
Sample(name: str, audio: AudioData, tags: List[str] = [], root_note: Optional[int] = None)
```

- **name** (`str`): Human-readable name of the sample.
- **audio** (`AudioData`): The underlying audio data.
- **tags** (`List[str]`): Categorization tags. Default: empty list.
- **root_note** (`Optional[int]`): MIDI note number of the sample's root pitch. Default: `None`.

### Methods

#### `.with_tags(*tags: str) -> Sample`

Return a copy of the sample with additional tags appended.

- **tags** (`str`): One or more tag strings.
- **Returns:** A new `Sample` with the combined tag list.

```python
tagged = sample.with_tags("drums", "kick")
```

#### `.pitched(semitones: float) -> Sample`

Return a pitch-shifted copy of the sample by resampling. The resulting sample has a modified name suffix (e.g., `"kick_pitch+3.0"`).

- **semitones** (`float`): Number of semitones to shift. Positive values shift up; negative values shift down.
- **Returns:** A new `Sample` with altered pitch and updated `root_note` (if the original had one).

```python
higher = sample.pitched(5)   # shift up 5 semitones
lower = sample.pitched(-2)   # shift down 2 semitones
```

### Class Methods / Factory Methods

#### `Sample.from_file(path: Path | str, name: Optional[str] = None) -> Sample`

Load a sample from an audio file on disk. Uses `beatmaker.io.load_audio` internally.

- **path** (`Path | str`): Path to the audio file.
- **name** (`Optional[str]`): Name for the sample. If omitted, the file stem is used.
- **Returns:** A `Sample` loaded from the file.

```python
kick = Sample.from_file("./samples/kick.wav")
kick = Sample.from_file("./samples/kick.wav", name="my_kick")
```

#### `Sample.from_synthesis(name: str, generator: Callable[[np.ndarray], np.ndarray], duration: float, sample_rate: int = 44100) -> Sample`

Create a sample from a synthesis (generator) function.

- **name** (`str`): Name for the resulting sample.
- **generator** (`Callable[[np.ndarray], np.ndarray]`): A function that receives time values and returns sample values.
- **duration** (`float`): Duration in seconds.
- **sample_rate** (`int`): Sample rate. Default: `44100`.
- **Returns:** A `Sample` containing the synthesized audio.

```python
import numpy as np
beep = Sample.from_synthesis("beep", lambda t: np.sin(2 * np.pi * 880 * t), 0.5)
```

---

## SamplePlacement

**Module:** `beatmaker.core`

A dataclass representing a sample placed at a specific time on a track, with per-placement volume and panning.

### Constructor

```python
SamplePlacement(sample: Sample, time: float, velocity: float = 1.0, pan: float = 0.0)
```

- **sample** (`Sample`): The sample to place.
- **time** (`float`): Start time in seconds.
- **velocity** (`float`): Volume multiplier, range `0.0` to `1.0`. Default: `1.0`.
- **pan** (`float`): Stereo pan position, range `-1.0` (full left) to `1.0` (full right). Default: `0.0` (center).

### Properties

- **end_time** (`float`): The time at which this placement finishes, computed as `time + sample.audio.duration`.

---

## AudioEffect

**Module:** `beatmaker.core`

Abstract base class for audio effects. All custom effects must inherit from this class and implement the `process` method.

### Methods

#### `.process(audio: AudioData) -> AudioData` *(abstract)*

Apply the effect to the given audio data and return the processed result.

- **audio** (`AudioData`): Input audio.
- **Returns:** Processed `AudioData`.

**Important notes:**

- This is an abstract method; concrete subclasses must override it.
- During track rendering, if an effect has a `set_context(bpm)` method, it will be called before `process` to provide tempo information.

```python
from beatmaker.core import AudioEffect, AudioData

class GainEffect(AudioEffect):
    def __init__(self, gain: float):
        self.gain = gain

    def process(self, audio: AudioData) -> AudioData:
        return AudioData(audio.samples * self.gain, audio.sample_rate, audio.channels)
```

---

## Track

**Module:** `beatmaker.core`

A dataclass representing a track that contains placed samples and an effect chain. Tracks are the primary organizational unit for grouping related sounds (drums, bass, vocals, etc.).

### Constructor

```python
Track(
    name: str,
    track_type: TrackType = TrackType.DRUMS,
    placements: List[SamplePlacement] = [],
    effects: List[AudioEffect] = [],
    volume: float = 1.0,
    pan: float = 0.0,
    muted: bool = False,
    solo: bool = False,
    volume_automation: Optional[object] = None,
    pan_automation: Optional[object] = None,
)
```

- **name** (`str`): Track name.
- **track_type** (`TrackType`): Purpose classification. Default: `TrackType.DRUMS`.
- **placements** (`List[SamplePlacement]`): Initial list of sample placements. Default: empty list.
- **effects** (`List[AudioEffect]`): Effect chain applied during render. Default: empty list.
- **volume** (`float`): Master volume multiplier for the track. Default: `1.0`.
- **pan** (`float`): Master pan position, `-1.0` (left) to `1.0` (right). Default: `0.0`.
- **muted** (`bool`): Whether the track is muted. Default: `False`. (Note: `muted` is stored but not checked by `render` -- the caller is responsible for skipping muted tracks.)
- **solo** (`bool`): Whether the track is soloed. Default: `False`. (Note: `solo` is stored but not checked by `render` -- the caller is responsible for solo logic.)
- **volume_automation** (`Optional[object]`): An automation curve object for volume. Must implement `render(bpm, sample_rate, duration_beats)`. Default: `None`.
- **pan_automation** (`Optional[object]`): An automation curve object for panning. Must implement `render(bpm, sample_rate, duration_beats)`. Default: `None`.

### Properties

- **duration** (`float`): Total duration of the track in seconds, determined by the latest-ending placement. Returns `0.0` if the track has no placements.

### Methods

#### `.add(sample: Sample, time: float, velocity: float = 1.0, pan: float = 0.0) -> Track`

Add a sample placement to the track at an absolute time.

- **sample** (`Sample`): The sample to place.
- **time** (`float`): Start time in seconds.
- **velocity** (`float`): Volume multiplier, `0.0`--`1.0`. Default: `1.0`.
- **pan** (`float`): Pan position, `-1.0`--`1.0`. Default: `0.0`.
- **Returns:** `self` (for method chaining).

```python
track.add(kick, 0.0).add(snare, 0.5)
```

#### `.add_at_beat(sample: Sample, beat: float, bpm: float, velocity: float = 1.0, pan: float = 0.0) -> Track`

Add a sample at a specific beat position, automatically converting to seconds.

- **sample** (`Sample`): The sample to place.
- **beat** (`float`): Beat position (0-indexed).
- **bpm** (`float`): Tempo in beats per minute.
- **velocity** (`float`): Volume multiplier. Default: `1.0`.
- **pan** (`float`): Pan position. Default: `0.0`.
- **Returns:** `self` (for method chaining).

```python
track.add_at_beat(kick, 0, 120.0).add_at_beat(snare, 2, 120.0)
```

#### `.add_pattern(sample: Sample, pattern: List[bool], step_duration: float, start_time: float = 0.0, velocity: float = 1.0) -> Track`

Add a sample repeatedly according to a boolean step-sequencer pattern.

- **sample** (`Sample`): The sample to place at each `True` step.
- **pattern** (`List[bool]`): Step pattern. Each `True` triggers the sample.
- **step_duration** (`float`): Duration of one step in seconds.
- **start_time** (`float`): Time offset for the first step. Default: `0.0`.
- **velocity** (`float`): Volume multiplier for all hits. Default: `1.0`.
- **Returns:** `self` (for method chaining).

```python
# Classic four-on-the-floor at 120 BPM (0.5s per beat)
track.add_pattern(kick, [True, False, True, False, True, False, True, False], 0.25)
```

#### `.add_effect(effect: AudioEffect) -> Track`

Append an audio effect to the track's effect chain. Effects are applied in order during rendering.

- **effect** (`AudioEffect`): The effect to add.
- **Returns:** `self` (for method chaining).

```python
track.add_effect(reverb).add_effect(compressor)
```

#### `.render(sample_rate: int = 44100, channels: int = 2, bpm: float = 120.0) -> AudioData`

Render all placements into a single `AudioData` buffer, applying volume, panning, automation, and effects.

- **sample_rate** (`int`): Output sample rate. Default: `44100`.
- **channels** (`int`): `1` for mono, `2` for stereo. Default: `2`.
- **bpm** (`float`): Song tempo, used for automation curve rendering. Default: `120.0`.
- **Returns:** Rendered `AudioData`.

**Rendering pipeline:**

1. An output buffer is allocated with 1 second of extra padding.
2. Each placement's audio is resampled and channel-converted as needed.
3. Per-placement velocity and combined panning (placement pan + track pan) are applied using constant-power panning.
4. Samples are summed (mixed) into the output buffer.
5. Volume automation is applied (if set).
6. Pan automation is applied (if set, stereo only).
7. Effects are applied in chain order. Effects with a `set_context(bpm)` method receive tempo context first.

```python
audio = track.render(sample_rate=44100, channels=2, bpm=140.0)
```

#### `.clear() -> Track`

Remove all placements from the track.

- **Returns:** `self` (for method chaining).

```python
track.clear()
```

### Iteration

`Track` implements `__iter__`, yielding `SamplePlacement` objects sorted by their `time` attribute.

```python
for placement in track:
    print(placement.time, placement.sample.name)
```

---

# Module: `beatmaker.io`

Functions and classes for loading, saving, and organizing audio files.

---

## SampleLibraryConfig

**Module:** `beatmaker.io`

A dataclass holding configuration options that control how a `SampleLibrary` loads and processes samples.

### Constructor

```python
SampleLibraryConfig(
    extensions: tuple[str, ...] = ('.wav', '.mp3', '.ogg', '.flac', '.aiff'),
    auto_tag: bool = True,
    lazy: bool = False,
    normalize: bool = False,
    normalize_peak: float = 0.95,
    target_sample_rate: Optional[int] = None,
    trim_silence: bool = False,
    trim_threshold: float = 0.001,
    default_tags: list[str] = [],
)
```

- **extensions** (`tuple[str, ...]`): File extensions to recognize as audio files. Default: `('.wav', '.mp3', '.ogg', '.flac', '.aiff')`.
- **auto_tag** (`bool`): When `True`, parent directory names are added as tags to each sample. Default: `True`.
- **lazy** (`bool`): When `True`, samples are not loaded from disk until first accessed. Default: `False`.
- **normalize** (`bool`): When `True`, each sample is peak-normalized after loading. Default: `False`.
- **normalize_peak** (`float`): Target peak level for normalization. Default: `0.95`.
- **target_sample_rate** (`Optional[int]`): If set, all loaded samples are resampled to this rate. Default: `None` (keep original).
- **trim_silence** (`bool`): When `True`, leading and trailing silence is trimmed from each sample. Default: `False`.
- **trim_threshold** (`float`): Amplitude threshold below which audio is considered silence (used when `trim_silence` is `True`). Default: `0.001`.
- **default_tags** (`list[str]`): Tags applied to every sample loaded through this config. Default: empty list.

```python
config = SampleLibraryConfig(lazy=True, normalize=True, target_sample_rate=44100)
```

---

## SampleLibrary

**Module:** `beatmaker.io`

A managed collection of `Sample` objects organized by path-based keys, tags, and configurable aliases. Supports eager and lazy loading, substring search, tag-based filtering, and dictionary-style access.

### Constructor

```python
SampleLibrary(config: Optional[SampleLibraryConfig] = None)
```

- **config** (`Optional[SampleLibraryConfig]`): Configuration controlling load and processing behavior. If `None`, default `SampleLibraryConfig()` is used.

### Factory Methods

#### `SampleLibrary.from_directory(directory: str | Path, config: Optional[SampleLibraryConfig] = None, *, extensions: Optional[tuple[str, ...]] = None, auto_tag: Optional[bool] = None, lazy: Optional[bool] = None) -> SampleLibrary`

Create and populate a `SampleLibrary` by recursively scanning a directory. Each file is keyed by its path relative to the root directory, without extension, using forward slashes.

- **directory** (`str | Path`): Root folder containing audio files.
- **config** (`Optional[SampleLibraryConfig]`): Full configuration object. Default: `None` (uses defaults).
- **extensions** (`Optional[tuple[str, ...]]`): Override `config.extensions`. Keyword-only.
- **auto_tag** (`Optional[bool]`): Override `config.auto_tag`. Keyword-only.
- **lazy** (`Optional[bool]`): Override `config.lazy`. Keyword-only.
- **Returns:** A populated `SampleLibrary`.
- **Raises:** `FileNotFoundError` if `directory` does not exist.

**Important:** When keyword arguments and a `config` are both supplied, keyword arguments take precedence over the corresponding config fields.

```python
lib = SampleLibrary.from_directory("./samples", lazy=True)
kick = lib["drums/kick"]       # key derived from drums/kick.wav
lib.list("drums")              # list all keys under drums/
```

### Properties

- **names** (`list[str]`): Sorted list of all sample keys in the library.
- **tags** (`list[str]`): Sorted list of all unique tags across all samples.
- **root** (`Optional[Path]`): The root directory, if the library was created via `from_directory`. Otherwise `None`.

### Methods

#### `.add(sample: Sample, key: Optional[str] = None) -> SampleLibrary`

Add a sample to the library. The sample's tags are indexed for tag-based retrieval.

- **sample** (`Sample`): The sample to add.
- **key** (`Optional[str]`): Explicit key. If omitted, `sample.name` is used.
- **Returns:** `self` (for method chaining).

```python
lib.add(my_sample, key="custom/key")
```

#### `.alias(short_name: str, target_key: str) -> SampleLibrary`

Register a single alias that maps `short_name` to an existing sample key. Backslashes in `target_key` are normalized to forward slashes.

- **short_name** (`str`): The alias name.
- **target_key** (`str`): The full sample key the alias points to.
- **Returns:** `self` (for method chaining).

```python
lib.alias("kick", "drums/808/kick_hard")
kick = lib["kick"]
```

#### `.aliases(**mapping: str) -> SampleLibrary`

Register multiple aliases at once via keyword arguments.

- **mapping** (`str`): Keyword arguments where each key is an alias and the value is the target sample key.
- **Returns:** `self` (for method chaining).

```python
lib.aliases(kick="drums/808/kick_hard", snare="drums/acoustic/snare_02")
```

#### `.resolve(name: str) -> str`

Resolve a name through the alias table. If `name` is a registered alias, returns the target key. Otherwise returns `name` unchanged.

- **name** (`str`): Name or alias to resolve.
- **Returns:** The resolved key string.

```python
lib.resolve("kick")  # "drums/808/kick_hard"
lib.resolve("drums/hat")  # "drums/hat" (no alias, returned as-is)
```

#### `.get(name: str) -> Optional[Sample]`

Get a sample by key or alias. Returns `None` if not found. Triggers lazy loading if the matched sample has not yet been loaded.

**Resolution order:**

1. Exact key match.
2. Alias resolution followed by key match.

- **name** (`str`): Sample key or alias.
- **Returns:** The `Sample`, or `None`.

```python
sample = lib.get("drums/kick")  # Sample or None
```

#### `.list(prefix: str = '') -> list[str]`

List all sample keys, optionally filtered by a path prefix. When a prefix is provided, only keys that start with `prefix/` are returned.

- **prefix** (`str`): Path prefix to filter by. Default: `''` (return all keys).
- **Returns:** Sorted list of matching key strings.

```python
lib.list("drums")         # ['drums/kick', 'drums/snare', ...]
lib.list("synths/pads")   # ['synths/pads/warm', ...]
lib.list()                 # all keys
```

#### `.search(pattern: str) -> list[str]`

Search all sample keys by substring match (case-insensitive).

- **pattern** (`str`): Substring to search for.
- **Returns:** Sorted list of matching key strings.

```python
lib.search("kick")  # ['drums/kick', 'drums/kick_hard', ...]
```

#### `.by_tag(tag: str) -> list[Sample]`

Retrieve all samples that have a specific tag. Triggers lazy loading for any deferred samples.

- **tag** (`str`): The tag to filter by.
- **Returns:** List of `Sample` objects.

```python
drum_samples = lib.by_tag("drums")
```

#### `.load_directory(directory: str | Path, tags: Optional[list[str]] = None, recursive: bool = False) -> SampleLibrary`

Load all samples from a directory and add them to the library with flat stem-based keys (file stem only, not path-based). Optionally applies additional tags.

- **directory** (`str | Path`): Directory to load from.
- **tags** (`Optional[list[str]]`): Tags to apply to all loaded samples. Default: `None`.
- **recursive** (`bool`): Whether to search subdirectories. Default: `False`.
- **Returns:** `self` (for method chaining).

```python
lib.load_directory("./extra_samples", tags=["extra"], recursive=True)
```

#### `.keys() -> list[str]`

Return a sorted list of all sample keys. Equivalent to the `names` property.

- **Returns:** Sorted list of key strings.

```python
all_keys = lib.keys()
```

#### `.values() -> list[Sample]`

Return all samples in the library (triggers lazy loading for every deferred sample).

- **Returns:** List of `Sample` objects.

```python
all_samples = lib.values()
```

#### `.items() -> list[tuple[str, Sample]]`

Return all `(key, sample)` pairs (triggers lazy loading for every deferred sample).

- **Returns:** List of `(str, Sample)` tuples.

```python
for key, sample in lib.items():
    print(key, sample.audio.duration)
```

### Special Methods

#### `lib[name]` (`__getitem__`)

Get a sample by key, alias, or stem fallback. Raises `KeyError` if not found.

**Resolution order:**

1. Exact key match.
2. Alias resolution.
3. Stem-only fallback: matches `name` against the last path component of each key.

```python
kick = lib["drums/kick"]
kick = lib["kick"]  # alias or stem fallback
```

#### `name in lib` (`__contains__`)

Check whether a key or alias exists in the library.

```python
if "drums/kick" in lib:
    ...
```

#### `len(lib)` (`__len__`)

Return the total number of samples in the library.

```python
print(len(lib))  # e.g., 42
```

#### `repr(lib)` (`__repr__`)

String representation including sample count and optional root directory.

```python
repr(lib)  # "SampleLibrary(42 samples, root='C:/samples')"
```

#### Iteration (`__iter__`)

Iterating over the library yields `(key, sample)` tuples sorted by key. Triggers lazy loading for any deferred samples.

```python
for key, sample in lib:
    print(key, sample.audio.duration)
```

### Important Notes

- **Lazy loading:** When `SampleLibraryConfig.lazy` is `True` (or the `lazy` keyword is passed to `from_directory`), samples are represented internally by deferred sentinel objects. Actual audio is loaded from disk only when the sample is first accessed via `get`, `__getitem__`, `by_tag`, iteration, `values`, or `items`.
- **Key normalization:** All keys use forward slashes (`/`) regardless of the OS. Backslashes passed to retrieval and alias methods are automatically converted.
- **Processing pipeline:** When loading (eagerly or lazily), audio goes through: silence trimming (optional) -> resampling (optional) -> normalization (optional), as controlled by `SampleLibraryConfig`.
- **Auto-tagging:** When `auto_tag` is enabled, parent directory names from the relative path are added as tags. For example, `drums/acoustic/snare.wav` receives tags `["drums", "acoustic"]`.

---

## Standalone Functions

### `load_audio(path: str | Path) -> AudioData`

**Module:** `beatmaker.io`

Load audio from a file and return it as an `AudioData` instance.

- **path** (`str | Path`): Path to the audio file.
- **Returns:** An `AudioData` containing the decoded audio.
- **Raises:** `ValueError` if the format is not WAV and `pydub` is not installed.

**Supported formats:**

| Format | Requirement                |
|--------|----------------------------|
| WAV    | Native (no dependencies)   |
| MP3    | Requires `pydub`           |
| OGG    | Requires `pydub`           |
| FLAC   | Requires `pydub`           |

```python
from beatmaker.io import load_audio
audio = load_audio("./samples/kick.wav")
```

### `save_audio(audio: AudioData, path: str | Path, format: Optional[str] = None) -> None`

**Module:** `beatmaker.io`

Save an `AudioData` instance to a file.

- **audio** (`AudioData`): The audio data to save.
- **path** (`str | Path`): Output file path.
- **format** (`Optional[str]`): Explicit format string (e.g., `"wav"`, `"mp3"`). If `None`, the format is inferred from the file extension. Default: `None`.
- **Returns:** `None`.
- **Raises:** `ValueError` if the format is not WAV and `pydub` is not installed.

**Supported formats:** Same as `load_audio`.

**Note:** WAV files are saved as 16-bit PCM by default.

```python
from beatmaker.io import save_audio
save_audio(audio, "./output/beat.wav")
save_audio(audio, "./output/beat.mp3", format="mp3")
```

### `load_samples_from_directory(directory: str | Path, recursive: bool = False, extensions: tuple = ('.wav', '.mp3', '.ogg', '.flac')) -> dict[str, Sample]`

**Module:** `beatmaker.io`

Load all audio files from a directory and return them as a dictionary mapping file stems to `Sample` objects.

- **directory** (`str | Path`): Directory to scan.
- **recursive** (`bool`): If `True`, scan subdirectories recursively. Default: `False`.
- **extensions** (`tuple`): File extensions to include. Default: `('.wav', '.mp3', '.ogg', '.flac')`.
- **Returns:** `dict[str, Sample]` mapping each file's stem (name without extension) to its `Sample`.

**Note:** Files that fail to load are skipped with a warning printed to stdout.

```python
from beatmaker.io import load_samples_from_directory
samples = load_samples_from_directory("./drums", recursive=True)
kick = samples["kick"]
```
