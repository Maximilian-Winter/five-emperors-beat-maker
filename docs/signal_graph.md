# Signal Graph

The signal graph is a modular audio processing framework that lets you build
arbitrary signal-flow networks from composable nodes. Instead of a fixed
processing chain, you wire together sources, processors, combiners, and
analysis nodes in any topology -- including fan-out, fan-in, feedback (via
sidechain), and parallel paths.

Source files:
`beatmaker/graph/core.py`, `beatmaker/graph/sources.py`,
`beatmaker/graph/processors.py`, `beatmaker/graph/combiners.py`,
`beatmaker/graph/analysis.py`, `beatmaker/graph/channels.py`,
`beatmaker/graph/bridge.py`

---

## 1. Concept

A **SignalGraph** contains **SignalNode** instances connected through **Port**
objects. Each node has named input and output ports. Signal flows from output
ports to input ports. When multiple outputs connect to the same input (fan-in),
their signals are summed. When one output connects to multiple inputs (fan-out),
the signal is copied.

The `>>` operator is the primary way to connect nodes:

```python
with SignalGraph() as g:
    osc = OscillatorNode(frequency=440)
    filt = FilterNode(cutoff=1000)
    osc >> filt >> g.sink
audio = g.render(duration=2.0)
```

The graph evaluates lazily -- no audio is processed until `render()` is called.
At render time, nodes are topologically sorted so each node processes only after
all its upstream dependencies have produced output. Cycles are detected and
raise a `ValueError`.

---

## 2. Port & PortDirection

```python
from beatmaker.graph.core import Port, PortDirection
```

### PortDirection

An enum with two members:

| Member   | Description                       |
|----------|-----------------------------------|
| `INPUT`  | Port receives signal              |
| `OUTPUT` | Port emits signal                 |

### Port

A named connection point on a `SignalNode`.

| Constructor Param | Type            | Description                |
|-------------------|-----------------|----------------------------|
| `name`            | `str`           | Port name (e.g. `"main"`)  |
| `node`            | `SignalNode`    | The node this port belongs to |
| `direction`       | `PortDirection` | INPUT or OUTPUT             |

#### The `>>` operator

The `>>` operator on ports creates connections in the current graph context:

```python
node_a.output("main") >> node_b.input("main")
```

Rules:
- The left side **must** be an OUTPUT port
- The right side **must** be an INPUT port
- If a `Port >> SignalNode` is used, it connects to the node's default input (`"main"`)
- Returns the right-hand node to enable chaining

---

## 3. SignalNode

```python
from beatmaker.graph.core import SignalNode
```

Abstract base class for all graph nodes. Every node has named input and output
ports and implements a `process_graph()` method that transforms input arrays
into output arrays.

### Constructor

| Parameter | Type  | Default                      | Description                          |
|-----------|-------|------------------------------|--------------------------------------|
| `name`    | `str` | `self.__class__.__name__`    | Node name for debugging / lookup     |

During `__init__`, the node calls `_setup_ports()` (override in subclasses to
declare ports) and auto-registers with the current graph context if one is
active.

### Port Access

#### `input(name: str = "main") -> Port`

Returns the named input port. Raises `KeyError` if the port does not exist.

#### `output(name: str = "main") -> Port`

Returns the named output port. Raises `KeyError` if the port does not exist.

### The `>>` operator

- **`Node >> Node`**: connects default output to default input.
- **`Node >> Port`**: connects default output to the specified port.

Returns the right-hand node, enabling chains like `a >> b >> c`.

### Abstract Method

#### `process_graph(inputs, sample_rate, num_samples) -> Dict[str, np.ndarray]`

| Parameter     | Type                        | Description                                   |
|---------------|-----------------------------|-----------------------------------------------|
| `inputs`      | `Dict[str, np.ndarray]`     | Input signals keyed by input port name         |
| `sample_rate` | `int`                       | The graph's sample rate                        |
| `num_samples` | `int`                       | Number of samples to produce                   |

Returns a dict mapping output port names to numpy arrays.

---

## 4. SignalGraph

```python
from beatmaker.graph.core import SignalGraph
```

The container and engine for a signal-processing graph.

### Constructor

```python
g = SignalGraph()
```

Takes no arguments. Creates an empty graph with an internal sink node.

### Properties

- **`sink -> Port`**: The graph's terminal input port. Connect your final node
  here to define the graph output.

