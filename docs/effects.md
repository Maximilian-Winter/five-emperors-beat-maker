# Effects & Sidechain API Reference

Complete API reference for the `beatmaker.effects` and `beatmaker.sidechain` modules.

All effect classes inherit from `AudioEffect` and implement the `.process(audio: AudioData) -> AudioData` method. Effects are dataclasses unless otherwise noted.

---

## Gain

Simple gain/volume adjustment. Multiplies all samples by a linear gain factor.

### Constructor

`Gain(level: float = 1.0)`

- **level**: Linear gain multiplier. A value of `1.0` means unity gain (no change), `2.0` doubles the amplitude, `0.5` halves it.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies the gain multiplier to all samples in the audio.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with scaled samples.

#### `@classmethod .from_db(db: float) -> Gain`

Factory method that creates a `Gain` instance from a decibel value. Converts dB to a linear multiplier using `10 ^ (db / 20)`.

- **db**: Gain in decibels. `0.0` is unity, `6.0` roughly doubles amplitude, `-6.0` roughly halves it.
- **Returns**: A new `Gain` instance with the corresponding linear level.

### Example

```python
# Boost by 6 dB
boost = Gain.from_db(6.0)
louder = boost.process(audio)

# Cut volume in half
quiet = Gain(level=0.5).process(audio)
```

---

## Limiter

Hard limiter that clamps sample values to prevent clipping.

### Constructor

`Limiter(threshold: float = 0.95)`

- **threshold**: Maximum absolute sample value. Samples are clipped to the range `[-threshold, threshold]`. Should be between `0.0` and `1.0`.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Clips all samples to the threshold range using `np.clip`.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with clipped samples.

### Example

```python
limiter = Limiter(threshold=0.9)
safe_audio = limiter.process(audio)
```

---

## SoftClipper

Soft clipping effect using hyperbolic tangent (`tanh`) for warm saturation and overdrive character.

### Constructor

`SoftClipper(drive: float = 1.0)`

- **drive**: Amount of drive/saturation. Values greater than `1.0` push the signal harder into the `tanh` curve, producing more saturation. A value of `1.0` applies gentle shaping.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Multiplies samples by the drive amount, then applies `tanh` soft clipping.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with soft-clipped samples.

### Example

```python
saturator = SoftClipper(drive=2.5)
warm_audio = saturator.process(audio)
```

---

## Delay

Simple delay effect with feedback taps. Produces 3 delay taps with exponentially decaying feedback.

### Constructor

`Delay(delay_time: float = 0.25, feedback: float = 0.3, mix: float = 0.5)`

- **delay_time**: Delay time in seconds.
- **feedback**: Feedback amount from `0.0` to `1.0`. Each successive tap is attenuated by `feedback ^ tap_number`.
- **mix**: Wet/dry mix. `0.0` is fully dry (no effect), `1.0` is fully wet.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies the delay effect. Produces 3 feedback taps and mixes wet and dry signals. The output may be longer than the input to accommodate the delay tail.

- **audio**: The input audio to process. Supports both mono and multi-channel audio.
- **Returns**: A new `AudioData` with the delay effect applied. Length is extended by `delay_samples * 2` to include the tail.

### Example

```python
delay = Delay(delay_time=0.375, feedback=0.4, mix=0.35)
echoed = delay.process(audio)
```

---

## Reverb

Simple algorithmic reverb using parallel comb filters followed by series allpass filters.

### Constructor

`Reverb(room_size: float = 0.5, damping: float = 0.5, mix: float = 0.3)`

- **room_size**: Room size from `0.0` to `1.0`. Controls comb filter delay lengths and feedback amounts, simulating small to large spaces.
- **damping**: High-frequency damping from `0.0` to `1.0`. Higher values absorb more high frequencies in the reverb tail.
- **mix**: Wet/dry mix. `0.0` is fully dry, `1.0` is fully wet.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies reverb processing. Stereo input is converted to mono for processing, then expanded back to stereo. Uses 4 parallel comb filters and 2 series allpass filters. Appends a 0.5-second reverb tail.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with reverb applied.

### Example

