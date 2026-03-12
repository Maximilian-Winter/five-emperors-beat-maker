# Builder API Reference

**Module:** `beatmaker.builder`

This module implements a **fluent builder pattern** for constructing songs, tracks, and arrangements. Every builder method returns `self`, enabling method chaining. The top-level entry point is `create_song()` or `SongBuilder(name)`.

---

## Song

A complete song composition. A dataclass that holds multiple tracks, global settings (BPM, time signature, sample rate), and master effects. This is the final product returned by `SongBuilder.build()`.

### Constructor

```python
Song(
    name: str = "Untitled",
    bpm: float = 120.0,
    time_signature: TimeSignature = TimeSignature(),
    sample_rate: int = 44100,
    tracks: List[Track] = [],
    master_effects: List[AudioEffect] = []
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | `"Untitled"` | Name of the song. |
| `bpm` | `float` | `120.0` | Tempo in beats per minute. |
| `time_signature` | `TimeSignature` | `TimeSignature()` | Time signature (default 4/4). |
| `sample_rate` | `int` | `44100` | Audio sample rate in Hz. |
| `tracks` | `List[Track]` | `[]` | List of tracks in the song. |
| `master_effects` | `List[AudioEffect]` | `[]` | Effects applied to the summed master output. |

### Properties

#### `.duration -> float`
Total duration of the song in seconds, determined by the longest track. Returns `0.0` if there are no tracks.

#### `.duration_bars -> float`
Total duration expressed in bars at the current tempo and time signature.

### Methods

#### `.add_track(track: Track) -> Song`
Add a `Track` to the song. Returns `self` for chaining.

```python
song.add_track(my_track)
```

#### `.get_track(name: str) -> Optional[Track]`
Look up a track by name. Returns `None` if no track with that name exists.

```python
drums = song.get_track("Drums")
```

#### `.beat_to_seconds(beat: float) -> float`
Convert a beat number to an absolute time in seconds using the song's BPM and time signature.

```python
time = song.beat_to_seconds(4.0)  # start of bar 2 in 4/4
```

#### `.bar_to_seconds(bar: float) -> float`
Convert a bar number to an absolute time in seconds.

```python
time = song.bar_to_seconds(2.0)  # start of bar 3
```

#### `.render(channels: int = 2) -> AudioData`
Render the entire song to an `AudioData` buffer by summing all tracks. Respects track `muted` and `solo` flags -- if any track is soloed, only soloed tracks are included. Master effects are applied after summation. A progress bar is displayed via `tqdm`.

```python
audio = song.render()           # stereo
audio = song.render(channels=1) # mono
```

#### `.export(path: Union[str, Path], format: Optional[str] = None) -> Path`
Render and save the song to a file. The `format` parameter is passed to `save_audio`; if `None`, it is inferred from the file extension. Returns the resolved `Path`.

```python
song.export("output.wav")
song.export("output.mp3", format="mp3")
```

---

## SongBuilder

Fluent builder for creating `Song` objects. This is the primary entry point for composition. All `add_*` methods accept a **callback** (a lambda or function) that receives a specialized track builder, configures it, and returns it.

### Constructor

```python
SongBuilder(name: str = "Untitled")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | `"Untitled"` | Name of the song. |

Internal state:
- `_current_bar_length` defaults to `4` (bars). Changed via `.bars()`.
- `_library` defaults to `None`. Set via `.samples()`.

### Methods

#### `.tempo(bpm: float) -> SongBuilder`
Set the song tempo in beats per minute.

```python
create_song("Demo").tempo(128)
```

#### `.time_signature(beats_per_bar: int = 4, beat_value: int = 4) -> SongBuilder`
Set the time signature.

```python
create_song("Waltz").time_signature(3, 4)
```

#### `.sample_rate(rate: int) -> SongBuilder`
Set the audio sample rate in Hz.

```python
create_song("HQ").sample_rate(48000)
```

#### `.bars(num_bars: int) -> SongBuilder`
Set the default pattern length (in bars) used by all subsequent track builders. This value is passed as `pattern_bars` to `DrumTrackBuilder`, `BassTrackBuilder`, etc.

```python
create_song("Long").bars(8)
```

#### `.samples(library) -> SongBuilder`
Attach a `SampleLibrary` instance to the builder. Once attached, the library is **automatically propagated** to every track builder created by `add_drums`, `add_bass`, `add_melody`, `add_harmony`, `add_track`, and `section`. This enables `.use_kit_from()`, `.use_sample()`, `.sample()`, and `.sample_note()` methods on those builders.

