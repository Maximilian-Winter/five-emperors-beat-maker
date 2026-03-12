# Signal Graph API Reference

Complete API reference for the `beatmaker.graph` module.

The signal graph system provides a **declarative** way to describe audio signal flow. Instead of manually processing buffers, you declare **nodes** (sources, processors, combiners, analyzers, splitters) and **connect** them with the `>>` operator. The graph is then lazily rendered to produce audio.

All node classes inherit from `SignalNode` and implement `.process_graph(inputs, sample_rate, num_samples) -> outputs`.

---

## Quick Start

```python
from beatmaker.graph import SignalGraph, AudioInput, GainNode, FilterNode

with SignalGraph() as g:
    source = AudioInput(my_audio, name="input")
    filt = FilterNode(cutoff=800, resonance=0.5)
    gain = GainNode(level=0.8)
    source >> filt >> gain >> g.sink

result = g.render(duration=2.0)
```

Key concepts:

- **`>>`** connects an output port to an input port (or node to node via default ports)
- **`g.sink`** is the graph output — connect your final node here
- **`g.render(duration)`** evaluates the graph and returns `AudioData`
- Nodes auto-register with the graph inside a `with SignalGraph()` context

---

## SignalGraph

The top-level container and execution engine. Holds nodes and connections, validates the graph, and renders audio via topological sort.

### Constructor

`SignalGraph()`

No parameters. Create via context manager or directly.

### Properties

#### `.sink -> Port`

The graph's output port. Connect your final node here:

```python
my_node >> g.sink
```

### Methods

#### `.add(node: SignalNode) -> SignalNode`

Manually add a node to the graph. Returns the node for chaining. Inside a `with SignalGraph()` block, nodes are auto-added when created or connected.

- **node**: The `SignalNode` to add.
- **Returns**: The same node.

#### `.connect(source: Port, target: Port) -> SignalGraph`

Explicitly connect an output port to an input port. Alternative to the `>>` operator.

- **source**: An output `Port`.
- **target**: An input `Port`.
- **Returns**: `self` for chaining.

#### `.render(duration: float, sample_rate: int = 44100) -> AudioData`

Render the graph to audio. Evaluates all nodes in topological order, routing signals between connected ports.

- **duration**: Output duration in seconds.
- **sample_rate**: Output sample rate (default 44100 Hz).
- **Returns**: `AudioData` with the sink node's output.
- **Raises**: `ValueError` if cycles are detected.

**Rendering rules:**
- Nodes are processed in topological order (sources first, sink last).
- Fan-in: multiple connections to the same input port are summed.
- Fan-out: one output port can feed multiple input ports (no copy needed).
- All buffers are aligned to `duration * sample_rate` samples.

#### `.to_effect(input_node_name: str = "input", **fixed_sources: AudioData) -> GraphEffect`

Wrap the graph as a standard `AudioEffect` for use in `Track.effects`, `EffectChain`, etc.

- **input_node_name**: Name of the `AudioInput` node that receives the effect's input signal.
- **fixed_sources**: Additional named `AudioInput` nodes with fixed audio (e.g., `carrier=synth_audio` for a vocoder).
- **Returns**: A `GraphEffect` instance.

### Context Manager

```python
with SignalGraph() as g:
    # Nodes created here are auto-added to g
    # Connections via >> are auto-registered
    ...
result = g.render(2.0)
```

### Example

```python
with SignalGraph() as g:
    osc = OscillatorNode(frequency=440, waveform='sine')
    gain = GainNode(level=0.5)
    osc >> gain >> g.sink

audio = g.render(duration=1.0)
# audio.samples is a 44100-sample array at half amplitude
```

---

## Port

A named connection point on a `SignalNode`. Ports have a direction (`INPUT` or `OUTPUT`) and support the `>>` operator.

### Properties

- **name** (`str`): Port name (e.g., `"main"`, `"envelope"`, `"band_0"`).
- **node** (`SignalNode`): The node this port belongs to.
- **direction** (`PortDirection`): `INPUT` or `OUTPUT`.

### Operators

#### `port >> port`

Connects an output port to an input port. Returns the target node for chaining.

```python
osc.output("main") >> filt.input("main")
```

#### `port >> node`

Connects to the node's default input port (`"main"`).