```python
reverb = Reverb(room_size=0.7, damping=0.4, mix=0.25)
spacious = reverb.process(audio)
```

---

## LowPassFilter

Simple one-pole low-pass filter. Attenuates frequencies above the cutoff.

### Constructor

`LowPassFilter(cutoff: float = 1000.0)`

- **cutoff**: Cutoff frequency in Hz. Frequencies above this are progressively attenuated.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies the one-pole low-pass filter using the standard RC filter formula. The filter coefficient `alpha` is derived from the cutoff frequency and sample rate.

- **audio**: The input audio to process. Supports mono and multi-channel.
- **Returns**: A new `AudioData` with high frequencies attenuated.

### Example

```python
lpf = LowPassFilter(cutoff=500.0)
muffled = lpf.process(audio)
```

---

## HighPassFilter

Simple one-pole high-pass filter. Attenuates frequencies below the cutoff.

### Constructor

`HighPassFilter(cutoff: float = 100.0)`

- **cutoff**: Cutoff frequency in Hz. Frequencies below this are progressively attenuated.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies the one-pole high-pass filter. Removes low-frequency content below the cutoff.

- **audio**: The input audio to process. Supports mono and multi-channel.
- **Returns**: A new `AudioData` with low frequencies attenuated.

### Example

```python
hpf = HighPassFilter(cutoff=80.0)
clean_audio = hpf.process(audio)
```

---

## Compressor

Dynamic range compressor with configurable threshold, ratio, attack, release, and makeup gain.

### Constructor

`Compressor(threshold: float = -10.0, ratio: float = 4.0, attack: float = 0.01, release: float = 0.1, makeup_gain: float = 0.0)`

- **threshold**: Threshold in dB. Signals above this level are compressed.
- **ratio**: Compression ratio. `4.0` means a 4:1 ratio (4 dB of input above threshold produces 1 dB of output above threshold). Higher values produce heavier compression.
- **attack**: Attack time in seconds. How quickly the compressor responds to signals exceeding the threshold.
- **release**: Release time in seconds. How quickly the compressor stops compressing after the signal drops below the threshold.
- **makeup_gain**: Makeup gain in dB applied after compression to compensate for volume reduction.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies dynamic range compression. Uses an envelope follower with separate attack and release coefficients. For multi-channel audio, the envelope is derived from the maximum absolute value across channels.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with compression and makeup gain applied.

### Example

```python
comp = Compressor(threshold=-12.0, ratio=6.0, attack=0.005, release=0.15, makeup_gain=3.0)
compressed = comp.process(audio)
```

---

## BitCrusher

Lo-fi bit depth reduction effect. Reduces bit depth and optionally reduces effective sample rate via sample-and-hold.

### Constructor

`BitCrusher(bit_depth: int = 8, sample_hold: int = 1)`

- **bit_depth**: Target bit depth from 1 to 16. Lower values produce more aggressive quantization and a grittier sound.
- **sample_hold**: Sample-and-hold factor for effective sample rate reduction. A value of `1` means no rate reduction. A value of `4` means every 4th sample is held, reducing the effective sample rate by 4x.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies bit depth reduction by quantizing samples to the specified number of levels (`2 ^ bit_depth`). If `sample_hold > 1`, applies sample-and-hold to reduce effective sample rate.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with reduced bit depth and optional rate reduction.

### Example

```python
crusher = BitCrusher(bit_depth=6, sample_hold=4)
lofi = crusher.process(audio)
```

---

## Chorus

Chorus effect using modulated delay lines. Creates a thicker, wider sound by mixing the dry signal with pitch-modulated copies.

### Constructor

`Chorus(rate: float = 1.5, depth: float = 0.002, mix: float = 0.5, voices: int = 2)`

- **rate**: LFO rate in Hz. Controls the speed of the modulation.
- **depth**: Modulation depth in seconds. Controls how far the delay time is modulated from the 20ms base delay.
- **mix**: Wet/dry mix. `0.0` is fully dry, `1.0` is fully wet.
- **voices**: Number of chorus voices. Each voice uses a different LFO phase offset (evenly distributed).

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies chorus by creating modulated delay lines for each voice. Each voice has a sinusoidal LFO with a phase offset of `voice_index * 2 * pi / voices`. The base delay is 20ms.