### Methods

#### `add(node: SignalNode) -> SignalNode`

Manually registers a node with the graph. Returns the node for chaining.
Nodes are also auto-registered when created inside a `with SignalGraph()` block
or when connected via `>>`.

#### `connect(source: Port, target: Port) -> SignalGraph`

Explicitly creates a connection between an output port and an input port.
Usually unnecessary -- the `>>` operator does this automatically.

| Parameter | Type   | Description               |
|-----------|--------|---------------------------|
| `source`  | `Port` | Must be an OUTPUT port    |
| `target`  | `Port` | Must be an INPUT port     |

#### `render(duration: float, sample_rate: int = 44100) -> AudioData`

Renders the graph to audio.

| Parameter     | Type    | Default  | Description                   |
|---------------|---------|----------|-------------------------------|
| `duration`    | `float` | --       | Duration in seconds           |
| `sample_rate` | `int`   | `44100`  | Audio sample rate             |

Returns a mono `AudioData` object. Internally:
1. Topologically sorts nodes (raises `ValueError` on cycles)
2. Processes each node in order, routing signals between ports
3. Sums fan-in connections
4. Returns whatever reaches the sink node

#### `to_effect(input_node_name: str = "input", **fixed_sources: AudioData) -> GraphEffect`

Wraps this graph as a standard `AudioEffect`. See the GraphEffect section below.

### Context Manager

The recommended usage pattern:

```python
with SignalGraph() as g:
    # Nodes created here auto-register
    osc = OscillatorNode(frequency=220, waveform='saw')
    filt = FilterNode(cutoff=800, resonance=0.5)
    gain = GainNode(level=0.7)

    osc >> filt >> gain >> g.sink

audio = g.render(duration=3.0, sample_rate=48000)
```

Thread-local storage ensures nested graphs or concurrent graphs do not
interfere with each other.

---

## 5. Source Nodes

Source nodes generate or inject signal into the graph. They have no default
input port -- only outputs.

### AudioInput

```python
from beatmaker.graph.sources import AudioInput
```

Injects existing `AudioData` into the graph.

| Constructor Param | Type                   | Default    | Description                      |
|-------------------|------------------------|------------|----------------------------------|
| `audio`           | `Optional[AudioData]`  | `None`     | Audio data to inject             |
| `name`            | `str`                  | `"input"`  | Node name                        |

**Ports**: output `"main"`

#### `set_audio(audio: AudioData) -> None`

Replace the audio data at runtime (used by `GraphEffect`).

If `audio` is `None` at render time, the node outputs silence.  Stereo audio is
automatically converted to mono. Sample rate mismatches are resolved via
resampling.

```python
with SignalGraph() as g:
    inp = AudioInput(my_audio_data)
    fx = EffectNode(Reverb())
    inp >> fx >> g.sink
```

### TrackInput

```python
from beatmaker.graph.sources import TrackInput
```

Renders a `Track` object and injects the result into the graph.

| Constructor Param | Type    | Default    | Description                  |
|-------------------|---------|------------|------------------------------|
| `track`           | `Track` | --         | The track to render          |
| `bpm`             | `float` | `120.0`    | Tempo for rendering          |
| `name`            | `str`   | `"track"`  | Node name                    |

**Ports**: output `"main"`

### OscillatorNode

```python
from beatmaker.graph.sources import OscillatorNode
```

Generates a periodic waveform for the full render duration.

| Constructor Param | Type    | Default  | Description                                               |
|-------------------|---------|----------|-----------------------------------------------------------|
| `frequency`       | `float` | `440.0`  | Oscillation frequency in Hz                               |
| `waveform`        | `str`   | `'sine'` | `'sine'`, `'saw'`/`'sawtooth'`, `'square'`, `'triangle'`, `'noise'`/`'white'`, `'pink'` |
| `amplitude`       | `float` | `1.0`    | Output amplitude                                          |
| `name`            | `str`   | `""`     | Defaults to `"osc_{frequency}hz"`                         |

**Ports**: output `"main"`

```python
osc = OscillatorNode(frequency=110, waveform='saw', amplitude=0.8)
```

### NoiseNode

```python
from beatmaker.graph.sources import NoiseNode
```

Generates white or pink noise.

| Constructor Param | Type    | Default    | Description                |
|-------------------|---------|------------|----------------------------|
| `color`           | `str`   | `'white'`  | `'white'` or `'pink'`     |
| `amplitude`       | `float` | `1.0`      | Output amplitude           |
| `name`            | `str`   | `"noise"`  | Node name                  |

