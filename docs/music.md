# Music Theory Utilities API Reference

**Module:** `beatmaker.music`

*New in v0.4.0*

This module centralizes music theory primitives that were previously scattered across `synth.py`, `arpeggiator.py`, and `melody.py`. It provides a single source of truth for note/MIDI/frequency conversions, scale definitions, and chord shapes.

All symbols are also re-exported from the top-level `beatmaker` package.

---

## Functions

### `note_name_to_midi(note: str) -> int`

Convert a note name to its MIDI number.

```python
from beatmaker.music import note_name_to_midi

note_name_to_midi('C4')   # 60
note_name_to_midi('A4')   # 69
note_name_to_midi('F#3')  # 54
note_name_to_midi('Bb2')  # 46
```

- **note**: Note name string, e.g. `'C4'`, `'F#3'`, `'Bb2'`. Supports sharps (`#`) and flats (`b`).
- **Returns**: MIDI note number (int).

---

### `midi_to_note_name(midi_note: int) -> str`

Convert a MIDI note number to its note name.

```python
from beatmaker.music import midi_to_note_name

midi_to_note_name(60)  # 'C4'
midi_to_note_name(69)  # 'A4'
```

- **midi_note**: MIDI note number (0-127).
- **Returns**: Note name string with octave, e.g. `'C4'`.

---

### `midi_to_freq(midi_note: int) -> float`

Convert a MIDI note number to frequency in Hz (A4 = 440 Hz).

```python
from beatmaker.music import midi_to_freq

midi_to_freq(69)  # 440.0
midi_to_freq(60)  # 261.63 (approximately)
```

---

### `freq_to_midi(frequency: float) -> int`

Convert a frequency in Hz to the nearest MIDI note number.

```python
from beatmaker.music import freq_to_midi

freq_to_midi(440.0)  # 69
freq_to_midi(261.6)  # 60
```

---

### `note_to_freq(note: str) -> float`

Convert a note name directly to frequency in Hz.

```python
from beatmaker.music import note_to_freq

note_to_freq('A4')  # 440.0
note_to_freq('C3')  # 130.81
```

---

## `NOTE_FREQS`

Dictionary mapping note letter names to lists of frequencies across octaves 0-7.

```python
from beatmaker.music import NOTE_FREQS

NOTE_FREQS['A']  # [27.5, 55.0, 110.0, 220.0, 440.0, 880.0, 1760.0, 3520.0]
NOTE_FREQS['C'][4]  # 261.63 (Middle C)
```

---

## Scale

A dataclass representing a musical scale.

### Constructor

```python
Scale(name: str, intervals: List[int])
```

- **name**: Human-readable scale name.
- **intervals**: List of semitone intervals from root.

### Methods

#### `.get_notes(root_midi: int, octaves: int = 1) -> List[int]`

Get MIDI note numbers for the scale starting from a root note.

```python
from beatmaker.music import Scale, note_name_to_midi

root = note_name_to_midi('C4')  # 60
Scale.MAJOR.get_notes(root)     # [60, 62, 64, 65, 67, 69, 71]
Scale.MINOR.get_notes(root, octaves=2)  # Two octaves of C minor
```

### Built-in Scales

| Constant | Intervals |
|---|---|
| `Scale.MAJOR` | `[0, 2, 4, 5, 7, 9, 11]` |
| `Scale.MINOR` | `[0, 2, 3, 5, 7, 8, 10]` |
| `Scale.DORIAN` | `[0, 2, 3, 5, 7, 9, 10]` |
| `Scale.PHRYGIAN` | `[0, 1, 3, 5, 7, 8, 10]` |
| `Scale.LYDIAN` | `[0, 2, 4, 6, 7, 9, 11]` |
| `Scale.MIXOLYDIAN` | `[0, 2, 4, 5, 7, 9, 10]` |
| `Scale.LOCRIAN` | `[0, 1, 3, 5, 6, 8, 10]` |
| `Scale.MINOR_PENTATONIC` | `[0, 3, 5, 7, 10]` |
| `Scale.MAJOR_PENTATONIC` | `[0, 2, 4, 7, 9]` |
| `Scale.BLUES` | `[0, 3, 5, 6, 7, 10]` |
| `Scale.HARMONIC_MINOR` | `[0, 2, 3, 5, 7, 8, 11]` |
| `Scale.MELODIC_MINOR` | `[0, 2, 3, 5, 7, 9, 11]` |

---

## ChordShape

A dataclass defining a chord by its intervals from the root.

### Constructor

```python
ChordShape(name: str, intervals: List[int])
```

- **name**: Human-readable chord name.
- **intervals**: List of semitone intervals from root.

### Built-in Chord Shapes

| Constant | Name | Intervals |
|---|---|---|
| `ChordShape.MAJOR` | `major` | `[0, 4, 7]` |
| `ChordShape.MINOR` | `minor` | `[0, 3, 7]` |
| `ChordShape.DIM` | `dim` | `[0, 3, 6]` |
| `ChordShape.AUG` | `aug` | `[0, 4, 8]` |
| `ChordShape.SUS2` | `sus2` | `[0, 2, 7]` |
| `ChordShape.SUS4` | `sus4` | `[0, 5, 7]` |
| `ChordShape.MAJOR7` | `maj7` | `[0, 4, 7, 11]` |
| `ChordShape.MINOR7` | `min7` | `[0, 3, 7, 10]` |
| `ChordShape.DOM7` | `dom7` | `[0, 4, 7, 10]` |
| `ChordShape.ADD9` | `add9` | `[0, 4, 7, 14]` |
| `ChordShape.DIM7` | `dim7` | `[0, 3, 6, 9]` |
| `ChordShape.HALF_DIM7` | `half_dim7` | `[0, 3, 6, 10]` |
| `ChordShape.MAJ9` | `maj9` | `[0, 4, 7, 11, 14]` |
| `ChordShape.MIN9` | `min9` | `[0, 3, 7, 10, 14]` |
| `ChordShape.DOM9` | `dom9` | `[0, 4, 7, 10, 14]` |
| `ChordShape.ADD11` | `add11` | `[0, 4, 7, 17]` |
| `ChordShape.MAJ13` | `maj13` | `[0, 4, 7, 11, 14, 21]` |

### Class Method

#### `ChordShape.custom(name: str, intervals: list) -> ChordShape`

Create a custom chord shape from arbitrary semitone intervals.

```python
power_chord = ChordShape.custom("power", [0, 7, 12])
```
