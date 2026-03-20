# Arrangement, Automation & Expression

This document covers three tightly related modules that together control the
macro-structure and micro-feel of a beatmaker project:

- **arrangement** -- sections, arrangement, transitions
- **automation** -- time-varying parameter curves
- **expression** -- vibrato, pitch bend, humanization, groove, velocity shaping

Source files:
`beatmaker/arrangement.py`, `beatmaker/automation.py`, `beatmaker/expression.py`

---

## 1. Section

```python
from beatmaker.arrangement import Section
```

A `Section` is a named, self-contained chunk of a song (intro, verse, chorus,
etc.). It owns a list of `Track` objects and has a length measured in bars.

### Fields

| Field    | Type          | Default | Description                       |
|----------|---------------|---------|-----------------------------------|
| `name`   | `str`         | --      | Human-readable label (e.g. `"verse1"`) |
| `bars`   | `int`         | --      | Length of the section in bars      |
| `tracks` | `List[Track]` | `[]`    | Tracks that play during this section |

### Methods

#### `add_track(track: Track) -> Section`

Appends `track` to the section's track list **in place** and returns `self`
for chaining.

```python
verse = Section("verse", bars=8)
verse.add_track(drums_track).add_track(bass_track)
```

#### `get_track(name: str) -> Optional[Track]`

Returns the first track whose `.name` matches, or `None`.

```python
bass = verse.get_track("Bass")
```

#### `variant(name: str, modifier: Callable[[Section], Section]) -> Section`

Creates a **deep copy** of the section, renames it to `name`, and passes the
copy through `modifier`.  The original section is unchanged.

```python
verse2 = verse.variant("verse2", lambda s: s.with_volume("Bass", 0.8))
```

| Parameter  | Type                             | Description                          |
|------------|----------------------------------|--------------------------------------|
| `name`     | `str`                            | Name for the new variant             |
| `modifier` | `Callable[[Section], Section]`   | Function that mutates and returns the copy |

#### `with_added_track(track: Track, name: Optional[str] = None) -> Section`

Returns a deep copy with `track` appended.  The new section is named `name`
(defaults to `"{original_name}_plus"`).

```python
verse_plus_pad = verse.with_added_track(pad_track, name="verse_lush")
```

| Parameter | Type             | Default                  | Description                |
|-----------|------------------|--------------------------|----------------------------|
| `track`   | `Track`          | --                       | Track to add               |
| `name`    | `Optional[str]`  | `"{self.name}_plus"`     | Name for the new section   |

#### `without_track(track_name: str, name: Optional[str] = None) -> Section`

Returns a deep copy with the track named `track_name` removed.  Defaults the
new section name to `"{self.name}_minus"`.

```python
breakdown = verse.without_track("Drums", name="breakdown")
```

| Parameter    | Type             | Default                  | Description                |
|--------------|------------------|--------------------------|----------------------------|
| `track_name` | `str`            | --                       | Name of the track to drop  |
| `name`       | `Optional[str]`  | `"{self.name}_minus"`    | Name for the new section   |

#### `with_volume(track_name: str, volume: float, name: Optional[str] = None) -> Section`

Returns a deep copy where the matched track's `.volume` is set to `volume`.

```python
quiet_verse = verse.with_volume("Synth", 0.4)
```

| Parameter    | Type             | Default      | Description                  |
|--------------|------------------|--------------|------------------------------|
| `track_name` | `str`            | --           | Target track name            |
| `volume`     | `float`          | --           | New volume level             |
| `name`       | `Optional[str]`  | `self.name`  | Name for the new section     |

#### `with_effect(track_name: str, effect: AudioEffect, name: Optional[str] = None) -> Section`

Returns a deep copy with `effect` appended to the matched track's effect chain.

```python
verse_reverb = verse.with_effect("Vocals", Reverb(room_size=0.6))
```

| Parameter    | Type             | Default      | Description                  |
|--------------|------------------|--------------|------------------------------|
| `track_name` | `str`            | --           | Target track name            |
| `effect`     | `AudioEffect`    | --           | Effect to append             |
| `name`       | `Optional[str]`  | `self.name`  | Name for the new section     |

#### `with_mute(track_name: str, name: Optional[str] = None) -> Section`