**Ports**: output `"main"`

---

## 6. Processor Nodes

Processor nodes transform a signal. They have at least one input and one
output port.

### EffectNode

```python
from beatmaker.graph.processors import EffectNode
```

Wraps any existing `AudioEffect` (Gain, Reverb, Compressor, Delay, Chorus,
etc.) as a graph node, without modification.

| Constructor Param | Type          | Default                            | Description          |
|-------------------|---------------|------------------------------------|----------------------|
| `effect`          | `AudioEffect` | --                                 | The effect to wrap   |
| `name`            | `str`         | `"fx_{effect.__class__.__name__}"`  | Node name            |

**Ports**: input `"main"`, output `"main"`

```python
from beatmaker.core import Reverb
with SignalGraph() as g:
    inp = AudioInput(vocal_audio)
    rev = EffectNode(Reverb(room_size=0.7))
    inp >> rev >> g.sink
```

### GainNode

```python
from beatmaker.graph.processors import GainNode
```

Amplitude control with optional CV (control voltage) modulation.

| Constructor Param | Type    | Default   | Description          |
|-------------------|---------|-----------|----------------------|
| `level`           | `float` | `1.0`     | Static gain level    |
| `name`            | `str`   | `"gain"`  | Node name            |

**Ports**: input `"main"`, input `"gain_cv"` (optional), output `"main"`

When `"gain_cv"` is connected, its signal is used as a per-sample multiplier
(amplitude modulation / VCA). When not connected, the static `level` is applied.

```python
with SignalGraph() as g:
    osc = OscillatorNode(440)
    lfo = OscillatorNode(4, waveform='sine', amplitude=0.5)
    vca = GainNode()
    osc >> vca.input("main")
    lfo >> vca.input("gain_cv")
    vca >> g.sink
```

### FilterNode

```python
from beatmaker.graph.processors import FilterNode
```

Resonant biquad filter with optional cutoff modulation.

| Constructor Param | Type    | Default      | Description                            |
|-------------------|---------|--------------|----------------------------------------|
| `cutoff`          | `float` | `1000.0`     | Cutoff frequency in Hz                 |
| `resonance`       | `float` | `0.0`        | Resonance amount                       |
| `filter_type`     | `str`   | `'lowpass'`  | Filter type (passed to `synths.Filter`) |
| `name`            | `str`   | `"filter"`   | Node name                              |

**Ports**: input `"main"`, input `"cutoff_cv"` (optional), output `"main"`

When `"cutoff_cv"` is connected, the cutoff is modulated per block (256
samples). The effective cutoff is `cutoff + mean(cv_block)`, clamped to 20 Hz
minimum.

```python
with SignalGraph() as g:
    osc = OscillatorNode(110, waveform='saw')
    env_lfo = OscillatorNode(0.5, amplitude=500)
    filt = FilterNode(cutoff=300, resonance=0.4)
    osc >> filt.input("main")
    env_lfo >> filt.input("cutoff_cv")
    filt >> g.sink
```

### CompressorNode

```python
from beatmaker.graph.processors import CompressorNode
```

Dynamic range compressor with optional sidechain input.

| Constructor Param | Type    | Default        | Description                         |
|-------------------|---------|----------------|-------------------------------------|
| `threshold`       | `float` | `-10.0`        | Threshold in dB                     |
| `ratio`           | `float` | `4.0`          | Compression ratio                   |
| `attack`          | `float` | `0.01`         | Attack time in seconds              |
| `release`         | `float` | `0.1`          | Release time in seconds             |
| `makeup_gain`     | `float` | `0.0`          | Makeup gain in dB                   |
| `name`            | `str`   | `"compressor"` | Node name                           |

**Ports**: input `"main"`, input `"sidechain"` (optional), output `"main"`

When `"sidechain"` is connected, the compressor's envelope follows the
sidechain signal rather than the main input. This enables classic sidechain
ducking effects.

```python
with SignalGraph() as g:
    pad = AudioInput(pad_audio, name="pad")
    kick = AudioInput(kick_audio, name="kick")
    comp = CompressorNode(threshold=-12, ratio=8, attack=0.001, release=0.15)
    pad >> comp.input("main")
    kick >> comp.input("sidechain")
    comp >> g.sink
```