```python
osc.output("main") >> filt  # same as above
```

---

## SignalNode

Abstract base class for all graph nodes. Provides port management and the `>>` operator.

### Methods

#### `.input(name: str = "main") -> Port`

Get an input port by name.

- **name**: Port name. Defaults to `"main"`.
- **Returns**: The `Port` object.
- **Raises**: `KeyError` if port name doesn't exist.

#### `.output(name: str = "main") -> Port`

Get an output port by name.

- **name**: Port name. Defaults to `"main"`.
- **Returns**: The `Port` object.
- **Raises**: `KeyError` if port name doesn't exist.

### Operators

#### `node >> node`

Connects default output to default input. Returns the right-hand node:

```python
a >> b >> c  # chains a -> b -> c
```

#### `node >> port`

Connects default output to a specific input port:

```python
osc >> mixer.input("input_0")
```

### Abstract Method

#### `.process_graph(inputs, sample_rate, num_samples) -> Dict[str, np.ndarray]`

Subclasses implement this to define their audio processing.

- **inputs**: `Dict[str, np.ndarray]` — named input arrays.
- **sample_rate**: `int` — the graph's sample rate.
- **num_samples**: `int` — number of samples to produce.
- **Returns**: `Dict[str, np.ndarray]` — named output arrays.

---

# Source Nodes

Nodes that produce audio from nothing (zero input ports).

---

## AudioInput

Injects existing `AudioData` into the graph. This is how external audio enters the signal graph.

### Constructor

`AudioInput(audio: Optional[AudioData] = None, name: str = "input")`

- **audio**: The audio data to inject. Can be `None` if set later via `.set_audio()` (used by `GraphEffect`).
- **name**: Node name. Important for `GraphEffect.to_effect()` matching.

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Output | `main` | The injected audio signal |

### Methods

#### `.set_audio(audio: AudioData)`

Set or replace the audio data. Used internally by `GraphEffect`.

### Example

```python
my_audio = load_audio("voice.wav")
source = AudioInput(my_audio, name="voice")
```

---

## TrackInput

Renders a `Track` and injects the result into the graph.

### Constructor

`TrackInput(track: Track, bpm: float = 120.0, name: str = "track")`

- **track**: The `Track` to render.
- **bpm**: Tempo for rendering (used by automation curves).
- **name**: Node name.

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Output | `main` | The rendered track audio |

---

## OscillatorNode

Generates a periodic waveform for the duration of the graph render.

### Constructor

`OscillatorNode(frequency: float = 440.0, waveform: str = 'sine', amplitude: float = 1.0, name: str = "")`

- **frequency**: Frequency in Hz.
- **waveform**: One of `'sine'`, `'saw'`/`'sawtooth'`, `'square'`, `'triangle'`, `'noise'`/`'white'`, `'pink'`.
- **amplitude**: Output amplitude (0.0 to 1.0).
- **name**: Node name (auto-generated from frequency if empty).

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Output | `main` | The generated waveform |

### Example

```python
lfo = OscillatorNode(frequency=5, waveform='sine', amplitude=0.5, name="lfo")
carrier = OscillatorNode(frequency=440, waveform='saw', name="carrier")
```

---

## NoiseNode

Generates white or pink noise.

### Constructor

`NoiseNode(color: str = 'white', amplitude: float = 1.0, name: str = "noise")`

- **color**: `'white'` or `'pink'`.
- **amplitude**: Output amplitude.
- **name**: Node name.

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Output | `main` | The noise signal |

---

# Processor Nodes

Nodes with one main input and one main output, possibly with additional CV (control voltage) inputs.

---

## EffectNode

Wraps any existing `AudioEffect` as a graph node. This is the backward-compatibility bridge — every `Gain`, `Reverb`, `Compressor`, `Delay`, and `Chorus` can flow through the signal graph.

### Constructor

`EffectNode(effect: AudioEffect, name: str = "")`

- **effect**: Any `AudioEffect` instance (from `beatmaker.effects`, `beatmaker.sidechain`, etc.).
- **name**: Node name (auto-generated from effect class name if empty).

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Input | `main` | Signal to process |
| Output | `main` | Processed signal |

### Example

