# Synthesis Module API Reference

Complete API reference for the `beatmaker.synthesis` and `beatmaker.music` modules.

---

## Table of Contents

1. [Waveform Generators](#waveform-generators)
2. [Oscillator](#oscillator)
3. [ADSREnvelope](#adsrenvelope)
4. [DrumSynth](#drumsynth)
5. [BassSynth](#basssynth)
6. [LFO](#lfo)
7. [Filter](#filter)
8. [PadSynth](#padsynth)
9. [LeadSynth](#leadsynth)
10. [PluckSynth](#plucksynth)
11. [FXSynth](#fxsynth)
12. [Convenience Functions](#convenience-functions)
13. [Music Theory Utilities](#music-theory-utilities)

---

## Waveform Generators

**Module:** `beatmaker.synthesis.waveforms`

Pure functions that generate basic waveform `AudioData` from frequency, duration, and sample rate parameters.

### `sine_wave`

```python
sine_wave(frequency: float, duration: float,
          sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData
```

Generate a pure sine wave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency of the sine wave in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate in samples per second |
| `amplitude` | `float` | `1.0` | Peak amplitude of the waveform (0.0 to 1.0) |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import sine_wave

# Generate a 440 Hz (A4) sine wave for 2 seconds
tone = sine_wave(440.0, 2.0)

# Lower amplitude, higher sample rate
quiet_tone = sine_wave(261.63, 1.0, sample_rate=48000, amplitude=0.5)
```

---

### `square_wave`

```python
square_wave(frequency: float, duration: float,
            sample_rate: int = 44100, amplitude: float = 1.0,
            duty_cycle: float = 0.5) -> AudioData
```

Generate a square wave with adjustable duty cycle.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |
| `amplitude` | `float` | `1.0` | Peak amplitude |
| `duty_cycle` | `float` | `0.5` | Fraction of the period that the wave is high (0.0 to 1.0). 0.5 produces a standard square wave; other values produce a pulse wave |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import square_wave

# Standard square wave
sq = square_wave(220.0, 1.0)

# Narrow pulse wave (25% duty cycle)
pulse = square_wave(220.0, 1.0, duty_cycle=0.25)
```

---

### `sawtooth_wave`

```python
sawtooth_wave(frequency: float, duration: float,
              sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData
```

Generate a sawtooth wave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |
| `amplitude` | `float` | `1.0` | Peak amplitude |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import sawtooth_wave

saw = sawtooth_wave(110.0, 1.5)
```

---

### `triangle_wave`

```python
triangle_wave(frequency: float, duration: float,
              sample_rate: int = 44100, amplitude: float = 1.0) -> AudioData
```

Generate a triangle wave.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |
| `amplitude` | `float` | `1.0` | Peak amplitude |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import triangle_wave

tri = triangle_wave(330.0, 1.0)
```

---

### `white_noise`

```python
white_noise(duration: float, sample_rate: int = 44100,
            amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData
```

Generate white noise (uniform random distribution across all frequencies).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |
| `amplitude` | `float` | `1.0` | Peak amplitude |
| `seed` | `Optional[int]` | `None` | Random seed for reproducible output. If `None`, output is non-deterministic |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import white_noise

noise = white_noise(0.5)

# Reproducible noise
noise_r = white_noise(1.0, amplitude=0.3, seed=42)
```

---

### `pink_noise`

```python
pink_noise(duration: float, sample_rate: int = 44100,
           amplitude: float = 1.0, seed: Optional[int] = None) -> AudioData
```

Generate pink noise (1/f spectrum) using the Voss-McCartney algorithm. Pink noise has equal energy per octave, resulting in a warmer sound than white noise.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |
| `amplitude` | `float` | `1.0` | Peak amplitude. Output is normalized so that the peak value equals this amplitude |
| `seed` | `Optional[int]` | `None` | Random seed for reproducible output |

**Returns:** `AudioData`

**Example:**

```python
from beatmaker.synthesis.waveforms import pink_noise

warm_noise = pink_noise(2.0, amplitude=0.6)
```

---

## Oscillator

**Module:** `beatmaker.synthesis.oscillator`

### `Waveform` Enum

```python
class Waveform(Enum):
    SINE = auto()
    SQUARE = auto()
    SAWTOOTH = auto()
    TRIANGLE = auto()
    NOISE = auto()
```

Enumeration of basic waveform types used by the `Oscillator` class.

| Member | Description |
|--------|-------------|
| `SINE` | Pure sine wave |
| `SQUARE` | Square wave (50% duty cycle) |
| `SAWTOOTH` | Sawtooth wave |
| `TRIANGLE` | Triangle wave |
| `NOISE` | White noise |

---

### `Oscillator` Class

```python
class Oscillator:
    def __init__(self, waveform: Waveform = Waveform.SINE,
                 detune: float = 0.0,
                 phase: float = 0.0)
```

Versatile oscillator for synthesis. Supports multiple waveforms with detune and phase offset.

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `waveform` | `Waveform` | `Waveform.SINE` | The waveform type to generate |
| `detune` | `float` | `0.0` | Detune amount in cents (100 cents = 1 semitone). Shifts the frequency by the specified number of cents |
| `phase` | `float` | `0.0` | Phase offset in radians |

#### `Oscillator.generate`

```python
def generate(self, frequency: float, duration: float,
             sample_rate: int = 44100) -> AudioData
```

Generate audio at the specified frequency, applying detune and phase offset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Base frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `AudioData`

The actual frequency is computed as `frequency * 2^(detune / 1200)`.

**Example:**

```python
from beatmaker.synthesis.oscillator import Oscillator, Waveform

# Basic sine oscillator
osc = Oscillator(Waveform.SINE)
audio = osc.generate(440.0, 1.0)

# Detuned sawtooth (7 cents sharp)
osc2 = Oscillator(Waveform.SAWTOOTH, detune=7.0)
audio2 = osc2.generate(220.0, 2.0)

# Two oscillators slightly detuned for a chorus effect
osc_a = Oscillator(Waveform.SAWTOOTH, detune=-5.0)
osc_b = Oscillator(Waveform.SAWTOOTH, detune=5.0)
```

---

## ADSREnvelope

**Module:** `beatmaker.synthesis.oscillator`

```python
@dataclass
class ADSREnvelope:
    attack: float = 0.01
    decay: float = 0.1
    sustain: float = 0.7
    release: float = 0.2
```

Attack-Decay-Sustain-Release envelope generator. Creates amplitude envelopes for shaping sound over time.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `attack` | `float` | `0.01` | Attack time in seconds. The time to ramp from 0 to peak amplitude (1.0) |
| `decay` | `float` | `0.1` | Decay time in seconds. The time to fall from peak amplitude to the sustain level |
| `sustain` | `float` | `0.7` | Sustain level (0.0 to 1.0). The amplitude held after decay until release begins |
| `release` | `float` | `0.2` | Release time in seconds. The time to fade from the sustain level to 0 |

#### `ADSREnvelope.generate`

```python
def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray
```

Generate the raw envelope samples for a given duration. The sustain phase fills the time remaining after attack, decay, and release segments.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Total duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `np.ndarray` -- array of amplitude values (0.0 to 1.0)

#### `ADSREnvelope.apply`

```python
def apply(self, audio: AudioData) -> AudioData
```

Apply the envelope to an `AudioData` object. The envelope duration is derived from the audio's own duration. Works with both mono and multi-channel audio.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio` | `AudioData` | *required* | The audio to shape |

**Returns:** `AudioData` -- new `AudioData` with the envelope applied

**Example:**

```python
from beatmaker.synthesis.oscillator import ADSREnvelope
from beatmaker.synthesis.waveforms import sawtooth_wave

# Plucky envelope with fast attack and no sustain
env = ADSREnvelope(attack=0.005, decay=0.3, sustain=0.0, release=0.1)

saw = sawtooth_wave(440.0, 1.0)
shaped = env.apply(saw)

# Slow pad envelope
pad_env = ADSREnvelope(attack=0.8, decay=0.5, sustain=0.6, release=1.0)
```

---

## DrumSynth

**Module:** `beatmaker.synthesis.drums`

```python
class DrumSynth:
```

Synthesizer optimized for drum and percussion sounds. All methods are static and return `Sample` objects.

### `DrumSynth.kick`

```python
@staticmethod
def kick(duration: float = 0.5, pitch: float = 60.0,
         punch: float = 0.8, sample_rate: int = 44100) -> Sample
```

Synthesize a kick drum. Uses a sine oscillator with a rapid pitch envelope dropping from high to low, combined with a noise click transient for attack.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | `0.5` | Duration of the kick in seconds |
| `pitch` | `float` | `60.0` | Starting pitch of the pitch envelope in Hz. The tone sweeps down from `pitch + 40` Hz to 40 Hz |
| `punch` | `float` | `0.8` | Amplitude of the initial click transient (0.0 to 1.0). Higher values give a harder attack |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["drums", "kick"]`

---

### `DrumSynth.snare`

```python
@staticmethod
def snare(duration: float = 0.3, tone_pitch: float = 180.0,
          noise_amount: float = 0.6, sample_rate: int = 44100) -> Sample
```

Synthesize a snare drum. Combines a tonal sine body with white noise for the snare rattle.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | `0.3` | Duration of the snare in seconds |
| `tone_pitch` | `float` | `180.0` | Pitch of the tonal body in Hz |
| `noise_amount` | `float` | `0.6` | Mix balance between tone and noise (0.0 = all tone, 1.0 = all noise) |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["drums", "snare"]`

---

### `DrumSynth.hihat`

```python
@staticmethod
def hihat(duration: float = 0.1, open_amount: float = 0.0,
          sample_rate: int = 44100) -> Sample
```

Synthesize a hi-hat, ranging from closed to open. Uses band-limited noise with tonal components at 3000 Hz and 6000 Hz.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | `0.1` | Base duration in seconds. Actual duration is extended by `open_amount * 0.4` seconds |
| `open_amount` | `float` | `0.0` | How open the hi-hat is (0.0 = closed, 1.0 = fully open). Controls both duration and decay rate |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- named `"hihat_open"` if `open_amount > 0.5`, else `"hihat_closed"`. Tagged with `["drums", "hihat"]`

---

### `DrumSynth.clap`

```python
@staticmethod
def clap(duration: float = 0.2, spread: float = 0.02,
         sample_rate: int = 44100) -> Sample
```

Synthesize a clap sound with multiple transients, simulating the effect of several hands clapping at slightly different times.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | `0.2` | Total duration in seconds |
| `spread` | `float` | `0.02` | Time spread in seconds across the 4 noise bursts. Larger values make the clap sound looser |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized, tagged with `["drums", "clap"]`

**Example:**

```python
from beatmaker.synthesis.drums import DrumSynth

kick = DrumSynth.kick(duration=0.5, pitch=50.0, punch=0.9)
snare = DrumSynth.snare(noise_amount=0.7)
closed_hh = DrumSynth.hihat(open_amount=0.0)
open_hh = DrumSynth.hihat(open_amount=0.8)
clap = DrumSynth.clap(spread=0.03)
```

---

## BassSynth

**Module:** `beatmaker.synthesis.bass`

```python
class BassSynth:
```

Synthesizer for bass sounds. All methods are static and return `Sample` objects.

### `BassSynth.sub_bass`

```python
@staticmethod
def sub_bass(frequency: float, duration: float,
             envelope: Optional[ADSREnvelope] = None,
             sample_rate: int = 44100) -> Sample
```

Pure sub-bass sine wave. Uses a simple sine oscillator, ideal for deep low-end.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Bass frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.1)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["bass", "sub"]`

---

### `BassSynth.acid_bass`

```python
@staticmethod
def acid_bass(frequency: float, duration: float,
              filter_freq: float = 500.0, resonance: float = 0.7,
              envelope: Optional[ADSREnvelope] = None,
              sample_rate: int = 44100) -> Sample
```

Classic acid bass (303-style). Uses a sawtooth oscillator with a decaying filter envelope for the characteristic squelchy sound.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Bass frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `filter_freq` | `float` | `500.0` | Peak filter frequency in Hz for the filter envelope. The filter sweeps down from this value |
| `resonance` | `float` | `0.7` | Filter resonance (currently used for envelope calculation) |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.001, decay=0.2, sustain=0.5, release=0.1)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["bass", "acid"]`

**Example:**

```python
from beatmaker.synthesis.bass import BassSynth
from beatmaker.synthesis.oscillator import ADSREnvelope

sub = BassSynth.sub_bass(55.0, 1.0)

acid = BassSynth.acid_bass(
    110.0, 0.5,
    filter_freq=800.0,
    envelope=ADSREnvelope(attack=0.001, decay=0.15, sustain=0.3, release=0.05)
)
```

---

## LFO

**Module:** `beatmaker.synthesis.modulation`

```python
@dataclass
class LFO:
    rate: float = 1.0
    depth: float = 1.0
    waveform: str = 'sine'
    phase: float = 0.0
```

Low Frequency Oscillator for modulation effects such as vibrato, tremolo, and filter sweeps.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate` | `float` | `1.0` | Oscillation rate in Hz |
| `depth` | `float` | `1.0` | Modulation depth. The output is scaled by this value |
| `waveform` | `str` | `'sine'` | LFO waveform shape. One of: `'sine'`, `'triangle'`, `'saw'`, `'square'`, `'random'` |
| `phase` | `float` | `0.0` | Starting phase (0.0 to 1.0, mapped to 0 to 2*pi internally for sine/square shapes) |

### `LFO.generate`

```python
def generate(self, duration: float, sample_rate: int = 44100) -> np.ndarray
```

Generate the LFO modulation signal.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `np.ndarray` -- modulation signal with values in the range `[-depth, +depth]`

The `'random'` waveform uses a sample-and-hold approach: a new random value is picked each cycle and held constant until the next cycle.

**Example:**

```python
from beatmaker.synthesis.modulation import LFO

# Slow vibrato
vibrato = LFO(rate=5.0, depth=0.02, waveform='sine')
mod_signal = vibrato.generate(2.0, sample_rate=44100)

# Apply as pitch modulation: freq * (1 + mod_signal)

# Tremolo with square LFO
tremolo = LFO(rate=4.0, depth=0.5, waveform='square')
```

---

## Filter

**Module:** `beatmaker.synthesis.modulation`

```python
@dataclass
class Filter:
    cutoff: float = 1000.0
    resonance: float = 0.0
    filter_type: str = 'lowpass'
```

Simple resonant biquad filter implementation.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cutoff` | `float` | `1000.0` | Cutoff frequency in Hz |
| `resonance` | `float` | `0.0` | Resonance amount (0.0 to 1.0). Internally mapped to Q factor as `0.5 + resonance * 10` |
| `filter_type` | `str` | `'lowpass'` | Filter type. One of: `'lowpass'`, `'highpass'`, `'bandpass'` |

### `Filter.process`

```python
def process(self, samples: np.ndarray, sample_rate: int) -> np.ndarray
```

Apply the filter to an array of samples.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `samples` | `np.ndarray` | *required* | Input sample array |
| `sample_rate` | `int` | *required* | Sample rate of the input audio |

**Returns:** `np.ndarray` -- filtered samples

The cutoff frequency is clamped to just below the Nyquist frequency to prevent instability.

**Example:**

```python
from beatmaker.synthesis.modulation import Filter
from beatmaker.synthesis.waveforms import sawtooth_wave

saw = sawtooth_wave(220.0, 1.0)

# Warm low-pass filter
lpf = Filter(cutoff=800.0, resonance=0.3, filter_type='lowpass')
filtered = lpf.process(saw.samples, saw.sample_rate)

# Resonant bandpass
bpf = Filter(cutoff=1500.0, resonance=0.6, filter_type='bandpass')
```

---

## PadSynth

**Module:** `beatmaker.synthesis.pads`

```python
class PadSynth:
```

Synthesizer for lush pad sounds. Creates warm, evolving textures perfect for ambient and melodic use. All methods are static and return `Sample` objects.

### `PadSynth.warm_pad`

```python
@staticmethod
def warm_pad(frequency: float, duration: float,
             num_voices: int = 4, detune: float = 0.1,
             envelope: Optional[ADSREnvelope] = None,
             sample_rate: int = 44100) -> Sample
```

Create a warm detuned pad. Layers multiple detuned voices mixing sawtooth (60%) and sine (40%) waves, applies a slow sine LFO for movement, and runs through a low-pass filter at 2000 Hz.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Base frequency in Hz |
| `duration` | `float` | *required* | Note duration in seconds |
| `num_voices` | `int` | `4` | Number of detuned voices. More voices produce a thicker sound |
| `detune` | `float` | `0.1` | Total detune spread in semitones. Voices are evenly distributed around the center pitch |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.5, decay=0.3, sustain=0.7, release=0.8)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["pad", "warm"]`

---

### `PadSynth.string_pad`

```python
@staticmethod
def string_pad(frequency: float, duration: float,
               envelope: Optional[ADSREnvelope] = None,
               sample_rate: int = 44100) -> Sample
```

Create a string-like pad sound. Builds from 5 sawtooth harmonics (1st through 5th) with slight random detuning for a chorus effect, filtered at 3000 Hz.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Base frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.3, decay=0.2, sustain=0.8, release=0.5)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized, tagged with `["pad", "string"]`

---

### `PadSynth.ambient_pad`

```python
@staticmethod
def ambient_pad(frequency: float, duration: float,
                sample_rate: int = 44100) -> Sample
```

Create an evolving ambient pad. Uses a sine base tone with 2nd and 3rd harmonics, a slow LFO-modulated filter, and a layer of subtle noise. Has a fixed envelope with very slow attack (2.0s) and release (2.0s).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Base frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.8 peak, tagged with `["pad", "ambient"]`

**Example:**

```python
from beatmaker.synthesis.pads import PadSynth

warm = PadSynth.warm_pad(261.63, 4.0, num_voices=6, detune=0.15)
strings = PadSynth.string_pad(220.0, 3.0)
ambient = PadSynth.ambient_pad(130.81, 8.0)
```

---

## LeadSynth

**Module:** `beatmaker.synthesis.leads`

```python
class LeadSynth:
```

Synthesizer for cutting, expressive lead tones. All methods are static and return `Sample` objects.

### `LeadSynth.saw_lead`

```python
@staticmethod
def saw_lead(frequency: float, duration: float,
             envelope: Optional[ADSREnvelope] = None,
             filter_env: bool = True,
             sample_rate: int = 44100) -> Sample
```

Classic saw lead with optional filter envelope. Uses two slightly detuned sawtooth waves (second is at `frequency * 1.005`) for thickness. When `filter_env` is enabled, applies a low-pass filter at 2500 Hz with 0.4 resonance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.01, decay=0.2, sustain=0.7, release=0.3)` |
| `filter_env` | `bool` | `True` | Whether to apply a filter envelope to the sound |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.9 peak, tagged with `["lead", "saw"]`

---

### `LeadSynth.square_lead`

```python
@staticmethod
def square_lead(frequency: float, duration: float,
                pulse_width: float = 0.5,
                envelope: Optional[ADSREnvelope] = None,
                sample_rate: int = 44100) -> Sample
```

Square/pulse wave lead with a sub oscillator. Adds a sine sub-oscillator one octave below at 30% amplitude, filtered at 3000 Hz.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `pulse_width` | `float` | `0.5` | Pulse width (0.0 to 1.0). 0.5 = standard square wave |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.01, decay=0.1, sustain=0.8, release=0.2)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["lead", "square"]`

---

### `LeadSynth.fm_lead`

```python
@staticmethod
def fm_lead(frequency: float, duration: float,
            mod_ratio: float = 2.0, mod_index: float = 3.0,
            envelope: Optional[ADSREnvelope] = None,
            sample_rate: int = 44100) -> Sample
```

FM synthesis lead. A sine carrier is frequency-modulated by a sine modulator.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Carrier frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `mod_ratio` | `float` | `2.0` | Modulator frequency ratio relative to carrier. `mod_freq = frequency * mod_ratio` |
| `mod_index` | `float` | `3.0` | Modulation index (depth). Higher values produce more harmonics |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.01, decay=0.15, sustain=0.6, release=0.25)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["lead", "fm"]`

**Example:**

```python
from beatmaker.synthesis.leads import LeadSynth

saw = LeadSynth.saw_lead(440.0, 1.0)
square = LeadSynth.square_lead(440.0, 1.0, pulse_width=0.3)
fm = LeadSynth.fm_lead(440.0, 1.0, mod_ratio=3.0, mod_index=5.0)
```

---

## PluckSynth

**Module:** `beatmaker.synthesis.plucks`

```python
class PluckSynth:
```

Synthesizer for plucked string sounds. Uses Karplus-Strong and other techniques. All methods are static and return `Sample` objects.

### `PluckSynth.karplus_strong`

```python
@staticmethod
def karplus_strong(frequency: float, duration: float,
                   brightness: float = 0.5,
                   sample_rate: int = 44100) -> Sample
```

Karplus-Strong plucked string synthesis. Initializes a delay buffer with noise and applies a low-pass averaging filter at each cycle to simulate string decay.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Note frequency in Hz. Determines the delay buffer length |
| `duration` | `float` | *required* | Duration in seconds |
| `brightness` | `float` | `0.5` | Tone brightness (0.0 to 1.0). Higher values produce a brighter, slower-decaying tone. The damping factor is computed as `0.996 - (1 - brightness) * 0.01` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.9 peak, tagged with `["pluck", "string"]`

---

### `PluckSynth.synth_pluck`

```python
@staticmethod
def synth_pluck(frequency: float, duration: float,
                envelope: Optional[ADSREnvelope] = None,
                sample_rate: int = 44100) -> Sample
```

Synthesized pluck sound. Mixes sawtooth (70%) and square wave with 30% duty cycle (30%), filtered at 2000 Hz with 0.5 resonance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `envelope` | `Optional[ADSREnvelope]` | `None` | ADSR envelope. If `None`, defaults to `ADSREnvelope(attack=0.001, decay=0.3, sustain=0.0, release=0.2)` |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["pluck", "synth"]`

---

### `PluckSynth.bell`

```python
@staticmethod
def bell(frequency: float, duration: float,
         sample_rate: int = 44100) -> Sample
```

Bell-like FM pluck. Uses FM synthesis with an inharmonic modulator ratio of 1.4 and a decaying modulation index for characteristic bell timbres. Adds a higher partial at `frequency * 2.76`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Base frequency in Hz |
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.8 peak, tagged with `["pluck", "bell"]`

**Example:**

```python
from beatmaker.synthesis.plucks import PluckSynth

guitar = PluckSynth.karplus_strong(330.0, 2.0, brightness=0.7)
pluck = PluckSynth.synth_pluck(440.0, 0.5)
bell = PluckSynth.bell(880.0, 3.0)
```

---

## FXSynth

**Module:** `beatmaker.synthesis.fx`

```python
class FXSynth:
```

Synthesizer for special effects and textures. All methods are static and return `Sample` objects.

### `FXSynth.riser`

```python
@staticmethod
def riser(duration: float, start_freq: float = 100,
          end_freq: float = 2000, sample_rate: int = 44100) -> Sample
```

Upward sweeping riser effect. Uses an exponential frequency sweep with a noise layer that fades in over time. Amplitude rises proportionally to the square root of time.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `start_freq` | `float` | `100` | Starting frequency of the sweep in Hz |
| `end_freq` | `float` | `2000` | Ending frequency of the sweep in Hz |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["fx", "riser"]`

---

### `FXSynth.downer`

```python
@staticmethod
def downer(duration: float, start_freq: float = 2000,
           end_freq: float = 50, sample_rate: int = 44100) -> Sample
```

Downward sweep effect. Uses an exponential frequency sweep with a quadratic amplitude decay.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `start_freq` | `float` | `2000` | Starting frequency of the sweep in Hz |
| `end_freq` | `float` | `50` | Ending frequency of the sweep in Hz |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- tagged with `["fx", "downer"]`

---

### `FXSynth.impact`

```python
@staticmethod
def impact(sample_rate: int = 44100) -> Sample
```

Cinematic impact sound. Combines a low 40 Hz boom with an exponential decay and a short white noise transient. Fixed duration of 1.5 seconds.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.95 peak, tagged with `["fx", "impact"]`

---

### `FXSynth.noise_sweep`

```python
@staticmethod
def noise_sweep(duration: float, sample_rate: int = 44100) -> Sample
```

Filtered noise sweep. White noise passed through a bandpass filter at 1500 Hz with 0.6 resonance, shaped by a sine amplitude envelope that peaks at the midpoint.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | `float` | *required* | Duration in seconds |
| `sample_rate` | `int` | `44100` | Audio sample rate |

**Returns:** `Sample` -- normalized to 0.7 peak, tagged with `["fx", "noise"]`

**Example:**

```python
from beatmaker.synthesis.fx import FXSynth

riser = FXSynth.riser(4.0, start_freq=80, end_freq=3000)
downer = FXSynth.downer(2.0)
boom = FXSynth.impact()
sweep = FXSynth.noise_sweep(3.0)
```

---

## Convenience Functions

Shortcut functions that accept a note name string (e.g., `'C4'`) instead of a raw frequency.

### `create_pad`

**Module:** `beatmaker.synthesis.pads`

```python
def create_pad(note: str, duration: float, pad_type: str = 'warm') -> Sample
```

Quick pad creation from a note name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note` | `str` | *required* | Note name with octave (e.g., `'C4'`, `'F#3'`) |
| `duration` | `float` | *required* | Duration in seconds |
| `pad_type` | `str` | `'warm'` | Pad type: `'warm'`, `'string'`, or `'ambient'`. Falls back to `'warm'` for unknown types |

**Returns:** `Sample`

---

### `create_lead`

**Module:** `beatmaker.synthesis.leads`

```python
def create_lead(note: str, duration: float, lead_type: str = 'saw') -> Sample
```

Quick lead creation from a note name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note` | `str` | *required* | Note name with octave (e.g., `'A4'`) |
| `duration` | `float` | *required* | Duration in seconds |
| `lead_type` | `str` | `'saw'` | Lead type: `'saw'`, `'square'`, or `'fm'`. Falls back to `'saw'` for unknown types |

**Returns:** `Sample`

---

### `create_pluck`

**Module:** `beatmaker.synthesis.plucks`

```python
def create_pluck(note: str, duration: float = 1.0, pluck_type: str = 'karplus') -> Sample
```

Quick pluck creation from a note name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note` | `str` | *required* | Note name with octave (e.g., `'E3'`) |
| `duration` | `float` | `1.0` | Duration in seconds |
| `pluck_type` | `str` | `'karplus'` | Pluck type: `'karplus'`, `'synth'`, or `'bell'`. Falls back to `'karplus'` for unknown types |

**Returns:** `Sample`

**Example:**

```python
from beatmaker.synthesis.pads import create_pad
from beatmaker.synthesis.leads import create_lead
from beatmaker.synthesis.plucks import create_pluck

pad = create_pad('C4', 4.0, pad_type='string')
lead = create_lead('A4', 1.0, lead_type='fm')
pluck = create_pluck('E3', 2.0, pluck_type='bell')
```

---

## Music Theory Utilities

**Module:** `beatmaker.music`

Shared music-theory primitives for note, MIDI, and frequency conversions, scale definitions, and chord shapes.

### Constants

#### `NOTE_FREQS`

```python
NOTE_FREQS: dict[str, list[float]]
```

Dictionary mapping natural note names (`'C'` through `'B'`) to a list of frequencies for octaves 0 through 7. For example, `NOTE_FREQS['A'][4]` is `440.0`.

---

### `note_to_freq`

```python
def note_to_freq(note: str) -> float
```

Convert a note name string to its frequency in Hz. Supports naturals, sharps (`#`), and flats (`b`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note` | `str` | *required* | Note name with octave, e.g., `'A4'`, `'C3'`, `'F#3'`, `'Bb2'` |

**Returns:** `float` -- frequency in Hz

**Raises:** `ValueError` if the note name is unrecognized.

```python
>>> note_to_freq('A4')
440.0
>>> note_to_freq('C3')
130.81
```

---

### `midi_to_freq`

```python
def midi_to_freq(midi_note: int) -> float
```

Convert a MIDI note number to frequency in Hz using standard A4=440 Hz tuning.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `midi_note` | `int` | *required* | MIDI note number (0-127) |

**Returns:** `float` -- frequency in Hz

```python
>>> midi_to_freq(69)
440.0
>>> midi_to_freq(60)
261.6255653005986
```

---

### `freq_to_midi`

```python
def freq_to_midi(frequency: float) -> int
```

Convert a frequency in Hz to the nearest MIDI note number.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | `float` | *required* | Frequency in Hz |

**Returns:** `int` -- nearest MIDI note number

```python
>>> freq_to_midi(440.0)
69
>>> freq_to_midi(261.63)
60
```

---

### `note_name_to_midi`

```python
def note_name_to_midi(note: str) -> int
```

Convert a note name to its MIDI note number.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note` | `str` | *required* | Note name with octave, e.g., `'C4'`, `'F#3'`, `'Bb2'` |

**Returns:** `int` -- MIDI note number

```python
>>> note_name_to_midi('C4')
60
>>> note_name_to_midi('A4')
69
>>> note_name_to_midi('F#3')
54
```

---

### `midi_to_note_name`

```python
def midi_to_note_name(midi_note: int) -> str
```

Convert a MIDI note number to its note name string.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `midi_note` | `int` | *required* | MIDI note number |

**Returns:** `str` -- note name with octave, e.g., `'C4'`, `'A4'`

```python
>>> midi_to_note_name(60)
'C4'
>>> midi_to_note_name(69)
'A4'
```

---

### `Scale`

```python
@dataclass
class Scale:
    name: str
    intervals: List[int]
```

Musical scale definition.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable scale name |
| `intervals` | `List[int]` | Semitone intervals from the root note |

#### `Scale.get_notes`

```python
def get_notes(self, root_midi: int, octaves: int = 1) -> List[int]
```

Get MIDI note numbers for the scale starting from a root note.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root_midi` | `int` | *required* | Root MIDI note number |
| `octaves` | `int` | `1` | Number of octaves to generate |

**Returns:** `List[int]` -- list of MIDI note numbers

#### Built-in Scales

| Class Attribute | Intervals |
|----------------|-----------|
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

**Example:**

```python
from beatmaker.music import Scale, note_name_to_midi

# Get C minor pentatonic notes across 2 octaves
root = note_name_to_midi('C3')  # MIDI 48
notes = Scale.MINOR_PENTATONIC.get_notes(root, octaves=2)
# [48, 51, 53, 55, 58, 60, 63, 65, 67, 70]
```

---

### `ChordShape`

```python
@dataclass
class ChordShape:
    name: str
    intervals: List[int]
```

Define a chord by its intervals from the root note.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Chord name |
| `intervals` | `List[int]` | Semitone intervals from root |

#### `ChordShape.custom`

```python
@classmethod
def custom(cls, name: str, intervals: list) -> ChordShape
```

Create a custom chord shape from arbitrary semitone intervals.

#### Built-in Chord Shapes

| Class Attribute | Name | Intervals |
|----------------|------|-----------|
| `ChordShape.MAJOR` | `"major"` | `[0, 4, 7]` |
| `ChordShape.MINOR` | `"minor"` | `[0, 3, 7]` |
| `ChordShape.DIM` | `"dim"` | `[0, 3, 6]` |
| `ChordShape.AUG` | `"aug"` | `[0, 4, 8]` |
| `ChordShape.SUS2` | `"sus2"` | `[0, 2, 7]` |
| `ChordShape.SUS4` | `"sus4"` | `[0, 5, 7]` |
| `ChordShape.MAJOR7` | `"maj7"` | `[0, 4, 7, 11]` |
| `ChordShape.MINOR7` | `"min7"` | `[0, 3, 7, 10]` |
| `ChordShape.DOM7` | `"dom7"` | `[0, 4, 7, 10]` |
| `ChordShape.ADD9` | `"add9"` | `[0, 4, 7, 14]` |
| `ChordShape.DIM7` | `"dim7"` | `[0, 3, 6, 9]` |
| `ChordShape.HALF_DIM7` | `"half_dim7"` | `[0, 3, 6, 10]` |
| `ChordShape.MAJ9` | `"maj9"` | `[0, 4, 7, 11, 14]` |
| `ChordShape.MIN9` | `"min9"` | `[0, 3, 7, 10, 14]` |
| `ChordShape.DOM9` | `"dom9"` | `[0, 4, 7, 10, 14]` |
| `ChordShape.ADD11` | `"add11"` | `[0, 4, 7, 17]` |
| `ChordShape.MAJ13` | `"maj13"` | `[0, 4, 7, 11, 14, 21]` |

**Example:**

```python
from beatmaker.music import ChordShape, note_name_to_midi, midi_to_freq

# Get frequencies for a Cmaj7 chord
root = note_name_to_midi('C4')  # MIDI 60
chord_notes = [root + i for i in ChordShape.MAJOR7.intervals]
# [60, 64, 67, 71]
freqs = [midi_to_freq(n) for n in chord_notes]

# Create a custom chord
power_chord = ChordShape.custom("power", [0, 7, 12])
```
