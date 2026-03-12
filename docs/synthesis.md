# Synthesis API Reference

Complete API documentation for the synthesis modules: `beatmaker.synth` and `beatmaker.synths`.

**Source files:**
- `beatmaker/synth.py` -- Core waveform generators, envelopes, oscillator, drum synth, bass synth, and utility functions
- `beatmaker/synths.py` -- Extended synthesizers: LFO, Filter, PadSynth, LeadSynth, PluckSynth, FXSynth, and convenience factories

---

## Table of Contents

- [Waveform (Enum)](#waveform-enum)
- [Waveform Generator Functions](#waveform-generator-functions)
- [ADSREnvelope](#adsrenvelope)
- [Oscillator](#oscillator)
- [DrumSynth](#drumsynth)
- [BassSynth](#basssynth)
- [Utility Functions](#utility-functions)
- [LFO](#lfo)
- [Filter](#filter)
- [PadSynth](#padsynth)
- [LeadSynth](#leadsynth)
- [PluckSynth](#plucksynth)
- [FXSynth](#fxsynth)
- [Convenience Factory Functions](#convenience-factory-functions)
- [Constants](#constants)

---

## Waveform (Enum)

```python
class Waveform(Enum)
```

Enumeration of basic waveform types used by `Oscillator` and other synthesis components.

| Member     | Description              |
|------------|--------------------------|
| `SINE`     | Pure sine wave           |
| `SQUARE`   | Square wave              |
| `SAWTOOTH` | Sawtooth wave            |
| `TRIANGLE` | Triangle wave            |
| `NOISE`    | White noise              |

---

## Waveform Generator Functions

Low-level functions that generate raw waveform data. Each returns an `AudioData` instance.

### `sine_wave(frequency, duration, sample_rate, amplitude) -> AudioData`

Generate a pure sine wave.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `frequency`   | `float` | --      | Frequency in Hz               |
| `duration`    | `float` | --      | Duration in seconds           |
| `sample_rate` | `int`   | `44100` | Sample rate in samples/second |
| `amplitude`   | `float` | `1.0`   | Peak amplitude                |

**Returns:** `AudioData` containing the generated sine wave samples.

```python
audio = sine_wave(440.0, 2.0)               # 440 Hz sine, 2 seconds
audio = sine_wave(261.63, 1.0, amplitude=0.5)  # Quieter middle C
```

---

### `square_wave(frequency, duration, sample_rate, amplitude, duty_cycle) -> AudioData`

Generate a square wave with adjustable duty cycle.

| Parameter     | Type    | Default | Description                                  |
|---------------|---------|---------|----------------------------------------------|
| `frequency`   | `float` | --      | Frequency in Hz                              |
| `duration`    | `float` | --      | Duration in seconds                          |
| `sample_rate` | `int`   | `44100` | Sample rate in samples/second                |
| `amplitude`   | `float` | `1.0`   | Peak amplitude                               |
| `duty_cycle`  | `float` | `0.5`   | Fraction of cycle spent high (0.0 to 1.0)    |

**Returns:** `AudioData` containing the generated square wave samples.

```python
audio = square_wave(220.0, 1.0)                    # Standard 50% duty
audio = square_wave(220.0, 1.0, duty_cycle=0.25)   # Narrow pulse
```

---

### `sawtooth_wave(frequency, duration, sample_rate, amplitude) -> AudioData`

Generate a sawtooth wave (ramp from -1 to +1).

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `frequency`   | `float` | --      | Frequency in Hz               |
| `duration`    | `float` | --      | Duration in seconds           |
| `sample_rate` | `int`   | `44100` | Sample rate in samples/second |
| `amplitude`   | `float` | `1.0`   | Peak amplitude                |

**Returns:** `AudioData`

```python
audio = sawtooth_wave(110.0, 1.0)
```

---

### `triangle_wave(frequency, duration, sample_rate, amplitude) -> AudioData`

Generate a triangle wave.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `frequency`   | `float` | --      | Frequency in Hz               |
| `duration`    | `float` | --      | Duration in seconds           |
| `sample_rate` | `int`   | `44100` | Sample rate in samples/second |
| `amplitude`   | `float` | `1.0`   | Peak amplitude                |

**Returns:** `AudioData`

```python
audio = triangle_wave(330.0, 0.5)
```

---

### `white_noise(duration, sample_rate, amplitude, seed) -> AudioData`

Generate white noise (uniform random samples scaled to [-amplitude, +amplitude]).

| Parameter     | Type            | Default | Description                             |
|---------------|-----------------|---------|-----------------------------------------|
| `duration`    | `float`         | --      | Duration in seconds                     |
| `sample_rate` | `int`           | `44100` | Sample rate in samples/second           |
| `amplitude`   | `float`         | `1.0`   | Peak amplitude                          |
| `seed`        | `Optional[int]` | `None`  | Random seed for reproducible output     |

**Returns:** `AudioData`

```python
audio = white_noise(2.0)
audio = white_noise(1.0, seed=42)  # Reproducible
```

---

### `pink_noise(duration, sample_rate, amplitude, seed) -> AudioData`

Generate pink noise (1/f spectrum) using the Voss-McCartney algorithm. Pink noise has equal energy per octave, giving it a warmer character than white noise.

| Parameter     | Type            | Default | Description                             |
|---------------|-----------------|---------|-----------------------------------------|
| `duration`    | `float`         | --      | Duration in seconds                     |
| `sample_rate` | `int`           | `44100` | Sample rate in samples/second           |
| `amplitude`   | `float`         | `1.0`   | Peak amplitude                          |
| `seed`        | `Optional[int]` | `None`  | Random seed for reproducible output     |

**Returns:** `AudioData` -- The output is normalized so its peak equals `amplitude`.

```python
audio = pink_noise(3.0)
audio = pink_noise(1.0, amplitude=0.5, seed=7)
```

---

## ADSREnvelope

```python
@dataclass
class ADSREnvelope
```

Attack-Decay-Sustain-Release envelope generator. Creates amplitude envelopes for shaping the volume of a sound over time. Implemented as a dataclass.

### Constructor

#### `ADSREnvelope(attack, decay, sustain, release)`

| Parameter | Type    | Default | Description                              |
|-----------|---------|---------|------------------------------------------|
| `attack`  | `float` | `0.01`  | Attack time in seconds (ramp 0 to 1)     |
| `decay`   | `float` | `0.1`   | Decay time in seconds (ramp 1 to sustain)|
| `sustain` | `float` | `0.7`   | Sustain level (0.0 to 1.0)              |
| `release` | `float` | `0.2`   | Release time in seconds (ramp sustain to 0) |

```python
env = ADSREnvelope()                                    # Defaults
env = ADSREnvelope(attack=0.5, decay=0.3, sustain=0.7, release=0.8)  # Slow pad
env = ADSREnvelope(attack=0.001, decay=0.2, sustain=0.0, release=0.1)  # Pluck
```

### Methods

#### `.generate(duration: float, sample_rate: int = 44100) -> np.ndarray`

Generate the envelope as a NumPy array of amplitude values (0.0 to 1.0).

The envelope is divided into four contiguous segments -- attack, decay, sustain, and release -- whose sample counts are derived from the respective time parameters. If the total of attack + decay + release exceeds `duration`, segments are truncated to fit.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `duration`    | `float` | --      | Total envelope duration in seconds |
| `sample_rate` | `int`   | `44100` | Sample rate                   |

**Returns:** `np.ndarray` of shape `(int(duration * sample_rate),)`.

```python
envelope_array = env.generate(2.0)
```

---

#### `.apply(audio: AudioData) -> AudioData`

Apply the envelope to an `AudioData` object by element-wise multiplication. Handles both mono and multi-channel audio. The envelope duration is derived from `audio.duration`.

| Parameter | Type        | Default | Description        |
|-----------|-------------|---------|--------------------|
| `audio`   | `AudioData` | --      | Audio to envelope  |

**Returns:** `AudioData` -- A new `AudioData` with the envelope applied. Preserves `sample_rate` and `channels`.

```python
audio = sine_wave(440.0, 1.0)
shaped = ADSREnvelope(attack=0.05, decay=0.2, sustain=0.6, release=0.3).apply(audio)
```

---

## Oscillator

```python
class Oscillator
```

Versatile oscillator for synthesis. Wraps the low-level waveform generators and adds detune (in cents) and phase offset support.

### Constructor

#### `Oscillator(waveform, detune, phase)`

| Parameter  | Type       | Default          | Description                                  |
|------------|------------|------------------|----------------------------------------------|
| `waveform` | `Waveform` | `Waveform.SINE`  | Waveform type to generate                    |
| `detune`   | `float`    | `0.0`            | Detune amount in cents (100 cents = 1 semitone) |
| `phase`    | `float`    | `0.0`            | Phase offset in radians                      |

```python
osc = Oscillator()                                          # Default sine
osc = Oscillator(Waveform.SAWTOOTH, detune=5.0)            # Slightly sharp saw
osc = Oscillator(Waveform.SQUARE, phase=np.pi / 2)         # Phase-shifted square
```

### Methods

#### `.generate(frequency: float, duration: float, sample_rate: int = 44100) -> AudioData`

Generate audio at the specified frequency. The frequency is adjusted by the oscillator's `detune` value using the formula `frequency * 2^(detune/1200)`. If `phase` is non-zero, the output samples are circularly shifted.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `frequency`   | `float` | --      | Base frequency in Hz          |
| `duration`    | `float` | --      | Duration in seconds           |
| `sample_rate` | `int`   | `44100` | Sample rate                   |

**Returns:** `AudioData`

```python
osc = Oscillator(Waveform.SAWTOOTH, detune=10)
audio = osc.generate(220.0, 2.0)
```

---

## DrumSynth

```python
class DrumSynth
```

Synthesizer optimized for drum and percussion sounds. All methods are static and return `Sample` objects.

### Static Methods

#### `DrumSynth.kick(duration, pitch, punch, sample_rate) -> Sample`

Synthesize a kick drum. Uses a sine wave with a rapid pitch envelope (exponential drop) combined with a short noise transient for the "click" attack.

| Parameter     | Type    | Default | Description                                  |
|---------------|---------|---------|----------------------------------------------|
| `duration`    | `float` | `0.5`   | Sound duration in seconds                    |
| `pitch`       | `float` | `60.0`  | Initial pitch of the pitch envelope (Hz)     |
| `punch`       | `float` | `0.8`   | Amplitude of the click transient (0.0 to 1.0)|
| `sample_rate` | `int`   | `44100` | Sample rate                                  |

**Returns:** `Sample` with name `"kick"` and tags `["drums", "kick"]`.

```python
kick = DrumSynth.kick()
kick = DrumSynth.kick(duration=0.3, pitch=80.0, punch=1.0)
```

---

#### `DrumSynth.snare(duration, tone_pitch, noise_amount, sample_rate) -> Sample`

Synthesize a snare drum. Combines a decaying sine tone (body) with filtered white noise (snare wires).

| Parameter      | Type    | Default | Description                                    |
|----------------|---------|---------|------------------------------------------------|
| `duration`     | `float` | `0.3`   | Sound duration in seconds                      |
| `tone_pitch`   | `float` | `180.0` | Frequency of the body tone in Hz               |
| `noise_amount` | `float` | `0.6`   | Balance between tone and noise (0.0 to 1.0)    |
| `sample_rate`  | `int`   | `44100` | Sample rate                                    |

**Returns:** `Sample` with name `"snare"` and tags `["drums", "snare"]`.

```python
snare = DrumSynth.snare()
snare = DrumSynth.snare(noise_amount=0.8)  # More sizzle
```

---

#### `DrumSynth.hihat(duration, open_amount, sample_rate) -> Sample`

Synthesize a hi-hat. Mixes white noise with metallic sine tones (3 kHz and 6 kHz). The `open_amount` parameter controls the decay time and extends the duration.

| Parameter     | Type    | Default | Description                                          |
|---------------|---------|---------|------------------------------------------------------|
| `duration`    | `float` | `0.1`   | Base duration in seconds                             |
| `open_amount` | `float` | `0.0`   | 0.0 = fully closed, 1.0 = fully open (extends duration by up to 0.4 s and slows decay) |
| `sample_rate` | `int`   | `44100` | Sample rate                                          |

**Returns:** `Sample` with name `"hihat_open"` (if `open_amount > 0.5`) or `"hihat_closed"`, and tags `["drums", "hihat"]`.

```python
closed_hh = DrumSynth.hihat()
open_hh = DrumSynth.hihat(open_amount=0.9)
```

---

#### `DrumSynth.clap(duration, spread, sample_rate) -> Sample`

Synthesize a clap sound. Creates multiple short noise bursts spread over time to simulate the sound of multiple hands, followed by a noise tail. The output is normalized.

| Parameter     | Type    | Default | Description                                      |
|---------------|---------|---------|--------------------------------------------------|
| `duration`    | `float` | `0.2`   | Total duration in seconds                        |
| `spread`      | `float` | `0.02`  | Time spread of the initial bursts in seconds     |
| `sample_rate` | `int`   | `44100` | Sample rate                                      |

**Returns:** `Sample` with name `"clap"` and tags `["drums", "clap"]`. Output is normalized.

```python
clap = DrumSynth.clap()
clap = DrumSynth.clap(spread=0.04)  # Wider spread
```

---

## BassSynth

```python
class BassSynth
```

Synthesizer for bass sounds. All methods are static and return `Sample` objects.

### Static Methods

#### `BassSynth.sub_bass(frequency, duration, envelope, sample_rate) -> Sample`

Generate a pure sub-bass sine wave with an ADSR envelope.

| Parameter     | Type                     | Default | Description                                      |
|---------------|--------------------------|---------|--------------------------------------------------|
| `frequency`   | `float`                  | --      | Frequency in Hz                                  |
| `duration`    | `float`                  | --      | Duration in seconds                              |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope to apply. Default: `ADSREnvelope(0.01, 0.1, 0.8, 0.1)` |
| `sample_rate` | `int`                    | `44100` | Sample rate                                      |

**Returns:** `Sample` with name `"sub_bass_{frequency}hz"` and tags `["bass", "sub"]`.

```python
bass = BassSynth.sub_bass(55.0, 2.0)
bass = BassSynth.sub_bass(40.0, 1.0, envelope=ADSREnvelope(attack=0.05))
```

---

#### `BassSynth.acid_bass(frequency, duration, filter_freq, resonance, envelope, sample_rate) -> Sample`

Classic acid bass sound (303-style). Uses a sawtooth oscillator run through a simple one-pole low-pass filter with an exponentially decaying cutoff envelope.

| Parameter     | Type                     | Default | Description                                      |
|---------------|--------------------------|---------|--------------------------------------------------|
| `frequency`   | `float`                  | --      | Frequency in Hz                                  |
| `duration`    | `float`                  | --      | Duration in seconds                              |
| `filter_freq` | `float`                  | `500.0` | Base filter cutoff frequency in Hz               |
| `resonance`   | `float`                  | `0.7`   | Filter resonance (not directly used in simplified implementation) |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope to apply. Default: `ADSREnvelope(0.001, 0.2, 0.5, 0.1)` |
| `sample_rate` | `int`                    | `44100` | Sample rate                                      |

**Returns:** `Sample` with name `"acid_bass_{frequency}hz"` and tags `["bass", "acid"]`.

```python
acid = BassSynth.acid_bass(110.0, 1.0)
acid = BassSynth.acid_bass(82.41, 0.5, filter_freq=800.0)
```

---

## Utility Functions

### `midi_to_freq(midi_note: int) -> float`

Convert a MIDI note number to frequency in Hz using the standard A440 tuning formula: `440 * 2^((midi_note - 69) / 12)`.

| Parameter   | Type  | Description       |
|-------------|-------|-------------------|
| `midi_note` | `int` | MIDI note number  |

**Returns:** `float` -- Frequency in Hz.

```python
midi_to_freq(69)   # 440.0  (A4)
midi_to_freq(60)   # 261.63 (C4, middle C)
```

---

### `freq_to_midi(frequency: float) -> int`

Convert a frequency in Hz to the nearest MIDI note number.

| Parameter   | Type    | Description      |
|-------------|---------|------------------|
| `frequency` | `float` | Frequency in Hz  |

**Returns:** `int` -- Nearest MIDI note number.

```python
freq_to_midi(440.0)   # 69
freq_to_midi(261.63)  # 60
```

---

### `note_to_freq(note: str) -> float`

Convert a note name string to frequency in Hz. Supports natural notes and sharps. The note string must end with an octave digit (0-7).

| Parameter | Type  | Description                                 |
|-----------|-------|---------------------------------------------|
| `note`    | `str` | Note name, e.g. `"A4"`, `"C3"`, `"F#5"`   |

**Returns:** `float` -- Frequency in Hz.

**Raises:** `ValueError` if the note name is unrecognized.

```python
note_to_freq('A4')   # 440.0
note_to_freq('C3')   # 130.81
note_to_freq('F#5')  # Interpolated between F5 and G5
```

---

## LFO

```python
@dataclass
class LFO
```

Low Frequency Oscillator for modulation. Generates control-rate signals used to modulate parameters such as pitch, filter cutoff, or amplitude. Implemented as a dataclass.

### Constructor

#### `LFO(rate, depth, waveform, phase)`

| Parameter  | Type    | Default  | Description                                                |
|------------|---------|----------|------------------------------------------------------------|
| `rate`     | `float` | `1.0`    | Oscillation rate in Hz                                     |
| `depth`    | `float` | `1.0`    | Modulation depth (output is scaled by this value)          |
| `waveform` | `str`   | `'sine'` | Shape: `'sine'`, `'triangle'`, `'saw'`, `'square'`, `'random'` |
| `phase`    | `float` | `0.0`    | Starting phase (0.0 to 1.0, as a fraction of a cycle)     |

```python
lfo = LFO(rate=0.3, depth=0.02, waveform='sine')
lfo = LFO(rate=4.0, depth=100, waveform='triangle')  # Vibrato-style
lfo = LFO(rate=2.0, depth=1.0, waveform='random')    # Sample-and-hold
```

### Methods

#### `.generate(duration: float, sample_rate: int = 44100) -> np.ndarray`

Generate the LFO signal as a NumPy array. The output range is `[-depth, +depth]`.

For the `'random'` waveform, a sample-and-hold pattern is produced: one random value per LFO cycle, held constant until the next cycle.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `duration`    | `float` | --      | Duration in seconds           |
| `sample_rate` | `int`   | `44100` | Sample rate                   |

**Returns:** `np.ndarray` of shape `(int(duration * sample_rate),)`.

```python
lfo = LFO(rate=5.0, depth=0.5, waveform='triangle')
signal = lfo.generate(2.0)
```

---

## Filter

```python
@dataclass
class Filter
```

Simple resonant biquad filter. Supports low-pass, high-pass, and band-pass modes. Implemented as a dataclass.

### Constructor

#### `Filter(cutoff, resonance, filter_type)`

| Parameter     | Type    | Default      | Description                                                |
|---------------|---------|--------------|------------------------------------------------------------|
| `cutoff`      | `float` | `1000.0`     | Cutoff frequency in Hz                                     |
| `resonance`   | `float` | `0.0`        | Resonance amount (0.0 to 1.0). Maps internally to Q factor as `Q = 0.5 + resonance * 10` |
| `filter_type` | `str`   | `'lowpass'`  | Filter mode: `'lowpass'`, `'highpass'`, or `'bandpass'`    |

```python
lpf = Filter(cutoff=2000, resonance=0.2)
hpf = Filter(cutoff=500, resonance=0.0, filter_type='highpass')
bpf = Filter(cutoff=1500, resonance=0.6, filter_type='bandpass')
```

### Methods

#### `.process(samples: np.ndarray, sample_rate: int) -> np.ndarray`

Apply the filter to an array of samples using a biquad (second-order IIR) implementation. The cutoff frequency is clamped to just below the Nyquist frequency to prevent instability.

| Parameter     | Type          | Default | Description                   |
|---------------|---------------|---------|-------------------------------|
| `samples`     | `np.ndarray`  | --      | Input sample array            |
| `sample_rate` | `int`         | --      | Sample rate in Hz             |

**Returns:** `np.ndarray` -- Filtered samples, same shape as input.

```python
filt = Filter(cutoff=1000, resonance=0.3, filter_type='lowpass')
filtered = filt.process(raw_samples, 44100)
```

---

## PadSynth

```python
class PadSynth
```

Synthesizer for lush pad sounds. Creates warm, evolving textures suitable for ambient and melodic use. All methods are static and return `Sample` objects.

### Static Methods

#### `PadSynth.warm_pad(frequency, duration, num_voices, detune, envelope, sample_rate) -> Sample`

Create a warm detuned pad. Layers multiple voices of mixed sawtooth and sine waves, each detuned slightly from center. Applies a slow sine LFO for movement and a low-pass filter for smoothness.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Base frequency in Hz                                      |
| `duration`    | `float`                  | --      | Note duration in seconds                                  |
| `num_voices`  | `int`                    | `4`     | Number of detuned voices (more voices = thicker sound)    |
| `detune`      | `float`                  | `0.1`   | Total detune spread in semitones                          |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.5, 0.3, 0.7, 0.8)`   |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"warm_pad_{frequency}hz"` and tags `["pad", "warm"]`.

```python
pad = PadSynth.warm_pad(261.63, 4.0)
pad = PadSynth.warm_pad(440.0, 3.0, num_voices=6, detune=0.2)
```

---

#### `PadSynth.string_pad(frequency, duration, envelope, sample_rate) -> Sample`

Create a string-like pad sound. Generates five harmonics (1x through 5x) of sawtooth waves with decreasing amplitude and slight random detuning for a chorus effect. Filtered at 3 kHz and normalized.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Base frequency in Hz                                      |
| `duration`    | `float`                  | --      | Note duration in seconds                                  |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.3, 0.2, 0.8, 0.5)`   |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"string_pad_{frequency}hz"` and tags `["pad", "string"]`.

```python
strings = PadSynth.string_pad(220.0, 3.0)
```

---

#### `PadSynth.ambient_pad(frequency, duration, sample_rate) -> Sample`

Create an evolving ambient pad. Built from a sine fundamental plus 2nd and 3rd harmonics, with subtle white noise and a slow LFO-modulated filter. Uses a very slow envelope (2 s attack, 2 s release). Output is normalized to 0.8 peak.

| Parameter     | Type    | Default | Description                   |
|---------------|---------|---------|-------------------------------|
| `frequency`   | `float` | --      | Base frequency in Hz          |
| `duration`    | `float` | --      | Note duration in seconds      |
| `sample_rate` | `int`   | `44100` | Sample rate                   |

**Returns:** `Sample` with name `"ambient_pad_{frequency}hz"` and tags `["pad", "ambient"]`.

```python
ambient = PadSynth.ambient_pad(130.81, 10.0)
```

---

## LeadSynth

```python
class LeadSynth
```

Synthesizer for lead sounds. Creates cutting, expressive lead tones. All methods are static and return `Sample` objects.

### Static Methods

#### `LeadSynth.saw_lead(frequency, duration, envelope, filter_env, sample_rate) -> Sample`

Classic sawtooth lead with filter envelope. Layers two slightly detuned sawtooth waves (1.005x frequency ratio) and applies a resonant low-pass filter. Output is normalized to 0.9 peak.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Frequency in Hz                                           |
| `duration`    | `float`                  | --      | Duration in seconds                                       |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.01, 0.2, 0.7, 0.3)`  |
| `filter_env`  | `bool`                   | `True`  | Whether to apply the filter envelope                      |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"saw_lead_{frequency}hz"` and tags `["lead", "saw"]`.

```python
lead = LeadSynth.saw_lead(440.0, 1.0)
lead = LeadSynth.saw_lead(330.0, 0.5, filter_env=False)
```

---

#### `LeadSynth.square_lead(frequency, duration, pulse_width, envelope, sample_rate) -> Sample`

Square/pulse wave lead with a sub-oscillator. Generates a pulse wave at the given `pulse_width` and adds a sine sub-oscillator one octave below at 30% mix. Filtered at 3 kHz.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Frequency in Hz                                           |
| `duration`    | `float`                  | --      | Duration in seconds                                       |
| `pulse_width` | `float`                  | `0.5`   | Pulse width (0.0 to 1.0). 0.5 = standard square wave     |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.01, 0.1, 0.8, 0.2)`  |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"square_lead_{frequency}hz"` and tags `["lead", "square"]`.

```python
lead = LeadSynth.square_lead(523.25, 0.5)
lead = LeadSynth.square_lead(440.0, 1.0, pulse_width=0.3)  # Narrower pulse
```

---

#### `LeadSynth.fm_lead(frequency, duration, mod_ratio, mod_index, envelope, sample_rate) -> Sample`

FM synthesis lead. A single-operator FM voice where a modulator sine wave modulates the phase of a carrier sine wave.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Carrier frequency in Hz                                   |
| `duration`    | `float`                  | --      | Duration in seconds                                       |
| `mod_ratio`   | `float`                  | `2.0`   | Ratio of modulator frequency to carrier frequency         |
| `mod_index`   | `float`                  | `3.0`   | Modulation index (depth of FM)                            |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.01, 0.15, 0.6, 0.25)` |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"fm_lead_{frequency}hz"` and tags `["lead", "fm"]`.

```python
lead = LeadSynth.fm_lead(440.0, 1.0)
lead = LeadSynth.fm_lead(330.0, 0.5, mod_ratio=3.0, mod_index=5.0)  # More metallic
```

---

## PluckSynth

```python
class PluckSynth
```

Synthesizer for plucked string sounds. Uses Karplus-Strong and other techniques. All methods are static and return `Sample` objects.

### Static Methods

#### `PluckSynth.karplus_strong(frequency, duration, brightness, sample_rate) -> Sample`

Karplus-Strong plucked string synthesis. Initializes a delay-line buffer with noise and iteratively averages adjacent samples with a damping factor to produce a naturally decaying plucked-string tone. Output is normalized to 0.9 peak.

| Parameter     | Type    | Default | Description                                          |
|---------------|---------|---------|------------------------------------------------------|
| `frequency`   | `float` | --      | Note frequency in Hz (determines delay-line length)  |
| `duration`    | `float` | --      | Duration in seconds                                  |
| `brightness`  | `float` | `0.5`   | Tone brightness from 0.0 (dark/fast decay) to 1.0 (bright/slow decay) |
| `sample_rate` | `int`   | `44100` | Sample rate                                          |

**Returns:** `Sample` with name `"pluck_{frequency}hz"` and tags `["pluck", "string"]`.

```python
pluck = PluckSynth.karplus_strong(440.0, 2.0)
pluck = PluckSynth.karplus_strong(330.0, 1.5, brightness=0.9)  # Brighter
```

---

#### `PluckSynth.synth_pluck(frequency, duration, envelope, sample_rate) -> Sample`

Synthesized pluck sound. Mixes sawtooth (70%) and narrow square (30%, duty 0.3) waves through a resonant low-pass filter with fast envelope decay.

| Parameter     | Type                     | Default | Description                                               |
|---------------|--------------------------|---------|-----------------------------------------------------------|
| `frequency`   | `float`                  | --      | Frequency in Hz                                           |
| `duration`    | `float`                  | --      | Duration in seconds                                       |
| `envelope`    | `Optional[ADSREnvelope]` | `None`  | Envelope. Default: `ADSREnvelope(0.001, 0.3, 0.0, 0.2)` |
| `sample_rate` | `int`                    | `44100` | Sample rate                                               |

**Returns:** `Sample` with name `"synth_pluck_{frequency}hz"` and tags `["pluck", "synth"]`.

```python
pluck = PluckSynth.synth_pluck(440.0, 1.0)
```

---

#### `PluckSynth.bell(frequency, duration, sample_rate) -> Sample`

Bell-like FM pluck. Uses FM synthesis with an inharmonic modulator ratio (1.4x carrier) and exponentially decaying modulation index for a metallic, bell-like tone. Adds an inharmonic partial at 2.76x the carrier. Output is normalized to 0.8 peak.

| Parameter     | Type    | Default | Description          |
|---------------|---------|---------|----------------------|
| `frequency`   | `float` | --      | Frequency in Hz      |
| `duration`    | `float` | --      | Duration in seconds  |
| `sample_rate` | `int`   | `44100` | Sample rate          |

**Returns:** `Sample` with name `"bell_{frequency}hz"` and tags `["pluck", "bell"]`.

```python
bell = PluckSynth.bell(880.0, 3.0)
```

---

## FXSynth

```python
class FXSynth
```

Synthesizer for special effects and textures. All methods are static and return `Sample` objects.

### Static Methods

#### `FXSynth.riser(duration, start_freq, end_freq, sample_rate) -> Sample`

Upward sweeping riser effect. Generates an exponential frequency sweep from `start_freq` to `end_freq`, layered with rising noise. Amplitude increases over time (square-root curve).

| Parameter     | Type    | Default | Description                      |
|---------------|---------|---------|----------------------------------|
| `duration`    | `float` | --      | Duration in seconds              |
| `start_freq`  | `float` | `100`   | Starting frequency in Hz         |
| `end_freq`    | `float` | `2000`  | Ending frequency in Hz           |
| `sample_rate` | `int`   | `44100` | Sample rate                      |

**Returns:** `Sample` with name `"riser"` and tags `["fx", "riser"]`.

```python
riser = FXSynth.riser(4.0)
riser = FXSynth.riser(2.0, start_freq=200, end_freq=5000)
```

---

#### `FXSynth.downer(duration, start_freq, end_freq, sample_rate) -> Sample`

Downward sweep effect. Generates an exponential frequency sweep from `start_freq` down to `end_freq`. Amplitude fades out with an inverse-square curve.

| Parameter     | Type    | Default | Description                      |
|---------------|---------|---------|----------------------------------|
| `duration`    | `float` | --      | Duration in seconds              |
| `start_freq`  | `float` | `2000`  | Starting frequency in Hz         |
| `end_freq`    | `float` | `50`    | Ending frequency in Hz           |
| `sample_rate` | `int`   | `44100` | Sample rate                      |

**Returns:** `Sample` with name `"downer"` and tags `["fx", "downer"]`.

```python
down = FXSynth.downer(3.0)
down = FXSynth.downer(1.0, start_freq=4000, end_freq=100)
```

---

#### `FXSynth.noise_sweep(duration, sample_rate) -> Sample`

Filtered noise sweep. Passes white noise through a resonant band-pass filter (1500 Hz, resonance 0.6) with a sine-shaped amplitude envelope (fades in, peaks at center, fades out). Output is normalized to 0.7 peak.

| Parameter     | Type    | Default | Description          |
|---------------|---------|---------|----------------------|
| `duration`    | `float` | --      | Duration in seconds  |
| `sample_rate` | `int`   | `44100` | Sample rate          |

**Returns:** `Sample` with name `"noise_sweep"` and tags `["fx", "noise"]`.

```python
sweep = FXSynth.noise_sweep(2.0)
```

---

#### `FXSynth.impact(sample_rate) -> Sample`

Cinematic impact sound. Combines a low-frequency boom (40 Hz sine with exponential decay) and a short white-noise transient. Fixed duration of 1.5 seconds. Output is normalized to 0.95 peak.

| Parameter     | Type  | Default | Description |
|---------------|-------|---------|-------------|
| `sample_rate` | `int` | `44100` | Sample rate |

**Returns:** `Sample` with name `"impact"` and tags `["fx", "impact"]`.

```python
hit = FXSynth.impact()
```

---

## Convenience Factory Functions

High-level helper functions defined in `beatmaker/synths.py` that accept note names (e.g. `"A4"`) instead of raw frequencies.

### `create_pad(note: str, duration: float, pad_type: str = 'warm') -> Sample`

Quick pad creation by note name. Internally converts the note to a frequency via `note_to_freq` and delegates to the appropriate `PadSynth` static method.

| Parameter  | Type    | Default  | Description                                        |
|------------|---------|----------|----------------------------------------------------|
| `note`     | `str`   | --       | Note name, e.g. `"C4"`, `"A3"`                    |
| `duration` | `float` | --       | Duration in seconds                                |
| `pad_type` | `str`   | `'warm'` | Pad variant: `'warm'`, `'string'`, or `'ambient'`  |

**Returns:** `Sample` -- Falls back to `'warm'` for unrecognized `pad_type`.

```python
pad = create_pad('C4', 4.0)
pad = create_pad('E3', 6.0, pad_type='ambient')
```

---

### `create_lead(note: str, duration: float, lead_type: str = 'saw') -> Sample`

Quick lead creation by note name. Delegates to the appropriate `LeadSynth` static method.

| Parameter   | Type    | Default | Description                                       |
|-------------|---------|---------|---------------------------------------------------|
| `note`      | `str`   | --      | Note name, e.g. `"A4"`                            |
| `duration`  | `float` | --      | Duration in seconds                               |
| `lead_type` | `str`   | `'saw'` | Lead variant: `'saw'`, `'square'`, or `'fm'`      |

**Returns:** `Sample` -- Falls back to `'saw'` for unrecognized `lead_type`.

```python
lead = create_lead('A4', 1.0)
lead = create_lead('E5', 0.5, lead_type='fm')
```

---

### `create_pluck(note: str, duration: float = 1.0, pluck_type: str = 'karplus') -> Sample`

Quick pluck creation by note name. Delegates to the appropriate `PluckSynth` static method.

| Parameter    | Type    | Default     | Description                                            |
|--------------|---------|-------------|--------------------------------------------------------|
| `note`       | `str`   | --          | Note name, e.g. `"G4"`                                |
| `duration`   | `float` | `1.0`       | Duration in seconds                                    |
| `pluck_type` | `str`   | `'karplus'` | Pluck variant: `'karplus'`, `'synth'`, or `'bell'`    |

**Returns:** `Sample` -- Falls back to `'karplus'` for unrecognized `pluck_type`.

```python
pluck = create_pluck('G4')
pluck = create_pluck('C5', 2.0, pluck_type='bell')
```

---

## Constants

### `NOTE_FREQS`

```python
NOTE_FREQS: dict[str, list[float]]
```

Dictionary mapping note letter names (`'C'` through `'B'`) to lists of frequencies across octaves 0 through 7. Used internally by `note_to_freq`.

| Key | Octave 0 | Octave 4 (middle) | Octave 7   |
|-----|----------|--------------------|------------|
| `C` | 16.35    | 261.63             | 2093.00    |
| `D` | 18.35    | 293.66             | 2349.32    |
| `E` | 20.60    | 329.63             | 2637.02    |
| `F` | 21.83    | 349.23             | 2793.83    |
| `G` | 24.50    | 392.00             | 3135.96    |
| `A` | 27.50    | 440.00             | 3520.00    |
| `B` | 30.87    | 493.88             | 3951.07    |