Returns a deep copy with the matched track's `.muted` flag set to `True`.

```python
no_bass = verse.with_mute("Bass")
```

| Parameter    | Type             | Default      | Description                  |
|--------------|------------------|--------------|------------------------------|
| `track_name` | `str`            | --           | Target track name            |
| `name`       | `Optional[str]`  | `self.name`  | Name for the new section     |

---

## 2. Arrangement

```python
from beatmaker.arrangement import Arrangement
```

An `Arrangement` is an ordered sequence of `ArrangementEntry` objects. It
describes the full song structure and can render itself onto a `Song` timeline.

### Constructor

```python
arr = Arrangement()
```

Takes no arguments. Internal state is an empty list of entries.

### `add(section, repeat=1, transition=None) -> Arrangement`

The general-purpose method for appending a section.

| Parameter    | Type                    | Default | Description                          |
|--------------|-------------------------|---------|--------------------------------------|
| `section`    | `Section`               | --      | The section to add                   |
| `repeat`     | `int`                   | `1`     | How many times to repeat this section |
| `transition` | `Optional[Transition]`  | `None`  | Transition into this section          |

Returns `self` for chaining.

### Semantic Aliases

These are convenience wrappers around `add` that improve readability.
All accept `(section: Section, repeat: int = 1)` and return `self`.

| Method        | Typical Use                          |
|---------------|--------------------------------------|
| `intro()`     | Opening section                      |
| `verse()`     | Verse                                |
| `chorus()`    | Chorus / hook                        |
| `bridge()`    | Bridge / transition                  |
| `outro()`     | Ending section                       |
| `breakdown()` | Breakdown / sparse section           |
| `drop()`      | Drop / climax                        |

```python
arr = (Arrangement()
    .intro(intro_section)
    .verse(verse_section, repeat=2)
    .chorus(chorus_section)
    .bridge(bridge_section)
    .chorus(chorus_section, repeat=2)
    .outro(outro_section))
```

### Properties and Methods

#### `entries -> List[ArrangementEntry]`

Read-only property returning a copy of the internal entry list.

#### `total_bars() -> int`

Returns the total number of bars across all entries, accounting for repeats.

#### `render_to_song(song) -> None`

Flattens the arrangement onto a `Song` object.  For each entry and each repeat,
it places every section track onto the song timeline at the computed bar offset.
Tracks with the same name across different sections are merged (their placements
accumulate on the same `Track` instance).

```python
from beatmaker.builder import Song
song = Song(bpm=128, time_signature=(4, 4))
arr.render_to_song(song)
audio = song.render()
```

---

## 3. ArrangementEntry

```python
from beatmaker.arrangement import ArrangementEntry
```

A dataclass representing one slot in an arrangement.

| Field        | Type                    | Default | Description                       |
|--------------|-------------------------|---------|-----------------------------------|
| `section`    | `Section`               | --      | The section placed here           |
| `repeat`     | `int`                   | `1`     | Number of repetitions             |
| `transition` | `Optional[Transition]`  | `None`  | How to transition into this entry |

---

## 4. Transition

```python
from beatmaker.arrangement import Transition
```

Configuration for the transition between two consecutive sections.

| Field           | Type    | Default | Description                                  |
|-----------------|---------|---------|----------------------------------------------|
| `type`          | `str`   | `'cut'` | `'cut'` (instant) or `'crossfade'`           |
| `duration_beats`| `float` | `0.0`   | Length of the crossfade in beats (ignored for `'cut'`) |

```python
arr.add(chorus, transition=Transition(type='crossfade', duration_beats=4.0))
```

---

## 5. AutomationCurve

```python
from beatmaker.automation import AutomationCurve
```

A series of breakpoints that define how a parameter changes over time (measured
in beats).  The curve can be sampled at any beat position and can also be
rendered to a per-sample numpy array for audio-rate modulation.

### Fields

| Field           | Type                      | Default | Description                            |
|-----------------|---------------------------|---------|----------------------------------------|
| `name`          | `str`                     | --      | Descriptive label                      |
| `points`        | `List[AutomationPoint]`   | `[]`    | Ordered breakpoints                    |
| `default_value` | `float`                   | `0.0`   | Value when no points are defined       |

### Methods

