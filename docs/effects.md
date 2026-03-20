# Effects Module API Reference

Complete API reference for the `beatmaker.effects` module. All effects inherit from the `AudioEffect` abstract base class and process audio through the `process()` method.

---

## AudioEffect (Base Class)

**Module:** `beatmaker.core`

Abstract base class that defines the interface every effect must implement.

```python
from abc import ABC, abstractmethod

class AudioEffect(ABC):
    @abstractmethod
    def process(self, audio: AudioData) -> AudioData:
        """Apply the effect to audio data."""
        pass
```

### Method: `process(audio)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `audio` | `AudioData` | Input audio to process |

**Returns:** `AudioData` -- a new `AudioData` instance with the effect applied. The original is not modified.

Every concrete effect class documented below is a `@dataclass` that extends `AudioEffect` and implements `process()`.

---

## Dynamics Effects

**Module:** `beatmaker.effects.dynamics`

```python
from beatmaker.effects.dynamics import Gain, Limiter, SoftClipper, Compressor
```

### Gain

Simple linear gain (volume) adjustment.

```python
@dataclass
class Gain(AudioEffect):
    level: float = 1.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `float` | `1.0` | Linear gain multiplier. `1.0` = unity, `0.5` = half volume, `2.0` = double volume. |

#### Class Method: `Gain.from_db(db)`

Factory that creates a `Gain` instance from a decibel value. Converts using the formula `level = 10 ** (db / 20)`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `db` | `float` | Gain in decibels. `0.0` = unity, `-6.0` ~ half volume, `+6.0` ~ double volume. |

**Returns:** `Gain`

#### Examples

```python
from beatmaker.effects.dynamics import Gain

# Halve the volume with a linear multiplier
quiet = Gain(level=0.5)
output = quiet.process(audio)

# Boost by 6 dB using the factory method
boost = Gain.from_db(6.0)
output = boost.process(audio)

# Cut by 3 dB
cut = Gain.from_db(-3.0)
```

---

### Limiter

Hard limiter that clips samples at a threshold to prevent clipping above the threshold level.

```python
@dataclass
class Limiter(AudioEffect):
    threshold: float = 0.95
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | `float` | `0.95` | Maximum absolute sample value. Samples are clipped to the range `[-threshold, +threshold]`. |

#### Example

```python
from beatmaker.effects.dynamics import Limiter

# Limit peaks to 0.9
limiter = Limiter(threshold=0.9)
output = limiter.process(audio)
```

---

### SoftClipper

Soft clipping saturation effect using `tanh` waveshaping. Produces warm distortion rather than the hard edges of a limiter.

```python
@dataclass
class SoftClipper(AudioEffect):
    drive: float = 1.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `drive` | `float` | `1.0` | Amount of drive/saturation. The input signal is multiplied by this value before `tanh` waveshaping. Higher values produce more saturation. `1.0` = subtle warmth, `3.0`+ = heavy distortion. |

#### Example

```python
from beatmaker.effects.dynamics import SoftClipper

# Subtle warmth
warm = SoftClipper(drive=1.5)

# Heavy saturation
saturated = SoftClipper(drive=4.0)
output = saturated.process(audio)
```

---

### Compressor

Dynamic range compressor with envelope follower. Reduces the volume of audio that exceeds a threshold, with configurable attack and release timing.

```python
@dataclass
class Compressor(AudioEffect):
    threshold: float = -10.0
    ratio: float = 4.0
    attack: float = 0.01
    release: float = 0.1
    makeup_gain: float = 0.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | `float` | `-10.0` | Threshold in dB. Signals above this level are compressed. |
| `ratio` | `float` | `4.0` | Compression ratio. `4.0` means 4:1 -- for every 4 dB above threshold, only 1 dB passes through. |
| `attack` | `float` | `0.01` | Attack time in seconds. How quickly the compressor responds to signals exceeding the threshold. |
| `release` | `float` | `0.1` | Release time in seconds. How quickly the compressor stops compressing after the signal drops below threshold. |
| `makeup_gain` | `float` | `0.0` | Makeup gain in dB applied after compression to restore perceived volume. |

The compressor handles both mono and stereo audio. For stereo signals, it derives the envelope from the maximum absolute value across channels, so both channels are compressed equally.

#### Example

