# API Reference: Melody, Harmony & Automation

This document covers the public API for three core beatmaker modules:

- **`beatmaker.melody`** -- Notes, Phrases, and Melodies for melodic composition
- **`beatmaker.harmony`** -- Keys, chord progressions, and voice leading
- **`beatmaker.automation`** -- Time-varying parameter curves and automated effects

---

## Table of Contents

- [melody.py](#melodypy)
  - [midi_to_note_name](#midi_to_note_name)
  - [Note](#note)
  - [Phrase](#phrase)
  - [Melody](#melody)
- [harmony.py](#harmonypy)
  - [Key](#key)
  - [ChordEntry](#chordentry)
  - [ChordProgression](#chordprogression)
- [automation.py](#automationpy)
  - [CurveType](#curvetype)
  - [AutomationPoint](#automationpoint)
  - [AutomationCurve](#automationcurve)
  - [AutomatableEffect](#automatableeffect)
  - [AutomatedGain](#automatedgain)
  - [AutomatedFilter](#automatedfilter)

---

# melody.py

Module providing first-class abstractions for melodic composition: individual notes, reusable phrases, and complete melodies positioned on a beat timeline.

---

## `midi_to_note_name`

```python
def midi_to_note_name(midi_note: int) -> str
```

Convert a MIDI note number to a human-readable note name string.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `midi_note` | `int` | MIDI note number (0--127) |

**Returns:** `str` -- Note name with octave, e.g. `"C4"`, `"F#3"`, `"A#5"`.

**Example:**

```python
midi_to_note_name(60)   # "C4"
midi_to_note_name(69)   # "A4"
```

---

## Note

```python
@dataclass(frozen=True)
class Note
```

A single musical note -- the atom of melodic expression. Instances are immutable (frozen dataclass). Pitch is stored as a MIDI note number (0--127), with `-1` denoting a rest. Duration is measured in beats. Velocity ranges from `0.0` to `1.0`.

### Constructor

```python
Note(pitch: int, duration: float, velocity: float = 1.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pitch` | `int` | *required* | MIDI note number (0--127), or `-1` for a rest |
| `duration` | `float` | *required* | Duration in beats |
| `velocity` | `float` | `1.0` | Velocity/dynamics (0.0--1.0) |

### Factory Methods

#### `Note.from_name(name: str, duration: float = 1.0, velocity: float = 1.0) -> Note`

Create a Note from a note name string (e.g. `"C4"`, `"F#3"`, `"Bb2"`). The name is converted to a MIDI number via `note_name_to_midi`.

```python
Note.from_name("C4")                    # middle C, 1 beat, full velocity
Note.from_name("F#3", 0.5, 0.8)         # F#3, half beat, velocity 0.8
Note.from_name("Bb2", duration=2.0)      # Bb2, 2 beats
```

#### `Note.rest(duration: float = 1.0) -> Note`

Create a rest (silence) of the given duration in beats. The resulting note has `pitch=-1` and `velocity=0.0`.

```python
Note.rest()       # 1-beat rest
Note.rest(0.5)    # half-beat rest
```

### Properties

#### `.is_rest -> bool`

`True` if this note is a rest (pitch < 0).

#### `.name -> str`

Human-readable note name. Returns `"R"` for rests, otherwise a string like `"C4"` or `"F#3"`.

### Transformation Methods

All transformation methods return a **new** `Note` instance (immutable style).

#### `.transpose(semitones: int) -> Note`

Return a copy transposed by the given number of semitones. The resulting pitch is clamped to the range 0--127. Rests are returned unchanged.

```python
Note.from_name("C4").transpose(7)    # G4
Note.from_name("C4").transpose(-12)  # C3
```

#### `.with_duration(duration: float) -> Note`

Return a copy with a different duration.

```python
Note.from_name("C4", 1.0).with_duration(0.5)
```

#### `.with_velocity(velocity: float) -> Note`

Return a copy with a different velocity.

```python
Note.from_name("C4").with_velocity(0.6)
```

---

## Phrase

```python
@dataclass
class Phrase
```

An ordered sequence of `Note` objects -- a reusable melodic idea. Phrases are the primary unit of melodic composition. They can be transposed, reversed, inverted, augmented, diminished, combined, and repeated to build complex melodies from simple motifs. All transformation methods return **new** `Phrase` objects (immutable style).

### Constructor

```python
Phrase(name: str, notes: List[Note] = [])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Identifier for this phrase |
| `notes` | `List[Note]` | `[]` | Ordered list of notes |

### Factory Methods

#### `Phrase.from_string(notation: str, name: str = "phrase") -> Phrase`

Parse concise melody notation into a Phrase.

**Format:** `"NoteName:Duration NoteName:Duration ..."` where tokens are space-separated.

- Duration is in beats (float). Omit `:Duration` to default to 1 beat.
- Use `"R"` or `"r"` for rests.
- An optional third component after a second colon sets velocity: `"C4:1:0.8"`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `notation` | `str` | *required* | Space-separated note tokens |
| `name` | `str` | `"phrase"` | Phrase identifier |

```python
Phrase.from_string("C4:1 D4:0.5 E4:0.5 R:1 G4:2")
Phrase.from_string("E4 G4 A4 B4")           # all quarter notes
Phrase.from_string("C4:1:0.8 E4:0.5:0.6")   # with velocity
```

#### `Phrase.from_notes(note_names: List[str], duration: float = 1.0, name: str = "phrase") -> Phrase`

Create a Phrase where all notes share the same duration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_names` | `List[str]` | *required* | List of note name strings |
| `duration` | `float` | `1.0` | Shared duration in beats |
| `name` | `str` | `"phrase"` | Phrase identifier |

```python
Phrase.from_notes(["C4", "E4", "G4"], duration=0.5)
```

#### `Phrase.from_midi_tuples(tuples: List[tuple], name: str = "phrase") -> Phrase`

Create from a list of tuples. Each tuple is either `(midi_note, duration_beats)` or `(midi_note, duration_beats, velocity)`. Use a negative MIDI number for rests.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tuples` | `List[tuple]` | *required* | List of `(midi, dur)` or `(midi, dur, vel)` tuples |
| `name` | `str` | `"phrase"` | Phrase identifier |

```python
Phrase.from_midi_tuples([(60, 1.0), (64, 0.5, 0.8), (-1, 1.0)])
```

### Properties

#### `.total_duration -> float`

Total duration in beats (sum of all note durations).

#### `.pitches -> List[int]`

List of MIDI pitch values, excluding rests.

#### `len(phrase) -> int`

Number of notes (including rests) in the phrase.

### Transformation Methods

All transformations return a **new** `Phrase`.

#### `.transpose(semitones: int) -> Phrase`

Transpose all notes by the given number of semitones. Rests are preserved. The resulting phrase name is appended with `_t+N` or `_t-N`.

```python
motif = Phrase.from_string("C4 E4 G4")
motif.transpose(5)   # F4 A4 C5
motif.transpose(-2)  # Bb3 D4 F4
```

#### `.reverse() -> Phrase`

Reverse the order of notes. Name is appended with `_rev`.

```python
Phrase.from_string("C4 D4 E4").reverse()  # E4 D4 C4
```

#### `.invert(axis: Optional[int] = None) -> Phrase`

Melodic inversion -- mirror pitches around an axis. If `axis` is `None`, the first sounding note's pitch is used as the axis. Rests are preserved unchanged. Resulting pitches are clamped to 0--127. Name is appended with `_inv`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `axis` | `Optional[int]` | `None` | MIDI pitch to mirror around; defaults to first non-rest pitch |

```python
Phrase.from_string("C4 E4 G4").invert()      # C4 Ab3 F3 (mirrored around C4=60)
Phrase.from_string("C4 E4 G4").invert(64)     # mirror around E4
```

#### `.retrograde_invert(axis: Optional[int] = None) -> Phrase`

Reverse and then invert -- a classic serial composition technique.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `axis` | `Optional[int]` | `None` | MIDI pitch to mirror around |

#### `.augment(factor: float = 2.0) -> Phrase`

Multiply all note durations by `factor` (slow down). Name is appended with `_aug`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | `float` | `2.0` | Duration multiplier |

```python
Phrase.from_string("C4:1 E4:1").augment(2.0)  # durations become 2.0 each
```

#### `.diminish(factor: float = 2.0) -> Phrase`

Divide all note durations by `factor` (speed up). Equivalent to `.augment(1.0 / factor)`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | `float` | `2.0` | Duration divisor |

```python
Phrase.from_string("C4:2 E4:2").diminish(2.0)  # durations become 1.0 each
```

#### `.with_velocity(velocity: float) -> Phrase`

Set uniform velocity for all sounding notes. Rests are unchanged.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `velocity` | `float` | *required* | New velocity (0.0--1.0) |

#### `.with_velocity_curve(curve: List[float]) -> Phrase`

Apply a velocity curve across all sounding notes. The curve list is linearly interpolated to match the number of sounding (non-rest) notes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `curve` | `List[float]` | *required* | Velocity values to interpolate across sounding notes |

```python
phrase.with_velocity_curve([0.3, 1.0, 0.5])  # crescendo then diminuendo
```

#### `.repeat(times: int) -> Phrase`

Repeat the phrase sequentially `times` times. Name is appended with `_xN`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `times` | `int` | *required* | Number of repetitions |

```python
Phrase.from_string("C4 E4").repeat(3)  # C4 E4 C4 E4 C4 E4
```

### Combination Methods

#### `.then(other: Phrase) -> Phrase`

Concatenate two phrases: play self, then `other` sequentially. The `+` operator is also supported.

```python
a = Phrase.from_string("C4 D4")
b = Phrase.from_string("E4 F4")
combined = a.then(b)    # C4 D4 E4 F4
combined = a + b         # same thing
```

### Event Conversion

#### `.to_events(start_beat: float = 0.0) -> List[Tuple[float, int, float, float]]`

Convert to a list of renderable events. Rests are omitted (they advance the beat cursor but produce no event).

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | `0.0` | Beat offset for the first note |

---

## Melody

```python
class Melody
```

A complete melody -- phrases positioned along a beat timeline. Melody is the top-level container that places `Phrase` objects at specific beats and converts the entire composition into a flat event list for rendering.

### Constructor

```python
Melody(name: str = "melody")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"melody"` | Identifier for this melody |

### Methods

#### `.add(phrase: Phrase, start_beat: Optional[float] = None) -> Melody`

Add a phrase at a specific beat position. If `start_beat` is `None`, the phrase is appended immediately after the last entry ends (auto-sequencing). Returns `self` for chaining.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `phrase` | `Phrase` | *required* | The phrase to add |
| `start_beat` | `Optional[float]` | `None` | Beat position; `None` for auto-sequence |

```python
mel = Melody("intro")
mel.add(verse_phrase)                # starts at beat 0
mel.add(chorus_phrase)               # auto-appended after verse ends
mel.add(bridge_phrase, start_beat=32.0)  # placed at beat 32
```

#### `.add_sequence(phrases: List[Phrase]) -> Melody`

Add multiple phrases end-to-end in order. Returns `self` for chaining.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `phrases` | `List[Phrase]` | *required* | Phrases to sequence |

```python
mel.add_sequence([intro, verse, chorus, outro])
```

### Properties

#### `.total_duration -> float`

Total duration in beats, computed as the maximum of `(start + phrase.total_duration)` across all entries.

#### `.entries -> List[Tuple[float, Phrase]]`

List of `(start_beat, Phrase)` entries (defensive copy).

### Event Conversion

#### `.to_events() -> List[Tuple[float, int, float, float]]`

Convert the entire melody to a flat event list, sorted by beat position.

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples.

```python
events = melody.to_events()
for beat, note, vel, dur in events:
    print(f"Beat {beat}: note={note} vel={vel} dur={dur}")
```

---

# harmony.py

Module providing a Key context, Roman numeral chord progressions, voice leading, and diatonic harmonic analysis.

---

## Key

```python
@dataclass
class Key
```

A musical key -- the harmonic context for composition. Provides scale degrees, diatonic chord construction, modulation, and diatonic membership checks.

### Constructor

```python
Key(root: str, scale: Scale)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | `str` | *required* | Root note name, e.g. `"C"`, `"F#"`, `"Bb"` |
| `scale` | `Scale` | *required* | Scale type (from `beatmaker.arpeggiator.Scale`) |

### Factory Methods

These class methods provide convenient construction for common key types.

#### `Key.major(root: str) -> Key`

Create a major key.

```python
Key.major('C')   # C major
Key.major('Bb')  # Bb major
```

#### `Key.minor(root: str) -> Key`

Create a natural minor key.

```python
Key.minor('A')   # A natural minor
```

#### `Key.harmonic_minor(root: str) -> Key`

Create a harmonic minor key.

#### `Key.melodic_minor(root: str) -> Key`

Create a melodic minor key.

#### `Key.dorian(root: str) -> Key`

Create a Dorian mode key.

#### `Key.mixolydian(root: str) -> Key`

Create a Mixolydian mode key.

#### `Key.pentatonic_minor(root: str) -> Key`

Create a minor pentatonic key.

#### `Key.pentatonic_major(root: str) -> Key`

Create a major pentatonic key.

#### `Key.blues(root: str) -> Key`

Create a blues scale key.

### Properties

#### `.root_pc -> int`

Root pitch class (0--11), where C=0, C#=1, ..., B=11.

### Scale Degree Access

#### `.degree_pc(degree: int) -> int`

Pitch class (0--11) for the given 1-indexed scale degree.

| Parameter | Type | Description |
|-----------|------|-------------|
| `degree` | `int` | 1-indexed scale degree |

```python
Key.major('C').degree_pc(5)  # 7 (G)
```

#### `.degree(degree: int, octave: int = 4) -> int`

MIDI note number for the given 1-indexed scale degree in the given octave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `degree` | `int` | *required* | 1-indexed scale degree |
| `octave` | `int` | `4` | Octave number |

```python
Key.major('C').degree(1, 4)  # 60 (middle C)
Key.major('C').degree(5, 4)  # 67 (G4)
```

#### `.scale_notes(octave: int = 4) -> List[int]`

All MIDI notes in the key for a single octave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `octave` | `int` | `4` | Octave number |

#### `.scale_notes_range(low_octave: int = 3, high_octave: int = 5) -> List[int]`

All MIDI notes in the key across a range of octaves, sorted and deduplicated.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `low_octave` | `int` | `3` | Lowest octave (inclusive) |
| `high_octave` | `int` | `5` | Highest octave (inclusive) |

### Diatonic Chords

#### `.chord(degree: int, extensions: int = 3, octave: int = 4) -> Tuple[int, ChordShape]`

Get a diatonic chord built on a scale degree.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `degree` | `int` | *required* | 1-indexed scale degree |
| `extensions` | `int` | `3` | `3` for triad, `4` for seventh chord |
| `octave` | `int` | `4` | Base octave for the chord root |

**Returns:** `(root_midi, ChordShape)` tuple.

```python
root, shape = Key.major('C').chord(1)       # C major triad
root, shape = Key.major('C').chord(2, 4)    # D minor 7th
```

#### `.chord_name(degree: int) -> str`

Human-readable chord name for a diatonic degree. Uses flats or sharps based on the key.

| Parameter | Type | Description |
|-----------|------|-------------|
| `degree` | `int` | 1-indexed scale degree |

```python
Key.major('C').chord_name(2)   # "Dm"
Key.major('C').chord_name(1)   # "C"
Key.major('F').chord_name(4)   # "Bb"
```

### Modulation

#### `.modulate(new_root: str, new_scale: Optional[Scale] = None) -> Key`

Return a new Key modulated to a different root. If `new_scale` is `None`, the current scale type is preserved.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `new_root` | `str` | *required* | New root note name |
| `new_scale` | `Optional[Scale]` | `None` | New scale; `None` keeps current |

```python
Key.major('C').modulate('G')                   # G major
Key.major('C').modulate('A', Scale.MINOR)      # A minor
```

#### `.relative_minor() -> Key`

Return the relative minor of a major key (built on the vi degree).

```python
Key.major('C').relative_minor()  # Key(A minor)
```

#### `.relative_major() -> Key`

Return the relative major of a minor key (built on the III degree).

```python
Key.minor('A').relative_major()  # Key(C major)
```

#### `.parallel_minor() -> Key`

Return the parallel minor -- same root, minor scale.

```python
Key.major('C').parallel_minor()  # Key(C minor)
```

#### `.parallel_major() -> Key`

Return the parallel major -- same root, major scale.

```python
Key.minor('C').parallel_major()  # Key(C major)
```

### Utility

#### `.is_diatonic(midi_note: int) -> bool`

Check if a MIDI note belongs to this key.

| Parameter | Type | Description |
|-----------|------|-------------|
| `midi_note` | `int` | MIDI note number |

```python
Key.major('C').is_diatonic(60)  # True  (C4)
Key.major('C').is_diatonic(61)  # False (C#4)
```

#### `.nearest_diatonic(midi_note: int) -> int`

Snap a MIDI note to the nearest diatonic pitch. If the note is already diatonic, it is returned unchanged. Otherwise, checks offsets of +/-1 then +/-2 semitones.

| Parameter | Type | Description |
|-----------|------|-------------|
| `midi_note` | `int` | MIDI note number to snap |

**Returns:** `int` -- nearest diatonic MIDI note.

---

## ChordEntry

```python
@dataclass
class ChordEntry
```

A single chord in a progression. Typically constructed internally by `ChordProgression`.

### Constructor

```python
ChordEntry(degree: int, shape: ChordShape, root_midi: int, duration_beats: float)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `degree` | `int` | 1-indexed scale degree |
| `shape` | `ChordShape` | Chord voicing shape |
| `root_midi` | `int` | MIDI note of the chord root |
| `duration_beats` | `float` | Duration of this chord in beats |

### Properties

#### `.midi_notes -> List[int]`

MIDI notes of this chord (root + each interval in the shape).

---

## ChordProgression

```python
@dataclass
class ChordProgression
```

A sequence of chords in a key. Supports Roman numeral notation, common preset progressions, voice leading, and conversion to renderable events.

### Constructor

```python
ChordProgression(key: Key, chords: List[ChordEntry] = [])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Key` | *required* | The harmonic key context |
| `chords` | `List[ChordEntry]` | `[]` | List of chord entries |

### Factory Methods

#### `ChordProgression.from_roman(key: Key, numerals: str, beats_per_chord: float = 4.0, octave: int = 3) -> ChordProgression`

Parse a chord progression from Roman numeral notation. Numerals are separated by `" - "` or whitespace. Uppercase = major, lowercase = minor. Supports quality modifiers (`dim`, `aug`, `sus2`, `sus4`) and extensions (`7`, `maj7`, `9`, `11`, `13`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Key` | *required* | Key context |
| `numerals` | `str` | *required* | Roman numeral string |
| `beats_per_chord` | `float` | `4.0` | Duration per chord in beats |
| `octave` | `int` | `3` | Base octave for chord roots |

```python
ChordProgression.from_roman(Key.major('C'), "I - IV - V - I")
ChordProgression.from_roman(Key.minor('A'), "i - iv - v - i")
ChordProgression.from_roman(Key.major('C'), "ii7 - V7 - Imaj7")
ChordProgression.from_roman(Key.major('G'), "I - V - vi - IV", beats_per_chord=2.0)
```

**Supported Roman numerals:** `I` through `VII` (uppercase = major) and `i` through `vii` (lowercase = minor).

**Supported quality modifiers:** `dim`, `aug`, `sus2`, `sus4`.

**Supported extensions:** `7`, `maj7`, `9`, `11`, `13`.

**Accidentals:** Prefix with `b` or `#` (e.g. `bVII`).

#### `ChordProgression.from_degrees(key: Key, degrees: List[int], beats_per_chord: float = 4.0, octave: int = 3) -> ChordProgression`

Create from a list of 1-indexed scale degree numbers. All chords are built as diatonic triads.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Key` | *required* | Key context |
| `degrees` | `List[int]` | *required* | List of scale degrees |
| `beats_per_chord` | `float` | `4.0` | Duration per chord |
| `octave` | `int` | `3` | Base octave |

```python
ChordProgression.from_degrees(Key.major('C'), [1, 4, 5, 1])
```

### Preset Progressions

All presets are class methods with the signature `(key: Key, beats_per_chord: float = 4.0) -> ChordProgression`.

#### `ChordProgression.pop(key, beats_per_chord=4.0)`

The ubiquitous pop progression: **I - V - vi - IV**.

```python
ChordProgression.pop(Key.major('G'))
```

#### `ChordProgression.blues(key, beats_per_chord=4.0)`

12-bar blues: **I - I - I - I - IV - IV - I - I - V - IV - I - V**.

```python
ChordProgression.blues(Key.major('E'))
```

#### `ChordProgression.jazz_ii_v_i(key, beats_per_chord=4.0)`

Jazz ii-V-I: **ii7 - V7 - Imaj7**.

```python
ChordProgression.jazz_ii_v_i(Key.major('Bb'))
```

#### `ChordProgression.andalusian(key, beats_per_chord=4.0)`

Flamenco/Andalusian cadence: **i - VII - VI - V**.

```python
ChordProgression.andalusian(Key.minor('D'))
```

#### `ChordProgression.canon(key, beats_per_chord=4.0)`

Pachelbel's Canon: **I - V - vi - iii - IV - I - IV - V**.

```python
ChordProgression.canon(Key.major('D'))
```

#### `ChordProgression.fifties(key, beats_per_chord=4.0)`

The '50s doo-wop progression: **I - vi - IV - V**.

```python
ChordProgression.fifties(Key.major('C'))
```

### Properties

#### `.total_duration -> float`

Total duration in beats (sum of all chord durations).

#### `len(progression) -> int`

Number of chords in the progression.

### Methods

#### `.voice_lead(num_voices: int = 4, base_octave: int = 3) -> List[List[int]]`

Generate voice-led MIDI notes for each chord. Uses minimal movement: each voice moves to the nearest available chord tone. The first chord is arranged in close position from `base_octave`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_voices` | `int` | `4` | Number of voices |
| `base_octave` | `int` | `3` | Starting octave for the first chord |

**Returns:** `List[List[int]]` -- one sorted list of MIDI notes per chord.

```python
prog = ChordProgression.pop(Key.major('C'))
voicings = prog.voice_lead(num_voices=4)
# voicings[0] might be [48, 52, 55, 60] for C major
```

#### `.to_arp_progression() -> List[Tuple[str, ChordShape]]`

Convert to a format compatible with the existing `Arpeggiator.generate_from_progression()`.

**Returns:** List of `(root_note_name, ChordShape)` tuples.

```python
prog.to_arp_progression()
# [("C3", ChordShape.MAJOR), ("G3", ChordShape.MAJOR), ...]
```

#### `.to_events(start_beat: float = 0.0, voice_led: bool = False, num_voices: int = 4) -> List[Tuple[float, int, float, float]]`

Convert to renderable note events. If `voice_led` is `True`, uses voice leading for smooth chord transitions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | `0.0` | Beat offset |
| `voice_led` | `bool` | `False` | Use voice leading |
| `num_voices` | `int` | `4` | Number of voices (when voice-led) |

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples. Velocity is fixed at `0.8`.

---

# automation.py

Module providing time-varying parameter automation curves and automated audio effects.

---

## CurveType

```python
class CurveType(Enum)
```

Interpolation method between automation breakpoints.

| Value | Description |
|-------|-------------|
| `CurveType.LINEAR` | Linear interpolation (straight line) |
| `CurveType.EXPONENTIAL` | Exponential interpolation (good for frequency/gain) |
| `CurveType.LOGARITHMIC` | Logarithmic interpolation |
| `CurveType.STEP` | Step/hold -- value stays constant until the next point |
| `CurveType.SMOOTH` | Cosine interpolation (smooth ease-in/ease-out) |

---

## AutomationPoint

```python
@dataclass
class AutomationPoint
```

A single automation breakpoint at a specific beat.

### Constructor

```python
AutomationPoint(beat: float, value: float, curve: CurveType = CurveType.LINEAR)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `beat` | `float` | *required* | Beat position of this breakpoint |
| `value` | `float` | *required* | Parameter value at this beat |
| `curve` | `CurveType` | `CurveType.LINEAR` | Interpolation method to use **from** this point to the next |

---

## AutomationCurve

```python
@dataclass
class AutomationCurve
```

A curve of parameter values over time (in beats). Automation curves define how a parameter changes across the duration of a track or song. They can be attached to track volume, pan, or any effect parameter via `AutomatableEffect`.

### Constructor

```python
AutomationCurve(name: str, points: List[AutomationPoint] = [], default_value: float = 0.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Identifier for this curve |
| `points` | `List[AutomationPoint]` | `[]` | Initial breakpoints |
| `default_value` | `float` | `0.0` | Value returned when no points are defined |

### Building Methods

All building methods return `self` for chaining.

#### `.add_point(beat: float, value: float, curve: CurveType = CurveType.LINEAR) -> AutomationCurve`

Add a breakpoint at the given beat. Points are automatically kept sorted by beat.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `beat` | `float` | *required* | Beat position |
| `value` | `float` | *required* | Parameter value |
| `curve` | `CurveType` | `CurveType.LINEAR` | Interpolation to next point |

```python
curve = AutomationCurve("volume")
curve.add_point(0, 0.0).add_point(4, 1.0).add_point(16, 1.0).add_point(20, 0.0)
```

#### `.ramp(start_beat: float, end_beat: float, start_value: float, end_value: float, curve: CurveType = CurveType.LINEAR) -> AutomationCurve`

Add a ramp (two breakpoints) between two values.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | *required* | Start beat |
| `end_beat` | `float` | *required* | End beat |
| `start_value` | `float` | *required* | Value at start |
| `end_value` | `float` | *required* | Value at end |
| `curve` | `CurveType` | `CurveType.LINEAR` | Interpolation type |

```python
curve.ramp(0, 8, 0.0, 1.0, CurveType.SMOOTH)
```

#### `.lfo(start_beat: float, end_beat: float, center: float, depth: float, rate_hz: float, waveform: str = 'sine', bpm: float = 120.0) -> AutomationCurve`

Generate LFO-style automation by adding many breakpoints that trace an oscillating waveform.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | *required* | Range start in beats |
| `end_beat` | `float` | *required* | Range end in beats |
| `center` | `float` | *required* | Center value of oscillation |
| `depth` | `float` | *required* | Amplitude of oscillation |
| `rate_hz` | `float` | *required* | Oscillation rate in Hz |
| `waveform` | `str` | `'sine'` | One of `'sine'`, `'triangle'`, `'square'`, `'saw'` |
| `bpm` | `float` | `120.0` | Tempo (needed to convert beats to time) |

```python
# Tremolo effect: oscillate volume between 0.5 and 1.0 at 4 Hz
curve.lfo(0, 16, center=0.75, depth=0.25, rate_hz=4.0, waveform='sine')
```

### Sampling Methods

#### `.sample_at(beat: float) -> float`

Get the interpolated value at a specific beat. Returns the value of the first point for beats before the curve, and the value of the last point for beats after the curve. Returns `default_value` when no points exist.

| Parameter | Type | Description |
|-----------|------|-------------|
| `beat` | `float` | Beat position to sample |

**Returns:** `float` -- interpolated parameter value.

#### `.render(bpm: float, sample_rate: int, duration_beats: float) -> np.ndarray`

Render the automation curve to a per-sample numpy array.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bpm` | `float` | Song tempo in beats per minute |
| `sample_rate` | `int` | Audio sample rate in Hz |
| `duration_beats` | `float` | Total length to render in beats |

**Returns:** `np.ndarray` -- 1D array of float values, one per audio sample.

```python
samples = curve.render(bpm=120, sample_rate=44100, duration_beats=16.0)
```

### Preset Curves (Class Methods)

#### `AutomationCurve.fade_in(beats: float) -> AutomationCurve`

Volume fade in from 0.0 to 1.0 over the given number of beats, starting at beat 0.

| Parameter | Type | Description |
|-----------|------|-------------|
| `beats` | `float` | Duration of the fade-in in beats |

```python
AutomationCurve.fade_in(8)  # 8-beat fade in
```

#### `AutomationCurve.fade_out(start_beat: float, duration: float) -> AutomationCurve`

Volume fade out from 1.0 to 0.0 starting at `start_beat`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_beat` | `float` | Beat to begin fading out |
| `duration` | `float` | Duration of the fade in beats |

```python
AutomationCurve.fade_out(24, 8)  # fade out from beat 24 to 32
```

#### `AutomationCurve.filter_sweep(start_beat: float, end_beat: float, start_freq: float, end_freq: float) -> AutomationCurve`

Exponential filter cutoff sweep between two frequencies.

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_beat` | `float` | Start beat |
| `end_beat` | `float` | End beat |
| `start_freq` | `float` | Starting cutoff frequency in Hz |
| `end_freq` | `float` | Ending cutoff frequency in Hz |

```python
AutomationCurve.filter_sweep(0, 16, 200.0, 8000.0)
```

#### `AutomationCurve.swell(peak_beat: float, peak_value: float = 1.0, start_value: float = 0.0) -> AutomationCurve`

Rise to `peak_beat` then fall back -- a crescendo-decrescendo shape. Uses smooth (cosine) interpolation. The swell ends at `peak_beat * 2`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `peak_beat` | `float` | *required* | Beat of the peak |
| `peak_value` | `float` | `1.0` | Value at the peak |
| `start_value` | `float` | `0.0` | Starting and ending value |

```python
AutomationCurve.swell(8, peak_value=0.9)  # swell peaking at beat 8, ending at beat 16
```

---

## AutomatableEffect

```python
class AutomatableEffect(AudioEffect)
```

Abstract base class for audio effects whose parameters can be automated over time. Subclasses define which parameters are automatable by reading from `_automations` in their `process()` method.

### Constructor

```python
AutomatableEffect()
```

Initializes an empty automation dictionary, default BPM of `120.0`, and start beat of `0.0`.

### Methods

#### `.automate(param_name: str, curve: AutomationCurve) -> AutomatableEffect`

Attach an automation curve to a named parameter. Returns `self` for chaining.

| Parameter | Type | Description |
|-----------|------|-------------|
| `param_name` | `str` | Name of the parameter to automate |
| `curve` | `AutomationCurve` | The automation curve to attach |

```python
gain = AutomatedGain(level=1.0)
gain.automate('level', AutomationCurve.fade_in(8))
```

#### `.set_context(bpm: float, start_beat: float = 0.0) -> None`

Set the temporal context for rendering automation. Must be called before `process()` if using non-default tempo.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bpm` | `float` | *required* | Song tempo |
| `start_beat` | `float` | `0.0` | Beat offset for this effect |

#### `.process(audio: AudioData) -> AudioData`

*Abstract method.* Subclasses must implement this to apply the effect to audio data.

---

## AutomatedGain

```python
class AutomatedGain(AutomatableEffect)
```

Gain effect with automatable level. Multiplies the audio signal by a gain value that can change over time.

**Automatable parameters:** `'level'`

### Constructor

```python
AutomatedGain(level: float = 1.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `float` | `1.0` | Default gain level (used when not automated) |

### Methods

#### `.process(audio: AudioData) -> AudioData`

Apply gain to the audio. If the `'level'` parameter is automated, the gain varies per sample. Supports both mono and stereo audio.

```python
gain = AutomatedGain(level=0.8)
gain.automate('level', AutomationCurve.fade_in(4))
gain.set_context(bpm=120)
output = gain.process(audio)
```

---

## AutomatedFilter

```python
class AutomatedFilter(AutomatableEffect)
```

Low-pass biquad filter with automatable cutoff frequency and resonance. Uses per-block coefficient updates (block size of 64 samples) for efficient time-varying filtering. Supports both mono and stereo audio.

**Automatable parameters:** `'cutoff'`, `'resonance'`

### Constructor

```python
AutomatedFilter(cutoff: float = 1000.0, resonance: float = 0.707)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cutoff` | `float` | `1000.0` | Default cutoff frequency in Hz (20 to Nyquist) |
| `resonance` | `float` | `0.707` | Default resonance / Q factor (0.1 to 10.0) |

### Methods

#### `.process(audio: AudioData) -> AudioData`

Apply the low-pass filter to the audio. Cutoff and resonance values are read per-block from automation curves if attached. Supports mono and stereo.

```python
filt = AutomatedFilter(cutoff=500.0, resonance=1.2)
filt.automate('cutoff', AutomationCurve.filter_sweep(0, 32, 200, 8000))
filt.set_context(bpm=128)
output = filt.process(audio)
```