#### `add_point(beat, value, curve=CurveType.LINEAR) -> AutomationCurve`

Inserts a breakpoint and keeps the list sorted by beat.

| Parameter | Type        | Default              | Description               |
|-----------|-------------|----------------------|---------------------------|
| `beat`    | `float`     | --                   | Position in beats         |
| `value`   | `float`     | --                   | Parameter value           |
| `curve`   | `CurveType` | `CurveType.LINEAR`   | Interpolation to next pt  |

```python
vol = AutomationCurve("volume")
vol.add_point(0, 0.0).add_point(4, 1.0).add_point(16, 0.5)
```

#### `ramp(start_beat, end_beat, start_value, end_value, curve=CurveType.LINEAR) -> AutomationCurve`

Convenience: adds two breakpoints forming a ramp.

| Parameter     | Type        | Default              | Description               |
|---------------|-------------|----------------------|---------------------------|
| `start_beat`  | `float`     | --                   | Ramp start beat           |
| `end_beat`    | `float`     | --                   | Ramp end beat             |
| `start_value` | `float`     | --                   | Value at start            |
| `end_value`   | `float`     | --                   | Value at end              |
| `curve`       | `CurveType` | `CurveType.LINEAR`   | Interpolation type        |

```python
vol = AutomationCurve("volume").ramp(0, 8, 0.0, 1.0, CurveType.SMOOTH)
```

#### `lfo(start_beat, end_beat, center, depth, rate_hz, waveform='sine', bpm=120.0) -> AutomationCurve`

Generates many breakpoints that trace an LFO oscillation between `start_beat`
and `end_beat`.

| Parameter    | Type    | Default    | Description                                |
|--------------|---------|------------|--------------------------------------------|
| `start_beat` | `float` | --         | Range start in beats                       |
| `end_beat`   | `float` | --         | Range end in beats                         |
| `center`     | `float` | --         | DC offset / center value                   |
| `depth`      | `float` | --         | Oscillation amplitude                      |
| `rate_hz`    | `float` | --         | Oscillation frequency in Hz                |
| `waveform`   | `str`   | `'sine'`   | `'sine'`, `'triangle'`, `'square'`, `'saw'` |
| `bpm`        | `float` | `120.0`    | Tempo for beat-to-time conversion          |

```python
wobble = AutomationCurve("cutoff").lfo(0, 16, 800, 600, 2.0, waveform='triangle')
```

#### `render(bpm, sample_rate, duration_beats) -> np.ndarray`

Renders the curve to a per-sample 1D numpy array.

| Parameter       | Type    | Description                    |
|-----------------|---------|--------------------------------|
| `bpm`           | `float` | Song tempo                     |
| `sample_rate`   | `int`   | Audio sample rate (e.g. 44100) |
| `duration_beats`| `float` | Total length in beats          |

Returns a 1D `np.ndarray` with one value per audio sample.

#### `sample_at(beat: float) -> float`

Returns the interpolated value at a specific beat, using the curve type
defined on the preceding breakpoint.

### Preset Factory Methods

| Method                                                                 | Description                              |
|------------------------------------------------------------------------|------------------------------------------|
| `AutomationCurve.fade_in(beats: float)`                                | 0 to 1 ramp over `beats`                |
| `AutomationCurve.fade_out(start_beat: float, duration: float)`         | 1 to 0 ramp starting at `start_beat`    |
| `AutomationCurve.filter_sweep(start_beat, end_beat, start_freq, end_freq)` | Exponential cutoff sweep            |
| `AutomationCurve.swell(peak_beat, peak_value=1.0, start_value=0.0)`   | Crescendo-decrescendo using SMOOTH curves |

---

## 6. AutomationPoint

```python
from beatmaker.automation import AutomationPoint
```

A single breakpoint in an automation curve.

| Field   | Type        | Default              | Description                            |
|---------|-------------|----------------------|----------------------------------------|
| `beat`  | `float`     | --                   | Position in beats                      |
| `value` | `float`     | --                   | Parameter value at this point          |
| `curve` | `CurveType` | `CurveType.LINEAR`   | Interpolation to the *next* point      |

---

## 7. CurveType

```python
from beatmaker.automation import CurveType
```

An enum defining how values are interpolated between two consecutive
`AutomationPoint` instances.