```python
from beatmaker.effects.dynamics import Compressor

# Moderate compression with makeup gain
comp = Compressor(
    threshold=-12.0,
    ratio=4.0,
    attack=0.005,
    release=0.15,
    makeup_gain=6.0
)
output = comp.process(audio)

# Heavy limiting-style compression
brick = Compressor(threshold=-6.0, ratio=20.0, attack=0.001, release=0.05)
```

---

## Time-Based Effects

**Module:** `beatmaker.effects.time_based`

```python
from beatmaker.effects.time_based import Delay, Reverb, Chorus
```

### Delay

Simple delay effect with feedback and wet/dry mix. Uses 3 delay taps with exponentially decaying feedback.

```python
@dataclass
class Delay(AudioEffect):
    delay_time: float = 0.25
    feedback: float = 0.3
    mix: float = 0.5
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delay_time` | `float` | `0.25` | Delay time in seconds. |
| `feedback` | `float` | `0.3` | Feedback amount, range `0.0` to `1.0`. Each successive tap is multiplied by `feedback ** tap_number`. |
| `mix` | `float` | `0.5` | Wet/dry mix. `0.0` = fully dry (no effect), `1.0` = fully wet. |

The output audio is longer than the input: the length is extended by `delay_time * 2` seconds to include the delay tail. Works with both mono and stereo audio.

#### Example

```python
from beatmaker.effects.time_based import Delay

# Quarter-note delay at 120 BPM (0.5 seconds)
delay = Delay(delay_time=0.5, feedback=0.4, mix=0.3)
output = delay.process(audio)

# Short slapback delay
slap = Delay(delay_time=0.08, feedback=0.1, mix=0.4)
```

---

### Reverb

Algorithmic reverb using parallel comb filters and series allpass filters. Converts stereo input to mono for processing and duplicates the result back to stereo on output.

```python
@dataclass
class Reverb(AudioEffect):
    room_size: float = 0.5
    damping: float = 0.5
    mix: float = 0.3
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `room_size` | `float` | `0.5` | Room size from `0.0` (small) to `1.0` (large). Controls comb filter delay lengths and feedback amount. |
| `damping` | `float` | `0.5` | High-frequency damping. `0.0` = no damping (bright), `1.0` = maximum damping (dark/muffled). |
| `mix` | `float` | `0.3` | Wet/dry mix. `0.0` = fully dry, `1.0` = fully wet. |

Internally uses 4 parallel comb filters and 2 series allpass filters. The output includes a 0.5-second reverb tail beyond the original audio length.

#### Example

```python
from beatmaker.effects.time_based import Reverb

# Medium room reverb
reverb = Reverb(room_size=0.5, damping=0.4, mix=0.25)
output = reverb.process(audio)

# Large hall with heavy damping
hall = Reverb(room_size=0.9, damping=0.8, mix=0.4)
```

---

### Chorus

Chorus effect using modulated delay lines with multiple voices. Each voice has a different LFO phase offset, creating a widening/thickening effect.

```python
@dataclass
class Chorus(AudioEffect):
    rate: float = 1.5
    depth: float = 0.002
    mix: float = 0.5
    voices: int = 2
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate` | `float` | `1.5` | LFO modulation rate in Hz. |
| `depth` | `float` | `0.002` | Modulation depth in seconds. Controls how far the delay time swings around the 20 ms base delay. |
| `mix` | `float` | `0.5` | Wet/dry mix. `0.0` = fully dry, `1.0` = fully wet. |
| `voices` | `int` | `2` | Number of chorus voices. Each voice is phase-offset by `2*pi / voices`. More voices produce a thicker sound. |

The base delay is fixed at 20 ms. Each voice modulates around this base delay by the `depth` amount.

#### Example

```python
from beatmaker.effects.time_based import Chorus

# Standard chorus
chorus = Chorus(rate=1.5, depth=0.003, mix=0.4, voices=2)
output = chorus.process(audio)

# Rich ensemble effect
ensemble = Chorus(rate=0.8, depth=0.005, mix=0.6, voices=4)
```

---

## Filter Effects

**Module:** `beatmaker.effects.filters`

```python
from beatmaker.effects.filters import LowPassFilter, HighPassFilter, BitCrusher
```

### LowPassFilter

One-pole low-pass filter. Attenuates frequencies above the cutoff.

```python
@dataclass
class LowPassFilter(AudioEffect):
    cutoff: float = 1000.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cutoff` | `float` | `1000.0` | Cutoff frequency in Hz. Frequencies above this are progressively attenuated. |

#### Example

```python
from beatmaker.effects.filters import LowPassFilter

