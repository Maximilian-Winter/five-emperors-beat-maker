# Arrangement & Expression API Reference

Comprehensive API documentation for the `beatmaker.arrangement` and `beatmaker.expression` modules.

---

# arrangement.py

Provides Section and Arrangement abstractions for composing full songs from reusable, transformable building blocks.

---

## Section

A named section of a song (verse, chorus, bridge, intro, etc.). Each section has a defined length in bars and contains its own collection of tracks. Sections can be reused, varied, and arranged into a complete song structure.

### Constructor

```python
Section(name: str, bars: int, tracks: List[Track] = [])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *(required)* | Identifier for this section (e.g. `"verse"`, `"chorus"`). |
| `bars` | `int` | *(required)* | Length of the section in bars. |
| `tracks` | `List[Track]` | `[]` | Tracks belonging to this section. |

### Methods

#### `.add_track(track: Track) -> Section`

Add a track to this section in-place.

| Parameter | Type | Description |
|-----------|------|-------------|
| `track` | `Track` | The track to add. |

**Returns:** `Section` -- the same section instance (for chaining).

---

#### `.get_track(name: str) -> Optional[Track]`

Retrieve a track by its name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name of the track to find. |

**Returns:** The matching `Track`, or `None` if not found.

---

#### `.variant(name: str, modifier: Callable[[Section], Section]) -> Section`

Create a named variation of this section. The modifier function receives a **deep copy** and can freely alter tracks, effects, volume, etc.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name for the new variant section. |
| `modifier` | `Callable[[Section], Section]` | Function that receives and returns the modified copy. |

**Returns:** A new `Section` (deep copy, modified).

```python
verse2 = verse.variant("verse2", lambda s: s.with_volume("Bass", 0.8))
```

---

#### `.with_added_track(track: Track, name: Optional[str] = None) -> Section`

Return a deep copy of the section with an additional track appended.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track` | `Track` | *(required)* | The track to add. |
| `name` | `Optional[str]` | `None` | Name for the new section. Defaults to `"{original_name}_plus"`. |

**Returns:** A new `Section` with the added track.

---

#### `.without_track(track_name: str, name: Optional[str] = None) -> Section`

Return a deep copy of the section with a track removed by name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_name` | `str` | *(required)* | Name of the track to remove. |
| `name` | `Optional[str]` | `None` | Name for the new section. Defaults to `"{original_name}_minus"`. |

**Returns:** A new `Section` without the specified track.

---

#### `.with_volume(track_name: str, volume: float, name: Optional[str] = None) -> Section`

Return a deep copy with a specific track's volume changed.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_name` | `str` | *(required)* | Name of the track to modify. |
| `volume` | `float` | *(required)* | New volume level. |
| `name` | `Optional[str]` | `None` | Name for the new section. Defaults to the original name. |

**Returns:** A new `Section` with adjusted volume.

---

#### `.with_effect(track_name: str, effect: AudioEffect, name: Optional[str] = None) -> Section`

Return a deep copy with an additional audio effect appended to a track's effect chain.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_name` | `str` | *(required)* | Name of the track to modify. |
| `effect` | `AudioEffect` | *(required)* | The effect to append. |
| `name` | `Optional[str]` | `None` | Name for the new section. Defaults to the original name. |

**Returns:** A new `Section` with the added effect.

---

#### `.with_mute(track_name: str, name: Optional[str] = None) -> Section`

Return a deep copy with a track muted.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track_name` | `str` | *(required)* | Name of the track to mute. |
| `name` | `Optional[str]` | `None` | Name for the new section. Defaults to the original name. |

**Returns:** A new `Section` with the track muted (`track.muted = True`).

---

### Usage Example

```python
from beatmaker.arrangement import Section
from beatmaker.core import Track, TrackType

drums = Track(name="Drums", track_type=TrackType.SAMPLER)
bass = Track(name="Bass", track_type=TrackType.SAMPLER)

verse = Section("verse", bars=8)
verse.add_track(drums).add_track(bass)

# Create a variant with louder bass
verse2 = verse.with_volume("Bass", 0.9, name="verse2")