| Member          | Behaviour                                                          |
|-----------------|--------------------------------------------------------------------|
| `LINEAR`        | Straight line between points                                       |
| `EXPONENTIAL`   | Exponential growth/decay (ratio-based when start > 0, quadratic fallback otherwise) |
| `LOGARITHMIC`   | Logarithmic curve via `log1p` -- fast rise, gentle tail            |
| `STEP`          | Hold the starting value until the next point                       |
| `SMOOTH`        | Cosine interpolation for S-shaped transitions                      |

---

## 8. AutomatableEffect, AutomatedGain, AutomatedFilter

### AutomatableEffect (abstract base)

```python
from beatmaker.automation import AutomatableEffect
```

Abstract subclass of `AudioEffect` that supports parameter automation. It holds
a dictionary of `AutomationCurve` objects keyed by parameter name.

#### `automate(param_name: str, curve: AutomationCurve) -> AutomatableEffect`

Attach a curve to a named parameter.

| Parameter    | Type              | Description           |
|--------------|-------------------|-----------------------|
| `param_name` | `str`             | Parameter to automate |
| `curve`      | `AutomationCurve` | The automation curve  |

#### `set_context(bpm: float, start_beat: float = 0.0) -> None`

Set the temporal context so that automation curves render correctly.

| Parameter    | Type    | Default | Description           |
|--------------|---------|---------|----------------------|
| `bpm`        | `float` | --      | Song tempo            |
| `start_beat` | `float` | `0.0`   | Beat offset           |

### AutomatedGain

```python
from beatmaker.automation import AutomatedGain
```

Gain effect with an automatable `'level'` parameter.

| Constructor Param | Type    | Default | Description       |
|-------------------|---------|---------|-------------------|
| `level`           | `float` | `1.0`   | Static gain level  |

```python
gain = AutomatedGain(level=0.5)
gain.automate('level', AutomationCurve.fade_in(8))
gain.set_context(bpm=120)
output = gain.process(audio)
```

### AutomatedFilter

```python
from beatmaker.automation import AutomatedFilter
```

Low-pass biquad filter with automatable `'cutoff'` and `'resonance'`.
Coefficients are updated every 64 samples for efficiency.

| Constructor Param | Type    | Default  | Description                        |
|-------------------|---------|----------|------------------------------------|
| `cutoff`          | `float` | `1000.0` | Static cutoff frequency in Hz      |
| `resonance`       | `float` | `0.707`  | Static Q factor                    |

```python
filt = AutomatedFilter(cutoff=200, resonance=1.5)
filt.automate('cutoff', AutomationCurve.filter_sweep(0, 16, 200, 8000))
filt.set_context(bpm=140)
output = filt.process(audio)
```

---

## 9. Vibrato

```python
from beatmaker.expression import Vibrato
```

Periodic pitch oscillation applied to a sustained note.

### Fields

| Field   | Type    | Default | Description                          |
|---------|---------|---------|--------------------------------------|
| `rate`  | `float` | `5.0`   | Oscillation rate in Hz               |
| `depth` | `float` | `0.5`   | Depth in semitones                   |
| `delay` | `float` | `0.1`   | Seconds before vibrato onset         |

### `apply(audio: AudioData, base_freq: float) -> AudioData`

Applies vibrato via phase modulation.  A 100 ms ramp-in smooths the onset
after the initial delay.

| Parameter    | Type        | Description                                |
|--------------|-------------|--------------------------------------------|
| `audio`      | `AudioData` | Input audio                                |
| `base_freq`  | `float`     | Fundamental frequency of the note (Hz)     |

```python
vib = Vibrato(rate=6.0, depth=0.3, delay=0.2)
output = vib.apply(synth_note, base_freq=440.0)
```

---

## 10. PitchBend

```python
from beatmaker.expression import PitchBend
```

A targeted pitch shift that ramps over a portion of a note's duration.

### Fields

| Field          | Type    | Default | Description                                      |
|----------------|---------|---------|--------------------------------------------------|
| `start_offset` | `float` | `0.0`   | Start time as a fraction of note duration (0..1) |
| `end_offset`   | `float` | `0.5`   | End time as a fraction of note duration (0..1)   |
| `semitones`    | `float` | `2.0`   | Bend amount in semitones                         |