# Muffled lo-fi sound
lpf = LowPassFilter(cutoff=500.0)
output = lpf.process(audio)

# Gentle high-end rolloff
gentle = LowPassFilter(cutoff=8000.0)
```

---

### HighPassFilter

One-pole high-pass filter. Attenuates frequencies below the cutoff.

```python
@dataclass
class HighPassFilter(AudioEffect):
    cutoff: float = 100.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cutoff` | `float` | `100.0` | Cutoff frequency in Hz. Frequencies below this are progressively attenuated. |

#### Example

```python
from beatmaker.effects.filters import HighPassFilter

# Remove sub-bass rumble
hpf = HighPassFilter(cutoff=80.0)
output = hpf.process(audio)

# Thin out a sound
thin = HighPassFilter(cutoff=500.0)
```

---

### BitCrusher

Lo-fi bit depth reduction and sample rate reduction effect.

```python
@dataclass
class BitCrusher(AudioEffect):
    bit_depth: int = 8
    sample_hold: int = 1
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bit_depth` | `int` | `8` | Target bit depth, range `1` to `16`. Lower values produce more quantization noise and a grittier sound. |
| `sample_hold` | `int` | `1` | Sample-and-hold factor for sample rate reduction. `1` = no reduction. `2` = every other sample is held, effectively halving the rate. Higher values produce more aliasing and lo-fi character. |

#### Example

```python
from beatmaker.effects.filters import BitCrusher

# Classic 8-bit sound
crusher = BitCrusher(bit_depth=8, sample_hold=1)
output = crusher.process(audio)

# Extreme lo-fi destruction
lofi = BitCrusher(bit_depth=4, sample_hold=4)
```

---

## EffectChain

**Module:** `beatmaker.effects.base`

Chains multiple effects together, processing audio through each in sequence.

```python
from beatmaker.effects.base import EffectChain
```

### Constructor

```python
EffectChain(*effects: AudioEffect)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*effects` | `AudioEffect` | Variable number of effects to chain, processed in the order given. |

### Method: `add(effect)`

Appends an effect to the end of the chain.

| Parameter | Type | Description |
|-----------|------|-------------|
| `effect` | `AudioEffect` | The effect to add. |

**Returns:** `EffectChain` -- returns `self` for method chaining.

### Method: `process(audio)`

Processes audio through all effects in order.

| Parameter | Type | Description |
|-----------|------|-------------|
| `audio` | `AudioData` | Input audio to process. |

**Returns:** `AudioData`

### Iteration

`EffectChain` supports iteration over its effects via `__iter__`.

### Examples

```python
from beatmaker.effects.base import EffectChain
from beatmaker.effects.dynamics import Compressor, Limiter, Gain
from beatmaker.effects.time_based import Reverb
from beatmaker.effects.filters import HighPassFilter

# Build a chain via the constructor
chain = EffectChain(
    HighPassFilter(cutoff=80.0),
    Compressor(threshold=-12.0, ratio=4.0),
    Reverb(room_size=0.4, mix=0.2),
    Limiter(threshold=0.95)
)
output = chain.process(audio)

# Build incrementally with add()
chain = EffectChain()
chain.add(Gain.from_db(-3.0))
chain.add(Compressor(threshold=-10.0, ratio=3.0, makeup_gain=4.0))
chain.add(Limiter())
output = chain.process(audio)

# Iterate over effects in the chain
for effect in chain:
    print(type(effect).__name__)
```

---

## Sidechain Effects

**Module:** `beatmaker.effects.sidechain`

```python
from beatmaker.effects.sidechain import (
    SidechainCompressor,
    SidechainEnvelope,
    PumpingBass,
    SidechainBuilder,
    SidechainPresets,
    create_sidechain,
)
```

### SidechainCompressor

True sidechain compressor that ducks the main signal in response to a trigger signal (typically a kick drum).

```python
@dataclass
class SidechainCompressor(AudioEffect):
    threshold: float = -20.0
    ratio: float = 8.0
    attack: float = 0.001
    release: float = 0.15
    hold: float = 0.0
    range: float = -24.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | `float` | `-20.0` | Trigger threshold in dB. The trigger signal must exceed this level to cause ducking. |
