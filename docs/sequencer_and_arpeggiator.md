# Sequencer & Arpeggiator API Reference

Complete reference for the `beatmaker.sequencer` and `beatmaker.arpeggiator` modules.

---

## Table of Contents

### Sequencer Module (`beatmaker.sequencer`)

- [StepValue](#stepvalue)
- [Step](#step)
- [Pattern](#pattern)
- [ClassicPatterns](#classicpatterns)
- [StepSequencer](#stepsequencer)
- [EuclideanPattern](#euclideanpattern)
- [PolyrhythmGenerator](#polyrhythmgenerator)

### Arpeggiator Module (`beatmaker.arpeggiator`)

- [ArpDirection](#arpdirection)
- [ArpMode](#arpmode)
- [ChordShape](#chordshape)
- [Scale](#scale)
- [note_name_to_midi](#note_name_to_midi)
- [Arpeggiator](#arpeggiator)
- [ArpeggiatorBuilder](#arpeggiatorbuilder)
- [create_arpeggiator](#create_arpeggiator)
- [ArpSynthesizer](#arpsynthesizer)
- [arp_chord](#arp_chord)
- [arp_scale](#arp_scale)

---

# Sequencer Module

Source: `beatmaker/sequencer.py`

## StepValue

```python
class StepValue(Enum)
```

Enum representing the possible states of a step in the sequencer grid.

### Values

| Member   | Value | Description                  |
|----------|-------|------------------------------|
| `OFF`    | `0`   | Step is silent               |
| `ON`     | `1`   | Normal hit                   |
| `ACCENT` | `2`   | Accented (louder) hit        |
| `GHOST`  | `3`   | Ghost note (soft/quiet hit)  |

### Example

```python
from beatmaker.sequencer import StepValue

state = StepValue.ACCENT
if state == StepValue.ON:
    print("Normal hit")
```

---

## Step

```python
@dataclass
class Step
```

Represents a single step in a sequence. Each step carries all the information needed to determine whether and how it triggers.

### Constructor

```python
Step(
    active: bool = False,
    velocity: float = 1.0,
    pitch_offset: int = 0,
    probability: float = 1.0,
    flam: bool = False,
    num_hits: int = 1,
)
```

| Parameter      | Type    | Default | Description                                            |
|----------------|---------|---------|--------------------------------------------------------|
| `active`       | `bool`  | `False` | Whether this step triggers a hit                       |
| `velocity`     | `float` | `1.0`   | Hit loudness (typical range 0.0 -- 1.2+)              |
| `pitch_offset` | `int`   | `0`     | Pitch shift in semitones from the sample's base pitch  |
| `probability`  | `float` | `1.0`   | Probability of triggering (0.0 to 1.0)                |
| `flam`         | `bool`  | `False` | If `True`, a quieter double-hit is added 20 ms later  |
| `num_hits`     | `int`   | `1`     | Number of hits (1 = normal, 2 = roll, 4 = fast roll)  |

### Class Methods

#### `.on(velocity: float = 1.0) -> Step`

Create an active step with the given velocity.

```python
step = Step.on(0.9)
```

#### `.off() -> Step`

Create an inactive (silent) step.

```python
step = Step.off()
```

#### `.accent() -> Step`

Create an accented step with velocity `1.2`.

```python
step = Step.accent()
```

#### `.ghost() -> Step`

Create a ghost-note step with velocity `0.4`.

```python
step = Step.ghost()
```

#### `.roll(divisions: int = 2, velocity: float = 0.8) -> Step`

Create a roll step that triggers multiple sub-hits within the step duration.

| Parameter   | Type    | Default | Description                        |
|-------------|---------|---------|-------------------------------------|
| `divisions` | `int`   | `2`     | Number of sub-hits in the roll     |
| `velocity`  | `float` | `0.8`   | Base velocity for the roll hits    |

```python
step = Step.roll(4, 0.7)  # fast roll, slightly quieter
```

#### `.prob(probability: float, velocity: float = 1.0) -> Step`

Create a probabilistic step that only triggers a fraction of the time.

| Parameter     | Type    | Default | Description                      |
|---------------|---------|---------|----------------------------------|
| `probability` | `float` | --      | Chance of triggering (0.0--1.0)  |
| `velocity`    | `float` | `1.0`   | Velocity when it does trigger    |

```python
step = Step.prob(0.5)  # 50% chance of firing
```

---

## Pattern

```python
@dataclass
class Pattern
```

A rhythmic pattern for step sequencing. Supports variable-length patterns with per-step control over velocity, probability, rolls, and flams.

### Constructor

```python
Pattern(
    name: str = "Pattern",
    steps: List[Step] = <16 inactive Steps>,
    length: int = 16,
    swing: float = 0.0,
)
```

| Parameter | Type         | Default             | Description                             |
|-----------|-------------|---------------------|-----------------------------------------|
| `name`    | `str`       | `"Pattern"`         | Human-readable pattern name             |
| `steps`   | `List[Step]`| 16 inactive `Step`s | The step data for the pattern           |
| `length`  | `int`       | `16`                | Pattern length in steps                 |
| `swing`   | `float`     | `0.0`               | Swing amount (0.0 = straight, 1.0 = max)|

On construction, the `steps` list is automatically padded or truncated to match `length`.

### Class Methods

#### `.from_string(pattern_str: str, name: str = "Pattern") -> Pattern`

Create a pattern from a compact string notation.

| Character | Meaning       |
|-----------|---------------|
| `x`       | Normal hit    |
| `X`       | Accented hit  |
| `.` or `-`| Rest (silent) |
| `o`       | Ghost note    |
| `r`       | Roll (2 hits) |

```python
kick = Pattern.from_string("x...x...x...x...", "four_on_floor")
```

#### `.from_list(hits: List[bool], name: str = "Pattern") -> Pattern`

Create a pattern from a boolean list where `True` = hit, `False` = rest.

```python
pat = Pattern.from_list([True, False, False, True, False, False, True, False])
```

#### `.from_positions(positions: List[int], length: int = 16, name: str = "Pattern") -> Pattern`

Create a pattern by specifying 0-indexed hit positions.

| Parameter   | Type        | Default     | Description                  |
|-------------|-------------|-------------|------------------------------|
| `positions` | `List[int]` | --          | Step indices to activate     |
| `length`    | `int`       | `16`        | Total number of steps        |
| `name`      | `str`       | `"Pattern"` | Pattern name                 |

```python
snare = Pattern.from_positions([4, 12], 16, "backbeat")
```

### Instance Methods

#### `.rotate(amount: int) -> Pattern`

Rotate (shift) the pattern rightward by `amount` steps. Returns a new `Pattern`.

```python
rotated = pattern.rotate(2)  # shift right by 2 steps
```

#### `.reverse() -> Pattern`

Reverse the order of steps. Returns a new `Pattern`.

```python
rev = pattern.reverse()
```

#### `.stretch(factor: int) -> Pattern`

Stretch the pattern by repeating each step `factor` times. The new length is `length * factor`. Returns a new `Pattern`.

```python
doubled = pattern.stretch(2)  # 16-step -> 32-step
```

#### `.compress(factor: int) -> Pattern`

Compress the pattern by keeping every *n*-th step. Returns a new `Pattern`.

```python
halved = pattern.compress(2)  # 16-step -> 8-step
```

#### `.combine(other: Pattern, mode: str = 'or') -> Pattern`

Combine two patterns using a logical operation. The resulting length is the maximum of the two pattern lengths; shorter patterns wrap around.

| Parameter | Type      | Default | Description                             |
|-----------|-----------|---------|-----------------------------------------|
| `other`   | `Pattern` | --      | The second pattern                      |
| `mode`    | `str`     | `'or'`  | `'or'` (union), `'and'` (intersection), `'xor'` (exclusive) |

Returns a new `Pattern`. The velocity of each combined step is the maximum of the two source velocities.

```python
combined = kick.combine(snare, mode='or')
```

#### `__str__() -> str`

Returns a compact string representation using the same character notation as `from_string`.

```python
print(pattern)  # e.g. "x...x...x...x..."
```

---

## ClassicPatterns

```python
class ClassicPatterns
```

A library of pre-built classic drum machine patterns. All attributes are `Pattern` instances.

### Kick Patterns (class attributes)

| Attribute        | String Representation   | Description              |
|------------------|-------------------------|--------------------------|
| `FOUR_ON_FLOOR`  | `x...x...x...x...`     | Standard house kick      |
| `KICK_2_AND_4`   | `....x.......x...`     | Kick on beats 2 and 4   |
| `BOOM_BAP_KICK`  | `x.....x.x.......`     | Classic boom-bap kick    |
| `TRAP_KICK`      | `x.......x.x.....`     | Trap-style kick          |
| `DNB_KICK`       | `x.....x.....x...`     | Drum & bass kick         |
| `BREAKBEAT_KICK` | `x.....x...x.....`     | Breakbeat kick           |

### Snare Patterns (class attributes)

| Attribute          | String Representation   | Description              |
|--------------------|-------------------------|--------------------------|
| `BACKBEAT`         | `....x.......x...`     | Standard backbeat        |
| `TRAP_SNARE`       | `....X.......X...`     | Accented trap snare      |
| `BREAKBEAT_SNARE`  | `....x.....x.x...`     | Breakbeat snare          |
| `DNB_SNARE`        | `....x.......x...`     | Drum & bass snare        |

### Hi-Hat Patterns (class attributes)

| Attribute        | String Representation    | Description              |
|------------------|--------------------------|--------------------------|
| `EIGHTH_HATS`    | `x.x.x.x.x.x.x.x.`    | Eighth-note hi-hats      |
| `SIXTEENTH_HATS` | `xxxxxxxxxxxxxxxx`       | Sixteenth-note hi-hats   |
| `OFFBEAT_HATS`   | `.x.x.x.x.x.x.x.x`    | Offbeat hi-hats          |
| `TRAP_HATS`      | `x.xxrxx.x.xxrxxx`     | Trap hi-hats with rolls  |

### Kit Methods

#### `.house_kit() -> Dict[str, Pattern]`

Returns a dictionary with keys `'kick'`, `'snare'`, `'hihat'` using `FOUR_ON_FLOOR`, `BACKBEAT`, `OFFBEAT_HATS`.

#### `.trap_kit() -> Dict[str, Pattern]`

Returns a dictionary with keys `'kick'`, `'snare'`, `'hihat'` using `TRAP_KICK`, `TRAP_SNARE`, `TRAP_HATS`.

#### `.dnb_kit() -> Dict[str, Pattern]`

Returns a dictionary with keys `'kick'`, `'snare'`, `'hihat'` using `DNB_KICK`, `DNB_SNARE`, `EIGHTH_HATS`.

#### `.boom_bap_kit() -> Dict[str, Pattern]`

Returns a dictionary with keys `'kick'`, `'snare'`, `'hihat'` using `BOOM_BAP_KICK`, `BACKBEAT`, `EIGHTH_HATS`.

### Example

```python
from beatmaker.sequencer import ClassicPatterns, StepSequencer

seq = StepSequencer(bpm=140)
seq.load_kit(ClassicPatterns.trap_kit())
```

---

## StepSequencer

```python
@dataclass
class StepSequencer
```

A TR-style step sequencer. Manages multiple named patterns for different instruments and renders them to audio `Track` objects.

### Constructor

```python
StepSequencer(
    bpm: float = 120.0,
    steps_per_beat: int = 4,
    swing: float = 0.0,
    patterns: Dict[str, Pattern] = {},
    samples: Dict[str, Sample] = {},
)
```

| Parameter        | Type                  | Default | Description                                              |
|------------------|-----------------------|---------|----------------------------------------------------------|
| `bpm`            | `float`               | `120.0` | Tempo in beats per minute                                |
| `steps_per_beat` | `int`                 | `4`     | Steps per beat (4 = 16th notes, 2 = 8th notes)          |
| `swing`          | `float`               | `0.0`   | Global swing amount (0.0 = straight, 1.0 = max)         |
| `patterns`       | `Dict[str, Pattern]`  | `{}`    | Named patterns keyed by instrument name                  |
| `samples`        | `Dict[str, Sample]`   | `{}`    | Audio samples keyed by instrument name                   |

### Methods

#### `.add_pattern(name: str, pattern: Pattern, sample: Optional[Sample] = None) -> StepSequencer`

Add a pattern for an instrument. Optionally attach a sample at the same time. Returns `self` for chaining.

| Parameter | Type              | Default | Description                      |
|-----------|-------------------|---------|----------------------------------|
| `name`    | `str`             | --      | Instrument/pattern name          |
| `pattern` | `Pattern`         | --      | The step pattern                 |
| `sample`  | `Optional[Sample]`| `None`  | Audio sample for this instrument |

```python
seq.add_pattern("kick", Pattern.from_string("x...x...x...x..."), kick_sample)
```

#### `.set_sample(name: str, sample: Sample) -> StepSequencer`

Set or replace the sample for a named instrument. Returns `self` for chaining.

| Parameter | Type     | Description                      |
|-----------|----------|----------------------------------|
| `name`    | `str`    | Instrument name                  |
| `sample`  | `Sample` | Audio sample to assign           |

#### `.load_kit(kit: Dict[str, Pattern], samples: Optional[Dict[str, Sample]] = None) -> StepSequencer`

Load a full kit of patterns (and optionally their samples) at once. Returns `self` for chaining.

| Parameter | Type                           | Default | Description                    |
|-----------|--------------------------------|---------|--------------------------------|
| `kit`     | `Dict[str, Pattern]`           | --      | Map of instrument name to pattern |
| `samples` | `Optional[Dict[str, Sample]]`  | `None`  | Map of instrument name to sample  |

```python
seq.load_kit(ClassicPatterns.house_kit(), my_samples)
```

#### `.load_samples_from(library, mapping: Dict[str, str]) -> StepSequencer`

Load samples from a `SampleLibrary` instance using a name-to-key mapping. Returns `self` for chaining.

| Parameter | Type              | Description                                            |
|-----------|-------------------|--------------------------------------------------------|
| `library` | `SampleLibrary`   | A sample library instance (supports `[]` access)       |
| `mapping` | `Dict[str, str]`  | Maps instrument names (pattern keys) to library keys   |

```python
seq.load_samples_from(lib, {
    "kick":  "drums/kick",
    "snare": "drums/snare",
    "hat":   "drums/hat_closed",
})
```

#### `.render_pattern(name: str, bars: int = 1, sample: Optional[Sample] = None) -> List[tuple]`

Render a single named pattern to a list of event tuples. Each tuple is `(time: float, velocity: float, sample: Sample)`.

| Parameter | Type              | Default | Description                            |
|-----------|-------------------|---------|----------------------------------------|
| `name`    | `str`             | --      | Name of the pattern to render          |
| `bars`    | `int`             | `1`     | Number of bars to render               |
| `sample`  | `Optional[Sample]`| `None`  | Override sample (falls back to stored) |

Returns an empty list if the pattern name is not found or no sample is available. Handles probability, rolls, and flams automatically.

#### `.render_to_track(bars: int = 4, name: str = "Sequencer", track_type: TrackType = TrackType.DRUMS) -> Track`

Render all patterns into a single `Track` object.

| Parameter    | Type        | Default            | Description                 |
|--------------|-------------|--------------------|-----------------------------|
| `bars`       | `int`       | `4`                | Number of bars to render    |
| `name`       | `str`       | `"Sequencer"`      | Track name                  |
| `track_type` | `TrackType` | `TrackType.DRUMS`  | Track type classification   |

```python
track = seq.render_to_track(bars=8, name="Drums")
```

#### `.apply_groove(groove_template) -> StepSequencer`

Apply a `GrooveTemplate` (from the expression module) to this sequencer. The template's velocity scales are multiplied into each active step's velocity. Returns `self` for chaining.

| Parameter        | Type             | Description                                   |
|------------------|------------------|-----------------------------------------------|
| `groove_template`| `GrooveTemplate` | A groove template with `length` and `velocity_scales` attributes |

#### `.create_variation(variation_type: str = 'fill') -> StepSequencer`

Create a variation of the current patterns. Returns a **new** `StepSequencer` instance with modified patterns (samples are shallow-copied).

| Parameter        | Type  | Default  | Description              |
|------------------|-------|----------|--------------------------|
| `variation_type` | `str` | `'fill'` | One of `'fill'`, `'sparse'`, `'double'` |

| Variation   | Behaviour                                                                 |
|-------------|---------------------------------------------------------------------------|
| `'fill'`    | Snare patterns get a busier fill pattern; other instruments unchanged     |
| `'sparse'`  | Randomly removes ~30% of hits from every pattern                         |
| `'double'`  | Randomly adds ghost notes on empty off-beat positions (~50% chance)      |

```python
fill_bar = seq.create_variation('fill')
```

---

## EuclideanPattern

```python
class EuclideanPattern
```

Generates Euclidean rhythms using Bjorklund's algorithm. Euclidean rhythms distribute *n* hits as evenly as possible across *k* steps, producing patterns found in many world music traditions.

### Static Methods

#### `.generate(hits: int, steps: int, rotation: int = 0) -> Pattern`

Generate a Euclidean rhythm pattern.

| Parameter  | Type  | Default | Description                            |
|------------|-------|---------|----------------------------------------|
| `hits`     | `int` | --      | Number of active hits to distribute    |
| `steps`    | `int` | --      | Total number of steps in the pattern   |
| `rotation` | `int` | `0`     | Rotate the result rightward by this many steps |

Well-known examples:

| Call         | Result          | Tradition                |
|--------------|-----------------|--------------------------|
| `E(3, 8)`    | `x..x..x.`      | Cuban tresillo           |
| `E(5, 8)`    | `x.xx.xx.`      | Cuban cinquillo          |
| `E(7, 12)`   | `x.xx.x.xx.x.`  | West African bell        |

```python
from beatmaker.sequencer import EuclideanPattern

tresillo = EuclideanPattern.generate(3, 8)
rotated = EuclideanPattern.generate(3, 8, rotation=1)
```

#### `.common_patterns() -> Dict[str, Pattern]`

Returns a dictionary of well-known Euclidean rhythm patterns.

| Key          | Euclidean | Origin          |
|--------------|-----------|-----------------|
| `'tresillo'` | E(3, 8)   | Cuban           |
| `'cinquillo'`| E(5, 8)   | Cuban           |
| `'bembe'`    | E(7, 12)  | West African    |
| `'aksak'`    | E(4, 9)   | Turkish         |
| `'rumba'`    | E(5, 12)  | Afro-Cuban      |
| `'soukous'`  | E(5, 16)  | Central African |

```python
patterns = EuclideanPattern.common_patterns()
seq.add_pattern("bell", patterns['tresillo'])
```

---

## PolyrhythmGenerator

```python
@dataclass
class PolyrhythmGenerator
```

Generates polyrhythmic pattern pairs.

### Static Methods

#### `.create(rhythm_a: int, rhythm_b: int, steps: int = 16) -> tuple`

Create two `Pattern` objects that form a polyrhythm by evenly distributing each rhythm's hits across the given number of steps.

| Parameter  | Type  | Default | Description                     |
|------------|-------|---------|---------------------------------|
| `rhythm_a` | `int` | --      | Number of beats for pattern A   |
| `rhythm_b` | `int` | --      | Number of beats for pattern B   |
| `steps`    | `int` | `16`    | Total pattern length in steps   |

Returns a `tuple` of two `Pattern` instances: `(pattern_a, pattern_b)`.

```python
from beatmaker.sequencer import PolyrhythmGenerator

three_against_four = PolyrhythmGenerator.create(3, 4, 12)
pat_3, pat_4 = three_against_four
```

---

# Arpeggiator Module

Source: `beatmaker/arpeggiator.py`

## ArpDirection

```python
class ArpDirection(Enum)
```

Enum controlling the order in which arpeggiator notes are played.

### Values

| Member     | Description                                              |
|------------|----------------------------------------------------------|
| `UP`       | Notes sorted ascending (low to high)                     |
| `DOWN`     | Notes sorted descending (high to low)                    |
| `UP_DOWN`  | Ascending then descending (endpoints not repeated)       |
| `DOWN_UP`  | Descending then ascending (endpoints not repeated)       |
| `RANDOM`   | Random order (reshuffled each generation)                |
| `ORDER`    | Notes played in the order they were supplied             |

---

## ArpMode

```python
class ArpMode(Enum)
```

Enum controlling how the arpeggiator expands the input note set before applying direction.

### Values

| Member          | Description                                               |
|-----------------|-----------------------------------------------------------|
| `NORMAL`        | Notes as-is, no expansion                                 |
| `OCTAVE`        | Original notes plus one octave above                      |
| `DOUBLE_OCTAVE` | Original notes plus one and two octaves above             |
| `POWER`         | For each note, adds root + fifth (+7) + octave (+12)     |

---

## ChordShape

```python
@dataclass
class ChordShape
```

Defines a chord as a list of semitone intervals from the root note.

### Constructor

```python
ChordShape(name: str, intervals: List[int])
```

| Parameter   | Type        | Description                          |
|-------------|-------------|--------------------------------------|
| `name`      | `str`       | Human-readable name of the chord     |
| `intervals` | `List[int]` | Semitone offsets from root (root = 0)|

### Preset Chord Shapes (class attributes)

#### Triads

| Attribute | Name      | Intervals        |
|-----------|-----------|------------------|
| `MAJOR`   | `major`   | `[0, 4, 7]`     |
| `MINOR`   | `minor`   | `[0, 3, 7]`     |
| `DIM`     | `dim`     | `[0, 3, 6]`     |
| `AUG`     | `aug`     | `[0, 4, 8]`     |
| `SUS2`    | `sus2`    | `[0, 2, 7]`     |
| `SUS4`    | `sus4`    | `[0, 5, 7]`     |

#### Seventh Chords

| Attribute    | Name         | Intervals          |
|--------------|--------------|--------------------|
| `MAJOR7`     | `maj7`       | `[0, 4, 7, 11]`   |
| `MINOR7`     | `min7`       | `[0, 3, 7, 10]`   |
| `DOM7`       | `dom7`       | `[0, 4, 7, 10]`   |
| `DIM7`       | `dim7`       | `[0, 3, 6, 9]`    |
| `HALF_DIM7`  | `half_dim7`  | `[0, 3, 6, 10]`   |

#### Extended Chords

| Attribute | Name     | Intervals                |
|-----------|----------|--------------------------|
| `ADD9`    | `add9`   | `[0, 4, 7, 14]`         |
| `MAJ9`    | `maj9`   | `[0, 4, 7, 11, 14]`     |
| `MIN9`    | `min9`   | `[0, 3, 7, 10, 14]`     |
| `DOM9`    | `dom9`   | `[0, 4, 7, 10, 14]`     |
| `ADD11`   | `add11`  | `[0, 4, 7, 17]`         |
| `MAJ13`   | `maj13`  | `[0, 4, 7, 11, 14, 21]` |

### Class Methods

#### `.custom(name: str, intervals: list) -> ChordShape`

Create a custom chord shape from arbitrary semitone intervals.

| Parameter   | Type   | Description                            |
|-------------|--------|----------------------------------------|
| `name`      | `str`  | Name for the custom chord              |
| `intervals` | `list` | Semitone intervals from root           |

```python
quartal = ChordShape.custom("quartal", [0, 5, 10, 15])
```

### Example

```python
from beatmaker.arpeggiator import ChordShape

chord = ChordShape.MINOR7
print(chord.name)       # "min7"
print(chord.intervals)  # [0, 3, 7, 10]
```

---

## Scale

```python
@dataclass
class Scale
```

Musical scale definition, storing a set of semitone intervals from the root.

### Constructor

```python
Scale(name: str, intervals: List[int])
```

| Parameter   | Type        | Description                             |
|-------------|-------------|-----------------------------------------|
| `name`      | `str`       | Human-readable scale name               |
| `intervals` | `List[int]` | Semitone offsets within one octave       |

### Methods

#### `.get_notes(root_midi: int, octaves: int = 1) -> List[int]`

Return a list of MIDI note numbers for this scale starting from the given root.

| Parameter   | Type  | Default | Description                         |
|-------------|-------|---------|-------------------------------------|
| `root_midi` | `int` | --      | MIDI note number of the root        |
| `octaves`   | `int` | `1`     | How many octaves to span            |

```python
c_major_notes = Scale.MAJOR.get_notes(60, 2)
# [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83]
```

### Preset Scales (class attributes)

#### Diatonic Modes

| Attribute     | Name          | Intervals                   |
|---------------|---------------|-----------------------------|
| `MAJOR`       | `major`       | `[0, 2, 4, 5, 7, 9, 11]`  |
| `MINOR`       | `minor`       | `[0, 2, 3, 5, 7, 8, 10]`  |
| `DORIAN`      | `dorian`      | `[0, 2, 3, 5, 7, 9, 10]`  |
| `PHRYGIAN`    | `phrygian`    | `[0, 1, 3, 5, 7, 8, 10]`  |
| `LYDIAN`      | `lydian`      | `[0, 2, 4, 6, 7, 9, 11]`  |
| `MIXOLYDIAN`  | `mixolydian`  | `[0, 2, 4, 5, 7, 9, 10]`  |
| `LOCRIAN`     | `locrian`     | `[0, 1, 3, 5, 6, 8, 10]`  |

#### Pentatonic & Blues

| Attribute           | Name          | Intervals                |
|---------------------|---------------|--------------------------|
| `MINOR_PENTATONIC`  | `minor_pent`  | `[0, 3, 5, 7, 10]`      |
| `MAJOR_PENTATONIC`  | `major_pent`  | `[0, 2, 4, 7, 9]`       |
| `BLUES`             | `blues`       | `[0, 3, 5, 6, 7, 10]`   |

#### Minor Variants

| Attribute         | Name              | Intervals                   |
|-------------------|-------------------|-----------------------------|
| `HARMONIC_MINOR`  | `harmonic_minor`  | `[0, 2, 3, 5, 7, 8, 11]`  |
| `MELODIC_MINOR`   | `melodic_minor`   | `[0, 2, 3, 5, 7, 9, 11]`  |

---

## note_name_to_midi

```python
def note_name_to_midi(note: str) -> int
```

Convert a human-readable note name to a MIDI note number. Supports sharps (`#`) and flats (`b`).

| Parameter | Type  | Description                              |
|-----------|-------|------------------------------------------|
| `note`    | `str` | Note name with octave, e.g. `"C4"`, `"F#3"`, `"Bb2"` |

Returns the integer MIDI note number.

```python
from beatmaker.arpeggiator import note_name_to_midi

note_name_to_midi("C4")   # 60
note_name_to_midi("A4")   # 69
note_name_to_midi("F#3")  # 54
```

---

## Arpeggiator

```python
@dataclass
class Arpeggiator
```

Musical arpeggiator that takes a chord or scale and creates rhythmic note patterns. This is the core engine -- it produces lists of timed MIDI events.

### Constructor

```python
Arpeggiator(
    bpm: float = 120.0,
    direction: ArpDirection = ArpDirection.UP,
    mode: ArpMode = ArpMode.NORMAL,
    octaves: int = 1,
    rate: float = 0.25,
    gate: float = 0.8,
    swing: float = 0.0,
    velocity_pattern: Optional[List[float]] = None,
)
```

| Parameter          | Type                     | Default             | Description                                                   |
|--------------------|--------------------------|---------------------|---------------------------------------------------------------|
| `bpm`              | `float`                  | `120.0`             | Tempo in beats per minute                                     |
| `direction`        | `ArpDirection`           | `ArpDirection.UP`   | Note ordering direction                                       |
| `mode`             | `ArpMode`                | `ArpMode.NORMAL`    | Note expansion mode                                           |
| `octaves`          | `int`                    | `1`                 | Number of octaves to span                                     |
| `rate`             | `float`                  | `0.25`              | Note duration in beats (0.25 = 16th, 0.5 = 8th, 1.0 = quarter) |
| `gate`             | `float`                  | `0.8`               | Fraction of `rate` that the note actually sounds (0.0--1.0)   |
| `swing`            | `float`                  | `0.0`               | Swing amount applied to off-beat notes (0.0--1.0)             |
| `velocity_pattern` | `Optional[List[float]]`  | `None`              | Cyclic velocity pattern applied to successive notes           |

### Methods

#### `.generate_pattern(notes: List[int], beats: int = 4) -> List[tuple]`

Generate arpeggio events from a list of MIDI note numbers. Returns a list of `(time, midi_note, velocity, duration)` tuples.

| Parameter | Type        | Default | Description                        |
|-----------|-------------|---------|-------------------------------------|
| `notes`   | `List[int]` | --      | MIDI note numbers to arpeggiate    |
| `beats`   | `int`       | `4`     | Pattern length in beats            |

The notes are processed through mode expansion, octave extension, and direction ordering before event generation.

```python
arp = Arpeggiator(bpm=120, direction=ArpDirection.UP)
events = arp.generate_pattern([60, 64, 67], beats=4)
# Each event: (time_seconds, midi_note, velocity, duration_seconds)
```

#### `.generate_from_chord(root: Union[str, int], chord: ChordShape, beats: int = 4) -> List[tuple]`

Generate arpeggio events from a root note and chord shape.

| Parameter | Type                | Default | Description                               |
|-----------|---------------------|---------|-------------------------------------------|
| `root`    | `Union[str, int]`   | --      | Root note as name (`"C4"`) or MIDI number |
| `chord`   | `ChordShape`        | --      | Chord shape to arpeggiate                 |
| `beats`   | `int`               | `4`     | Pattern length in beats                   |

```python
events = arp.generate_from_chord("C4", ChordShape.MINOR7, beats=8)
```

#### `.generate_from_scale(root: Union[str, int], scale: Scale, beats: int = 4) -> List[tuple]`

Generate arpeggio events from a root note and scale.

| Parameter | Type                | Default | Description                               |
|-----------|---------------------|---------|-------------------------------------------|
| `root`    | `Union[str, int]`   | --      | Root note as name (`"C4"`) or MIDI number |
| `scale`   | `Scale`             | --      | Scale to arpeggiate                       |
| `beats`   | `int`               | `4`     | Pattern length in beats                   |

```python
events = arp.generate_from_scale("A3", Scale.MINOR_PENTATONIC, beats=4)
```

#### `.generate_from_progression(progression: List[tuple], beats_per_chord: int = 4) -> List[tuple]`

Generate a continuous arpeggio over a chord progression. Events are offset in time so each chord follows the previous.

| Parameter         | Type          | Default | Description                                        |
|-------------------|---------------|---------|----------------------------------------------------|
| `progression`     | `List[tuple]` | --      | List of `(root, ChordShape)` tuples               |
| `beats_per_chord` | `int`         | `4`     | Number of beats to spend on each chord             |

```python
progression = [
    ('C3', ChordShape.MAJOR),
    ('G3', ChordShape.MAJOR),
    ('A3', ChordShape.MINOR),
    ('F3', ChordShape.MAJOR),
]
events = arp.generate_from_progression(progression, beats_per_chord=4)
```

---

## ArpeggiatorBuilder

```python
@dataclass
class ArpeggiatorBuilder
```

Fluent builder for configuring an `Arpeggiator` instance. All setter methods return `self`, enabling method chaining.

### Constructor

```python
ArpeggiatorBuilder()
```

Creates a builder wrapping a default `Arpeggiator`.

### Methods -- Tempo

#### `.tempo(bpm: float) -> ArpeggiatorBuilder`

Set the tempo in beats per minute.

### Methods -- Direction

#### `.up() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.UP`.

#### `.down() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.DOWN`.

#### `.up_down() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.UP_DOWN`.

#### `.down_up() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.DOWN_UP`.

#### `.random() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.RANDOM`.

#### `.as_played() -> ArpeggiatorBuilder`

Set direction to `ArpDirection.ORDER` (notes played in input order).

### Methods -- Rate

#### `.rate(beats: float) -> ArpeggiatorBuilder`

Set note rate in beats. Common values: `0.25` (16th), `0.5` (8th), `1.0` (quarter).

#### `.sixteenth() -> ArpeggiatorBuilder`

Shorthand for `.rate(0.25)`.

#### `.eighth() -> ArpeggiatorBuilder`

Shorthand for `.rate(0.5)`.

#### `.quarter() -> ArpeggiatorBuilder`

Shorthand for `.rate(1.0)`.

#### `.triplet() -> ArpeggiatorBuilder`

Shorthand for `.rate(1/3)`.

### Methods -- Gate / Articulation

#### `.gate(value: float) -> ArpeggiatorBuilder`

Set gate length as a fraction of note duration (0.0--1.0).

#### `.staccato() -> ArpeggiatorBuilder`

Shorthand for `.gate(0.3)`.

#### `.legato() -> ArpeggiatorBuilder`

Shorthand for `.gate(1.0)`.

### Methods -- Range

#### `.octaves(num: int) -> ArpeggiatorBuilder`

Set the number of octaves the arpeggio spans.

### Methods -- Swing

#### `.swing(amount: float) -> ArpeggiatorBuilder`

Set swing amount (0.0--1.0).

### Methods -- Mode

#### `.with_octave() -> ArpeggiatorBuilder`

Set mode to `ArpMode.OCTAVE` (adds one octave above).

#### `.with_double_octave() -> ArpeggiatorBuilder`

Set mode to `ArpMode.DOUBLE_OCTAVE` (adds two octaves above).

#### `.power_chords() -> ArpeggiatorBuilder`

Set mode to `ArpMode.POWER` (root + fifth + octave per note).

### Methods -- Velocity

#### `.velocity_pattern(pattern: List[float]) -> ArpeggiatorBuilder`

Set a cyclic velocity pattern applied to successive notes.

#### `.accent_downbeat() -> ArpeggiatorBuilder`

Apply the pattern `[1.0, 0.6, 0.7, 0.6]` to accent every 4th note (the downbeat).

### Methods -- Build

#### `.build() -> Arpeggiator`

Return the configured `Arpeggiator` instance.

### Example

```python
from beatmaker.arpeggiator import create_arpeggiator, ChordShape

arp = (
    create_arpeggiator()
    .tempo(130)
    .up_down()
    .sixteenth()
    .staccato()
    .octaves(2)
    .swing(0.1)
    .accent_downbeat()
    .build()
)

events = arp.generate_from_chord("C4", ChordShape.MINOR7, beats=8)
```

---

## create_arpeggiator

```python
def create_arpeggiator() -> ArpeggiatorBuilder
```

Convenience factory function. Returns a new `ArpeggiatorBuilder` instance with default settings.

```python
from beatmaker.arpeggiator import create_arpeggiator

builder = create_arpeggiator()
arp = builder.tempo(140).up().eighth().build()
```

---

## ArpSynthesizer

```python
class ArpSynthesizer
```

Synthesizer that renders arpeggiator MIDI events to audio (`AudioData`). Supports basic waveforms shaped by an ADSR envelope.

### Constructor

```python
ArpSynthesizer(
    waveform: str = 'saw',
    envelope: Optional[ADSREnvelope] = None,
    sample_rate: int = 44100,
)
```

| Parameter     | Type                     | Default                          | Description                               |
|---------------|--------------------------|----------------------------------|-------------------------------------------|
| `waveform`    | `str`                    | `'saw'`                          | Waveform type: `'sine'`, `'saw'`, `'square'`, `'triangle'` |
| `envelope`    | `Optional[ADSREnvelope]` | `ADSREnvelope(0.01, 0.1, 0.7, 0.1)` | ADSR amplitude envelope                  |
| `sample_rate` | `int`                    | `44100`                          | Audio sample rate in Hz                   |

### Methods

#### `.render_note(midi_note: int, duration: float, velocity: float = 1.0) -> AudioData`

Render a single synthesized note to `AudioData`.

| Parameter   | Type    | Default | Description                         |
|-------------|---------|---------|-------------------------------------|
| `midi_note` | `int`   | --      | MIDI note number                    |
| `duration`  | `float` | --      | Note duration in seconds            |
| `velocity`  | `float` | `1.0`   | Velocity multiplier for amplitude   |

```python
synth = ArpSynthesizer(waveform='square')
note_audio = synth.render_note(60, 0.5, velocity=0.8)
```

#### `.render_events(events: List[tuple]) -> AudioData`

Render a full list of arpeggiator events to a single `AudioData` buffer. Events are mixed (summed) together.

| Parameter | Type          | Description                                                |
|-----------|---------------|------------------------------------------------------------|
| `events`  | `List[tuple]` | List of `(time, midi_note, velocity, duration)` tuples     |

Returns an `AudioData` instance. If `events` is empty, returns silence.

```python
arp = Arpeggiator(bpm=120)
events = arp.generate_from_chord("C4", ChordShape.MAJOR)

synth = ArpSynthesizer(waveform='saw')
audio = synth.render_events(events)
```

---

## arp_chord

```python
def arp_chord(
    root: str,
    chord: ChordShape,
    beats: int = 4,
    direction: ArpDirection = ArpDirection.UP,
    rate: float = 0.25,
    bpm: float = 120,
) -> List[tuple]
```

Convenience function for quick arpeggio generation from a chord. Creates a temporary `Arpeggiator` internally.

| Parameter   | Type           | Default            | Description                        |
|-------------|----------------|--------------------|------------------------------------|
| `root`      | `str`          | --                 | Root note name (e.g. `"C4"`)      |
| `chord`     | `ChordShape`   | --                 | Chord shape to arpeggiate          |
| `beats`     | `int`          | `4`                | Pattern length in beats            |
| `direction` | `ArpDirection` | `ArpDirection.UP`  | Note direction                     |
| `rate`      | `float`        | `0.25`             | Note rate in beats                 |
| `bpm`       | `float`        | `120`              | Tempo                              |

Returns a list of `(time, midi_note, velocity, duration)` tuples.

```python
from beatmaker.arpeggiator import arp_chord, ChordShape

events = arp_chord("A3", ChordShape.MINOR, beats=4, rate=0.5)
```

---

## arp_scale

```python
def arp_scale(
    root: str,
    scale: Scale,
    beats: int = 4,
    direction: ArpDirection = ArpDirection.UP,
    rate: float = 0.25,
    bpm: float = 120,
) -> List[tuple]
```

Convenience function for quick arpeggio generation from a scale. Creates a temporary `Arpeggiator` internally.

| Parameter   | Type           | Default            | Description                        |
|-------------|----------------|--------------------|------------------------------------|
| `root`      | `str`          | --                 | Root note name (e.g. `"C4"`)      |
| `scale`     | `Scale`        | --                 | Scale to arpeggiate                |
| `beats`     | `int`          | `4`                | Pattern length in beats            |
| `direction` | `ArpDirection` | `ArpDirection.UP`  | Note direction                     |
| `rate`      | `float`        | `0.25`             | Note rate in beats                 |
| `bpm`       | `float`        | `120`              | Tempo                              |

Returns a list of `(time, midi_note, velocity, duration)` tuples.

```python
from beatmaker.arpeggiator import arp_scale, Scale, ArpDirection

events = arp_scale("D3", Scale.BLUES, beats=8, direction=ArpDirection.UP_DOWN)
```