```python
from beatmaker import Reverb, Delay

reverb = EffectNode(Reverb(room_size=0.7, mix=0.3), name="hall")
delay = EffectNode(Delay(delay_time=0.375, feedback=0.4), name="echo")

source >> reverb >> delay >> g.sink
```

---

## GainNode

Amplitude control with optional CV (control voltage) modulation.

### Constructor

`GainNode(level: float = 1.0, name: str = "gain")`

- **level**: Static gain multiplier. Used when `gain_cv` is not connected.
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `main` | Signal to amplify |
| Input | `gain_cv` | *(Optional)* Per-sample gain control signal. Overrides `level`. |
| Output | `main` | Amplified signal |

### Example

```python
# Static gain
half = GainNode(level=0.5)
source >> half >> g.sink

# CV-controlled gain (amplitude modulation / VCA)
envelope.output("envelope") >> vca.input("gain_cv")
carrier >> vca
```

---

## FilterNode

Resonant biquad filter with optional cutoff modulation.

### Constructor

`FilterNode(cutoff: float = 1000.0, resonance: float = 0.0, filter_type: str = 'lowpass', name: str = "filter")`

- **cutoff**: Cutoff frequency in Hz.
- **resonance**: Filter resonance from `0.0` to `1.0`. Higher values create a peak at the cutoff.
- **filter_type**: One of `'lowpass'`, `'highpass'`, `'bandpass'`.
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `main` | Signal to filter |
| Input | `cutoff_cv` | *(Optional)* Additive cutoff offset in Hz. Enables filter sweeps and auto-wah. |
| Output | `main` | Filtered signal |

### Example

```python
# Static filter
lpf = FilterNode(cutoff=2000, resonance=0.5, filter_type='lowpass')
source >> lpf >> g.sink

# Envelope-controlled filter (auto-wah)
env = EnvelopeFollower(attack=0.001, release=0.05)
env_scaled = GainNode(level=3000)  # scale envelope to Hz range

source >> env
env.output("envelope") >> env_scaled >> wah.input("cutoff_cv")
source >> wah >> g.sink
```

---

## CompressorNode

Dynamic range compressor with optional sidechain input.

### Constructor

`CompressorNode(threshold: float = -10.0, ratio: float = 4.0, attack: float = 0.01, release: float = 0.1, makeup_gain: float = 0.0, name: str = "compressor")`

- **threshold**: Threshold in dB.
- **ratio**: Compression ratio.
- **attack**: Attack time in seconds.
- **release**: Release time in seconds.
- **makeup_gain**: Makeup gain in dB.
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `main` | Signal to compress |
| Input | `sidechain` | *(Optional)* External key signal for envelope detection |
| Output | `main` | Compressed signal |

### Example

```python
# Standard compression
comp = CompressorNode(threshold=-12, ratio=4)
source >> comp >> g.sink

# Sidechain compression (duck pad with kick)
comp = CompressorNode(threshold=-20, ratio=10)
kick >> comp.input("sidechain")
pad >> comp
comp >> g.sink
```

---

# Combiner Nodes

Nodes that merge multiple input signals into one output.

---

## MixNode

Weighted sum of multiple input signals.

### Constructor

`MixNode(num_inputs: int = 2, weights: Optional[List[float]] = None, name: str = "mix")`

- **num_inputs**: Number of input ports to create.
- **weights**: Per-input gain weights. Defaults to equal weighting (`1/num_inputs` each).
- **name**: Node name.

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Input | `input_0` through `input_N-1` | Signals to mix |
| Output | `main` | Weighted sum |

### Example

```python
mixer = MixNode(num_inputs=3, weights=[0.5, 0.3, 0.2])
track_a >> mixer.input("input_0")
track_b >> mixer.input("input_1")
track_c >> mixer.input("input_2")
mixer >> g.sink
```

---

## MultiplyNode

Element-wise multiplication of two signals. The fundamental building block for ring modulation, amplitude modulation, and VCA (voltage-controlled amplifier) behavior.

### Constructor

`MultiplyNode(name: str = "multiply")`

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Input | `a` | First signal |
| Input | `b` | Second signal |
| Output | `main` | `a * b` (element-wise) |

### Example

```python
# Ring modulation
ring = MultiplyNode(name="ring_mod")
audio_source >> ring.input("a")
mod_oscillator >> ring.input("b")
ring >> g.sink

# VCA (carrier * envelope)
vca = MultiplyNode()
carrier >> vca.input("a")
envelope_follower.output("envelope") >> vca.input("b")
```

