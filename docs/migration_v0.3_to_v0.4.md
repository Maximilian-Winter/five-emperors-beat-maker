# Migration Guide: v0.3 to v0.4

This guide covers breaking changes and new features in beatmaker v0.4.0.

---

## Overview of Changes

1. **Synthesis modules restructured** into `beatmaker/synthesis/` subpackage
2. **Effects modules restructured** into `beatmaker/effects/` subpackage
3. **Graph module restructured** into `beatmaker/graph/` subpackage
4. **SPC700 extracted** to separate `beatmaker-spc700` package
5. **New `beatmaker.music` module** centralizes music theory utilities
6. Old module files kept as **backward-compatibility re-export stubs** (deprecated)

---

## New Subpackage Import Paths

### Synthesis

The old `beatmaker.synth` and `beatmaker.synths` modules have been split into the `beatmaker.synthesis` subpackage.

| Before (v0.3) | After (v0.4) |
|---|---|
| `from beatmaker.synth import Oscillator` | `from beatmaker.synthesis import Oscillator` |
| `from beatmaker.synth import DrumSynth` | `from beatmaker.synthesis import DrumSynth` |
| `from beatmaker.synth import BassSynth` | `from beatmaker.synthesis import BassSynth` |
| `from beatmaker.synth import sine_wave, sawtooth_wave` | `from beatmaker.synthesis import sine_wave, sawtooth_wave` |
| `from beatmaker.synths import PadSynth, LeadSynth` | `from beatmaker.synthesis import PadSynth, LeadSynth` |
| `from beatmaker.synths import LFO, Filter` | `from beatmaker.synthesis import LFO, Filter` |
| `from beatmaker.synths import PluckSynth, FXSynth` | `from beatmaker.synthesis import PluckSynth, FXSynth` |
| `from beatmaker.synths import create_pad, create_lead` | `from beatmaker.synthesis import create_pad, create_lead` |

For more granular imports, you can target individual submodules:

```python
from beatmaker.synthesis.waveforms import sine_wave, square_wave, white_noise
from beatmaker.synthesis.oscillator import Oscillator, ADSREnvelope
from beatmaker.synthesis.drums import DrumSynth
from beatmaker.synthesis.bass import BassSynth
from beatmaker.synthesis.modulation import LFO, Filter
from beatmaker.synthesis.pads import PadSynth, create_pad
from beatmaker.synthesis.leads import LeadSynth, create_lead
from beatmaker.synthesis.plucks import PluckSynth, create_pluck
from beatmaker.synthesis.fx import FXSynth
```

### Effects

The old `beatmaker.effects` and `beatmaker.sidechain` modules have been consolidated into the `beatmaker.effects` subpackage.

| Before (v0.3) | After (v0.4) |
|---|---|
| `from beatmaker.effects import Reverb, Delay` | `from beatmaker.effects import Reverb, Delay` (unchanged) |
| `from beatmaker.effects import Compressor, Gain` | `from beatmaker.effects import Compressor, Gain` (unchanged) |
| `from beatmaker.sidechain import PumpingBass` | `from beatmaker.effects import PumpingBass` |
| `from beatmaker.sidechain import SidechainCompressor` | `from beatmaker.effects import SidechainCompressor` |
| `from beatmaker.sidechain import create_sidechain` | `from beatmaker.effects import create_sidechain` |

Granular submodule imports:

```python
from beatmaker.effects.base import AudioEffect, EffectChain
from beatmaker.effects.dynamics import Gain, Limiter, SoftClipper, Compressor
from beatmaker.effects.time_based import Delay, Reverb, Chorus
from beatmaker.effects.filters import LowPassFilter, HighPassFilter, BitCrusher
from beatmaker.effects.sidechain import SidechainCompressor, PumpingBass, create_sidechain
```

### Signal Graph

The old `beatmaker.graph` module has been split into the `beatmaker.graph` subpackage.

| Before (v0.3) | After (v0.4) |
|---|---|
| `from beatmaker.graph import SignalGraph` | `from beatmaker.graph import SignalGraph` (unchanged) |
| `from beatmaker.graph import AudioInput` | `from beatmaker.graph import AudioInput` (unchanged) |

The top-level `from beatmaker.graph import ...` continues to work. For granular imports:

```python
from beatmaker.graph.core import SignalGraph, SignalNode, Port
from beatmaker.graph.sources import AudioInput, OscillatorSource, SilenceSource
from beatmaker.graph.processors import GainNode, FilterNode, CompressorNode
from beatmaker.graph.combiners import MixerNode, CrossfadeNode
from beatmaker.graph.analysis import LevelMeter, SpectrumAnalyzer
from beatmaker.graph.channels import SplitterNode, MergeNode, PanNode
from beatmaker.graph.bridge import graph_to_audio, audio_to_graph
```

---

## SPC700 Now a Separate Package

The SPC700 (Super Nintendo audio) support has been extracted to the standalone `beatmaker-spc700` package.

**Before (v0.3):**
```python
from beatmaker.spc700 import SPC700Emulator
```

**After (v0.4):**
```bash
pip install beatmaker-spc700
```
```python
from beatmaker_spc700 import SPC700Emulator
```

Or install as an optional extra:
```bash
pip install beatmaker[spc700]
```

---

## New `beatmaker.music` Module

Music theory utilities that were previously scattered across `synth.py`, `arpeggiator.py`, and `melody.py` are now consolidated in `beatmaker.music`:

```python
from beatmaker.music import (
    note_name_to_midi,   # 'C4' → 60
    midi_to_note_name,   # 60 → 'C4'
    midi_to_freq,        # 69 → 440.0
    freq_to_midi,        # 440.0 → 69
    note_to_freq,        # 'A4' → 440.0
    Scale,               # Scale.MAJOR, Scale.MINOR, Scale.BLUES, ...
    ChordShape,          # ChordShape.MAJOR, ChordShape.MINOR7, ...
    NOTE_FREQS,          # Frequency lookup table
)
```

These symbols are also re-exported from the top-level `beatmaker` package and from the modules where they previously lived. Using `beatmaker.music` directly is preferred for new code.

---

## Backward Compatibility

The old module files (`beatmaker/synth.py`, `beatmaker/synths.py`, `beatmaker/sidechain.py`, `beatmaker/graph.py`) have been replaced with **re-export stubs** that import everything from the new subpackages. Your existing code will continue to work without changes.

```python
# This still works in v0.4 (but emits a deprecation warning):
from beatmaker.synth import DrumSynth
from beatmaker.synths import PadSynth
from beatmaker.sidechain import PumpingBass
```

---

## Deprecation Timeline

| Version | Status |
|---------|--------|
| **v0.4.0** | Old import paths work via stubs. Deprecation warnings emitted. |
| **v0.5.0** (planned) | Old import paths continue to work. Warnings upgraded to `DeprecationWarning`. |
| **v0.6.0** (planned) | Old stub files removed. Only new subpackage imports supported. |

**Recommendation:** Update your imports now to avoid breakage in future versions. A search-and-replace is usually sufficient:

- `beatmaker.synth` / `beatmaker.synths` → `beatmaker.synthesis`
- `beatmaker.sidechain` → `beatmaker.effects.sidechain` (or just `beatmaker.effects`)
- `from beatmaker.synth import midi_to_freq` → `from beatmaker.music import midi_to_freq`

---

## Top-Level Imports Still Work

The `from beatmaker import X` style continues to work for all public symbols:

```python
# These are unchanged and remain the simplest way to import
from beatmaker import create_song, DrumSynth, Reverb, Delay
from beatmaker import Scale, ChordShape, note_name_to_midi
```