```python
lib = SampleLibrary.from_directory("./my_samples")
create_song("Demo").samples(lib).add_drums(lambda d: d
    .use_kit_from("drums/808")
    .four_on_floor()
)
```

> **Important:** If `.samples()` is not called, any attempt to use library-dependent methods on track builders will raise `RuntimeError`.

#### `.add_track(name: str, track_type: TrackType = TrackType.DRUMS, builder: Optional[Callable[[TrackBuilder], TrackBuilder]] = None) -> SongBuilder`
Add a generic track. If a `builder` callback is provided, a `TrackBuilder` is instantiated and passed to it.

```python
create_song("FX").add_track("Risers", TrackType.FX, lambda t: t
    .sample("fx/riser", beat=0)
    .volume(0.6)
)
```

#### `.add_drums(builder: Callable[[DrumTrackBuilder], DrumTrackBuilder]) -> SongBuilder`
Add a drum track. Creates a track named `"Drums"` with `TrackType.DRUMS`, wraps it in a `DrumTrackBuilder`, and passes it to the callback.

```python
create_song("Beat").add_drums(lambda d: d
    .kick(beats=[0, 2])
    .snare(beats=[1, 3])
    .eighth_hats()
)
```

#### `.add_bass(builder: Callable[[BassTrackBuilder], BassTrackBuilder]) -> SongBuilder`
Add a bass track. Creates a track named `"Bass"` with `TrackType.BASS`, wraps it in a `BassTrackBuilder`, and passes it to the callback.

```python
create_song("Groove").add_bass(lambda b: b
    .note('E2', beat=0, duration=1)
    .note('G2', beat=2, duration=1)
)
```

#### `.add_vocal(path: Union[str, Path], start_bar: float = 0, volume: float = 1.0) -> SongBuilder`
Load an audio file and add it as a vocal track starting at the given bar.

```python
create_song("Song").add_vocal("vocals/verse1.wav", start_bar=4, volume=0.9)
```

#### `.add_backing_track(path: Union[str, Path], start_bar: float = 0, volume: float = 0.8) -> SongBuilder`
Load an audio file and add it as a backing track.

```python
create_song("Remix").add_backing_track("stems/keys.wav", volume=0.6)
```

#### `.add_sample_track(name: str, samples: List[tuple], track_type: TrackType = TrackType.FX) -> SongBuilder`
Add a track with pre-defined sample placements. Each tuple in `samples` is either `(sample, beat)` or `(sample, beat, velocity)`.

```python
create_song("Perc").add_sample_track("Shakers", [
    (shaker_sample, 0.5),
    (shaker_sample, 1.5, 0.7),
])
```

#### `.master_effect(effect: AudioEffect) -> SongBuilder`
Add an effect to the master bus.

```python
create_song("Loud").master_effect(Limiter(0.9))
```

#### `.master_limiter(threshold: float = 0.95) -> SongBuilder`
Shorthand for adding a `Limiter` to the master bus.

```python
create_song("Safe").master_limiter(0.9)
```

#### `.master_compressor(threshold: float = -10.0, ratio: float = 4.0) -> SongBuilder`
Shorthand for adding a `Compressor` to the master bus.

```python
create_song("Punchy").master_compressor(threshold=-12.0, ratio=6.0)
```

#### `.add_melody(builder: Callable[[MelodyTrackBuilder], MelodyTrackBuilder], name: str = "Melody", synth_type: str = 'saw') -> SongBuilder`
Add a melodic track. After the callback completes, `render_melody()` is called automatically to synthesize all phrase events onto the track.

```python
create_song("Tune").add_melody(lambda m: m
    .synth('pluck')
    .play("C4:1 E4:0.5 G4:0.5 C5:2")
    .volume(0.7)
, synth_type='saw')
```

#### `.add_harmony(builder: Callable[[HarmonyTrackBuilder], HarmonyTrackBuilder], name: str = "Harmony", synth_type: str = 'saw') -> SongBuilder`
Add a harmony/chord track. After the callback completes, `render_harmony()` is called automatically.

```python
create_song("Chords").add_harmony(lambda h: h
    .key("C", "major")
    .progression("I - V - vi - IV", beats_per_chord=4)
    .voice_lead()
    .volume(0.5)
, synth_type='warm_pad')
```

#### `.section(name: str, bars: int) -> SectionBuilder`
Create a `SectionBuilder` for building a reusable song section. The returned builder uses the current song context (BPM, time signature) and the attached library.