---

## CrossfadeNode

Blend between two signals with a static or CV-controlled mix parameter.

### Constructor

`CrossfadeNode(mix: float = 0.5, name: str = "crossfade")`

- **mix**: Blend amount. `0.0` = signal `a` only, `1.0` = signal `b` only. Overridden by `mix_cv` if connected.
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `a` | First signal (dry) |
| Input | `b` | Second signal (wet) |
| Input | `mix_cv` | *(Optional)* Per-sample mix control (0.0-1.0) |
| Output | `main` | Blended signal: `a * (1 - mix) + b * mix` |

---

# Analyzer Nodes

Nodes that extract control signals from audio.

---

## EnvelopeFollower

Extracts the amplitude envelope of a signal. Produces a slowly-varying control signal that traces the loudness contour of the input.

### Constructor

`EnvelopeFollower(attack: float = 0.005, release: float = 0.02, name: str = "envelope_follower")`

- **attack**: Attack time in seconds. How fast the envelope rises when signal gets louder.
- **release**: Release time in seconds. How fast the envelope falls when signal gets quieter.
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `main` | Signal to analyze |
| Output | `envelope` | Amplitude envelope (always positive, slowly varying) |

**Note:** The output port is named `"envelope"`, not `"main"`. Use `.output("envelope")` to connect it.

### Example

```python
env = EnvelopeFollower(attack=0.001, release=0.05)
source >> env
env.output("envelope") >> gain_node.input("gain_cv")
```

---

# Splitter Nodes

Nodes that divide a single input into multiple outputs.

---

## FilterBankNode

Splits a signal into frequency bands using cascaded bandpass filters. Given N-1 crossover frequencies, produces N bands.

### Constructor

`FilterBankNode(crossover_freqs: List[float], resonance: float = 0.3, name: str = "filterbank")`

- **crossover_freqs**: List of crossover frequencies in Hz (will be sorted). For N-1 frequencies, produces N bands.
- **resonance**: Filter resonance for each band (0.0 to 1.0).
- **name**: Node name.

### Ports

| Port | Direction | Name | Description |
|------|-----------|------|-------------|
| Input | `main` | Signal to split |
| Output | `band_0` | Lowest band (below first crossover) |
| Output | `band_1` ... `band_N-2` | Middle bands (bandpass between adjacent crossovers) |
| Output | `band_N-1` | Highest band (above last crossover) |

### Example

```python
# 4-band split at 200Hz, 1kHz, 5kHz
bank = FilterBankNode(crossover_freqs=[200, 1000, 5000])
source >> bank

bank.output("band_0")  # Sub bass (< 200 Hz)
bank.output("band_1")  # Low mids (200-1000 Hz)
bank.output("band_2")  # High mids (1000-5000 Hz)
bank.output("band_3")  # Highs (> 5000 Hz)
```

---

## ChannelSplitNode

Splits a signal into left and right channels. For mono input, duplicates to both outputs.

### Constructor

`ChannelSplitNode(name: str = "channel_split")`

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Input | `main` | Signal to split |
| Output | `left` | Left channel |
| Output | `right` | Right channel |

---

## StereoMergeNode

Combines left and right mono signals. Currently outputs the average for mono compatibility.

### Constructor

`StereoMergeNode(name: str = "stereo_merge")`

### Ports

| Port | Direction | Name |
|------|-----------|------|
| Input | `left` | Left channel |
| Input | `right` | Right channel |
| Output | `main` | Combined signal |

---

# GraphEffect

Wraps a `SignalGraph` as a standard `AudioEffect`. Allows signal graphs to be used in `Track.effects`, `EffectChain`, `Song.master_effects`, or anywhere an `AudioEffect` is accepted.

### Constructor

`GraphEffect(graph: SignalGraph, input_node_name: str = "input", fixed_sources: Optional[Dict[str, AudioData]] = None)`

- **graph**: The `SignalGraph` to wrap.
- **input_node_name**: Name of the `AudioInput` node that receives the `process()` input audio.
- **fixed_sources**: Dict of additional named `AudioInput` nodes with fixed audio data.