- **audio**: The input audio to process. Supports mono and multi-channel.
- **Returns**: A new `AudioData` with the chorus effect applied.

### Example

```python
chorus = Chorus(rate=1.0, depth=0.003, mix=0.4, voices=3)
wide_audio = chorus.process(audio)
```

---

## EffectChain

Chains multiple effects together, processing audio through each effect in sequence. This is not a dataclass; it uses a standard `__init__` constructor.

### Constructor

`EffectChain(*effects: AudioEffect)`

- **effects**: Variable number of `AudioEffect` instances to chain together in order.

### Methods

#### `.add(effect: AudioEffect) -> EffectChain`

Adds an effect to the end of the chain.

- **effect**: The `AudioEffect` to append.
- **Returns**: `self` for method chaining.

#### `.process(audio: AudioData) -> AudioData`

Processes audio through all effects in the chain, in order. The output of each effect becomes the input to the next.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` after passing through all effects.

#### `.__iter__()`

Allows iteration over the effects in the chain.

- **Returns**: An iterator over the list of `AudioEffect` instances.

### Example

```python
chain = EffectChain(
    HighPassFilter(cutoff=80.0),
    Compressor(threshold=-12.0, ratio=4.0),
    Reverb(room_size=0.4, mix=0.2),
    Limiter(threshold=0.95),
)
processed = chain.process(audio)