### `generate_curve(num_samples: int) -> np.ndarray`

Returns a 1D array of per-sample frequency multipliers.  Values are `1.0` (no
bend) outside the bend region.  The bend ramps linearly from 0 to `semitones`
between `start_offset` and `end_offset`, then holds the final value through the
remainder of the note.

| Parameter      | Type  | Description                      |
|----------------|-------|----------------------------------|
| `num_samples`  | `int` | Length of the output array       |

```python
bend = PitchBend(start_offset=0.0, end_offset=0.3, semitones=-2)
curve = bend.generate_curve(44100)  # 1 second at 44.1 kHz
```

---

## 11. Portamento & NoteExpression

### Portamento

```python
from beatmaker.expression import Portamento
```

Smooth pitch glide between two consecutive notes.

| Field        | Type    | Default          | Description                            |
|--------------|---------|------------------|----------------------------------------|
| `glide_time` | `float` | `0.1`            | Glide duration in seconds              |
| `curve`      | `str`   | `'exponential'`  | `'linear'` or `'exponential'`          |

#### `generate_glide(from_freq, to_freq, sample_rate) -> np.ndarray`

Returns mono audio samples of a frequency sweep from `from_freq` to `to_freq`.

| Parameter     | Type    | Description                |
|---------------|---------|----------------------------|
| `from_freq`   | `float` | Starting frequency (Hz)    |
| `to_freq`     | `float` | Ending frequency (Hz)      |
| `sample_rate` | `int`   | Audio sample rate          |

```python
porta = Portamento(glide_time=0.05, curve='exponential')
glide_audio = porta.generate_glide(440.0, 880.0, 44100)
```

### NoteExpression

```python
from beatmaker.expression import NoteExpression
```

A container that bundles all expression types for a single note.

| Field        | Type                   | Default | Description          |
|--------------|------------------------|---------|----------------------|
| `vibrato`    | `Optional[Vibrato]`    | `None`  | Vibrato settings     |
| `pitch_bend` | `Optional[PitchBend]` | `None`  | Pitch bend settings  |
| `portamento` | `Optional[Portamento]`| `None`  | Portamento settings  |

```python
expr = NoteExpression(
    vibrato=Vibrato(rate=5, depth=0.3),
    pitch_bend=PitchBend(semitones=2),
)
```

---

## 12. Humanizer

```python
from beatmaker.expression import Humanizer
```

Adds human-like imperfections to timing and velocity.

### Fields

| Field                | Type            | Default | Description                                    |
|----------------------|-----------------|---------|------------------------------------------------|
| `timing_jitter`      | `float`         | `0.01`  | Maximum timing offset in seconds               |
| `velocity_variation` | `float`         | `0.1`   | Maximum velocity offset (0..1 range)            |
| `seed`               | `Optional[int]` | `None`  | Random seed for reproducibility                |

### `apply_to_events(events, bpm) -> List[Tuple[float, int, float, float]]`

Applies humanization to a list of beat-based event tuples.

| Parameter | Type                                          | Description                             |
|-----------|-----------------------------------------------|-----------------------------------------|
| `events`  | `List[Tuple[float, int, float, float]]`       | `(beat, midi_note, velocity, duration)`  |
| `bpm`     | `float`                                       | Song tempo (for timing conversion)      |

Returns a new list with jittered timing and velocity.  Velocity is clamped to
`[0.01, 1.0]` and beat times are clamped to `>= 0`.

### `apply_to_track(track: Track) -> Track`

Applies timing jitter and velocity variation to all `SamplePlacement` objects
in the track **in place**.  Returns the same track for chaining.

| Parameter | Type    | Description     |
|-----------|---------|-----------------|
| `track`   | `Track` | Track to modify |

```python
humanizer = Humanizer(timing_jitter=0.015, velocity_variation=0.08, seed=42)

# On raw events
events = humanizer.apply_to_events(my_events, bpm=120)

# On a track
humanizer.apply_to_track(drums_track)
```

---

## 13. GrooveTemplate

```python
from beatmaker.expression import GrooveTemplate
```

Per-step timing and velocity offsets that repeat cyclically across a track.
Each position maps to a 16th-note step in 4/4 time (16 positions per bar by
default).

