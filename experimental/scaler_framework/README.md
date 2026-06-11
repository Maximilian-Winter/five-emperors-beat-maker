# Scaler Framework

A Python music theory toolkit inspired by Scaler 2/3. Detects keys and chords from MIDI or audio, suggests chord progressions, generates melodies, voices chords in 12 styles, and builds MPC-style key groups from samples.

## Install

```
pip install numpy mido librosa soundfile
```

## Quick Start

```python
from scaler_framework import ScalerSession

session = ScalerSession()
session.set_key(0, "major")                          # C major
session.set_progression("Cmaj7 | Am7 | Dm7 | G7")
session.generate_melody()
session.melody.print_ascii(session.progression)
session.export_midi("output.mid")
```

## Pipeline

The framework follows a four-stage pipeline: **Detect -> Suggest -> Generate -> Export**.

### 1. Detect

Detect key and chords from MIDI or audio files:

```python
session = ScalerSession()
session.detect_from_midi("song.mid")
# or
session.detect_from_audio("song.wav")

print(session.key)               # C major (92%)
print(session.detected_chords)   # [Cmaj7, Am7, ...]
```

Or set the key manually:

```python
session.set_key(9, "natural_minor")  # A minor
```

### 2. Suggest

Get chord suggestions based on functional harmony rules and Markov chain analysis:

```python
suggestions = session.suggest_next_chord(["I", "V", "vi"])
for s in suggestions:
    print(s)
# IV (Fmaj)  score: 1.00 -- Common pop movement
# ii (Dmin)  score: 0.76 -- Circle of fifths motion
```

Generate a full progression automatically:

```python
session.generate_progression(length=8, temperature=0.5)
print(session.progression)  # G | C | Em | D | G | Am | C | D
```

### 3. Generate

#### Melodies

Four generation strategies:

```python
from scaler_framework import GeneratorConfig, GenerationStrategy

config = GeneratorConfig(
    strategy=GenerationStrategy.HYBRID,  # or RULE_BASED, MARKOV, CONTOUR
    rhythm_pattern="syncopated_2",       # or mixed_1, dotted, eighth_notes, ...
    contour_shape="arch",                # or wave, question, ascending, ...
    pitch_range=(60, 84),
    seed=42,                             # reproducible output
)
session.generate_melody(config=config)
session.melody.print_ascii(session.progression)
```

#### Voicings

12 chord voicing styles with automatic voice leading:

```python
from scaler_framework import VoicingEngine, VoicingStyle, Chord

engine = VoicingEngine()
chord = Chord.from_string("Cmaj7")

for style in [VoicingStyle.CLOSE, VoicingStyle.DROP_2, VoicingStyle.SHELL, VoicingStyle.PAD]:
    vc = engine.voice(chord, style=style, octave=4)
    print(f"{style.value:>8}: {', '.join(vc.note_names)}")
#    close: C4, E4, G4, B4
#   drop_2: G3, C4, E4, B4
#    shell: C3, E4, B4
#      pad: C3, E3, G3, B3, C4, E4, G4, B4, C5, E5, G5, B5
```

Voice a full progression with smooth voice leading:

```python
voiced = session.voice_progression(style=VoicingStyle.DROP_2, voice_lead=True)
for vc in voiced:
    print(f"{vc.chord.name:>8}: {', '.join(vc.note_names)}")
```

### 4. Export

```python
# MIDI (chords use voicing engine)
session.export_midi("output.mid", voicing_style=VoicingStyle.OPEN)

# Audio via key groups (see below)
session.export_audio("output.wav")
```

## Key Groups (MPC-style)

Take a sample, detect its pitch, and build a playable scale instrument:

```python
session = ScalerSession()
session.set_key(0, "major")
session.create_key_group("piano_c4.wav", octave_range=(3, 5))
```

This creates a `.keygroup/` directory with pitched WAV files and a JSON manifest:

```
piano_c4.keygroup/
  manifest.json
  samples/
    C3.wav, D3.wav, E3.wav, ...
```

Load it back later and render melodies to audio:

```python
session.load_key_group("piano_c4.keygroup")
session.set_progression("C | Am | F | G")
session.generate_melody()
session.export_audio("rendered.wav")
```

## CLI

```
python -m scaler_framework demo
python -m scaler_framework detect song.mid
python -m scaler_framework detect song.wav --json
python -m scaler_framework generate --key C --scale major --preset jazz_turnaround
python -m scaler_framework keygroup create sample.wav --scale major --octaves 3-5
python -m scaler_framework keygroup info my_sample.keygroup
python -m scaler_framework keygroup render my_sample.keygroup --progression "C | Am | F | G"
```

## Using Components Directly

Every module can be used standalone without `ScalerSession`:

```python
from scaler_framework.theory.chord import Chord, ChordProgression
from scaler_framework.theory.scale import Scale
from scaler_framework.detection.key import KeyEstimator
from scaler_framework.detection.midi import MidiParser, MidiChordDetector
from scaler_framework.detection.audio import ChromagramExtractor, AudioChordDetector
from scaler_framework.generation.progression import ProgressionEngine
from scaler_framework.generation.melody import MelodyGenerator, GeneratorConfig
from scaler_framework.generation.voicing import VoicingEngine, VoicingStyle
from scaler_framework.sampling.pitch import PitchDetector
from scaler_framework.sampling.keygroup import KeyGroup
from scaler_framework.sampling.renderer import KeyGroupRenderer
```

## Package Structure

```
scaler_framework/
  theory/
    constants.py       Note names, chord templates, scale templates
    chord.py           Chord, DetectedChord, ChordProgression
    scale.py           Scale, KeyEstimate
    roman.py           Roman numerals, functional harmony rules
  detection/
    key.py             Krumhansl-Schmuckler key estimation
    midi.py            MIDI parsing and chord detection
    audio.py           Chromagram extraction and audio chord detection
  generation/
    progression.py     Rule-based + Markov progression engine
    melody.py          Four-strategy melody generator
    rhythm.py          Rhythm patterns and melodic contour shapes
    voicing.py         12 voicing styles + voice leading
  sampling/
    pitch.py           Pitch detection (librosa pyin)
    keygroup.py        Key group create / save / load
    renderer.py        Audio rendering from key group + melody
  session.py           ScalerSession orchestrator
  midi_io.py           MIDI export with voicing integration
  cli.py               Unified CLI
```

## Available Presets

**Progressions:** pop_1, pop_2, jazz_ii_v_i, jazz_turnaround, blues_basic, sad, epic, lofi, bossa, rnb, anime

**Rhythm patterns:** quarter_notes, eighth_notes, syncopated_1, syncopated_2, dotted, sparse, driving_eighths, triplet_feel, mixed_1, mixed_2, rest_heavy, long_short

**Contour shapes:** ascending, descending, arch, valley, zigzag_up, zigzag_down, plateau, question, answer, wave

**Voicing styles:** close, open, drop_2, drop_3, spread, piano_lh, piano_rh, piano_full, guitar, pad, power, shell

**Scales:** major, natural_minor, harmonic_minor, melodic_minor, dorian, phrygian, lydian, mixolydian, locrian, pentatonic_major, pentatonic_minor, blues, whole_tone, chromatic