# Or build incrementally
chain = EffectChain()
chain.add(Gain.from_db(3.0)).add(Limiter())
```

---

# Sidechain Module

Classes for sidechain compression and rhythmic ducking effects.

---

## SidechainCompressor

Sidechain compressor that uses a trigger signal (typically a kick drum) to duck the main signal, creating the classic pumping effect found in electronic music.

### Constructor

`SidechainCompressor(threshold: float = -20.0, ratio: float = 8.0, attack: float = 0.001, release: float = 0.15, hold: float = 0.0, range: float = -24.0)`

- **threshold**: Trigger threshold in dB. When the trigger signal exceeds this level, compression engages.
- **ratio**: Compression ratio. Higher values produce more aggressive ducking.
- **attack**: Attack time in seconds. How quickly the ducking engages when the trigger fires. Default is very fast (1ms).
- **release**: Release time in seconds. How quickly the signal recovers after ducking.
- **hold**: Hold time in seconds before the release phase begins. Keeps the signal ducked for a fixed duration after the trigger drops below threshold.
- **range**: Maximum gain reduction in dB. Limits how much the signal can be ducked (e.g., `-24.0` means at most 24 dB of reduction).

### Methods

#### `.set_trigger(trigger: AudioData) -> SidechainCompressor`

Sets the sidechain trigger signal. This is typically a kick drum or other rhythmic element whose transients drive the ducking.

- **trigger**: The trigger audio signal.
- **Returns**: `self` for method chaining.

#### `.process(audio: AudioData) -> AudioData`

Applies sidechain compression. If no trigger has been set, returns the audio unchanged. The trigger is resampled if its sample rate differs from the audio. For multi-channel triggers, a mono envelope is derived by averaging channels. The envelope is smoothed with attack/release coefficients and an optional hold phase.

- **audio**: The input audio to duck.
- **Returns**: A new `AudioData` with sidechain compression applied.

### Example

```python
sc = SidechainCompressor(threshold=-20.0, ratio=8.0, release=0.15)
sc.set_trigger(kick_audio)
ducked_pad = sc.process(pad_audio)
```

---

## SidechainEnvelope

Envelope-based sidechain effect that creates rhythmic pumping without needing a trigger signal. Generates a volume envelope synchronized to a given tempo and beat pattern.

### Constructor

`SidechainEnvelope(bpm: float = 120.0, pattern: str = "1/4", depth: float = 0.8, attack: float = 0.01, release: float = 0.5, shape: str = "exp", offset: float = 0.0)`

- **bpm**: Tempo in beats per minute.
- **pattern**: Beat division as a fraction string. Supported values include `"1/4"` (quarter notes), `"1/8"` (eighth notes), `"1/2"` (half notes), `"1/1"` (whole notes), or any numeric string.
- **depth**: Ducking depth from `0.0` to `1.0`. `0.0` means no ducking, `1.0` means full silence at the duck point.
- **attack**: Attack curve duration as a fraction of the pattern cycle (`0.0` to `1.0`). `0.0` means instant ducking.
- **release**: Release curve shape factor (`0.0` to `1.0`). Controls how quickly volume recovers after the duck.
- **shape**: Envelope curve shape. One of `"exp"` (exponential), `"linear"`, or `"log"` (logarithmic).
- **offset**: Phase offset in beats. Shifts the envelope start point.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies the generated envelope to the audio. The envelope is a repeating pattern synchronized to the BPM. Supports both mono and multi-channel audio.

- **audio**: The input audio to process.
- **Returns**: A new `AudioData` with the rhythmic ducking applied.

### Example

```python
pump = SidechainEnvelope(bpm=128, pattern="1/4", depth=0.8, shape="exp")
pumping_pad = pump.process(pad_audio)
```

---

## PumpingBass

Specialized sidechain effect for bass lines that pumps with the kick. Internally uses `SidechainEnvelope` with a quarter-note pattern.

### Constructor

`PumpingBass(bpm: float = 120.0, depth: float = 0.9, release: float = 0.3, filter_freq: float = 200.0)`

- **bpm**: Tempo in beats per minute.
- **depth**: Ducking depth from `0.0` to `1.0`.
- **release**: Release time factor for the envelope.
- **filter_freq**: Low-pass filter frequency in Hz (parameter is defined but filtering is not currently applied in the processing).

### Methods

#### `.process(audio: AudioData) -> AudioData`

Applies quarter-note sidechain ducking to the bass audio using `SidechainEnvelope`.

- **audio**: The input bass audio.
- **Returns**: A new `AudioData` with rhythmic ducking applied.

### Example

```python
bass_pump = PumpingBass(bpm=128, depth=0.9, release=0.3)
pumping_bass = bass_pump.process(bass_audio)
```

---

## SidechainBuilder

Fluent builder for constructing sidechain effects. Provides a chainable API to configure either an envelope-based or trigger-based sidechain, then builds the appropriate effect object.

### Constructor

`SidechainBuilder()`

No parameters. Initializes with defaults: type `"envelope"`, bpm `120.0`, depth `0.8`, attack `0.01`, release `0.3`, pattern `"1/4"`, shape `"exp"`, trigger `None`.

### Methods

#### `.tempo(bpm: float) -> SidechainBuilder`

Sets the tempo.

- **bpm**: Tempo in beats per minute.
- **Returns**: `self` for method chaining.

#### `.depth(value: float) -> SidechainBuilder`

Sets the ducking depth.

- **value**: Depth from `0.0` to `1.0`.
- **Returns**: `self` for method chaining.

#### `.attack(seconds: float) -> SidechainBuilder`

Sets the attack time.

- **seconds**: Attack time in seconds.
- **Returns**: `self` for method chaining.

#### `.release(seconds: float) -> SidechainBuilder`

Sets the release time.

- **seconds**: Release time in seconds.
- **Returns**: `self` for method chaining.

#### `.quarter_notes() -> SidechainBuilder`

Sets the pattern to quarter notes (`"1/4"`).

- **Returns**: `self` for method chaining.

#### `.eighth_notes() -> SidechainBuilder`

Sets the pattern to eighth notes (`"1/8"`).

- **Returns**: `self` for method chaining.

#### `.half_notes() -> SidechainBuilder`

Sets the pattern to half notes (`"1/2"`).

- **Returns**: `self` for method chaining.

#### `.pattern(value: str) -> SidechainBuilder`

Sets a custom beat pattern.

- **value**: Pattern string (e.g., `"1/4"`, `"1/8"`, `"3/16"`).
- **Returns**: `self` for method chaining.

#### `.shape_exp() -> SidechainBuilder`

Sets the envelope shape to exponential.

- **Returns**: `self` for method chaining.

#### `.shape_linear() -> SidechainBuilder`

Sets the envelope shape to linear.

- **Returns**: `self` for method chaining.

#### `.shape_log() -> SidechainBuilder`

Sets the envelope shape to logarithmic.

- **Returns**: `self` for method chaining.

#### `.trigger(audio: AudioData) -> SidechainBuilder`

Sets an audio signal as the sidechain trigger. Switches the builder to produce a `SidechainCompressor` instead of a `SidechainEnvelope`.

- **audio**: The trigger audio (e.g., a kick drum track).
- **Returns**: `self` for method chaining.

#### `.from_track(track: Track, sample_rate: int = 44100) -> SidechainBuilder`

Uses a `Track` object as the sidechain trigger. Renders the track to audio and calls `.trigger()`.

- **track**: The `Track` to render as a trigger signal.
- **sample_rate**: Sample rate for rendering the track. Defaults to `44100`.
- **Returns**: `self` for method chaining.

#### `.build() -> AudioEffect`

Builds and returns the configured sidechain effect. If a trigger was set via `.trigger()` or `.from_track()`, returns a `SidechainCompressor`. Otherwise, returns a `SidechainEnvelope`.

- **Returns**: A configured `SidechainCompressor` or `SidechainEnvelope`.

### Example

```python
# Envelope-based sidechain
effect = (create_sidechain()
    .tempo(128)
    .depth(0.85)
    .quarter_notes()
    .shape_exp()
    .release(0.3)
    .build())