### Fields

| Field             | Type          | Description                                                |
|-------------------|---------------|------------------------------------------------------------|
| `name`            | `str`         | Template name (e.g. `"mpc_swing"`)                         |
| `timing_offsets`  | `List[float]` | Per-step timing shift as a fraction of one step duration    |
| `velocity_scales` | `List[float]` | Per-step velocity multiplier                               |

### Properties

- **`length -> int`** -- Number of steps in the template (`len(timing_offsets)`).

### `apply_to_events(events, bpm, steps_per_beat=4) -> List[Tuple[float, int, float, float]]`

Applies groove to beat-based event tuples.  Each event is quantized to its
nearest step and the corresponding offset/scale is applied.

| Parameter        | Type                                    | Default | Description                     |
|------------------|-----------------------------------------|---------|---------------------------------|
| `events`         | `List[Tuple[float, int, float, float]]` | --      | `(beat, midi_note, vel, dur)`   |
| `bpm`            | `float`                                 | --      | Song tempo                      |
| `steps_per_beat` | `int`                                   | `4`     | Subdivision (4 = 16th notes)    |

### `apply_to_track(track, bpm, steps_per_beat=4) -> Track`

Applies groove to all placements in a track **in place**.

| Parameter        | Type    | Default | Description                  |
|------------------|---------|---------|------------------------------|
| `track`          | `Track` | --      | Track to modify              |
| `bpm`            | `float` | --      | Song tempo                   |
| `steps_per_beat` | `int`   | `4`     | Subdivision                  |

### Preset Factory Methods

All return a `GrooveTemplate` with 16 steps.

| Method                              | Description                                         |
|-------------------------------------|-----------------------------------------------------|
| `mpc_swing(amount=0.6)`            | MPC-style swing. `0.5` = straight, `0.67` = classic, `1.0` = full triplet. Delays every other 16th note. |
| `funk()`                            | Pushed offbeats and syncopated accents               |
| `shuffle(depth=0.67)`              | Shuffle / triplet feel with downbeat emphasis        |
| `lazy()`                            | Laid-back feel -- everything slightly behind the beat |
| `driving()`                         | Rushing feel -- everything slightly ahead of the beat |
| `hip_hop()`                         | Heavy downbeats, lazy backbeats                      |

```python
groove = GrooveTemplate.mpc_swing(amount=0.62)
events = groove.apply_to_events(hat_events, bpm=95)

# Or apply directly to a track
GrooveTemplate.funk().apply_to_track(drums_track, bpm=110)
```

---

## 14. VelocityCurve

```python
from beatmaker.expression import VelocityCurve
```

A collection of static methods that map input velocity (0..1) to output
velocity (0..1), reshaping the dynamic contour of a sequence.

### Static Curve Functions

All accept a `velocity: float` (0..1) and return a `float` (0..1).

| Method                                       | Description                                         |
|----------------------------------------------|-----------------------------------------------------|
| `linear(velocity)`                           | Identity mapping -- returns `velocity` unchanged     |
| `exponential(velocity, power=2.0)`           | Exponential curve. Quieter soft notes, louder loud notes. `power` controls steepness. |
| `logarithmic(velocity)`                      | Logarithmic curve. Boosts soft notes, compresses loud. |
| `compressed(velocity, amount=0.5)`           | Reduces dynamic range by blending with a constant. `amount=1.0` makes all velocities equal. |
| `s_curve(velocity)`                          | S-curve (cubic Hermite). Accentuates extremes, flattens the middle. |

### `apply_to_events(events, curve_fn) -> List[Tuple[float, int, float, float]]`

Applies any velocity curve function to all events in a list.  Velocity is
clamped to `[0.01, 1.0]`.

| Parameter  | Type                                      | Description                |
|------------|-------------------------------------------|----------------------------|
| `events`   | `List[Tuple[float, int, float, float]]`   | `(beat, note, vel, dur)`   |
| `curve_fn` | `Callable[[float], float]`                | Any velocity mapping       |

```python
shaped = VelocityCurve.apply_to_events(events, VelocityCurve.exponential)

# Using a custom curve
shaped = VelocityCurve.apply_to_events(
    events,
    lambda v: VelocityCurve.compressed(v, amount=0.3)
)
```