```python
verse = song_builder.section("verse", bars=8).add_drums(...).build()
```

#### `.arrange(arrangement) -> SongBuilder`
Apply an `Arrangement` to the song. Calls `arrangement.render_to_song(self._song)` which places all section tracks onto the song timeline.

```python
song_builder.arrange(
    Arrangement()
        .add(verse, at_bar=0)
        .add(chorus, at_bar=8)
)
```

#### `.build() -> Song`
Build and return the completed `Song` object.

```python
song = create_song("Final").tempo(120).add_drums(...).build()
```

---

## TrackBuilder

Base builder for track construction. Provides volume, pan, effects, humanization, groove, automation, and sample placement. All specialized track builders (`DrumTrackBuilder`, `BassTrackBuilder`, `MelodyTrackBuilder`, `HarmonyTrackBuilder`) inherit from this class.

### Constructor

```python
TrackBuilder(track: Track, song: Song, library=None)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track` | `Track` | *(required)* | The underlying `Track` object being configured. |
| `song` | `Song` | *(required)* | The parent song (used for beat/bar-to-seconds conversion). |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library for `.sample()` lookups. |

> **Note:** You typically do not instantiate `TrackBuilder` directly. It is created internally by `SongBuilder.add_track()` and passed to your callback.

### Methods

#### `.volume(level: float) -> TrackBuilder`
Set track volume. Range is `0.0` (silent) to `1.0` (full).

```python
lambda t: t.volume(0.8)
```

#### `.pan(value: float) -> TrackBuilder`
Set stereo pan position. `-1.0` is hard left, `0.0` is center, `1.0` is hard right.

```python
lambda t: t.pan(-0.3)
```

#### `.mute() -> TrackBuilder`
Mute the track. Muted tracks are skipped during `Song.render()`.

```python
lambda t: t.mute()
```

#### `.solo() -> TrackBuilder`
Solo the track. When any track in the song is soloed, only soloed tracks are rendered.

```python
lambda t: t.solo()
```

#### `.effect(effect: AudioEffect) -> TrackBuilder`
Add an audio effect to the track's effect chain.

```python
lambda t: t.effect(Reverb(decay=1.5))
```

#### `.add(sample: Sample, beat: float, velocity: float = 1.0, pan: float = 0.0) -> TrackBuilder`
Place a `Sample` at a specific beat position on the track.

```python
lambda t: t.add(kick_sample, beat=0, velocity=0.9)
```

#### `.add_at_bar(sample: Sample, bar: float, velocity: float = 1.0, pan: float = 0.0) -> TrackBuilder`
Place a `Sample` at a specific bar position.

```python
lambda t: t.add_at_bar(crash_sample, bar=0)
```

#### `.sample(key: str, beat: float, velocity: float = 1.0, pan: float = 0.0) -> TrackBuilder`
Look up a sample from the attached `SampleLibrary` by key, alias, or stem name, and place it at the given beat.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | *(required)* | Library key, alias, or stem name. |
| `beat` | `float` | *(required)* | Beat position. |
| `velocity` | `float` | `1.0` | Volume multiplier (0.0--1.0). |
| `pan` | `float` | `0.0` | Stereo position (-1.0 to 1.0). |

**Raises:** `RuntimeError` if no library is attached. `KeyError` if the key is not found.

```python
create_song("FX").samples(lib).add_track("FX", TrackType.FX, lambda t: t
    .sample("fx/riser", beat=0)
    .sample("fx/impact", beat=16)
)
```