---

## 7. Combiner Nodes

### MixNode

```python
from beatmaker.graph.combiners import MixNode
```

Weighted sum of multiple input signals.

| Constructor Param | Type                    | Default                        | Description                          |
|-------------------|-------------------------|--------------------------------|--------------------------------------|
| `num_inputs`      | `int`                   | `2`                            | Number of input ports                |
| `weights`         | `Optional[List[float]]` | `[1/num_inputs] * num_inputs`  | Per-input weights                    |
| `name`            | `str`                   | `"mix"`                        | Node name                            |

**Ports**: inputs `"input_0"` through `"input_{N-1}"`, output `"main"`

```python
with SignalGraph() as g:
    osc1 = OscillatorNode(220, waveform='saw')
    osc2 = OscillatorNode(221, waveform='saw')  # slight detune
    mixer = MixNode(num_inputs=2, weights=[0.5, 0.5])
    osc1 >> mixer.input("input_0")
    osc2 >> mixer.input("input_1")
    mixer >> g.sink
```

### MultiplyNode

```python
from beatmaker.graph.combiners import MultiplyNode
```

Element-wise multiplication of two signals. Used for ring modulation,
amplitude modulation, and VCA behaviour.

| Constructor Param | Type  | Default      | Description |
|-------------------|-------|--------------|-------------|
| `name`            | `str` | `"multiply"` | Node name   |

**Ports**: input `"a"`, input `"b"`, output `"main"`

Output = `a * b` (sample by sample).

```python
with SignalGraph() as g:
    carrier = OscillatorNode(440)
    modulator = OscillatorNode(3, amplitude=0.5)
    ring = MultiplyNode()
    carrier >> ring.input("a")
    modulator >> ring.input("b")
    ring >> g.sink
```

### CrossfadeNode

```python
from beatmaker.graph.combiners import CrossfadeNode
```

Blends between two signals using an equal-power-style linear crossfade.

| Constructor Param | Type    | Default       | Description                               |
|-------------------|---------|---------------|-------------------------------------------|
| `mix`             | `float` | `0.5`         | Static mix (0.0 = full A, 1.0 = full B)  |
| `name`            | `str`   | `"crossfade"` | Node name                                 |

**Ports**: input `"a"`, input `"b"`, input `"mix_cv"` (optional), output `"main"`

Output = `a * (1 - mix) + b * mix`.

When `"mix_cv"` is connected, its per-sample values (clamped 0..1) override the
static `mix` parameter.

```python
with SignalGraph() as g:
    dry = AudioInput(vocals)
    wet = EffectNode(Reverb())
    dry >> wet  # feed dry into reverb

    xfade = CrossfadeNode(mix=0.3)
    dry >> xfade.input("a")
    wet >> xfade.input("b")
    xfade >> g.sink
```

---

## 8. Analysis Nodes

### EnvelopeFollower

```python
from beatmaker.graph.analysis import EnvelopeFollower
```

Extracts the amplitude envelope of a signal, producing a slowly-varying
control signal.

| Constructor Param | Type    | Default                | Description                |
|-------------------|---------|------------------------|----------------------------|
| `attack`          | `float` | `0.005`                | Attack time in seconds     |
| `release`         | `float` | `0.02`                 | Release time in seconds    |
| `name`            | `str`   | `"envelope_follower"`  | Node name                  |

**Ports**: input `"main"`, output `"envelope"`

The output port is named `"envelope"` (not `"main"`), so connections must
target it explicitly:

```python
with SignalGraph() as g:
    src = AudioInput(my_audio)
    follower = EnvelopeFollower(attack=0.01, release=0.05)
    gain = GainNode()

    src >> follower
    follower.output("envelope") >> gain.input("gain_cv")
    src >> gain.input("main")
    gain >> g.sink
```

### FilterBankNode

```python
from beatmaker.graph.analysis import FilterBankNode
```

Splits a signal into frequency bands using cascaded bandpass filters.
Given N-1 crossover frequencies, produces N output bands.

| Constructor Param  | Type           | Default         | Description                        |
|--------------------|----------------|-----------------|------------------------------------|
| `crossover_freqs`  | `List[float]`  | --              | Crossover frequencies (sorted)     |
| `resonance`        | `float`        | `0.3`           | Filter resonance for all bands     |
| `name`             | `str`          | `"filterbank"`  | Node name                          |

