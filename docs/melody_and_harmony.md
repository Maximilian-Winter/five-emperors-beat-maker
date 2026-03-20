# Melody and Harmony API Reference

Complete API reference for the `beatmaker.melody`, `beatmaker.harmony`, and `beatmaker.music` modules. These modules provide first-class abstractions for melodic composition, harmonic context, chord progressions, scale definitions, and chord shapes.

**Module paths:**

- `beatmaker.melody` — `Note`, `Phrase`, `Melody`
- `beatmaker.harmony` — `Key`, `ChordEntry`, `ChordProgression`
- `beatmaker.music` — `Scale`, `ChordShape`, note/MIDI/frequency conversions

---

## Table of Contents

1. [Note](#note)
2. [Phrase](#phrase)
3. [Melody](#melody)
4. [Key](#key)
5. [ChordEntry](#chordentry)
6. [ChordProgression](#chordprogression)
7. [Scale](#scale)
8. [ChordShape](#chordshape)
9. [Composition Workflow Examples](#composition-workflow-examples)

---

## Note

```python
from beatmaker.melody import Note
```

A frozen dataclass representing a single musical note — the atom of melodic expression. Because the dataclass is frozen, all instances are immutable; transformation methods return new `Note` objects.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pitch` | `int` | *(required)* | MIDI note number (0--127). A value of `-1` denotes a rest. |
| `duration` | `float` | *(required)* | Duration in beats. |
| `velocity` | `float` | `1.0` | Velocity / dynamics, normalized to `0.0`--`1.0`. |

### Factory Methods

#### `Note.from_name(name, duration=1.0, velocity=1.0)`

Create a `Note` from a human-readable note name string.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *(required)* | Note name with octave, e.g. `"C4"`, `"F#3"`, `"Bb2"`. |
| `duration` | `float` | `1.0` | Duration in beats. |
| `velocity` | `float` | `1.0` | Velocity (0.0--1.0). |

```python
Note.from_name("C4")                # middle C, 1 beat, full velocity
Note.from_name("F#3", 0.5, 0.8)    # F#3, half beat, velocity 0.8
Note.from_name("Bb2", duration=2.0) # Bb2, 2 beats
```

#### `Note.rest(duration=1.0)`

Create a rest (silence) of the given duration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | `1.0` | Duration of silence in beats. |

```python
Note.rest()      # 1-beat rest
Note.rest(0.5)   # half-beat rest
```

### Properties

#### `is_rest -> bool`

Returns `True` if the note is a rest (pitch < 0).

#### `name -> str`

Returns the human-readable note name (e.g. `"C4"`, `"F#3"`). Returns `"R"` for rests.

### Transformation Methods

All transformations return a new `Note` (the original is unchanged).

#### `transpose(semitones) -> Note`

Return a copy transposed by the given number of semitones. Rests are returned unchanged. The resulting pitch is clamped to the valid MIDI range 0--127.

| Parameter | Type | Description |
|-----------|------|-------------|
| `semitones` | `int` | Number of semitones to shift (positive = up, negative = down). |

```python
Note.from_name("C4").transpose(7)   # -> G4
Note.from_name("C4").transpose(-12) # -> C3
```

#### `with_duration(duration) -> Note`

Return a copy with a different duration.

| Parameter | Type | Description |
|-----------|------|-------------|
| `duration` | `float` | New duration in beats. |

#### `with_velocity(velocity) -> Note`

Return a copy with a different velocity.

| Parameter | Type | Description |
|-----------|------|-------------|
| `velocity` | `float` | New velocity (0.0--1.0). |

---

## Phrase

```python
from beatmaker.melody import Phrase
```

A dataclass representing an ordered sequence of `Note` objects — a reusable melodic idea. Phrases are the primary unit of melodic composition. All transformation methods return new `Phrase` objects (immutable style).

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *(required)* | Identifier for the phrase. |
| `notes` | `List[Note]` | `[]` | Ordered list of notes in the phrase. |

### Factory Methods

#### `Phrase.from_string(notation, name="phrase")`

Parse concise melody notation into a `Phrase`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `notation` | `str` | *(required)* | Space-separated note tokens (see notation format below). |
| `name` | `str` | `"phrase"` | Name for the phrase. |

**Notation format:** `NoteName:Duration` or `NoteName:Duration:Velocity`

- Each token is a note name followed by an optional colon-separated duration (in beats) and velocity.
- Omit `:Duration` to default to 1 beat at full velocity.
- Use `R` or `r` for rests.

| Token | Meaning |
|-------|---------|
| `C4` | C4, 1 beat, velocity 1.0 |
| `C4:0.5` | C4, half beat, velocity 1.0 |
| `C4:0.5:0.7` | C4, half beat, velocity 0.7 |
| `R:2` | Rest, 2 beats |
| `R` | Rest, 1 beat |

```python
Phrase.from_string("C4:1 D4:0.5 E4:0.5 R:1 G4:2")
Phrase.from_string("E4 G4 A4 B4")           # all quarter notes (1 beat each)
Phrase.from_string("C4:0.5:0.6 E4:0.5:0.8") # with explicit velocities
```

#### `Phrase.from_notes(note_names, duration=1.0, name="phrase")`

Create a `Phrase` where all notes share the same duration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_names` | `List[str]` | *(required)* | List of note name strings. |
| `duration` | `float` | `1.0` | Shared duration in beats. |
| `name` | `str` | `"phrase"` | Name for the phrase. |

```python
Phrase.from_notes(["C4", "E4", "G4"], duration=0.5)
```

#### `Phrase.from_midi_tuples(tuples, name="phrase")`

Create a `Phrase` from raw MIDI data tuples.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tuples` | `List[tuple]` | *(required)* | List of `(midi_note, duration_beats)` or `(midi_note, duration_beats, velocity)` tuples. Use a negative `midi_note` for rests. |
| `name` | `str` | `"phrase"` | Name for the phrase. |

```python
Phrase.from_midi_tuples([(60, 1.0), (64, 0.5, 0.8), (-1, 1.0)])
```

### Properties

#### `total_duration -> float`

Total duration in beats (sum of all note durations, including rests).

#### `pitches -> List[int]`

List of MIDI pitch values for sounding notes only (rests are excluded).

#### `__len__() -> int`

Number of notes (including rests) in the phrase.

### Transformation Methods

All transformations return a new `Phrase`.

#### `transpose(semitones) -> Phrase`

Transpose all notes by the given number of semitones. Rests pass through unchanged. The resulting phrase name is suffixed with `_t+N` or `_t-N`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `semitones` | `int` | Semitones to shift (positive = up, negative = down). |

```python
motif = Phrase.from_string("C4 E4 G4")
motif.transpose(5)   # -> F4 A4 C5
motif.transpose(-2)  # -> Bb3 D4 F4
```

#### `reverse() -> Phrase`

Reverse the order of notes. Name is suffixed with `_rev`.

```python
motif = Phrase.from_string("C4 D4 E4")
motif.reverse()  # -> E4 D4 C4
```

#### `invert(axis=None) -> Phrase`

Melodic inversion — mirror pitches around an axis. Rests are preserved unchanged. Name is suffixed with `_inv`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `axis` | `Optional[int]` | `None` | MIDI pitch to invert around. If `None`, the first sounding note's pitch is used. |

```python
motif = Phrase.from_string("C4 E4 G4")
motif.invert()      # invert around C4 (MIDI 60) -> C4 Ab3 F3
motif.invert(64)    # invert around E4 (MIDI 64) -> E4 C4 Ab3
```

#### `retrograde_invert(axis=None) -> Phrase`

Reverse + invert — a classic serial composition technique. Equivalent to `self.reverse().invert(axis)`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `axis` | `Optional[int]` | `None` | Inversion axis (see `invert`). |

#### `augment(factor=2.0) -> Phrase`

Multiply all note durations by `factor` (rhythmic augmentation / slow down). Name is suffixed with `_aug`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | `float` | `2.0` | Duration multiplier. |

```python
Phrase.from_string("C4:1 E4:1").augment()     # durations become 2.0
Phrase.from_string("C4:1 E4:1").augment(1.5)  # durations become 1.5
```

#### `diminish(factor=2.0) -> Phrase`

Divide all note durations by `factor` (rhythmic diminution / speed up). Equivalent to `self.augment(1.0 / factor)`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | `float` | `2.0` | Duration divisor. |

```python
Phrase.from_string("C4:2 E4:2").diminish()   # durations become 1.0
```

#### `with_velocity(velocity) -> Phrase`

Set a uniform velocity for all sounding notes. Rests are left unchanged.

| Parameter | Type | Description |
|-----------|------|-------------|
| `velocity` | `float` | Velocity value (0.0--1.0). |

#### `with_velocity_curve(curve) -> Phrase`

Apply a velocity curve across all sounding notes. The `curve` list is linearly interpolated to match the number of sounding notes in the phrase.

| Parameter | Type | Description |
|-----------|------|-------------|
| `curve` | `List[float]` | Velocity control points (0.0--1.0). Values are clamped to this range. |

```python
phrase = Phrase.from_string("C4 D4 E4 F4 G4 A4 B4 C5")
phrase.with_velocity_curve([0.3, 1.0, 0.3])  # crescendo then decrescendo
phrase.with_velocity_curve([0.5, 1.0])        # gradual crescendo
```

#### `repeat(times) -> Phrase`

Repeat the phrase sequentially. Name is suffixed with `_xN`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `times` | `int` | Number of repetitions. |

```python
Phrase.from_string("C4 E4 G4").repeat(4)  # play the arpeggio 4 times
```

### Combination Methods

#### `then(other) -> Phrase`

Concatenate two phrases: play `self`, then `other` sequentially. The resulting name is `"self_name+other_name"`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `other` | `Phrase` | Phrase to append. |

#### `__add__(other) -> Phrase`

Operator overload for sequential combination. `phrase_a + phrase_b` is equivalent to `phrase_a.then(phrase_b)`.

```python
verse = Phrase.from_string("C4 D4 E4 F4", name="verse")
chorus = Phrase.from_string("G4 A4 B4 C5", name="chorus")
full = verse + chorus  # or verse.then(chorus)
```

### Event Conversion

#### `to_events(start_beat=0.0) -> List[Tuple[float, int, float, float]]`

Convert the phrase to a list of renderable events. Rests are omitted from the output (they advance the beat cursor but produce no event).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | `0.0` | Beat position where the phrase begins. |

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples.

```python
events = Phrase.from_string("C4:1 R:0.5 E4:0.5").to_events(start_beat=4.0)
# [(4.0, 60, 1.0, 1.0), (5.5, 64, 1.0, 0.5)]
```

---

## Melody

```python
from beatmaker.melody import Melody
```

A container that places `Phrase` objects at specific beat positions along a timeline. This is the top-level structure for building complete melodies from reusable phrases.

### Constructor

```python
Melody(name: str = "melody")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"melody"` | Identifier for the melody. |

### Methods

#### `add(phrase, start_beat=None) -> Melody`

Add a phrase at a specific beat position. Returns `self` for method chaining.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `phrase` | `Phrase` | *(required)* | The phrase to place. |
| `start_beat` | `Optional[float]` | `None` | Beat position. If `None`, the phrase is appended immediately after the last entry ends (auto-sequencing). |

```python
mel = Melody("lead")
mel.add(intro, start_beat=0.0)
mel.add(verse)       # auto-appended at end of intro
mel.add(fill, start_beat=8.0)  # explicit placement (can overlap)
```

#### `add_sequence(phrases) -> Melody`

Add multiple phrases end-to-end in sequential order. Returns `self` for method chaining.

| Parameter | Type | Description |
|-----------|------|-------------|
| `phrases` | `List[Phrase]` | Phrases to append one after another. |

```python
mel = Melody()
mel.add_sequence([verse, chorus, verse, chorus, bridge, chorus])
```

### Properties

#### `total_duration -> float`

Total duration in beats (the latest end-point across all placed phrases).

#### `entries -> List[Tuple[float, Phrase]]`

List of `(start_beat, Phrase)` entries. Returns a copy of the internal list.

### Event Conversion

#### `to_events() -> List[Tuple[float, int, float, float]]`

Convert the entire melody to a flat event list, sorted by beat position. Phrases placed at overlapping beat positions will produce interleaved events.

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples.

---

## Key

```python
from beatmaker.harmony import Key
```

A dataclass representing a musical key — the harmonic context for composition. Provides scale degree access, diatonic chord construction, modulation, and diatonic membership tests.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `root` | `str` | Root note name (e.g. `"C"`, `"F#"`, `"Bb"`). |
| `scale` | `Scale` | The scale type (e.g. `Scale.MAJOR`). |

### Factory Methods

All factory methods take a single `root: str` parameter and return a `Key`.

| Method | Scale | Example |
|--------|-------|---------|
| `Key.major(root)` | Major (Ionian) | `Key.major("C")` |
| `Key.minor(root)` | Natural Minor (Aeolian) | `Key.minor("A")` |
| `Key.harmonic_minor(root)` | Harmonic Minor | `Key.harmonic_minor("A")` |
| `Key.melodic_minor(root)` | Melodic Minor (ascending) | `Key.melodic_minor("D")` |
| `Key.dorian(root)` | Dorian | `Key.dorian("D")` |
| `Key.mixolydian(root)` | Mixolydian | `Key.mixolydian("G")` |
| `Key.pentatonic_minor(root)` | Minor Pentatonic | `Key.pentatonic_minor("A")` |
| `Key.pentatonic_major(root)` | Major Pentatonic | `Key.pentatonic_major("C")` |
| `Key.blues(root)` | Blues | `Key.blues("E")` |

### Scale Degree Access

#### `degree(degree, octave=4) -> int`

Get the MIDI note number for a 1-indexed scale degree in a given octave. Degrees above the scale length wrap into higher octaves.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `degree` | `int` | *(required)* | 1-indexed scale degree. |
| `octave` | `int` | `4` | Base octave. |

```python
key = Key.major("C")
key.degree(1, 4)  # 60 (C4, middle C)
key.degree(5, 4)  # 67 (G4)
key.degree(8, 4)  # 72 (C5, one octave up)
```

#### `degree_pc(degree) -> int`

Get the pitch class (0--11) for a 1-indexed scale degree.

| Parameter | Type | Description |
|-----------|------|-------------|
| `degree` | `int` | 1-indexed scale degree. |

```python
Key.major("C").degree_pc(5)  # 7 (G)
Key.major("C").degree_pc(3)  # 4 (E)
```

#### `root_pc -> int` *(property)*

Root pitch class (0--11).

#### `scale_notes(octave=4) -> List[int]`

All MIDI notes in the key for a single octave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `octave` | `int` | `4` | Octave to generate. |

```python
Key.major("C").scale_notes(4)  # [60, 62, 64, 65, 67, 69, 71]
```

#### `scale_notes_range(low_octave=3, high_octave=5) -> List[int]`

All MIDI notes in the key across a range of octaves, sorted and deduplicated.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `low_octave` | `int` | `3` | Lowest octave (inclusive). |
| `high_octave` | `int` | `5` | Highest octave (inclusive). |

### Diatonic Chord Methods

#### `chord(degree, extensions=3, octave=4) -> Tuple[int, ChordShape]`

Get a diatonic chord built on a scale degree.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `degree` | `int` | *(required)* | 1-indexed scale degree. |
| `extensions` | `int` | `3` | `3` for triad, `4` for seventh chord. |
| `octave` | `int` | `4` | Base octave for the chord root. |

**Returns:** `(root_midi, ChordShape)` tuple.

```python
key = Key.major("C")
root, shape = key.chord(1)    # C major triad
root, shape = key.chord(2, extensions=4)  # D minor 7th
```

#### `chord_name(degree) -> str`

Human-readable chord name for a diatonic degree. Uses flats or sharps based on the key's root note convention.

| Parameter | Type | Description |
|-----------|------|-------------|
| `degree` | `int` | 1-indexed scale degree. |

```python
key = Key.major("C")
key.chord_name(1)  # "C"
key.chord_name(2)  # "Dm"
key.chord_name(7)  # "Bdim"

key = Key.major("F")
key.chord_name(4)  # "Bb"
```

### Diatonic Membership

#### `is_diatonic(midi_note) -> bool`

Check whether a MIDI note belongs to this key.

| Parameter | Type | Description |
|-----------|------|-------------|
| `midi_note` | `int` | MIDI note number. |

```python
key = Key.major("C")
key.is_diatonic(60)  # True  (C)
key.is_diatonic(61)  # False (C#)
```

#### `nearest_diatonic(midi_note) -> int`

Snap a MIDI note to the nearest diatonic pitch. Tries offsets of +/-1 then +/-2 semitones.

| Parameter | Type | Description |
|-----------|------|-------------|
| `midi_note` | `int` | MIDI note number. |

### Modulation Methods

All modulation methods return a new `Key`.

#### `modulate(new_root, new_scale=None) -> Key`

Return a new key modulated to a different root. If `new_scale` is `None`, the current scale type is preserved.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `new_root` | `str` | *(required)* | New root note name. |
| `new_scale` | `Optional[Scale]` | `None` | New scale type, or keep the same. |

```python
Key.major("C").modulate("G")                    # G major
Key.major("C").modulate("A", Scale.MINOR)       # A minor
```

#### `relative_minor() -> Key`

Return the relative minor of a major key (down a minor 3rd / degree vi).

```python
Key.major("C").relative_minor()  # Key(A minor)
```

#### `relative_major() -> Key`

Return the relative major of a minor key (up a minor 3rd / degree III).

```python
Key.minor("A").relative_major()  # Key(C major)
```

#### `parallel_minor() -> Key`

Same root, minor scale.

```python
Key.major("C").parallel_minor()  # Key(C minor)
```

#### `parallel_major() -> Key`

Same root, major scale.

```python
Key.minor("C").parallel_major()  # Key(C major)
```

---

## ChordEntry

```python
from beatmaker.harmony import ChordEntry
```

A dataclass representing a single chord in a progression.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `degree` | `int` | 1-indexed scale degree of the chord root. |
| `shape` | `ChordShape` | The chord's interval structure. |
| `root_midi` | `int` | MIDI note number of the chord root. |
| `duration_beats` | `float` | How long the chord lasts in beats. |

### Properties

#### `midi_notes -> List[int]`

List of MIDI note numbers for all notes in the chord (root + intervals applied).

```python
entry = ChordEntry(degree=1, shape=ChordShape.MAJOR, root_midi=48, duration_beats=4.0)
entry.midi_notes  # [48, 52, 55]  (C3, E3, G3)
```

---

## ChordProgression

```python
from beatmaker.harmony import ChordProgression
```

A dataclass representing a sequence of chords in a key. Supports Roman numeral parsing, preset progressions, voice leading, and event conversion.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `key` | `Key` | *(required)* | The harmonic context. |
| `chords` | `List[ChordEntry]` | `[]` | Ordered list of chord entries. |

### Factory Methods

#### `ChordProgression.from_roman(key, numerals, beats_per_chord=4.0, octave=3)`

Parse a chord progression from Roman numeral notation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Key` | *(required)* | The key context. |
| `numerals` | `str` | *(required)* | Roman numeral string (see notation below). |
| `beats_per_chord` | `float` | `4.0` | Duration of each chord in beats. |
| `octave` | `int` | `3` | Base octave for chord roots. |

**Roman numeral notation:**

Numerals are separated by ` - ` (space-dash-space) or whitespace.

| Convention | Meaning | Example |
|------------|---------|---------|
| Uppercase | Major triad | `I`, `IV`, `V` |
| Lowercase | Minor triad | `ii`, `iii`, `vi` |
| `dim` suffix | Diminished triad | `viidim` |
| `aug` suffix | Augmented triad | `IIIaug` |
| `sus2` / `sus4` suffix | Suspended chord | `Isus4` |
| `7` suffix | Seventh chord (dominant if major, minor 7 if minor, dim 7 if dim) | `V7`, `ii7` |
| `maj7` suffix | Major seventh | `Imaj7` |
| `9`, `11`, `13` suffix | Extended chords | `V9`, `ii11` |
| `b` / `#` prefix | Accidental on the root | `bVII`, `#IV` |

```python
key = Key.major("C")

# Basic progressions
ChordProgression.from_roman(key, "I - IV - V - I")
ChordProgression.from_roman(key, "I - V - vi - IV")       # pop
ChordProgression.from_roman(key, "ii7 - V7 - Imaj7")     # jazz ii-V-I

# Custom timing
ChordProgression.from_roman(key, "I - IV - V", beats_per_chord=2.0)
```

#### `ChordProgression.from_degrees(key, degrees, beats_per_chord=4.0, octave=3)`

Create from a list of 1-indexed scale degree numbers. All chords are built as diatonic triads.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `Key` | *(required)* | The key context. |
| `degrees` | `List[int]` | *(required)* | List of scale degree numbers. |
| `beats_per_chord` | `float` | `4.0` | Duration of each chord. |
| `octave` | `int` | `3` | Base octave. |

```python
ChordProgression.from_degrees(Key.major("G"), [1, 5, 6, 4])
```

### Preset Progressions

All presets take `(key: Key, beats_per_chord: float = 4.0)` and return a `ChordProgression`.

| Method | Progression | Description |
|--------|------------|-------------|
| `ChordProgression.pop(key)` | I - V - vi - IV | Ubiquitous pop progression |
| `ChordProgression.blues(key)` | I I I I - IV IV I I - V IV I V | 12-bar blues |
| `ChordProgression.jazz_ii_v_i(key)` | ii7 - V7 - Imaj7 | Jazz ii-V-I |
| `ChordProgression.andalusian(key)` | i - VII - VI - V | Flamenco / Andalusian cadence |
| `ChordProgression.canon(key)` | I - V - vi - iii - IV - I - IV - V | Pachelbel's Canon |
| `ChordProgression.fifties(key)` | I - vi - IV - V | 1950s doo-wop progression |

```python
prog = ChordProgression.pop(Key.major("G"))
prog = ChordProgression.jazz_ii_v_i(Key.major("Bb"), beats_per_chord=2.0)
```

### Properties

#### `total_duration -> float`

Total duration in beats (sum of all chord durations).

#### `__len__() -> int`

Number of chords in the progression.

### Voice Leading

#### `voice_lead(num_voices=4, base_octave=3) -> List[List[int]]`

Generate voice-led MIDI notes for each chord. Uses minimal movement: each voice moves to the nearest available chord tone. The first chord is arranged in close position.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_voices` | `int` | `4` | Number of voices / parts. |
| `base_octave` | `int` | `3` | Starting octave for the first chord voicing. |

**Returns:** List of chords, each a sorted list of MIDI note numbers.

```python
prog = ChordProgression.pop(Key.major("C"))
voicings = prog.voice_lead(num_voices=4)
# Each chord is a list of 4 MIDI notes with smooth transitions
```

### Conversion Methods

#### `to_arp_progression() -> List[Tuple[str, ChordShape]]`

Convert to format compatible with `Arpeggiator.generate_from_progression()`.

**Returns:** List of `(root_note_name, ChordShape)` tuples.

#### `to_events(start_beat=0.0, voice_led=False, num_voices=4) -> List[Tuple[float, int, float, float]]`

Convert to renderable note events.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_beat` | `float` | `0.0` | Beat position where the progression starts. |
| `voice_led` | `bool` | `False` | If `True`, uses voice leading for smooth transitions. |
| `num_voices` | `int` | `4` | Number of voices (only used when `voice_led=True`). |

**Returns:** List of `(beat, midi_note, velocity, duration_beats)` tuples. Velocity is fixed at `0.8` for all chord events.

---

## Scale

```python
from beatmaker.music import Scale
```

A dataclass defining a musical scale by its interval pattern.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable scale name. |
| `intervals` | `List[int]` | Semitone offsets from the root (always starts with `0`). |

### Built-in Scales

| Constant | Name | Intervals |
|----------|------|-----------|
| `Scale.MAJOR` | `"major"` | `[0, 2, 4, 5, 7, 9, 11]` |
| `Scale.MINOR` | `"minor"` | `[0, 2, 3, 5, 7, 8, 10]` |
| `Scale.DORIAN` | `"dorian"` | `[0, 2, 3, 5, 7, 9, 10]` |
| `Scale.PHRYGIAN` | `"phrygian"` | `[0, 1, 3, 5, 7, 8, 10]` |
| `Scale.LYDIAN` | `"lydian"` | `[0, 2, 4, 6, 7, 9, 11]` |
| `Scale.MIXOLYDIAN` | `"mixolydian"` | `[0, 2, 4, 5, 7, 9, 10]` |
| `Scale.LOCRIAN` | `"locrian"` | `[0, 1, 3, 5, 6, 8, 10]` |
| `Scale.MINOR_PENTATONIC` | `"minor_pent"` | `[0, 3, 5, 7, 10]` |
| `Scale.MAJOR_PENTATONIC` | `"major_pent"` | `[0, 2, 4, 7, 9]` |
| `Scale.BLUES` | `"blues"` | `[0, 3, 5, 6, 7, 10]` |
| `Scale.HARMONIC_MINOR` | `"harmonic_minor"` | `[0, 2, 3, 5, 7, 8, 11]` |
| `Scale.MELODIC_MINOR` | `"melodic_minor"` | `[0, 2, 3, 5, 7, 9, 11]` |

### Methods

#### `get_notes(root_midi, octaves=1) -> List[int]`

Get MIDI note numbers for the scale starting from a given root.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root_midi` | `int` | *(required)* | MIDI note number of the root. |
| `octaves` | `int` | `1` | Number of octaves to span. |

**Returns:** List of MIDI note numbers.

```python
Scale.MAJOR.get_notes(60, octaves=1)
# [60, 62, 64, 65, 67, 69, 71]

Scale.BLUES.get_notes(40, octaves=2)
# [40, 43, 45, 46, 47, 50, 52, 55, 57, 58, 59, 62]
```

You can also create custom scales:

```python
whole_tone = Scale("whole_tone", [0, 2, 4, 6, 8, 10])
whole_tone.get_notes(60)  # [60, 62, 64, 66, 68, 70]
```

---

## ChordShape

```python
from beatmaker.music import ChordShape
```

A dataclass defining a chord by its interval structure from the root.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable chord shape name. |
| `intervals` | `List[int]` | Semitone offsets from root (always starts with `0`). |

### Built-in Chord Shapes

| Constant | Name | Intervals | Description |
|----------|------|-----------|-------------|
| `ChordShape.MAJOR` | `"major"` | `[0, 4, 7]` | Major triad |
| `ChordShape.MINOR` | `"minor"` | `[0, 3, 7]` | Minor triad |
| `ChordShape.DIM` | `"dim"` | `[0, 3, 6]` | Diminished triad |
| `ChordShape.AUG` | `"aug"` | `[0, 4, 8]` | Augmented triad |
| `ChordShape.SUS2` | `"sus2"` | `[0, 2, 7]` | Suspended 2nd |
| `ChordShape.SUS4` | `"sus4"` | `[0, 5, 7]` | Suspended 4th |
| `ChordShape.MAJOR7` | `"maj7"` | `[0, 4, 7, 11]` | Major 7th |
| `ChordShape.MINOR7` | `"min7"` | `[0, 3, 7, 10]` | Minor 7th |
| `ChordShape.DOM7` | `"dom7"` | `[0, 4, 7, 10]` | Dominant 7th |
| `ChordShape.ADD9` | `"add9"` | `[0, 4, 7, 14]` | Add 9 |
| `ChordShape.DIM7` | `"dim7"` | `[0, 3, 6, 9]` | Diminished 7th |
| `ChordShape.HALF_DIM7` | `"half_dim7"` | `[0, 3, 6, 10]` | Half-diminished 7th |
| `ChordShape.MAJ9` | `"maj9"` | `[0, 4, 7, 11, 14]` | Major 9th |
| `ChordShape.MIN9` | `"min9"` | `[0, 3, 7, 10, 14]` | Minor 9th |
| `ChordShape.DOM9` | `"dom9"` | `[0, 4, 7, 10, 14]` | Dominant 9th |
| `ChordShape.ADD11` | `"add11"` | `[0, 4, 7, 17]` | Add 11 |
| `ChordShape.MAJ13` | `"maj13"` | `[0, 4, 7, 11, 14, 21]` | Major 13th |

### Factory Methods

#### `ChordShape.custom(name, intervals) -> ChordShape`

Create a custom chord shape from arbitrary semitone intervals.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name for the chord shape. |
| `intervals` | `list` | List of semitone intervals from root. |

```python
quartal = ChordShape.custom("quartal", [0, 5, 10, 15])
mu_chord = ChordShape.custom("mu", [0, 2, 4, 7])
```

---

## Composition Workflow Examples

### Building a Melody from Phrases

```python
from beatmaker.melody import Note, Phrase, Melody

# Define motifs
motif_a = Phrase.from_string("C4:1 E4:0.5 G4:0.5 C5:2", name="motif_a")
motif_b = Phrase.from_string("B4:1 A4:1 G4:1 R:1", name="motif_b")

# Transform and combine
melody = Melody("lead_line")
melody.add(motif_a)                          # beats 0-4
melody.add(motif_a.transpose(5))             # beats 4-8, up a 4th
melody.add(motif_b)                          # beats 8-12
melody.add(motif_a.reverse().with_velocity(0.7))  # beats 12-16, softer

events = melody.to_events()  # ready for rendering
```

### Chord Progression with Voice Leading

```python
from beatmaker.harmony import Key, ChordProgression

key = Key.major("C")
prog = ChordProgression.from_roman(key, "I - V - vi - IV", beats_per_chord=4.0)

# Smooth voice-led rendering
events = prog.to_events(voice_led=True, num_voices=4)

# Or convert for use with an arpeggiator
arp_data = prog.to_arp_progression()
```

### Key-Aware Melody Construction

```python
from beatmaker.harmony import Key
from beatmaker.melody import Note, Phrase

key = Key.minor("A")

# Build a phrase from scale degrees
notes = [Note(pitch=key.degree(d, 4), duration=0.5) for d in [1, 3, 4, 5, 7, 8]]
scale_run = Phrase(name="minor_run", notes=notes)

# Check if notes fit the key
for event in scale_run.to_events():
    beat, midi, vel, dur = event
    assert key.is_diatonic(midi)
```

### Modulation Between Keys

```python
from beatmaker.harmony import Key, ChordProgression
from beatmaker.melody import Phrase, Melody

key_c = Key.major("C")
key_g = Key.major("G")

verse_chords = ChordProgression.from_roman(key_c, "I - vi - IV - V")
chorus_chords = ChordProgression.from_roman(key_g, "I - IV - V - I")

# Melody that modulates
verse_mel = Phrase.from_string("C4 E4 G4 A4", name="verse")
chorus_mel = verse_mel.transpose(7)  # shift up to G major territory
```

### Using Velocity Curves for Expression

```python
from beatmaker.melody import Phrase

phrase = Phrase.from_string(
    "C4:0.5 D4:0.5 E4:0.5 F4:0.5 G4:0.5 A4:0.5 B4:0.5 C5:0.5",
    name="ascending"
)

# Crescendo
loud = phrase.with_velocity_curve([0.3, 1.0])

# Accent pattern (strong-weak-medium-weak)
accented = phrase.with_velocity_curve([1.0, 0.4, 0.7, 0.4])
```

### Serial Techniques

```python
from beatmaker.melody import Phrase, Melody

row = Phrase.from_string("C4 Db4 F4 E4 Ab4 G4 Bb4 A4 D5 Eb5 B4 Gb4", name="row")

melody = Melody("twelve_tone")
melody.add_sequence([
    row,                          # prime
    row.reverse(),                # retrograde
    row.invert(),                 # inversion
    row.retrograde_invert(),      # retrograde inversion
])
```

### Preset Progressions

```python
from beatmaker.harmony import Key, ChordProgression

key = Key.major("G")

pop     = ChordProgression.pop(key)             # I - V - vi - IV
blues   = ChordProgression.blues(key)           # 12-bar blues
jazz    = ChordProgression.jazz_ii_v_i(key)     # ii7 - V7 - Imaj7
flam    = ChordProgression.andalusian(Key.minor("E"))  # i - VII - VI - V
pachel  = ChordProgression.canon(key)           # Pachelbel's Canon
doowop  = ChordProgression.fifties(key)         # I - vi - IV - V
```