| `ratio` | `float` | `8.0` | Compression ratio applied when the trigger exceeds the threshold. |
| `attack` | `float` | `0.001` | Attack time in seconds. How quickly ducking engages when the trigger fires. |
| `release` | `float` | `0.15` | Release time in seconds. How quickly the signal returns to full volume after the trigger drops. |
| `hold` | `float` | `0.0` | Hold time in seconds. The compressor holds maximum gain reduction for this duration before starting the release phase. |
| `range` | `float` | `-24.0` | Maximum gain reduction in dB. Limits how much the signal can be ducked. |

#### Method: `set_trigger(trigger)`

Sets the sidechain trigger signal. Must be called before `process()`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `trigger` | `AudioData` | The trigger audio signal (e.g., a kick drum track). |

**Returns:** `SidechainCompressor` -- returns `self` for method chaining.

If no trigger is set, `process()` returns the audio unmodified. The trigger is automatically resampled to match the input audio's sample rate if they differ. Stereo triggers are converted to mono internally.

#### Example

```python
from beatmaker.effects.sidechain import SidechainCompressor

sc = SidechainCompressor(
    threshold=-20.0,
    ratio=10.0,
    attack=0.001,
    release=0.2,
    hold=0.01,
    range=-30.0
)
sc.set_trigger(kick_audio)
ducked_bass = sc.process(bass_audio)
```

---

### SidechainEnvelope

Envelope-based sidechain effect that creates the pumping effect without needing a trigger signal. It generates a rhythmic volume envelope based on tempo and beat division.

```python
@dataclass
class SidechainEnvelope(AudioEffect):
    bpm: float = 120.0
    pattern: str = "1/4"
    depth: float = 0.8
    attack: float = 0.01
    release: float = 0.5
    shape: str = "exp"
    offset: float = 0.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bpm` | `float` | `120.0` | Tempo in beats per minute. |
| `pattern` | `str` | `"1/4"` | Beat division as a fraction string. Controls the rate of the pumping cycle. Common values: `"1/4"` (quarter notes), `"1/8"` (eighth notes), `"1/2"` (half notes), `"1/1"` (whole notes). |
| `depth` | `float` | `0.8` | Ducking depth from `0.0` (no ducking) to `1.0` (full silence at the duck point). |
| `attack` | `float` | `0.01` | Attack phase as a proportion of the cycle (`0.0` to `1.0`). `0.0` = instant duck, higher values = slower duck. |
| `release` | `float` | `0.5` | Release curve shape factor (`0.0` to `1.0`). Controls how quickly volume returns after the duck. |
| `shape` | `str` | `"exp"` | Envelope curve shape. One of `"exp"` (exponential), `"linear"`, or `"log"` (logarithmic). |
| `offset` | `float` | `0.0` | Phase offset in beats. Shifts the envelope timing. |

#### Example

```python
from beatmaker.effects.sidechain import SidechainEnvelope

# Quarter-note pump at 128 BPM
pump = SidechainEnvelope(
    bpm=128,
    pattern="1/4",
    depth=0.8,
    attack=0.01,
    release=0.4,
    shape="exp"
)
output = pump.process(pad_audio)

# Eighth-note stutter
stutter = SidechainEnvelope(bpm=140, pattern="1/8", depth=0.6, shape="linear")
```

---

### PumpingBass

Specialized sidechain effect for bass lines. Internally creates a `SidechainEnvelope` with a fixed `"1/4"` pattern and applies volume ducking.

```python
@dataclass
class PumpingBass(AudioEffect):
    bpm: float = 120.0
    depth: float = 0.9
    release: float = 0.3
    filter_freq: float = 200.0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bpm` | `float` | `120.0` | Tempo in beats per minute. |
| `depth` | `float` | `0.9` | Ducking depth (`0.0` to `1.0`). |
| `release` | `float` | `0.3` | Release time factor. |
| `filter_freq` | `float` | `200.0` | Low-pass filter frequency in Hz (reserved for future use; the current implementation applies volume ducking only). |

#### Example

```python
from beatmaker.effects.sidechain import PumpingBass

pump_bass = PumpingBass(bpm=128, depth=0.85, release=0.35)
output = pump_bass.process(bass_audio)
```

---

### SidechainBuilder