**Ports**: input `"main"`, outputs `"band_0"` through `"band_N-1"`

- `band_0` = lowpass below the lowest crossover frequency
- `band_{N-1}` = highpass above the highest crossover frequency
- Middle bands = bandpass between adjacent crossover frequencies

```python
with SignalGraph() as g:
    src = AudioInput(full_mix)
    bank = FilterBankNode(crossover_freqs=[200, 2000, 8000])
    src >> bank

    # Process each band independently
    low_gain = GainNode(level=1.2, name="low_boost")
    mid_gain = GainNode(level=0.8, name="mid_cut")
    hi_gain = GainNode(level=1.0, name="hi_flat")
    air_gain = GainNode(level=1.5, name="air_boost")

    bank.output("band_0") >> low_gain
    bank.output("band_1") >> mid_gain
    bank.output("band_2") >> hi_gain
    bank.output("band_3") >> air_gain

    mixer = MixNode(num_inputs=4, weights=[1, 1, 1, 1])
    low_gain >> mixer.input("input_0")
    mid_gain >> mixer.input("input_1")
    hi_gain >> mixer.input("input_2")
    air_gain >> mixer.input("input_3")
    mixer >> g.sink
```

---

## 9. Channel Nodes

### ChannelSplitNode

```python
from beatmaker.graph.channels import ChannelSplitNode
```

Splits a signal into left and right mono channels.

| Constructor Param | Type  | Default            | Description |
|-------------------|-------|--------------------|-------------|
| `name`            | `str` | `"channel_split"`  | Node name   |

**Ports**: input `"main"`, outputs `"left"` and `"right"`

Note: in the current implementation, both outputs receive a copy of the
mono input signal. This is designed for graph topologies where different
processing is applied to each path before merging.

### StereoMergeNode

```python
from beatmaker.graph.channels import StereoMergeNode
```

Combines left and right mono signals by averaging.

| Constructor Param | Type  | Default            | Description |
|-------------------|-------|--------------------|-------------|
| `name`            | `str` | `"stereo_merge"`   | Node name   |

**Ports**: inputs `"left"` and `"right"`, output `"main"`

Output = `(left + right) * 0.5`.

```python
with SignalGraph() as g:
    src = AudioInput(audio)
    split = ChannelSplitNode()
    src >> split

    left_fx = EffectNode(Delay(time=0.3), name="left_delay")
    right_fx = EffectNode(Delay(time=0.45), name="right_delay")

    split.output("left") >> left_fx
    split.output("right") >> right_fx

    merge = StereoMergeNode()
    left_fx >> merge.input("left")
    right_fx >> merge.input("right")
    merge >> g.sink
```

---

## 10. GraphEffect

```python
from beatmaker.graph.bridge import GraphEffect
```

An adapter that wraps a `SignalGraph` as a standard `AudioEffect`, so it can
be used in `Track.effects`, `EffectChain`, or `Song.master_effects`.

### Constructor

| Parameter         | Type                              | Default    | Description                                           |
|-------------------|-----------------------------------|------------|-------------------------------------------------------|
| `graph`           | `SignalGraph`                     | --         | The graph to wrap                                     |
| `input_node_name` | `str`                             | `"input"`  | Name of the `AudioInput` node that receives the input |
| `fixed_sources`   | `Optional[Dict[str, AudioData]]`  | `None`     | Additional named audio sources (e.g. carrier for vocoder) |

### `process(audio: AudioData) -> AudioData`

Feeds the input audio into the graph's designated `AudioInput` node, sets any
fixed sources, calls `render()`, and returns the result. Channel counts are
automatically matched between input and output.

### Usage

The easiest way to create a `GraphEffect` is via `SignalGraph.to_effect()`:

```python
with SignalGraph() as g:
    inp = AudioInput(name="input")
    filt = FilterNode(cutoff=500, resonance=0.6)
    gain = GainNode(level=0.8)
    inp >> filt >> gain >> g.sink

effect = g.to_effect(input_node_name="input")

# Now use it like any other AudioEffect
track.effects.append(effect)
```

For a vocoder-style setup with a fixed carrier:

```python
with SignalGraph() as g:
    voice = AudioInput(name="input")
    carrier = AudioInput(name="carrier")
    # ... vocoder processing ...

effect = g.to_effect(
    input_node_name="input",
    carrier=carrier_audio  # passed as fixed_sources
)
```