#### `.humanize(timing: float = 0.01, velocity: float = 0.1, seed: Optional[int] = None) -> TrackBuilder`
Apply humanization to all sample placements on the track. Adds random timing jitter and velocity variation to make patterns feel less mechanical.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timing` | `float` | `0.01` | Maximum timing jitter in seconds. |
| `velocity` | `float` | `0.1` | Maximum velocity variation. |
| `seed` | `Optional[int]` | `None` | Random seed for reproducibility. |

```python
lambda t: t.four_on_floor().humanize(timing=0.005, seed=42)
```

#### `.groove(template) -> TrackBuilder`
Apply a groove template to all placements. The template object must implement `apply_to_track(track, bpm)`.

```python
lambda t: t.eighth_hats().groove(swing_template)
```

#### `.automate_volume(curve: AutomationCurve) -> TrackBuilder`
Attach a volume automation curve to the track.

```python
from beatmaker.automation import AutomationCurve
fade_in = AutomationCurve([(0, 0.0), (4, 1.0)])
lambda t: t.automate_volume(fade_in)
```

#### `.automate_pan(curve: AutomationCurve) -> TrackBuilder`
Attach a pan automation curve to the track.

```python
sweep = AutomationCurve([(0, -1.0), (8, 1.0)])
lambda t: t.automate_pan(sweep)
```

---

## DrumTrackBuilder

Specialized builder for drum tracks. Extends `TrackBuilder` with drum-specific methods for placing kick, snare, hi-hat, and clap hits using beat lists or 16-step boolean patterns. Also provides convenience methods for common drum patterns.

If no samples are explicitly provided (via `use_kit`, `use_sample`, or `use_kit_from`), samples are **auto-generated** using `DrumSynth` on first use.

### Constructor

```python
DrumTrackBuilder(
    track: Track,
    song: Song,
    pattern_bars: int = 4,
    library=None
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track` | `Track` | *(required)* | The drum track being built. |
| `song` | `Song` | *(required)* | Parent song context. |
| `pattern_bars` | `int` | `4` | Number of bars the pattern spans. Beat lists repeat per bar for this many bars. |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library. |

### Methods

#### `.use_kit(kick: Sample, snare: Sample, hihat: Sample, clap: Optional[Sample] = None) -> DrumTrackBuilder`
Assign explicit `Sample` objects to the four drum roles.

```python
lambda d: d.use_kit(my_kick, my_snare, my_hat, my_clap)
```

#### `.use_sample(role: str, key: str) -> DrumTrackBuilder`
Assign a sample from the attached library to a specific drum role.

| Parameter | Type | Description |
|---|---|---|
| `role` | `str` | One of `'kick'`, `'snare'`, `'hihat'` (also `'hat'`, `'hh'`), `'clap'` (also `'cp'`). |
| `key` | `str` | Library key, alias, or stem name. |

**Raises:** `RuntimeError` if no library is attached. `ValueError` if the role is unrecognized.

```python
lambda d: d
    .use_sample("kick", "drums/808/kick_heavy")
    .use_sample("snare", "drums/vinyl/snare_03")
```

#### `.use_kit_from(prefix: str) -> DrumTrackBuilder`
Auto-detect and assign drum samples from a library prefix. Searches the library under the given prefix for samples whose stem names contain common drum terms: `kick`, `bd`, `bass_drum` for kick; `snare`, `sd`, `snr` for snare; `hihat`, `hat`, `hh`, `hi_hat` for hi-hat; `clap`, `cp`, `handclap` for clap.

Only replaces roles where a matching sample is found. Roles with no match remain unchanged (falling back to synthesis if never set).

**Raises:** `RuntimeError` if no library is attached.

```python
lambda d: d
    .use_kit_from("drums/acoustic")
    .four_on_floor()
    .backbeat()
```

#### `.kick(beats: Optional[List[float]] = None, pattern: Optional[List[bool]] = None, velocity: float = 1.0) -> DrumTrackBuilder`
Add kick drum hits. Provide either `beats` or `pattern` (not both).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `beats` | `Optional[List[float]]` | `None` | Beat positions within a single bar (e.g., `[0, 2]`). Repeated across `pattern_bars`. |
| `pattern` | `Optional[List[bool]]` | `None` | 16-step boolean pattern at 16th-note resolution. |
| `velocity` | `float` | `1.0` | Hit velocity. |

```python
lambda d: d.kick(beats=[0, 2.5])
lambda d: d.kick(pattern=[True,False,False,False, True,False,False,False,
                          True,False,True,False,  True,False,False,False])
```

#### `.snare(beats: Optional[List[float]] = None, pattern: Optional[List[bool]] = None, velocity: float = 1.0) -> DrumTrackBuilder`
Add snare drum hits. Same parameter semantics as `.kick()`.

```python
lambda d: d.snare(beats=[1, 3])
```

#### `.hihat(beats: Optional[List[float]] = None, pattern: Optional[List[bool]] = None, velocity: float = 0.7, open_beats: Optional[List[float]] = None) -> DrumTrackBuilder`
Add hi-hat hits.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `beats` | `Optional[List[float]]` | `None` | Beat positions within a bar. |
| `pattern` | `Optional[List[bool]]` | `None` | 16-step boolean pattern. |
| `velocity` | `float` | `0.7` | Hit velocity. |
| `open_beats` | `Optional[List[float]]` | `None` | Beat positions (within a bar) where an open hi-hat should be used instead of a closed one. |

```python
lambda d: d.hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], open_beats=[1.5, 3.5])
```

#### `.clap(beats: Optional[List[float]] = None, velocity: float = 0.9) -> DrumTrackBuilder`
Add clap hits at the specified beat positions (repeated across `pattern_bars`).

```python
lambda d: d.clap(beats=[1, 3])
```

#### `.four_on_floor(velocity: float = 1.0) -> DrumTrackBuilder`
Shorthand for kick on every beat: `kick(beats=[0, 1, 2, 3])`.

```python
lambda d: d.four_on_floor()
```

#### `.backbeat(velocity: float = 1.0) -> DrumTrackBuilder`
Shorthand for snare on beats 2 and 4: `snare(beats=[1, 3])`.

```python
lambda d: d.backbeat()
```

#### `.eighth_hats(velocity: float = 0.7) -> DrumTrackBuilder`
Eighth-note hi-hats (8 hits per bar).

```python
lambda d: d.eighth_hats()
```

#### `.sixteenth_hats(velocity: float = 0.6) -> DrumTrackBuilder`
Sixteenth-note hi-hats (16 hits per bar).

```python
lambda d: d.sixteenth_hats()
```

> **Inherited methods:** `.volume()`, `.pan()`, `.mute()`, `.solo()`, `.effect()`, `.add()`, `.add_at_bar()`, `.sample()`, `.humanize()`, `.groove()`, `.automate_volume()`, `.automate_pan()` -- see `TrackBuilder`.

---

## BassTrackBuilder

Specialized builder for bass tracks. Extends `TrackBuilder` with methods for synthesized bass notes and bass lines.

### Constructor

```python
BassTrackBuilder(
    track: Track,
    song: Song,
    pattern_bars: int = 4,
    library=None
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track` | `Track` | *(required)* | The bass track being built. |
| `song` | `Song` | *(required)* | Parent song context. |
| `pattern_bars` | `int` | `4` | Number of bars the pattern spans. |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library. |

### Methods

#### `.note(note: str, beat: float, duration: float = 1.0, velocity: float = 1.0) -> BassTrackBuilder`
Add a synthesized sub-bass note.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `note` | `str` | *(required)* | Note name with octave (e.g., `'E2'`, `'G2'`, `'A1'`). |
| `beat` | `float` | *(required)* | Beat position. |
| `duration` | `float` | `1.0` | Duration in beats. |
| `velocity` | `float` | `1.0` | Note velocity. |

Uses `BassSynth.sub_bass()` for synthesis.

```python
lambda b: b.note('E2', beat=0, duration=2)
```

#### `.acid_note(note: str, beat: float, duration: float = 0.5, velocity: float = 1.0) -> BassTrackBuilder`
Add an acid-style bass note using `BassSynth.acid_bass()`.

```python
lambda b: b.acid_note('E2', beat=0, duration=0.5)
```

#### `.line(notes: List[tuple]) -> BassTrackBuilder`
Add a sequence of bass notes. Each tuple is either `(note, beat)` (duration defaults to `1.0`) or `(note, beat, duration)`.

```python
lambda b: b.line([
    ('E2', 0, 1),
    ('G2', 1, 0.5),
    ('A2', 1.5, 0.5),
    ('E2', 2, 2),
])
```

#### `.octave_pattern(root: str, beats: List[float], duration: float = 0.5) -> BassTrackBuilder`
Play root note alternating with the note one octave above. Even-indexed beats get the root; odd-indexed beats get the octave.

```python
lambda b: b.octave_pattern('E2', beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
```

#### `.sample_note(key: str, beat: float, duration: float = 1.0, velocity: float = 1.0, transpose: float = 0.0) -> BassTrackBuilder`
Place a bass sample from the attached library with optional pitch shifting.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | *(required)* | Library key for the bass sample. |
| `beat` | `float` | *(required)* | Beat position. |
| `duration` | `float` | `1.0` | Duration in beats (used to trim the sample). |
| `velocity` | `float` | `1.0` | Volume multiplier. |
| `transpose` | `float` | `0.0` | Semitones to pitch-shift. `0` = original pitch. |

**Raises:** `RuntimeError` if no library is attached.

```python
lambda b: b
    .sample_note("bass/sub_C2", beat=0, duration=2)
    .sample_note("bass/sub_C2", beat=2, transpose=5)
```

> **Inherited methods:** `.volume()`, `.pan()`, `.mute()`, `.solo()`, `.effect()`, `.add()`, `.add_at_bar()`, `.sample()`, `.humanize()`, `.groove()`, `.automate_volume()`, `.automate_pan()` -- see `TrackBuilder`.

---

## MelodyTrackBuilder

Builder for melodic tracks using **Phrase-based composition**. Notes are accumulated via `.phrase()` or `.play()` calls, then synthesized and placed on the track when `render_melody()` is called (which `SongBuilder.add_melody()` does automatically).

### Constructor

```python
MelodyTrackBuilder(
    track: Track,
    song: Song,
    pattern_bars: int = 4,
    synth_type: str = 'saw',
    library=None
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track` | `Track` | *(required)* | The melody track being built. |
| `song` | `Song` | *(required)* | Parent song context. |
| `pattern_bars` | `int` | `4` | Number of bars the pattern spans. |
| `synth_type` | `str` | `'saw'` | Default synthesizer waveform. |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library. |

### Methods

#### `.synth(synth_type: str) -> MelodyTrackBuilder`
Set the synthesizer type used to render notes.

Supported types: `'saw'` (default), `'sine'`, `'square'`, `'triangle'`, `'fm'`, `'pluck'`.

The `'fm'` type attempts to use `LeadSynth.fm_lead()` and falls back to sawtooth. The `'pluck'` type attempts to use `PluckSynth.karplus_strong()` and falls back to sawtooth.

```python
lambda m: m.synth('pluck')
```

#### `.phrase(phrase, start_beat: Optional[float] = None) -> MelodyTrackBuilder`
Add a `Phrase` object at a specific beat position. If `start_beat` is `None`, the phrase is auto-appended after the last event.

```python
from beatmaker.melody import Phrase
motif = Phrase.from_string("C4:1 E4:0.5 G4:0.5")
lambda m: m.phrase(motif, start_beat=0).phrase(motif.transpose(5), start_beat=4)
```

#### `.play(notation: str, start_beat: Optional[float] = None) -> MelodyTrackBuilder`
Shorthand for creating a `Phrase` from inline string notation and adding it. Notation format is `"NOTE:DURATION NOTE:DURATION ..."`.

```python
lambda m: m.play("C4:1 E4:0.5 G4:0.5 C5:2")
```

#### `.render_melody() -> None`
Render all accumulated melody events to sample placements on the track. This is called **automatically** by `SongBuilder.add_melody()` after the callback completes. You do not normally call this yourself.

#### `.humanize(timing: float = 0.01, velocity: float = 0.1, seed: Optional[int] = None) -> MelodyTrackBuilder`
Apply humanization to all placements after rendering.

```python
lambda m: m.play("C4:1 E4:1").humanize(timing=0.008)
```

#### `.groove(template) -> MelodyTrackBuilder`
Apply a groove template to all placements.

#### `.automate_volume(curve: AutomationCurve) -> MelodyTrackBuilder`
Attach a volume automation curve to the track.

#### `.automate_pan(curve: AutomationCurve) -> MelodyTrackBuilder`
Attach a pan automation curve to the track.

> **Inherited methods:** `.volume()`, `.pan()`, `.mute()`, `.solo()`, `.effect()`, `.add()`, `.add_at_bar()`, `.sample()` -- see `TrackBuilder`.

---

## HarmonyTrackBuilder

Builder for harmony/chord tracks. Uses `ChordProgression` to define chords via Roman numeral notation, with optional voice leading and arpeggiation.

### Constructor

```python
HarmonyTrackBuilder(
    track: Track,
    song: Song,
    pattern_bars: int = 4,
    synth_type: str = 'saw',
    library=None
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track` | `Track` | *(required)* | The harmony track being built. |
| `song` | `Song` | *(required)* | Parent song context. |
| `pattern_bars` | `int` | `4` | Number of bars the pattern spans. |
| `synth_type` | `str` | `'saw'` | Default synthesizer waveform. |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library. |

### Methods

#### `.key(root: str, scale_type: str = 'major') -> HarmonyTrackBuilder`
Set the musical key for chord construction. Must be called before `.progression()`.

Supported scale types: `'major'`, `'minor'`, `'dorian'`, `'mixolydian'`, `'harmonic_minor'`, `'melodic_minor'`.

```python
lambda h: h.key("C", "minor")
```

#### `.progression(numerals: str, beats_per_chord: float = 4.0, octave: int = 3) -> HarmonyTrackBuilder`
Set the chord progression from Roman numeral notation. Requires `.key()` to be called first.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `numerals` | `str` | *(required)* | Roman numeral progression (e.g., `"I - V - vi - IV"`). |
| `beats_per_chord` | `float` | `4.0` | Duration of each chord in beats. |
| `octave` | `int` | `3` | Base octave for chord voicings. |

**Raises:** `ValueError` if `.key()` has not been called.

```python
lambda h: h.key("C", "major").progression("I - V - vi - IV", beats_per_chord=4)
```

#### `.voice_lead(enable: bool = True, num_voices: int = 4) -> HarmonyTrackBuilder`
Enable voice leading for smoother chord transitions. When enabled, chord inversions are chosen to minimize note movement between successive chords.

```python
lambda h: h.key("C").progression("I - IV - V - I").voice_lead(num_voices=4)
```

#### `.arpeggiate(rate: float = 0.25, direction: str = 'up') -> HarmonyTrackBuilder`
Arpeggiate the chord progression instead of rendering block chords. Uses the `Arpeggiator` module.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rate` | `float` | `0.25` | Note rate in beats (0.25 = sixteenth notes). |
| `direction` | `str` | `'up'` | Arpeggio direction: `'up'`, `'down'`, `'up_down'`, or `'random'`. |

```python
lambda h: h.key("Am").progression("i - iv - v - i").arpeggiate(rate=0.25, direction='up_down')
```

#### `.synth(synth_type: str) -> HarmonyTrackBuilder`
Set the synthesizer type.

Supported types: `'saw'` (default), `'sine'`, `'square'`, `'triangle'`, `'warm_pad'` (alias `'pad'`), `'string_pad'`.

The `'warm_pad'` and `'string_pad'` types attempt to use `PadSynth` and fall back to sawtooth.

```python
lambda h: h.synth('warm_pad')
```

#### `.render_harmony() -> None`
Render all chord events to sample placements on the track. Called **automatically** by `SongBuilder.add_harmony()`. If arpeggiation is enabled, uses `Arpeggiator`; otherwise renders block chords via `ChordProgression.to_events()`.

#### `.humanize(timing: float = 0.01, velocity: float = 0.1, seed: Optional[int] = None) -> HarmonyTrackBuilder`
Apply humanization to all placements.

#### `.groove(template) -> HarmonyTrackBuilder`
Apply a groove template to all placements.

#### `.automate_volume(curve: AutomationCurve) -> HarmonyTrackBuilder`
Attach a volume automation curve.

#### `.automate_pan(curve: AutomationCurve) -> HarmonyTrackBuilder`
Attach a pan automation curve.

> **Inherited methods:** `.volume()`, `.pan()`, `.mute()`, `.solo()`, `.effect()`, `.add()`, `.add_at_bar()`, `.sample()` -- see `TrackBuilder`.

---

## SectionBuilder

Builder for creating reusable song sections. Provides the same track-building API as `SongBuilder` but produces `Section` objects (from `beatmaker.arrangement`) that can be combined into an `Arrangement` and placed on the song timeline.

The `SectionBuilder` receives the parent song context for beat/bar conversion and inherits the attached sample library.

### Constructor

```python
SectionBuilder(
    name: str,
    bars: int,
    song_context: Song,
    library=None
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | *(required)* | Section name (e.g., `"verse"`, `"chorus"`). |
| `bars` | `int` | *(required)* | Length of the section in bars. |
| `song_context` | `Song` | *(required)* | Parent song (used for tempo and time signature context). |
| `library` | `SampleLibrary` or `None` | `None` | Optional sample library. |

> **Note:** You typically create a `SectionBuilder` via `SongBuilder.section(name, bars)` rather than instantiating it directly.

### Methods

#### `.add_drums(builder: Callable[[DrumTrackBuilder], DrumTrackBuilder]) -> SectionBuilder`
Add a drum track to the section. Works identically to `SongBuilder.add_drums()`.

```python
verse = song_builder.section("verse", 8).add_drums(lambda d: d
    .four_on_floor()
    .backbeat()
).build()
```

#### `.add_bass(builder: Callable[[BassTrackBuilder], BassTrackBuilder]) -> SectionBuilder`
Add a bass track to the section.

```python
verse = song_builder.section("verse", 8).add_bass(lambda b: b
    .line([('E2', 0, 2), ('G2', 2, 2)])
).build()
```

#### `.add_melody(builder: Callable[[MelodyTrackBuilder], MelodyTrackBuilder], name: str = "Melody", synth_type: str = 'saw') -> SectionBuilder`
Add a melodic track to the section. Calls `render_melody()` automatically after the callback.

#### `.add_harmony(builder: Callable[[HarmonyTrackBuilder], HarmonyTrackBuilder], name: str = "Harmony", synth_type: str = 'saw') -> SectionBuilder`
Add a harmony track to the section. Calls `render_harmony()` automatically after the callback.

#### `.add_track(name: str, track_type: TrackType = TrackType.FX, builder: Optional[Callable[[TrackBuilder], TrackBuilder]] = None) -> SectionBuilder`
Add a generic track to the section.

#### `.build() -> Section`
Build and return the `Section` object for use with `Arrangement`.

```python
verse = song_builder.section("verse", 8).add_drums(...).add_bass(...).build()
chorus = song_builder.section("chorus", 8).add_drums(...).build()

song = (song_builder
    .arrange(Arrangement()
        .add(verse, at_bar=0)
        .add(chorus, at_bar=8)
        .add(verse, at_bar=16)
    )
    .build())
```

---

## create_song

```python
def create_song(name: str = "Untitled") -> SongBuilder
```

Convenience function that returns a new `SongBuilder`. Equivalent to `SongBuilder(name)`.

```python
song = (create_song("My Beat")
    .tempo(128)
    .bars(4)
    .samples(lib)
    .add_drums(lambda d: d
        .use_kit_from("drums/808")
        .four_on_floor()
        .backbeat()
        .eighth_hats()
    )
    .add_bass(lambda b: b
        .note('E2', 0, 2)
        .note('G2', 2, 2)
    )
    .add_melody(lambda m: m
        .synth('pluck')
        .play("C4:1 E4:0.5 G4:0.5 C5:2")
    )
    .add_harmony(lambda h: h
        .key("C", "major")
        .progression("I - V - vi - IV")
        .voice_lead()
    , synth_type='warm_pad')
    .master_limiter()
    .build())

song.export("my_beat.wav")
```

---

## Design Patterns and Notes

### Fluent Builder (Method Chaining)

Every builder method returns `self`, allowing calls to be chained:

```python
create_song("X").tempo(140).bars(8).add_drums(...).add_bass(...).build()
```

### Callback Pattern

Track-adding methods (`add_drums`, `add_bass`, `add_melody`, `add_harmony`, `add_track`) accept a **callback function** that receives a specialized builder instance. The callback configures the builder; the outer method handles track creation and registration. This keeps each track's configuration scoped inside a lambda or function:

```python
.add_drums(lambda d: d.four_on_floor().backbeat())
```

The callback does not need to return the builder explicitly; the return value is ignored. The builder mutates the track in-place.

### SampleLibrary Propagation

When `.samples(library)` is called on `SongBuilder`, the library reference is stored and **automatically forwarded** to every track builder, section builder, and their children. This makes sample-based methods (`.sample()`, `.use_sample()`, `.use_kit_from()`, `.sample_note()`) available without re-attaching the library at each level.

Flow: `SongBuilder.samples(lib)` -> stored in `_library` -> passed to `TrackBuilder(library=...)` / `SectionBuilder(library=...)` constructors -> available as `self._library` in all builder methods.

### Automatic Synthesis Fallback

- **DrumTrackBuilder:** If no samples are assigned via `use_kit()`, `use_sample()`, or `use_kit_from()`, drum hits are auto-generated using `DrumSynth` (kick, snare, hihat, clap).
- **MelodyTrackBuilder / HarmonyTrackBuilder:** Notes are always synthesized on-the-fly. Advanced synth types (`'fm'`, `'pluck'`, `'warm_pad'`, `'string_pad'`) attempt to use specialized synth modules and fall back to sawtooth wave on failure.

### Section and Arrangement Workflow

1. Create sections with `SongBuilder.section(name, bars)` -> `SectionBuilder`.
2. Build each section with `.add_drums(...)`, `.add_bass(...)`, etc., then `.build()` to get a `Section`.
3. Combine sections using an `Arrangement` and apply it with `SongBuilder.arrange(arrangement)`.
4. Call `.build()` on the `SongBuilder` to get the final `Song`.

### Rendering Pipeline

`Song.render()` sums all non-muted (or soloed) tracks, then applies master effects. Each `Track.render()` is responsible for placing its samples at the correct times. The progress bar (`tqdm`) shows track-level progress.

### Beat vs Bar Addressing

- **Beats** are zero-indexed within the song. Beat `0` is the start, beat `4` is the start of bar 2 in 4/4 time.
- **Bars** are also zero-indexed. Bar `0` is the first bar.
- Drum pattern `beats` parameters are **within a single bar** and are automatically repeated across `pattern_bars`.