# Create a breakdown without drums
breakdown = verse.without_track("Drums", name="breakdown")
```

---

## Transition

Configuration for a transition between arrangement sections.

### Constructor

```python
Transition(type: str = 'cut', duration_beats: float = 0.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | `str` | `'cut'` | Transition type. Supported values: `'cut'`, `'crossfade'`. |
| `duration_beats` | `float` | `0.0` | Duration of the transition in beats (relevant for crossfade). |

---

## ArrangementEntry

A single entry in an arrangement: a section placed with a repeat count and optional transition.

### Constructor

```python
ArrangementEntry(section: Section, repeat: int = 1, transition: Optional[Transition] = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `section` | `Section` | *(required)* | The section to place. |
| `repeat` | `int` | `1` | Number of times to repeat this section. |
| `transition` | `Optional[Transition]` | `None` | Transition configuration leading into this section. |

---

## Arrangement

The full arrangement of a song -- an ordered sequence of sections. Sections can be added with semantic aliases (intro, verse, chorus, etc.) and with repeat counts. The arrangement is flattened into a Song by placing section tracks on the song timeline at computed offsets.

### Constructor

```python
Arrangement()
```

Takes no parameters. Initializes an empty arrangement.

### Methods

#### `.add(section: Section, repeat: int = 1, transition: Optional[Transition] = None) -> Arrangement`

Add a section to the arrangement.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `section` | `Section` | *(required)* | The section to add. |
| `repeat` | `int` | `1` | How many times to repeat the section. |
| `transition` | `Optional[Transition]` | `None` | Transition config for entering this section. |

**Returns:** `Arrangement` (self, for chaining).

---

#### `.intro(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds an intro section.

---

#### `.verse(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds a verse section.

---

#### `.chorus(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds a chorus section.

---

#### `.bridge(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds a bridge section.

---

#### `.outro(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds an outro section.

---

#### `.breakdown(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds a breakdown section.

---

#### `.drop(section: Section, repeat: int = 1) -> Arrangement`

Semantic alias for `.add()`. Adds a drop section.

---

#### `.entries` *(property)* `-> List[ArrangementEntry]`

Returns a copy of the internal list of arrangement entries.

---

#### `.total_bars() -> int`

Calculate the total number of bars across all entries (accounting for repeats).

**Returns:** `int` -- total bar count.

---

#### `.render_to_song(song) -> None`

Render the arrangement onto a `Song` object. Places all section tracks onto the song timeline at the correct bar offsets. Tracks with the same name are merged (placements accumulated).

| Parameter | Type | Description |
|-----------|------|-------------|
| `song` | `Song` | A `builder.Song` instance to render onto. |

---

#### `.__len__() -> int`

Returns the number of entries in the arrangement.

---

### Usage Example

```python
from beatmaker.arrangement import Section, Arrangement, Transition

intro_sec = Section("intro", bars=4)
verse_sec = Section("verse", bars=8)
chorus_sec = Section("chorus", bars=8)
outro_sec = Section("outro", bars=4)

arrangement = (
    Arrangement()
    .intro(intro_sec)
    .verse(verse_sec, repeat=2)
    .chorus(chorus_sec)
    .bridge(verse_sec.without_track("Drums", name="bridge"))
    .chorus(chorus_sec)
    .outro(outro_sec)
)

print(arrangement.total_bars())  # 44
arrangement.render_to_song(song)
```

---

# expression.py

Provides pitch expression (vibrato, bend, portamento), humanization (timing jitter, velocity variation), groove templates, and velocity curves -- everything needed to make programmatic music feel alive.

---

## Vibrato

Periodic pitch oscillation applied during a note. Creates a subtle pitch wavering that adds warmth and expressiveness, particularly for sustained notes.

### Constructor

```python
Vibrato(rate: float = 5.0, depth: float = 0.5, delay: float = 0.1)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate` | `float` | `5.0` | Oscillation rate in Hz. |
| `depth` | `float` | `0.5` | Depth of vibrato in semitones. |
| `delay` | `float` | `0.1` | Seconds before vibrato onset (allows attack to remain clean). |

### Methods

#### `.apply(audio: AudioData, base_freq: float) -> AudioData`

Apply vibrato to audio via phase modulation of the waveform. Preserves the original amplitude envelope.

| Parameter | Type | Description |
|-----------|------|-------------|
| `audio` | `AudioData` | The source audio data to process. |
| `base_freq` | `float` | Fundamental frequency of the note in Hz. |

**Returns:** `AudioData` -- new audio with vibrato applied.

---

## PitchBend

A targeted pitch shift within a note's duration. Useful for slides, scoops, and falls.

### Constructor

```python
PitchBend(start_offset: float = 0.0, end_offset: float = 0.5, semitones: float = 2.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_offset` | `float` | `0.0` | Start time as a fraction of note duration (`0.0` to `1.0`). |
| `end_offset` | `float` | `0.5` | End time as a fraction of note duration (`0.0` to `1.0`). |
| `semitones` | `float` | `2.0` | Bend amount in semitones (positive = up, negative = down). |

### Methods

#### `.generate_curve(num_samples: int) -> np.ndarray`

Generate a per-sample pitch multiplier curve. Values of `1.0` mean no bend; values above or below represent frequency multipliers. The bend value is held constant after `end_offset`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `num_samples` | `int` | Total number of samples in the note. |

**Returns:** `np.ndarray` of frequency multipliers with shape `(num_samples,)`.

```python
bend = PitchBend(start_offset=0.0, end_offset=0.3, semitones=2.0)
curve = bend.generate_curve(44100)  # 1 second at 44.1kHz
```

---

## Portamento

Smooth pitch transition (glide) between two notes. Applied between consecutive notes in a phrase.

### Constructor

```python
Portamento(glide_time: float = 0.1, curve: str = 'exponential')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `glide_time` | `float` | `0.1` | Glide duration in seconds. |
| `curve` | `str` | `'exponential'` | Interpolation curve type: `'linear'` or `'exponential'`. |

### Methods

#### `.generate_glide(from_freq: float, to_freq: float, sample_rate: int) -> np.ndarray`

Generate mono audio samples for a pitch glide from one frequency to another.

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_freq` | `float` | Starting frequency in Hz. |
| `to_freq` | `float` | Target frequency in Hz. |
| `sample_rate` | `int` | Audio sample rate (e.g. `44100`). |

**Returns:** `np.ndarray` -- mono audio samples for the glide.

```python
porta = Portamento(glide_time=0.05, curve='exponential')
glide_samples = porta.generate_glide(440.0, 880.0, 44100)
```

---

## NoteExpression

Full expression data for a single note. Bundles vibrato, pitch bend, and portamento into one container that can be attached to a Note.

### Constructor

```python
NoteExpression(
    vibrato: Optional[Vibrato] = None,
    pitch_bend: Optional[PitchBend] = None,
    portamento: Optional[Portamento] = None
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vibrato` | `Optional[Vibrato]` | `None` | Vibrato expression for this note. |
| `pitch_bend` | `Optional[PitchBend]` | `None` | Pitch bend expression for this note. |
| `portamento` | `Optional[Portamento]` | `None` | Portamento/glide into this note. |

### Usage Example

```python
expr = NoteExpression(
    vibrato=Vibrato(rate=6.0, depth=0.3),
    pitch_bend=PitchBend(start_offset=0.8, end_offset=1.0, semitones=-2.0),
)
```

---

## Humanizer

Adds human-like imperfections to timing and velocity. Transforms perfectly quantized music into something that breathes.

### Constructor

```python
Humanizer(
    timing_jitter: float = 0.01,
    velocity_variation: float = 0.1,
    seed: Optional[int] = None
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timing_jitter` | `float` | `0.01` | Maximum timing offset in seconds. |
| `velocity_variation` | `float` | `0.1` | Maximum velocity variation (`0.0` to `1.0`). |
| `seed` | `Optional[int]` | `None` | Random seed for reproducibility. |

### Methods

#### `.apply_to_events(events: List[Tuple[float, int, float, float]], bpm: float) -> List[Tuple[float, int, float, float]]`

Apply humanization to beat-based event tuples. Adds random timing jitter and velocity variation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `events` | `List[Tuple[float, int, float, float]]` | List of `(beat, midi_note, velocity, duration)` tuples. |
| `bpm` | `float` | Song tempo in beats per minute (used for timing conversion). |

**Returns:** New list of tuples with humanized timing and velocity. Velocity is clamped to `[0.01, 1.0]`.

---

#### `.apply_to_track(track: Track) -> Track`

Apply timing jitter and velocity variation to all placements in a track. Modifies the track **in-place**.

| Parameter | Type | Description |
|-----------|------|-------------|
| `track` | `Track` | The track to humanize. |

**Returns:** The same `Track` instance (for chaining).

### Usage Example

```python
humanizer = Humanizer(timing_jitter=0.015, velocity_variation=0.12, seed=42)

# On event tuples
events = [(0.0, 36, 0.9, 0.25), (1.0, 38, 0.8, 0.25)]
humanized = humanizer.apply_to_events(events, bpm=120)

# On a track
humanizer.apply_to_track(drum_track)
```

---

## GrooveTemplate

A groove template providing per-step timing and velocity offsets. Each position in the template maps to a 16th-note position within a bar (16 positions per bar in 4/4 time). The offsets repeat cyclically across the duration of a track or pattern.

### Constructor

```python
GrooveTemplate(
    name: str,
    timing_offsets: List[float],
    velocity_scales: List[float]
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *(required)* | Descriptive name for this groove. |
| `timing_offsets` | `List[float]` | *(required)* | Timing shift per step as a fraction of step duration. Positive = late, negative = early. |
| `velocity_scales` | `List[float]` | *(required)* | Velocity multiplier per step (`1.0` = unchanged). |

### Properties

#### `.length -> int`

Number of steps in the groove template.

### Methods

#### `.apply_to_events(events: List[Tuple[float, int, float, float]], bpm: float, steps_per_beat: int = 4) -> List[Tuple[float, int, float, float]]`

Apply groove template to beat-based event tuples. Each event is quantized to its nearest step position, and the corresponding timing offset and velocity scale are applied.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `events` | `List[Tuple[float, int, float, float]]` | *(required)* | List of `(beat, midi_note, velocity, duration)` tuples. |
| `bpm` | `float` | *(required)* | Song tempo in BPM. |
| `steps_per_beat` | `int` | `4` | Step resolution (4 = 16th notes). |

**Returns:** New list of tuples with groove-adjusted timing and velocity. Velocity is clamped to `[0.01, 1.0]`.

---

#### `.apply_to_track(track: Track, bpm: float, steps_per_beat: int = 4) -> Track`

Apply groove template to all placements in a track. Modifies the track **in-place**.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track` | `Track` | *(required)* | The track to apply the groove to. |
| `bpm` | `float` | *(required)* | Song tempo in BPM. |
| `steps_per_beat` | `int` | `4` | Step resolution (4 = 16th notes). |

**Returns:** The same `Track` instance (for chaining).

---

### Preset Methods

All preset methods are `@classmethod` constructors that return a pre-configured `GrooveTemplate`.

#### `GrooveTemplate.mpc_swing(amount: float = 0.6) -> GrooveTemplate`

MPC-style swing. Delays every other 16th note.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `amount` | `float` | `0.6` | Swing amount. `0.5` = straight, `0.67` = classic swing, `1.0` = full triplet feel. |

Velocity pattern alternates between `1.0` (on-beat) and `0.75` (off-beat).

---

#### `GrooveTemplate.funk() -> GrooveTemplate`

Funk groove with pushed offbeats and syncopated accents. Uses a fixed 16-step pattern with negative offsets on certain positions (pulling notes slightly early) and positive offsets on others (pushing notes late).

---

#### `GrooveTemplate.shuffle(depth: float = 0.67) -> GrooveTemplate`

Shuffle / triplet feel with emphasis on downbeats.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `depth` | `float` | `0.67` | Shuffle depth. `0.5` = straight, higher values = more pronounced shuffle. |

Velocity pattern alternates between `1.0` (on-beat) and `0.6` (off-beat).

---

#### `GrooveTemplate.lazy() -> GrooveTemplate`

Laid-back feel where everything sits slightly behind the beat. All timing offsets are positive (late). Velocity emphasizes downbeats with a relaxed dynamic pattern.

---

#### `GrooveTemplate.driving() -> GrooveTemplate`

Driving/rushing feel where notes sit slightly ahead of the beat. All timing offsets are negative (early). Strong, even velocity pattern with accented downbeats.

---

#### `GrooveTemplate.hip_hop() -> GrooveTemplate`

Hip-hop groove with heavy downbeats and lazy backbeats. Features moderate positive timing offsets on off-beats with strong velocity contrast between downbeats (`1.0`) and ghost notes (`0.4`).

---

### Usage Example

```python
from beatmaker.expression import GrooveTemplate

# Use a preset
groove = GrooveTemplate.mpc_swing(amount=0.67)

# Apply to events
events = [(0.0, 36, 0.9, 0.25), (0.25, 42, 0.6, 0.25), (0.5, 36, 0.9, 0.25)]
grooved = groove.apply_to_events(events, bpm=90)

# Apply to a track
groove.apply_to_track(hi_hat_track, bpm=90)

# Custom groove template
custom = GrooveTemplate(
    name="my_groove",
    timing_offsets=[0.0, 0.05, 0.0, -0.02] * 4,
    velocity_scales=[1.0, 0.6, 0.8, 0.5] * 4,
)
```

---

## VelocityCurve

Maps input velocity to output velocity, shaping dynamics. All methods are static -- `VelocityCurve` is used as a namespace rather than instantiated.

### Static Methods

#### `VelocityCurve.linear(velocity: float) -> float`

Identity mapping. Returns the input velocity unchanged.

| Parameter | Type | Description |
|-----------|------|-------------|
| `velocity` | `float` | Input velocity (`0.0` to `1.0`). |

**Returns:** `float` -- same as input.

---

#### `VelocityCurve.exponential(velocity: float, power: float = 2.0) -> float`

Exponential curve. Makes soft notes quieter and loud notes louder, increasing dynamic range.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `velocity` | `float` | *(required)* | Input velocity (`0.0` to `1.0`). |
| `power` | `float` | `2.0` | Exponent controlling curve steepness. |

**Returns:** `float` -- `velocity ** power`.

---

#### `VelocityCurve.logarithmic(velocity: float) -> float`

Logarithmic curve. Makes soft notes louder and loud notes gentler, compressing dynamic range upward.

| Parameter | Type | Description |
|-----------|------|-------------|
| `velocity` | `float` | Input velocity (`0.0` to `1.0`). |

**Returns:** `float` -- `log(1 + velocity * (e - 1))`.

---

#### `VelocityCurve.compressed(velocity: float, amount: float = 0.5) -> float`

Reduce dynamic range by mixing input velocity with a constant.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `velocity` | `float` | *(required)* | Input velocity (`0.0` to `1.0`). |
| `amount` | `float` | `0.5` | Compression amount. `0.0` = no compression, `1.0` = flat output at 1.0. |

**Returns:** `float` -- `velocity * (1 - amount) + amount`.

---

#### `VelocityCurve.s_curve(velocity: float) -> float`

S-curve mapping. Accentuates extremes and flattens the middle of the dynamic range.

| Parameter | Type | Description |
|-----------|------|-------------|
| `velocity` | `float` | Input velocity (`0.0` to `1.0`). |

**Returns:** `float` -- `3v^2 - 2v^3` (Hermite smoothstep).

---

#### `VelocityCurve.apply_to_events(events: List[Tuple[float, int, float, float]], curve_fn: Callable[[float], float]) -> List[Tuple[float, int, float, float]]`

Apply any velocity curve function to all events in a list.

| Parameter | Type | Description |
|-----------|------|-------------|
| `events` | `List[Tuple[float, int, float, float]]` | List of `(beat, midi_note, velocity, duration)` tuples. |
| `curve_fn` | `Callable[[float], float]` | A velocity mapping function (e.g. `VelocityCurve.exponential`). |

**Returns:** New list of tuples with transformed velocities, clamped to `[0.01, 1.0]`.

### Usage Example

```python
from beatmaker.expression import VelocityCurve

events = [(0.0, 60, 0.5, 1.0), (1.0, 62, 0.8, 1.0)]

# Apply exponential curve
shaped = VelocityCurve.apply_to_events(events, VelocityCurve.exponential)

# Apply with custom power
shaped = VelocityCurve.apply_to_events(
    events,
    lambda v: VelocityCurve.exponential(v, power=3.0)
)

# Apply compression
shaped = VelocityCurve.apply_to_events(
    events,
    lambda v: VelocityCurve.compressed(v, amount=0.3)
)
```