Fluent builder API for constructing sidechain effects. Start with `create_sidechain()` or instantiate directly.

```python
class SidechainBuilder:
    def __init__(self): ...
```

The builder defaults to an envelope-based sidechain with these initial values:

| Internal Key | Default | Description |
|--------------|---------|-------------|
| `type` | `"envelope"` | Switches to `"compressor"` when `trigger()` is called. |
| `bpm` | `120.0` | Tempo. |
| `depth` | `0.8` | Ducking depth. |
| `attack` | `0.01` | Attack time. |
| `release` | `0.3` | Release time. |
| `pattern` | `"1/4"` | Beat division. |
| `shape` | `"exp"` | Envelope shape. |
| `trigger` | `None` | Trigger signal. |

#### Builder Methods

All setter methods return `self` (`SidechainBuilder`) for method chaining.

| Method | Parameter | Description |
|--------|-----------|-------------|
| `tempo(bpm)` | `bpm: float` | Set the tempo in BPM. |
| `depth(value)` | `value: float` | Set ducking depth (`0.0` to `1.0`). |
| `attack(seconds)` | `seconds: float` | Set attack time in seconds. |
| `release(seconds)` | `seconds: float` | Set release time in seconds. |
| `quarter_notes()` | -- | Set pattern to `"1/4"`. |
| `eighth_notes()` | -- | Set pattern to `"1/8"`. |
| `half_notes()` | -- | Set pattern to `"1/2"`. |
| `pattern(value)` | `value: str` | Set an arbitrary pattern string (e.g., `"1/4"`, `"1/8"`). |
| `shape_exp()` | -- | Set shape to `"exp"`. |
| `shape_linear()` | -- | Set shape to `"linear"`. |
| `shape_log()` | -- | Set shape to `"log"`. |
| `trigger(audio)` | `audio: AudioData` | Use an actual audio signal as the sidechain trigger. Switches the builder to produce a `SidechainCompressor` instead of a `SidechainEnvelope`. |
| `from_track(track, sample_rate)` | `track: Track`, `sample_rate: int = 44100` | Render a `Track` and use its audio as the trigger. Calls `track.render(sample_rate, 2)` internally. |

#### Method: `build()`

Builds and returns the configured effect.

**Returns:** `AudioEffect` -- either a `SidechainCompressor` (if `trigger()` or `from_track()` was called) or a `SidechainEnvelope` (otherwise).

When building a `SidechainCompressor`, the `range` parameter is calculated as `-20 * depth`.

#### Example

```python
from beatmaker.effects.sidechain import create_sidechain

# Envelope-based sidechain via the builder
effect = (
    create_sidechain()
    .tempo(128)
    .quarter_notes()
    .depth(0.8)
    .attack(0.01)
    .release(0.4)
    .shape_exp()
    .build()
)
output = effect.process(pad_audio)

# True sidechain compression with a trigger signal
effect = (
    create_sidechain()
    .trigger(kick_audio)
    .attack(0.001)
    .release(0.2)
    .depth(0.9)
    .build()
)
output = effect.process(bass_audio)

# Build from a track
effect = (
    create_sidechain()
    .from_track(kick_track, sample_rate=44100)
    .release(0.15)
    .depth(0.85)
    .build()
)
```

---

### create_sidechain()

Factory function that returns a new `SidechainBuilder`.

```python
def create_sidechain() -> SidechainBuilder
```

This is the recommended entry point for constructing sidechain effects with the fluent API.

---

### SidechainPresets

Static methods that return pre-configured `SidechainEnvelope` instances for common electronic music styles.

```python
class SidechainPresets:
    @staticmethod
    def classic_house(bpm: float = 128) -> SidechainEnvelope: ...
    @staticmethod
    def heavy_edm(bpm: float = 128) -> SidechainEnvelope: ...
    @staticmethod
    def subtle_groove(bpm: float = 120) -> SidechainEnvelope: ...
    @staticmethod
    def fast_trance(bpm: float = 140) -> SidechainEnvelope: ...
    @staticmethod
    def half_time(bpm: float = 140) -> SidechainEnvelope: ...
```

Each preset accepts a single `bpm` parameter and returns a `SidechainEnvelope` with tuned settings:

| Preset | Default BPM | Pattern | Depth | Attack | Release | Shape | Character |
|--------|-------------|---------|-------|--------|---------|-------|-----------|
| `classic_house` | 128 | `"1/4"` | 0.7 | 0.01 | 0.4 | `"exp"` | Classic four-on-the-floor pump |
| `heavy_edm` | 128 | `"1/4"` | 0.95 | 0.005 | 0.5 | `"exp"` | Aggressive, near-full ducking |
| `subtle_groove` | 120 | `"1/4"` | 0.3 | 0.02 | 0.25 | `"linear"` | Gentle rhythmic movement |
| `fast_trance` | 140 | `"1/8"` | 0.6 | 0.01 | 0.2 | `"exp"` | Rapid eighth-note gating |
| `half_time` | 140 | `"1/2"` | 0.5 | 0.02 | 0.6 | `"log"` | Slow, wide pump on half notes |

#### Examples

```python
from beatmaker.effects.sidechain import SidechainPresets

# Apply classic house pump to a pad
pump = SidechainPresets.classic_house(bpm=126)
pumped_pad = pump.process(pad_audio)

# Heavy EDM sidechain on a supersaw
heavy = SidechainPresets.heavy_edm(bpm=150)
output = heavy.process(supersaw_audio)

# Subtle groove on a chord stab
groove = SidechainPresets.subtle_groove(bpm=118)
output = groove.process(chords_audio)
```

---

## Common Effect Combinations

### Mix-Ready Vocal Chain

```python
from beatmaker.effects.base import EffectChain
from beatmaker.effects.filters import HighPassFilter
from beatmaker.effects.dynamics import Compressor, Gain, Limiter
from beatmaker.effects.time_based import Reverb

vocal_chain = EffectChain(
    HighPassFilter(cutoff=120.0),
    Compressor(threshold=-15.0, ratio=3.0, attack=0.01, release=0.1, makeup_gain=4.0),
    Reverb(room_size=0.3, damping=0.6, mix=0.15),
    Limiter(threshold=0.95),
)
output = vocal_chain.process(vocal_audio)
```

### Lo-Fi Beat Processing

```python
from beatmaker.effects.base import EffectChain
from beatmaker.effects.filters import LowPassFilter, BitCrusher
from beatmaker.effects.dynamics import SoftClipper, Gain

lofi_chain = EffectChain(
    SoftClipper(drive=2.0),
    BitCrusher(bit_depth=12, sample_hold=2),
    LowPassFilter(cutoff=4000.0),
    Gain.from_db(-3.0),
)
output = lofi_chain.process(drum_audio)
```

### EDM Bass with Sidechain

```python
from beatmaker.effects.base import EffectChain
from beatmaker.effects.filters import HighPassFilter
from beatmaker.effects.dynamics import Compressor, Limiter
from beatmaker.effects.sidechain import SidechainPresets

bass_chain = EffectChain(
    HighPassFilter(cutoff=30.0),
    Compressor(threshold=-8.0, ratio=6.0, attack=0.005, release=0.05),
    SidechainPresets.heavy_edm(bpm=128),
    Limiter(threshold=0.9),
)
output = bass_chain.process(bass_audio)
```

### Ambient Pad with Chorus and Reverb

```python
from beatmaker.effects.base import EffectChain
from beatmaker.effects.time_based import Chorus, Reverb, Delay
from beatmaker.effects.dynamics import Gain

ambient_chain = EffectChain(
    Chorus(rate=0.5, depth=0.004, mix=0.4, voices=3),
    Delay(delay_time=0.375, feedback=0.35, mix=0.2),
    Reverb(room_size=0.85, damping=0.6, mix=0.5),
    Gain.from_db(-2.0),
)
output = ambient_chain.process(pad_audio)
```

### Track-Level Effect Application

Effects can be added directly to tracks rather than using `EffectChain`. They are applied during `track.render()`:

```python
from beatmaker.core import Track, TrackType
from beatmaker.effects.dynamics import Compressor, Limiter
from beatmaker.effects.filters import HighPassFilter

drums = Track(name="drums", track_type=TrackType.DRUMS)
drums.add_effect(HighPassFilter(cutoff=60.0))
drums.add_effect(Compressor(threshold=-10.0, ratio=4.0, makeup_gain=3.0))
drums.add_effect(Limiter(threshold=0.95))

# Effects are applied when the track is rendered
output = drums.render(sample_rate=44100, channels=2, bpm=120.0)
```