pumping = effect.process(pad_audio)

# Trigger-based sidechain
effect = (create_sidechain()
    .trigger(kick_audio)
    .attack(0.001)
    .release(0.2)
    .depth(0.9)
    .build())

ducked = effect.process(synth_audio)
```

---

## SidechainPresets

Static class providing common sidechain preset configurations. All methods return a pre-configured `SidechainEnvelope`.

### Methods

#### `@staticmethod .classic_house(bpm: float = 128) -> SidechainEnvelope`

Classic house music pumping. Quarter-note pattern, 0.7 depth, exponential shape, 0.4 release.

- **bpm**: Tempo. Defaults to `128`.
- **Returns**: A configured `SidechainEnvelope`.

#### `@staticmethod .heavy_edm(bpm: float = 128) -> SidechainEnvelope`

Heavy EDM pumping with aggressive ducking. Quarter-note pattern, 0.95 depth, exponential shape, 0.5 release, 5ms attack.

- **bpm**: Tempo. Defaults to `128`.
- **Returns**: A configured `SidechainEnvelope`.

#### `@staticmethod .subtle_groove(bpm: float = 120) -> SidechainEnvelope`

Subtle groove pumping for understated movement. Quarter-note pattern, 0.3 depth, linear shape, 0.25 release.

- **bpm**: Tempo. Defaults to `120`.
- **Returns**: A configured `SidechainEnvelope`.

#### `@staticmethod .fast_trance(bpm: float = 140) -> SidechainEnvelope`

Fast trance gating effect. Eighth-note pattern, 0.6 depth, exponential shape, 0.2 release.

- **bpm**: Tempo. Defaults to `140`.
- **Returns**: A configured `SidechainEnvelope`.

#### `@staticmethod .half_time(bpm: float = 140) -> SidechainEnvelope`

Half-time feel sidechain. Half-note pattern, 0.5 depth, logarithmic shape, 0.6 release.

- **bpm**: Tempo. Defaults to `140`.
- **Returns**: A configured `SidechainEnvelope`.

### Example

```python
pump = SidechainPresets.classic_house(bpm=126)
pumped = pump.process(pad_audio)

edm = SidechainPresets.heavy_edm(bpm=150)
ducked = edm.process(synth_audio)
```

---

## create_sidechain

`create_sidechain() -> SidechainBuilder`

Module-level factory function that returns a new `SidechainBuilder` instance. This is the recommended entry point for building sidechain effects with the fluent API.

### Example

```python
effect = create_sidechain().tempo(128).depth(0.8).build()
result = effect.process(audio)
```