Typically created via `SignalGraph.to_effect()` rather than directly.

### Methods

#### `.process(audio: AudioData) -> AudioData`

Feeds `audio` into the graph's designated input node, renders the graph, and returns the output. Fixed sources are also updated before rendering.

- **audio**: Input audio to process.
- **Returns**: Processed `AudioData` matching input channels.

### Example

```python
# Build a graph with a named input
with SignalGraph() as g:
    src = AudioInput(name="input")
    fx = EffectNode(Reverb(room_size=0.8, mix=0.4))
    src >> fx >> g.sink

# Wrap as effect and use in a track
effect = g.to_effect(input_node_name="input")
track.add_effect(effect)

# Vocoder as effect (with fixed carrier)
vocoder_effect = vocoder_graph.to_effect(
    input_node_name="voice",
    synth=carrier_audio
)
track.add_effect(vocoder_effect)
```

---

# SongBuilder Integration

## `.add_graph_track(name, graph, duration, track_type=TrackType.FX)`

Added to `SongBuilder`. Renders a signal graph and adds the result as a new track.

- **name**: Track name.
- **graph**: A `SignalGraph` instance.
- **duration**: Duration in seconds.
- **track_type**: `TrackType` (default: `FX`).
- **Returns**: `self` for chaining.

### Example

```python
song = (create_song("My Song")
    .tempo(128)
    .bars(8)
    .add_drums(lambda d: d.four_on_floor())
    .add_graph_track("vocoder_pad", vocoder_graph, duration=4.0)
    .build())
```

---

# Cookbook: Common Patterns

## Ring Modulator

```python
with SignalGraph() as g:
    src = AudioInput(audio)
    mod = OscillatorNode(frequency=80, waveform='sine')
    ring = MultiplyNode()
    src >> ring.input("a")
    mod >> ring.input("b")
    ring >> g.sink
result = g.render(audio.duration)
```

## Parallel (NY) Compression

```python
with SignalGraph() as g:
    src = AudioInput(audio)
    dry = GainNode(level=0.6)
    wet = EffectNode(Compressor(threshold=-20, ratio=8, makeup_gain=6))
    wet_lvl = GainNode(level=0.4)
    mixer = MixNode(num_inputs=2, weights=[1.0, 1.0])
    src >> dry >> mixer.input("input_0")
    src >> wet >> wet_lvl >> mixer.input("input_1")
    mixer >> g.sink
result = g.render(audio.duration)
```

## Auto-Wah (Envelope-Controlled Filter)

```python
with SignalGraph() as g:
    src = AudioInput(audio)
    env = EnvelopeFollower(attack=0.001, release=0.05)
    env_hz = GainNode(level=3000)
    wah = FilterNode(cutoff=200, resonance=0.65, filter_type='bandpass')
    src >> env
    env.output("envelope") >> env_hz >> wah.input("cutoff_cv")
    src >> wah >> g.sink
result = g.render(audio.duration)
```

## Vocoder

```python
num_bands = 16
freqs = np.geomspace(80, 8000, num_bands + 1)[1:-1].tolist()

with SignalGraph() as g:
    voice = AudioInput(voice_audio, name="voice")
    synth = AudioInput(carrier_audio, name="synth")
    mod_bank = FilterBankNode(freqs, name="mod_fb")
    car_bank = FilterBankNode(freqs, name="car_fb")
    voice >> mod_bank
    synth >> car_bank
    mixer = MixNode(num_inputs=num_bands)
    for i in range(num_bands):
        env = EnvelopeFollower(attack=0.002, release=0.015)
        vca = MultiplyNode()
        mod_bank.output(f"band_{i}") >> env
        car_bank.output(f"band_{i}") >> vca.input("a")
        env.output("envelope") >> vca.input("b")
        vca >> mixer.input(f"input_{i}")
    mixer >> g.sink
result = g.render(voice_audio.duration)
```

## Sidechain Compression via Graph

```python
with SignalGraph() as g:
    kick = AudioInput(kick_audio, name="kick")
    pad = AudioInput(pad_audio, name="pad")
    comp = CompressorNode(threshold=-20, ratio=10, attack=0.001, release=0.15)
    kick >> comp.input("sidechain")
    pad >> comp
    comp >> g.sink
result = g.render(pad_audio.duration)
```
