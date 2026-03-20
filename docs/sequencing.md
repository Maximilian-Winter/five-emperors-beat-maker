# Sequencing, Patterns & Arpeggiator API Reference

Complete API reference for the `beatmaker.sequencer` and `beatmaker.arpeggiator` modules.

---

## Table of Contents

- [StepValue Enum](#stepvalue-enum)
- [Step](#step)
- [Pattern](#pattern)
- [StepSequencer](#stepsequencer)
- [ClassicPatterns](#classicpatterns)
- [EuclideanPattern](#euclideanpattern)
- [PolyrhythmGenerator](#polyrhythmgenerator)
- [ArpDirection & ArpMode Enums](#arpdirection--arpmode-enums)
- [Arpeggiator](#arpeggiator)
- [ArpeggiatorBuilder](#arpeggiatorbuilder)
- [ArpSynthesizer](#arpsynthesizer)
- [Convenience Functions](#convenience-functions)

---

## StepValue Enum

```python
from beatmaker.sequencer import StepValue
```

Represents the state of a single step in a step sequencer.

| Member   | Value | Description                          |
|----------|-------|--------------------------------------|
| `OFF`    | `0`   | Step is silent (rest)                |
| `ON`     | `1`   | Normal hit at default velocity       |
| `ACCENT` | `2`  | Accented hit (louder than normal)    |
| `GHOST`  | `3`   | Ghost note (soft, understated hit)   |

---

## Step

```python
from beatmaker.sequencer import Step
```

A single step in a sequence, represented as a dataclass.

### Fields

| Field          | Type    | Default | Description                                            |
|----------------|---------|---------|--------------------------------------------------------|
| `active`       | `bool`  | `False` | Whether this step triggers a sound                     |
| `velocity`     | `float` | `1.0`   | Hit velocity (amplitude multiplier)                    |
| `pitch_offset` | `int`   | `0`     | Pitch offset in semitones from the base sample pitch   |
| `probability`  | `float` | `1.0`   | Trigger probability from 0.0 (never) to 1.0 (always)  |
| `flam`         | `bool`  | `False` | When `True`, a quieter second hit plays 20 ms later    |
| `num_hits`     | `int`   | `1`     | Number of hits within the step (1 = normal, 2+ = roll) |

### Factory Methods

#### `Step.on(velocity: float = 1.0) -> Step`

Creates an active step at the given velocity.

```python
step = Step.on()          # velocity 1.0
step = Step.on(0.7)       # velocity 0.7
```

#### `Step.off() -> Step`

Creates an inactive (silent) step.

```python
step = Step.off()
```

#### `Step.accent() -> Step`

Creates an accented step with `velocity=1.2`.

```python
step = Step.accent()      # active=True, velocity=1.2
```

#### `Step.ghost() -> Step`

Creates a ghost-note step with `velocity=0.4`.

```python
step = Step.ghost()       # active=True, velocity=0.4
```

#### `Step.roll(divisions: int = 2, velocity: float = 0.8) -> Step`

Creates a roll step that subdivides into multiple rapid hits.

| Parameter   | Type    | Default | Description                          |
|-------------|---------|---------|--------------------------------------|
| `divisions` | `int`   | `2`     | Number of hits within the step time  |
| `velocity`  | `float` | `0.8`   | Base velocity (each successive hit decreases by 0.1) |

```python
step = Step.roll()        # 2-hit roll at velocity 0.8
step = Step.roll(4, 0.9)  # 4-hit fast roll at velocity 0.9
```

#### `Step.prob(probability: float, velocity: float = 1.0) -> Step`

Creates a probabilistic step that fires only some of the time.

| Parameter     | Type    | Default | Description                    |
|---------------|---------|---------|--------------------------------|
| `probability` | `float` | --      | Chance of triggering (0.0-1.0) |
| `velocity`    | `float` | `1.0`   | Hit velocity when triggered    |

```python
step = Step.prob(0.5)           # 50% chance, full velocity
step = Step.prob(0.75, 0.6)     # 75% chance, velocity 0.6
```

---

## Pattern

```python
from beatmaker.sequencer import Pattern
```

A rhythmic pattern for step sequencing, represented as a dataclass. Supports variable-length patterns with per-step control.

### Constructor

```python
Pattern(name: str = "Pattern",
        steps: List[Step] = <16 inactive steps>,
        length: int = 16,
        swing: float = 0.0)
```

| Parameter | Type         | Default            | Description                              |
|-----------|--------------|--------------------|------------------------------------------|
| `name`    | `str`        | `"Pattern"`        | Human-readable name                      |
| `steps`   | `List[Step]` | 16 inactive `Step` objects | The step data                  |
| `length`  | `int`        | `16`               | Pattern length in steps                  |
| `swing`   | `float`      | `0.0`              | Per-pattern swing amount (0.0-1.0)       |

On construction, the steps list is automatically padded or truncated to match `length`.

### Factory Methods

#### `Pattern.from_string(pattern_str: str, name: str = "Pattern") -> Pattern`

Creates a pattern from a compact string notation.

**Notation characters:**

| Character | Meaning                          |
|-----------|----------------------------------|
| `x`       | Normal hit (velocity 1.0)        |
| `X`       | Accented hit (velocity 1.2)      |
| `o`       | Ghost note (velocity 0.4)        |
| `r`       | Roll (2-hit subdivision)         |
| `.` or `-`| Rest (no hit)                    |

```python
# Four on the floor kick
kick = Pattern.from_string("x...x...x...x...", "kick")

# Trap hi-hats with rolls and accents
hats = Pattern.from_string("x.xxrxx.x.xxrxxx", "trap_hats")

# Ghost note groove
groove = Pattern.from_string("x..ox..ox..ox..o", "ghost_groove")
```

#### `Pattern.from_list(hits: List[bool], name: str = "Pattern") -> Pattern`

Creates a pattern from a list of booleans. `True` positions become `Step.on()`, `False` positions become `Step.off()`.

```python
pattern = Pattern.from_list(
    [True, False, False, True, False, False, True, False],
    "tresillo"
)
```

#### `Pattern.from_positions(positions: List[int], length: int = 16, name: str = "Pattern") -> Pattern`

Creates a pattern by specifying which step positions (0-indexed) should be active.

| Parameter   | Type        | Default     | Description                         |
|-------------|-------------|-------------|-------------------------------------|
| `positions` | `List[int]` | --          | 0-indexed step positions to activate|
| `length`    | `int`       | `16`        | Total pattern length                |
| `name`      | `str`       | `"Pattern"` | Pattern name                        |

```python
# Kick on 1 and 3 (steps 0 and 8 in a 16-step pattern)
kick = Pattern.from_positions([0, 8], 16, "kick")

# Snare on 2 and 4
snare = Pattern.from_positions([4, 12], 16, "snare")
```

### Transformation Methods

All transformations return a new `Pattern`, leaving the original unchanged.

#### `pattern.rotate(amount: int) -> Pattern`

Rotates the pattern by `amount` steps. Positive values rotate right (steps shift forward); the steps that fall off the end wrap to the beginning.

```python
kick = Pattern.from_string("x...x...x...x...")
shifted = kick.rotate(2)   # "..x...x...x...x."
```

The resulting pattern is named `"{original_name}_rot{amount}"`.

#### `pattern.reverse() -> Pattern`

Reverses the step order.

```python
p = Pattern.from_string("x..x....")
rev = p.reverse()  # "....x..x"
```

The resulting pattern is named `"{original_name}_rev"`.

#### `pattern.stretch(factor: int) -> Pattern`

Stretches the pattern by repeating each step `factor` times, increasing the total length by that factor.

```python
p = Pattern.from_string("x.x.")           # 4 steps
stretched = p.stretch(2)                    # "xx..xx.." -> 8 steps
```

The resulting pattern is named `"{original_name}_x{factor}"`.

#### `pattern.compress(factor: int) -> Pattern`

Compresses the pattern by keeping every nth step, reducing the total length.

```python
p = Pattern.from_string("x.x.x.x.")       # 8 steps
compressed = p.compress(2)                  # "xxxx" -> 4 steps
```

The resulting pattern is named `"{original_name}_/{factor}"`.

#### `pattern.combine(other: Pattern, mode: str = 'or') -> Pattern`

Combines two patterns using a logical operation. The resulting length is the maximum of both patterns; shorter patterns wrap cyclically.

| `mode` value | Description                                  |
|--------------|----------------------------------------------|
| `'or'`       | Hit if **either** pattern has a hit (default) |
| `'and'`      | Hit only where **both** patterns have a hit   |
| `'xor'`      | Hit where **exactly one** pattern has a hit   |

Velocity of each combined step is the maximum of the two source velocities.

```python
a = Pattern.from_string("x...x...")
b = Pattern.from_string("..x...x.")
merged = a.combine(b, mode='or')   # "x.x.x.x."
```

The resulting pattern is named `"{name_a}+{name_b}"`.

### String Representation

`str(pattern)` returns a compact string using the same notation as `from_string`. Active steps map to `X` (velocity > 1.1), `o` (velocity < 0.5), `r` (num_hits > 1), or `x` (normal). Inactive steps render as `.`.

---

## StepSequencer

```python
from beatmaker.sequencer import StepSequencer
```

A TR-style step sequencer that manages multiple patterns for different instruments and renders them to a `Track`.

### Constructor

```python
StepSequencer(bpm: float = 120.0,
              steps_per_beat: int = 4,
              swing: float = 0.0,
              patterns: Dict[str, Pattern] = {},
              samples: Dict[str, Sample] = {})
```

| Parameter        | Type                   | Default | Description                                              |
|------------------|------------------------|---------|----------------------------------------------------------|
| `bpm`            | `float`                | `120.0` | Tempo in beats per minute                                |
| `steps_per_beat` | `int`                  | `4`     | Step resolution (4 = 16th notes, 2 = 8th notes)         |
| `swing`          | `float`                | `0.0`   | Global swing amount (0.0-1.0), applied to off-beat steps|
| `patterns`       | `Dict[str, Pattern]`   | `{}`    | Instrument-name-to-pattern mapping                       |
| `samples`        | `Dict[str, Sample]`    | `{}`    | Instrument-name-to-sample mapping                        |

### Methods

#### `add_pattern(name: str, pattern: Pattern, sample: Optional[Sample] = None) -> StepSequencer`

Adds a pattern for the named instrument. Optionally associates a sample at the same time. Returns `self` for chaining.

```python
seq = StepSequencer(bpm=128)
seq.add_pattern("kick", Pattern.from_string("x...x...x...x..."), kick_sample) \
   .add_pattern("snare", Pattern.from_string("....x.......x..."), snare_sample)
```

#### `set_sample(name: str, sample: Sample) -> StepSequencer`

Sets or replaces the sample for a named instrument. Returns `self` for chaining.

#### `load_kit(kit: Dict[str, Pattern], samples: Optional[Dict[str, Sample]] = None) -> StepSequencer`

Loads an entire kit (dictionary of name-to-pattern mappings). If `samples` is provided, matching names are associated. Returns `self` for chaining.

```python
seq.load_kit(ClassicPatterns.house_kit(), {
    'kick': kick_sample,
    'snare': snare_sample,
    'hihat': hat_sample,
})
```

#### `load_samples_from(library, mapping: Dict[str, str]) -> StepSequencer`

Loads samples from a `SampleLibrary` instance using a name-to-library-key mapping. Returns `self` for chaining.

| Parameter | Type              | Description                                    |
|-----------|-------------------|------------------------------------------------|
| `library` | `SampleLibrary`   | A sample library instance                      |
| `mapping` | `Dict[str, str]`  | Maps instrument names to library keys          |

```python
seq.load_samples_from(lib, {
    "kick":  "drums/kick",
    "snare": "drums/snare",
    "hat":   "drums/hat_closed",
})
```

#### `render_pattern(name: str, bars: int = 1, sample: Optional[Sample] = None) -> List[tuple]`

Renders a single named pattern to a list of `(time, velocity, sample)` tuples. If no sample is found for the instrument, returns an empty list. Probability-gated steps are evaluated randomly at render time. Rolls subdivide the step time into `num_hits` hits with decreasing velocity. Flam steps add a second hit 20 ms later at 60% velocity.

#### `render_to_track(bars: int = 4, name: str = "Sequencer", track_type: TrackType = TrackType.DRUMS) -> Track`

Renders all patterns into a single `Track` object.

| Parameter    | Type        | Default            | Description                  |
|--------------|-------------|--------------------|------------------------------|
| `bars`       | `int`       | `4`                | Number of bars to render     |
| `name`       | `str`       | `"Sequencer"`      | Track name                   |
| `track_type` | `TrackType` | `TrackType.DRUMS`  | Track type tag               |

```python
seq = StepSequencer(bpm=120)
seq.load_kit(ClassicPatterns.house_kit(), samples)
track = seq.render_to_track(bars=8, name="Drums")
```

#### `apply_groove(groove_template) -> StepSequencer`

Applies a `GrooveTemplate` (from the expression module) to scale step velocities according to the template's `velocity_scales`. Returns `self` for chaining.

#### `create_variation(variation_type: str = 'fill') -> StepSequencer`

Creates a new `StepSequencer` with modified patterns. Returns a **new** sequencer (does not mutate the original).

| `variation_type` | Description                                                       |
|-------------------|------------------------------------------------------------------|
| `'fill'`          | Adds extra snare hits for fill patterns                          |
| `'sparse'`        | Randomly removes ~30% of hits                                   |
| `'double'`        | Adds ghost notes on empty off-beat steps (~50% chance)           |

---

## ClassicPatterns

```python
from beatmaker.sequencer import ClassicPatterns
```

A collection of pre-built classic drum machine patterns. All patterns are 16 steps.

### Kick Patterns

| Attribute         | Notation                 | Style              |
|-------------------|--------------------------|---------------------|
| `FOUR_ON_FLOOR`   | `x...x...x...x...`      | House / Disco       |
| `KICK_2_AND_4`    | `....x.......x...`      | Pop / Rock          |
| `BOOM_BAP_KICK`   | `x.....x.x.......`      | Hip-hop (boom bap)  |
| `TRAP_KICK`       | `x.......x.x.....`      | Trap                |
| `DNB_KICK`        | `x.....x.....x...`      | Drum & Bass         |
| `BREAKBEAT_KICK`  | `x.....x...x.....`      | Breakbeat           |

### Snare Patterns

| Attribute           | Notation                 | Style              |
|---------------------|--------------------------|---------------------|
| `BACKBEAT`          | `....x.......x...`      | Standard backbeat   |
| `TRAP_SNARE`        | `....X.......X...`      | Trap (accented)     |
| `BREAKBEAT_SNARE`   | `....x.....x.x...`      | Breakbeat           |
| `DNB_SNARE`         | `....x.......x...`      | Drum & Bass         |

### Hi-Hat Patterns

| Attribute         | Notation                   | Style              |
|-------------------|----------------------------|---------------------|
| `EIGHTH_HATS`     | `x.x.x.x.x.x.x.x.`       | Straight 8ths      |
| `SIXTEENTH_HATS`  | `xxxxxxxxxxxxxxxx`         | Straight 16ths     |
| `OFFBEAT_HATS`    | `.x.x.x.x.x.x.x.x`       | Offbeat (house)    |
| `TRAP_HATS`       | `x.xxrxx.x.xxrxxx`        | Trap (with rolls)  |

### Kit Methods

These class methods return `Dict[str, Pattern]` suitable for `StepSequencer.load_kit()`.

| Method           | Kick             | Snare              | Hi-Hat           |
|------------------|------------------|---------------------|------------------|
| `house_kit()`    | `FOUR_ON_FLOOR`  | `BACKBEAT`          | `OFFBEAT_HATS`   |
| `trap_kit()`     | `TRAP_KICK`      | `TRAP_SNARE`        | `TRAP_HATS`      |
| `dnb_kit()`      | `DNB_KICK`       | `DNB_SNARE`         | `EIGHTH_HATS`    |
| `boom_bap_kit()` | `BOOM_BAP_KICK`  | `BACKBEAT`          | `EIGHTH_HATS`    |

```python
seq = StepSequencer(bpm=174)
seq.load_kit(ClassicPatterns.dnb_kit())
```

---

## EuclideanPattern

```python
from beatmaker.sequencer import EuclideanPattern
```

Generates Euclidean rhythms using Bjorklund's algorithm. Euclidean rhythms distribute `n` hits as evenly as possible across `k` steps, producing patterns found in music traditions worldwide.

### `EuclideanPattern.generate(hits: int, steps: int, rotation: int = 0) -> Pattern`

| Parameter  | Type  | Default | Description                           |
|------------|-------|---------|---------------------------------------|
| `hits`     | `int` | --      | Number of active hits to distribute   |
| `steps`    | `int` | --      | Total number of steps in the pattern  |
| `rotation` | `int` | `0`     | Rotate the result by this many steps  |

If `hits > steps`, hits is clamped to `steps`. If `hits <= 0`, an all-rest pattern is returned. The resulting pattern is named `"E({hits},{steps})"`.

**Musical examples:**

| Call                 | Pattern        | Tradition                        |
|----------------------|----------------|----------------------------------|
| `generate(3, 8)`    | `x..x..x.`     | Cuban tresillo                  |
| `generate(5, 8)`    | `x.xx.xx.`     | Cuban cinquillo                 |
| `generate(7, 12)`   | `x.xx.x.xx.x.` | West African bell (bembe)       |
| `generate(4, 9)`    | 9-step aksak   | Turkish aksak                   |
| `generate(5, 12)`   | 12-step rumba  | Afro-Cuban rumba clave          |
| `generate(5, 16)`   | 16-step soukous| Central African soukous         |

```python
tresillo = EuclideanPattern.generate(3, 8)
rotated_tresillo = EuclideanPattern.generate(3, 8, rotation=1)
```

### `EuclideanPattern.common_patterns() -> Dict[str, Pattern]`

Returns a dictionary of well-known Euclidean rhythms:

| Key          | Euclidean | Origin           |
|--------------|-----------|------------------|
| `'tresillo'` | E(3,8)    | Cuban            |
| `'cinquillo'` | E(5,8)   | Cuban            |
| `'bembé'`    | E(7,12)   | West African     |
| `'aksak'`    | E(4,9)    | Turkish          |
| `'rumba'`    | E(5,12)   | Afro-Cuban       |
| `'soukous'`  | E(5,16)   | Central African  |

---

## PolyrhythmGenerator

```python
from beatmaker.sequencer import PolyrhythmGenerator
```

Generates pairs of patterns that form a polyrhythm by evenly distributing two different beat counts across the same step grid.

### `PolyrhythmGenerator.create(rhythm_a: int, rhythm_b: int, steps: int = 16) -> tuple`

| Parameter  | Type  | Default | Description                             |
|------------|-------|---------|-----------------------------------------|
| `rhythm_a` | `int` | --      | Number of beats for the first pattern   |
| `rhythm_b` | `int` | --      | Number of beats for the second pattern  |
| `steps`    | `int` | `16`    | Total number of steps                   |

Returns a tuple of two `Pattern` objects named `"poly_{rhythm_a}"` and `"poly_{rhythm_b}"`.

```python
# 3-against-4 polyrhythm
pattern_3, pattern_4 = PolyrhythmGenerator.create(3, 4, 12)
# pattern_3 has 3 evenly spaced hits across 12 steps
# pattern_4 has 4 evenly spaced hits across 12 steps

# Combine them into a single composite pattern
combined = pattern_3.combine(pattern_4, mode='or')
```

---

## ArpDirection & ArpMode Enums

```python
from beatmaker.arpeggiator import ArpDirection, ArpMode
```

### ArpDirection

Controls the order in which notes are played.

| Member     | Description                                                        |
|------------|--------------------------------------------------------------------|
| `UP`       | Notes sorted ascending (lowest to highest)                         |
| `DOWN`     | Notes sorted descending (highest to lowest)                        |
| `UP_DOWN`  | Ascending then descending, excluding repeated top and bottom notes |
| `DOWN_UP`  | Descending then ascending, excluding repeated endpoints            |
| `RANDOM`   | Notes in random order (reshuffled each call)                       |
| `ORDER`    | Notes played in input order (as played / as given)                 |

### ArpMode

Controls how notes are expanded before direction is applied.

| Member          | Description                                                |
|-----------------|------------------------------------------------------------|
| `NORMAL`        | Use notes as given                                         |
| `OCTAVE`        | Duplicate all notes one octave (+12 semitones) higher      |
| `DOUBLE_OCTAVE` | Duplicate notes at +12 and +24 semitones                   |
| `POWER`         | For each note, add a fifth (+7) and octave (+12) above it  |

---

## Arpeggiator

```python
from beatmaker.arpeggiator import Arpeggiator
```

Takes a chord, scale, or note list and creates rhythmic melodic patterns.

### Constructor

```python
Arpeggiator(bpm: float = 120.0,
            direction: ArpDirection = ArpDirection.UP,
            mode: ArpMode = ArpMode.NORMAL,
            octaves: int = 1,
            rate: float = 0.25,
            gate: float = 0.8,
            swing: float = 0.0,
            velocity_pattern: Optional[List[float]] = None)
```

| Parameter          | Type                   | Default              | Description                                        |
|--------------------|------------------------|----------------------|----------------------------------------------------|
| `bpm`              | `float`                | `120.0`              | Tempo in beats per minute                          |
| `direction`        | `ArpDirection`         | `ArpDirection.UP`    | Note ordering direction                            |
| `mode`             | `ArpMode`              | `ArpMode.NORMAL`     | Note expansion mode                                |
| `octaves`          | `int`                  | `1`                  | Number of octaves to span (1 = no extra octaves)   |
| `rate`             | `float`                | `0.25`               | Note duration in beats (0.25 = 16th, 0.5 = 8th, 1.0 = quarter) |
| `gate`             | `float`                | `0.8`                | Note length as fraction of rate (0.0-1.0)          |
| `swing`            | `float`                | `0.0`                | Swing amount applied to off-beat notes (0.0-1.0)   |
| `velocity_pattern` | `Optional[List[float]]`| `None`               | Cyclic velocity pattern (e.g., `[1.0, 0.6, 0.7, 0.6]`) |

### Methods

#### `generate_pattern(notes: List[int], beats: int = 4) -> List[tuple]`

The core generation method. Takes raw MIDI note numbers and returns a list of events.

| Parameter | Type         | Default | Description                       |
|-----------|--------------|---------|-----------------------------------|
| `notes`   | `List[int]`  | --      | MIDI note numbers (e.g., `[60, 64, 67]`) |
| `beats`   | `int`        | `4`     | Pattern length in beats           |

**Returns:** `List[tuple]` where each tuple is `(time: float, midi_note: int, velocity: float, duration: float)`.

Processing order: mode expansion, octave extension, direction sorting, then event generation with swing and velocity pattern applied.

```python
arp = Arpeggiator(bpm=120, direction=ArpDirection.UP, rate=0.25)
events = arp.generate_pattern([60, 64, 67], beats=4)
# Returns 16 events (4 beats / 0.25 beats per note), cycling through C4-E4-G4
```

#### `generate_from_chord(root: Union[str, int], chord: ChordShape, beats: int = 4) -> List[tuple]`

Generates an arpeggio from a named root note and chord shape.

| Parameter | Type                | Default | Description                           |
|-----------|---------------------|---------|---------------------------------------|
| `root`    | `Union[str, int]`   | --      | Root note as name (`"C4"`) or MIDI number |
| `chord`   | `ChordShape`        | --      | Chord shape (e.g., `ChordShape.MAJOR`) |
| `beats`   | `int`               | `4`     | Pattern length in beats               |

```python
events = arp.generate_from_chord("C4", ChordShape.MAJOR, beats=4)
```

#### `generate_from_scale(root: Union[str, int], scale: Scale, beats: int = 4) -> List[tuple]`

Generates an arpeggio from a root note and scale.

| Parameter | Type                | Default | Description                           |
|-----------|---------------------|---------|---------------------------------------|
| `root`    | `Union[str, int]`   | --      | Root note as name (`"C4"`) or MIDI number |
| `scale`   | `Scale`             | --      | Scale definition                      |
| `beats`   | `int`               | `4`     | Pattern length in beats               |

```python
events = arp.generate_from_scale("A3", Scale.MINOR, beats=8)
```

#### `generate_from_progression(progression: List[tuple], beats_per_chord: int = 4) -> List[tuple]`

Generates a continuous arpeggio across a chord progression. Each chord gets `beats_per_chord` beats of arpeggiation, and events are time-offset so they play sequentially.

| Parameter         | Type               | Default | Description                                 |
|-------------------|--------------------|---------|---------------------------------------------|
| `progression`     | `List[tuple]`      | --      | List of `(root, ChordShape)` tuples         |
| `beats_per_chord` | `int`              | `4`     | Number of beats spent on each chord          |

```python
arp = Arpeggiator(bpm=120, direction=ArpDirection.UP_DOWN, rate=0.25)
progression = [
    ('C3', ChordShape.MAJOR),
    ('G3', ChordShape.MAJOR),
    ('A3', ChordShape.MINOR),
    ('F3', ChordShape.MAJOR),
]
events = arp.generate_from_progression(progression, beats_per_chord=4)
# 16 beats total of continuous arpeggiation
```

---

## ArpeggiatorBuilder

```python
from beatmaker.arpeggiator import ArpeggiatorBuilder, create_arpeggiator
```

A fluent builder for constructing an `Arpeggiator` with readable, chainable syntax. Every method (except `build`) returns `self`.

### Creating a Builder

```python
builder = ArpeggiatorBuilder()
# or use the convenience function:
builder = create_arpeggiator()
```

### Tempo

| Method             | Description                      |
|--------------------|----------------------------------|
| `tempo(bpm: float)` | Set tempo in BPM               |

### Direction Methods

| Method         | Sets direction to       |
|----------------|-------------------------|
| `up()`         | `ArpDirection.UP`       |
| `down()`       | `ArpDirection.DOWN`     |
| `up_down()`    | `ArpDirection.UP_DOWN`  |
| `down_up()`    | `ArpDirection.DOWN_UP`  |
| `random()`     | `ArpDirection.RANDOM`   |
| `as_played()`  | `ArpDirection.ORDER`    |

### Rate Methods

| Method                  | Sets rate to          | Equivalent to          |
|-------------------------|-----------------------|------------------------|
| `rate(beats: float)`   | Custom value in beats | --                     |
| `sixteenth()`           | `0.25`                | `rate(0.25)`          |
| `eighth()`              | `0.5`                 | `rate(0.5)`           |
| `quarter()`             | `1.0`                 | `rate(1.0)`           |
| `triplet()`             | `1/3` (~0.333)        | `rate(1/3)`           |

### Gate Methods

| Method                 | Sets gate to | Description                        |
|------------------------|--------------|------------------------------------|
| `gate(value: float)`  | Custom value | Gate length 0.0-1.0               |
| `staccato()`           | `0.3`        | Short, detached notes              |
| `legato()`             | `1.0`        | Notes fill full step duration      |

### Mode Methods

| Method               | Sets mode to             | Description                          |
|----------------------|--------------------------|--------------------------------------|
| `with_octave()`      | `ArpMode.OCTAVE`         | Adds notes +12 semitones             |
| `with_double_octave()` | `ArpMode.DOUBLE_OCTAVE`| Adds notes at +12 and +24 semitones  |
| `power_chords()`     | `ArpMode.POWER`          | Adds fifth (+7) and octave (+12) per note |

### Other Methods

| Method                                  | Description                                            |
|-----------------------------------------|--------------------------------------------------------|
| `octaves(num: int)`                     | Set number of octaves to span                          |
| `swing(amount: float)`                  | Set swing amount (0.0-1.0)                             |
| `velocity_pattern(pattern: List[float])`| Set a cyclic velocity pattern                          |
| `accent_downbeat()`                     | Set velocity pattern to `[1.0, 0.6, 0.7, 0.6]`        |

### Building

| Method    | Returns       | Description                    |
|-----------|---------------|--------------------------------|
| `build()` | `Arpeggiator` | Returns the configured instance|

### Full Example

```python
arp = (create_arpeggiator()
       .tempo(140)
       .up_down()
       .sixteenth()
       .staccato()
       .octaves(2)
       .swing(0.3)
       .accent_downbeat()
       .build())

events = arp.generate_from_chord("C3", ChordShape.MINOR7, beats=8)
```

---

## ArpSynthesizer

```python
from beatmaker.arpeggiator import ArpSynthesizer
```

A synthesizer that converts arpeggiator events (MIDI note tuples) into rendered audio.

### Constructor

```python
ArpSynthesizer(waveform: str = 'saw',
               envelope: Optional[ADSREnvelope] = None,
               sample_rate: int = 44100)
```

| Parameter     | Type                      | Default                              | Description                                   |
|---------------|---------------------------|--------------------------------------|-----------------------------------------------|
| `waveform`    | `str`                     | `'saw'`                              | Oscillator waveform: `'sine'`, `'saw'`, `'square'`, `'triangle'` |
| `envelope`    | `Optional[ADSREnvelope]`  | `ADSREnvelope(0.01, 0.1, 0.7, 0.1)` | Amplitude envelope                            |
| `sample_rate` | `int`                     | `44100`                              | Audio sample rate in Hz                       |

### Methods

#### `render_note(midi_note: int, duration: float, velocity: float = 1.0) -> AudioData`

Renders a single synthesized note.

| Parameter   | Type    | Default | Description                        |
|-------------|---------|---------|------------------------------------|
| `midi_note` | `int`   | --      | MIDI note number (e.g., 60 = C4)  |
| `duration`  | `float` | --      | Note duration in seconds           |
| `velocity`  | `float` | `1.0`   | Amplitude multiplier               |

The waveform is generated at the MIDI note's frequency, shaped by the ADSR envelope, and scaled by velocity.

#### `render_events(events: List[tuple]) -> AudioData`

Renders a full list of arpeggiator events into a single `AudioData` buffer. Events are mixed (summed) into the output, allowing overlapping notes.

| Parameter | Type           | Description                                                |
|-----------|----------------|------------------------------------------------------------|
| `events`  | `List[tuple]`  | List of `(time, midi_note, velocity, duration)` tuples     |

Returns an `AudioData` object whose length covers all events plus one second of padding.

```python
arp = Arpeggiator(bpm=120, direction=ArpDirection.UP_DOWN, rate=0.25)
events = arp.generate_from_chord("C3", ChordShape.MAJOR, beats=4)

synth = ArpSynthesizer(waveform='saw')
audio = synth.render_events(events)
```

---

## Convenience Functions

### `create_arpeggiator() -> ArpeggiatorBuilder`

Returns a new `ArpeggiatorBuilder` instance. Equivalent to `ArpeggiatorBuilder()`.

```python
from beatmaker.arpeggiator import create_arpeggiator

arp = create_arpeggiator().tempo(128).up().eighth().build()
```

### `arp_chord(root, chord, beats=4, direction=ArpDirection.UP, rate=0.25, bpm=120) -> List[tuple]`

Quick one-call arpeggio generation from a chord, without manually constructing an `Arpeggiator`.

| Parameter   | Type            | Default              | Description                          |
|-------------|-----------------|----------------------|--------------------------------------|
| `root`      | `str`           | --                   | Root note name (e.g., `"C3"`)       |
| `chord`     | `ChordShape`    | --                   | Chord shape                          |
| `beats`     | `int`           | `4`                  | Pattern length in beats              |
| `direction` | `ArpDirection`  | `ArpDirection.UP`    | Note direction                       |
| `rate`      | `float`         | `0.25`               | Note rate in beats                   |
| `bpm`       | `float`         | `120`                | Tempo                                |

```python
from beatmaker.arpeggiator import arp_chord, ChordShape

events = arp_chord("A3", ChordShape.MINOR, beats=4, rate=0.5)
```

### `arp_scale(root, scale, beats=4, direction=ArpDirection.UP, rate=0.25, bpm=120) -> List[tuple]`

Quick one-call arpeggio generation from a scale.

| Parameter   | Type            | Default              | Description                          |
|-------------|-----------------|----------------------|--------------------------------------|
| `root`      | `str`           | --                   | Root note name (e.g., `"C4"`)       |
| `scale`     | `Scale`         | --                   | Scale definition                     |
| `beats`     | `int`           | `4`                  | Pattern length in beats              |
| `direction` | `ArpDirection`  | `ArpDirection.UP`    | Note direction                       |
| `rate`      | `float`         | `0.25`               | Note rate in beats                   |
| `bpm`       | `float`         | `120`                | Tempo                                |

```python
from beatmaker.arpeggiator import arp_scale, Scale

events = arp_scale("C4", Scale.PENTATONIC_MINOR, beats=8, direction=ArpDirection.UP_DOWN)
```
