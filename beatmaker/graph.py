"""
靈寶五帝策使編碼之法 - Signal Graph Module
A declarative apparatus for weaving audio signals through topological patterns.

As the Jacquard loom weaves flowers and leaves from threads,
so this engine weaves sound from operations upon operations.
The user declares the pattern; the engine throws the shuttles.

By the Azure Dragon's authority,
Let signal flow as water through channels,
Each node a gate, each connection a path,
急急如律令敕
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

from .core import AudioData, AudioEffect, Sample, Track, TrackType
from .synth import (
    Oscillator, Waveform,
    sine_wave, sawtooth_wave, square_wave, triangle_wave,
    white_noise, pink_noise,
)
from .synths import Filter


# ---------------------------------------------------------------------------
# Section 1: Core Types — The Atomic Units of Signal Topology
# ---------------------------------------------------------------------------

class PortDirection(Enum):
    """Direction of a port: whether it receives or emits signal."""
    INPUT = auto()
    OUTPUT = auto()


class Port:
    """
    A named connection point on a SignalNode.

    Ports are the terminals through which signal flows between nodes.
    An output port may connect to one or many input ports (fan-out).
    An input port may receive from one or many output ports (fan-in: summed).

    The >> operator creates connections:
        node_a.output("main") >> node_b.input("main")
    """

    def __init__(self, name: str, node: 'SignalNode', direction: PortDirection):
        self.name = name
        self.node = node
        self.direction = direction

    def __rshift__(self, other):
        """Port >> Port creates a connection in the current graph."""
        if isinstance(other, Port):
            if self.direction != PortDirection.OUTPUT:
                raise ValueError(
                    f"Left side of >> must be an output port, "
                    f"got {self.direction.name} port '{self.name}' on '{self.node.name}'"
                )
            if other.direction != PortDirection.INPUT:
                raise ValueError(
                    f"Right side of >> must be an input port, "
                    f"got {other.direction.name} port '{other.name}' on '{other.node.name}'"
                )
            graph = _get_current_graph()
            if graph is not None:
                graph._ensure_node(self.node)
                graph._ensure_node(other.node)
                graph.connect(self, other)
            return other.node
        elif isinstance(other, SignalNode):
            # Port >> Node: connect to node's default input
            return self >> other.input()
        else:
            return NotImplemented

    def __repr__(self):
        arrow = "→" if self.direction == PortDirection.OUTPUT else "←"
        return f"Port({arrow} {self.node.name}.{self.name})"


class SignalNode(ABC):
    """
    Base class for all signal graph nodes.

    A SignalNode is a unit of audio computation with named input
    and output ports. Subclasses implement process_graph() to define
    their transformation of input signals to output signals.

    The science of operations teaches us that the nature of the
    operation is independent of the subject upon which it acts.
    So too here: each node defines its operation abstractly,
    and the graph engine applies it to whatever signals flow through.
    """

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self._inputs: Dict[str, Port] = {}
        self._outputs: Dict[str, Port] = {}
        self._setup_ports()
        # Auto-register with current graph context
        graph = _get_current_graph()
        if graph is not None:
            graph._ensure_node(self)

    def _setup_ports(self):
        """Override to declare ports. Called during __init__."""
        pass

    def _add_input(self, name: str) -> Port:
        """Declare an input port."""
        port = Port(name, self, PortDirection.INPUT)
        self._inputs[name] = port
        return port

    def _add_output(self, name: str) -> Port:
        """Declare an output port."""
        port = Port(name, self, PortDirection.OUTPUT)
        self._outputs[name] = port
        return port

    def input(self, name: str = "main") -> Port:
        """Get an input port by name."""
        if name not in self._inputs:
            raise KeyError(
                f"Node '{self.name}' has no input port '{name}'. "
                f"Available: {list(self._inputs.keys())}"
            )
        return self._inputs[name]

    def output(self, name: str = "main") -> Port:
        """Get an output port by name."""
        if name not in self._outputs:
            raise KeyError(
                f"Node '{self.name}' has no output port '{name}'. "
                f"Available: {list(self._outputs.keys())}"
            )
        return self._outputs[name]

    def __rshift__(self, other):
        """
        Node >> Node: connect default output to default input.
        Node >> Port: connect default output to specific port.

        Returns the right-hand node to enable chaining:
            a >> b >> c  (connects a→b→c)
        """
        if isinstance(other, SignalNode):
            self.output() >> other.input()
            return other
        elif isinstance(other, Port):
            self.output() >> other
            return other.node
        else:
            return NotImplemented

    @abstractmethod
    def process_graph(self, inputs: Dict[str, np.ndarray],
                      sample_rate: int, num_samples: int) -> Dict[str, np.ndarray]:
        """
        Core processing method.

        Args:
            inputs: Dict mapping input port names to numpy arrays.
                    Missing optional inputs will not be present.
            sample_rate: The graph's sample rate.
            num_samples: The number of samples to produce.

        Returns:
            Dict mapping output port names to numpy arrays.
        """
        pass

    def __repr__(self):
        ins = list(self._inputs.keys())
        outs = list(self._outputs.keys())
        return f"{self.__class__.__name__}('{self.name}', in={ins}, out={outs})"


# ---------------------------------------------------------------------------
# Section 2: SignalGraph Engine — The Analytical Engine of Sound
# ---------------------------------------------------------------------------

# Thread-local storage for the current graph context
_graph_context = threading.local()


def _get_current_graph() -> Optional['SignalGraph']:
    """Get the current graph from thread-local context."""
    return getattr(_graph_context, 'current', None)


def _set_current_graph(graph: Optional['SignalGraph']):
    """Set the current graph in thread-local context."""
    _graph_context.current = graph


@dataclass
class Connection:
    """A directed connection between an output port and an input port."""
    source: Port
    target: Port


class _SinkNode(SignalNode):
    """Internal node representing the graph's output."""

    def _setup_ports(self):
        self._add_input("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        # The sink simply passes through its input
        return {"_result": inputs.get("main", np.zeros(num_samples))}


class SignalGraph:
    """
    A declarative graph of signal processing nodes.

    Build the graph by creating nodes and connecting them with >>,
    then call render() to produce audio. The graph evaluates lazily:
    no audio is processed until render() is called.

    Usage with context manager (recommended):
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            filt = FilterNode(cutoff=1000)
            osc >> filt >> g.sink
        audio = g.render(duration=2.0)

    Usage without context manager:
        g = SignalGraph()
        osc = g.add(OscillatorNode(frequency=440))
        filt = g.add(FilterNode(cutoff=1000))
        g.connect(osc.output(), filt.input())
        g.connect(filt.output(), g.sink)
        audio = g.render(duration=2.0)
    """

    def __init__(self):
        self.nodes: List[SignalNode] = []
        self.connections: List[Connection] = []
        self._sink_node = _SinkNode(name="_sink")
        self._previous_graph: Optional[SignalGraph] = None

    @property
    def sink(self) -> Port:
        """The graph's output port. Connect your final node here."""
        return self._sink_node.input("main")

    def add(self, node: SignalNode) -> SignalNode:
        """Add a node to the graph. Returns the node for chaining."""
        if node not in self.nodes and node is not self._sink_node:
            self.nodes.append(node)
        return node

    def _ensure_node(self, node: SignalNode):
        """Add node if not already present."""
        if node is self._sink_node:
            return
        if node not in self.nodes:
            self.nodes.append(node)

    def connect(self, source: Port, target: Port) -> 'SignalGraph':
        """Explicitly connect an output port to an input port."""
        if source.direction != PortDirection.OUTPUT:
            raise ValueError(f"Source must be an output port, got {source}")
        if target.direction != PortDirection.INPUT:
            raise ValueError(f"Target must be an input port, got {target}")
        self.connections.append(Connection(source, target))
        return self

    def __enter__(self) -> 'SignalGraph':
        """Enter context: set this as the current graph."""
        self._previous_graph = _get_current_graph()
        _set_current_graph(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context: restore previous graph."""
        _set_current_graph(self._previous_graph)
        self._previous_graph = None
        return False

    def _topological_sort(self) -> List[SignalNode]:
        """
        Topological sort of all nodes, respecting connection dependencies.
        Source nodes (no connected inputs) come first; the sink comes last.

        Raises ValueError if cycles are detected.
        """
        all_nodes = self.nodes + [self._sink_node]

        # Build adjacency: node -> set of nodes it depends on
        depends_on: Dict[int, set] = {id(n): set() for n in all_nodes}
        for conn in self.connections:
            target_node = conn.target.node
            source_node = conn.source.node
            depends_on[id(target_node)].add(id(source_node))

        node_by_id = {id(n): n for n in all_nodes}
        sorted_nodes = []
        visited = set()
        in_stack = set()

        def visit(node_id):
            if node_id in in_stack:
                node = node_by_id[node_id]
                raise ValueError(
                    f"Cycle detected in signal graph involving node '{node.name}'"
                )
            if node_id in visited:
                return
            in_stack.add(node_id)
            for dep_id in depends_on[node_id]:
                visit(dep_id)
            in_stack.remove(node_id)
            visited.add(node_id)
            sorted_nodes.append(node_by_id[node_id])

        for node_id in depends_on:
            visit(node_id)

        return sorted_nodes

    def _connections_to(self, port: Port) -> List[Connection]:
        """Find all connections targeting a specific input port."""
        return [c for c in self.connections
                if c.target.node is port.node and c.target.name == port.name]

    def render(self, duration: float, sample_rate: int = 44100) -> AudioData:
        """
        Render the graph to audio.

        Evaluates all nodes in topological order, routing signals
        between connected ports. Fan-in signals are summed.

        Args:
            duration: Output duration in seconds.
            sample_rate: Output sample rate (default 44100 Hz).

        Returns:
            AudioData with the sink node's output.
        """
        num_samples = int(duration * sample_rate)
        order = self._topological_sort()

        # Buffer storage: keyed by (node_id, port_name) for outputs
        buffers: Dict[Tuple[int, str], np.ndarray] = {}

        for node in order:
            # Gather inputs from connected output ports
            inputs: Dict[str, np.ndarray] = {}
            for port_name, port in node._inputs.items():
                conns = self._connections_to(port)
                if conns:
                    # Sum all signals connected to this input (fan-in)
                    signals = []
                    for c in conns:
                        key = (id(c.source.node), c.source.name)
                        if key in buffers:
                            signals.append(buffers[key])
                    if signals:
                        # Align lengths and sum
                        result = np.zeros(num_samples)
                        for sig in signals:
                            length = min(len(sig), num_samples)
                            result[:length] += sig[:length]
                        inputs[port_name] = result

            # Process the node
            outputs = node.process_graph(inputs, sample_rate, num_samples)

            # Store outputs
            for port_name, data in outputs.items():
                buffers[(id(node), port_name)] = data

        # Retrieve sink result
        sink_key = (id(self._sink_node), "_result")
        if sink_key in buffers:
            samples = buffers[sink_key]
            # Ensure correct length
            if len(samples) > num_samples:
                samples = samples[:num_samples]
            elif len(samples) < num_samples:
                padded = np.zeros(num_samples)
                padded[:len(samples)] = samples
                samples = padded
            return AudioData(samples, sample_rate, 1)
        else:
            return AudioData.silence(duration, sample_rate)

    def to_effect(self, input_node_name: str = "input",
                  **fixed_sources: AudioData) -> 'GraphEffect':
        """
        Wrap this graph as a standard AudioEffect.

        The resulting effect can be used in Track.effects, EffectChain, etc.
        When process() is called, the audio is fed into the node named
        `input_node_name`, and the sink output is returned.

        Args:
            input_node_name: Name of the AudioInput node that receives
                            the effect's input signal.
            **fixed_sources: Additional named AudioInput nodes with fixed audio.
                            e.g. carrier=synth_audio for a vocoder.
        """
        return GraphEffect(self, input_node_name, fixed_sources)


# ---------------------------------------------------------------------------
# Section 3: Source Nodes — The Springs from Which Signal Flows
# ---------------------------------------------------------------------------

class AudioInput(SignalNode):
    """
    Injects existing AudioData into the graph.

    This is how external audio enters the signal graph —
    a voice recording, a synthesized tone, a loaded sample.
    """

    def __init__(self, audio: Optional[AudioData] = None,
                 name: str = "input"):
        self.audio = audio
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def set_audio(self, audio: AudioData):
        """Set or replace the audio data (used by GraphEffect)."""
        self.audio = audio

    def process_graph(self, inputs, sample_rate, num_samples):
        if self.audio is None:
            return {"main": np.zeros(num_samples)}

        # Resample if needed
        audio = self.audio
        if audio.sample_rate != sample_rate:
            audio = audio.resample(sample_rate)

        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.to_mono()

        samples = audio.samples
        # Pad or trim to num_samples
        if len(samples) >= num_samples:
            return {"main": samples[:num_samples].copy()}
        else:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            return {"main": padded}


class TrackInput(SignalNode):
    """Render a Track and inject it into the graph."""

    def __init__(self, track: Track, bpm: float = 120.0, name: str = "track"):
        self.track = track
        self.bpm = bpm
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        audio = self.track.render(sample_rate, 1, self.bpm)
        samples = audio.samples
        if len(samples) >= num_samples:
            return {"main": samples[:num_samples].copy()}
        else:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            return {"main": padded}


class OscillatorNode(SignalNode):
    """
    Generates a periodic waveform.

    Wraps the existing Oscillator and waveform generators,
    producing continuous signal for the duration of the graph render.
    """

    def __init__(self, frequency: float = 440.0,
                 waveform: str = 'sine',
                 amplitude: float = 1.0,
                 name: str = ""):
        self.frequency = frequency
        self.waveform = waveform
        self.amplitude = amplitude
        super().__init__(name=name or f"osc_{frequency:.0f}hz")

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        duration = num_samples / sample_rate

        if self.waveform == 'sine':
            audio = sine_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'saw' or self.waveform == 'sawtooth':
            audio = sawtooth_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'square':
            audio = square_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'triangle':
            audio = triangle_wave(self.frequency, duration, sample_rate, self.amplitude)
        elif self.waveform == 'noise' or self.waveform == 'white':
            audio = white_noise(duration, sample_rate, self.amplitude)
        elif self.waveform == 'pink':
            audio = pink_noise(duration, sample_rate, self.amplitude)
        else:
            audio = sine_wave(self.frequency, duration, sample_rate, self.amplitude)

        samples = audio.samples[:num_samples]
        return {"main": samples}


class NoiseNode(SignalNode):
    """Generates white or pink noise."""

    def __init__(self, color: str = 'white', amplitude: float = 1.0,
                 name: str = "noise"):
        self.color = color
        self.amplitude = amplitude
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        duration = num_samples / sample_rate
        if self.color == 'pink':
            audio = pink_noise(duration, sample_rate, self.amplitude)
        else:
            audio = white_noise(duration, sample_rate, self.amplitude)
        return {"main": audio.samples[:num_samples]}


# ---------------------------------------------------------------------------
# Section 4: Processor Nodes — The Operations That Transform
# ---------------------------------------------------------------------------

class EffectNode(SignalNode):
    """
    Wraps any existing AudioEffect as a graph node.

    This is the bridge between the old world and the new —
    every Gain, Reverb, Compressor, Delay, and Chorus can flow
    through the signal graph without modification.
    """

    def __init__(self, effect: AudioEffect, name: str = ""):
        self.effect = effect
        super().__init__(name=name or f"fx_{effect.__class__.__name__}")

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        audio = AudioData(signal, sample_rate, 1)
        result = self.effect.process(audio)
        # Ensure mono and correct length
        if result.channels > 1:
            result = result.to_mono()
        samples = result.samples
        if len(samples) > num_samples:
            samples = samples[:num_samples]
        elif len(samples) < num_samples:
            padded = np.zeros(num_samples)
            padded[:len(samples)] = samples
            samples = padded
        return {"main": samples}


class GainNode(SignalNode):
    """
    Amplitude control with optional CV modulation.

    If a signal is connected to the gain_cv input,
    it is used as a per-sample multiplier (amplitude modulation).
    Otherwise, the static level parameter is applied.
    """

    def __init__(self, level: float = 1.0, name: str = "gain"):
        self.level = level
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("gain_cv")  # Optional: per-sample gain control
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        if "gain_cv" in inputs:
            # Use CV signal as per-sample gain
            cv = inputs["gain_cv"]
            return {"main": signal * cv}
        else:
            return {"main": signal * self.level}


class FilterNode(SignalNode):
    """
    Resonant filter with optional cutoff modulation.

    Wraps the biquad Filter from synths.py. If cutoff_cv is connected,
    the filter cutoff is modulated per-block (not per-sample, for efficiency).
    """

    def __init__(self, cutoff: float = 1000.0, resonance: float = 0.0,
                 filter_type: str = 'lowpass', name: str = "filter"):
        self.cutoff = cutoff
        self.resonance = resonance
        self.filter_type = filter_type
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("cutoff_cv")  # Optional: modulates cutoff
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        if "cutoff_cv" in inputs:
            # CV modulates the cutoff: interpret CV as additive offset in Hz
            cv = inputs["cutoff_cv"]
            # Process in blocks with varying cutoff
            block_size = 256
            output = np.zeros(num_samples)
            for start in range(0, num_samples, block_size):
                end = min(start + block_size, num_samples)
                avg_cv = np.mean(cv[start:end])
                effective_cutoff = max(20.0, self.cutoff + avg_cv)
                filt = Filter(
                    cutoff=effective_cutoff,
                    resonance=self.resonance,
                    filter_type=self.filter_type
                )
                output[start:end] = filt.process(signal[start:end], sample_rate)
            return {"main": output}
        else:
            filt = Filter(
                cutoff=self.cutoff,
                resonance=self.resonance,
                filter_type=self.filter_type
            )
            return {"main": filt.process(signal, sample_rate)}


class CompressorNode(SignalNode):
    """
    Dynamic range compressor with optional sidechain input.

    When a sidechain signal is connected, the compressor's envelope
    follows the sidechain rather than the main input.
    """

    def __init__(self, threshold: float = -10.0, ratio: float = 4.0,
                 attack: float = 0.01, release: float = 0.1,
                 makeup_gain: float = 0.0, name: str = "compressor"):
        self.threshold = threshold
        self.ratio = ratio
        self.attack = attack
        self.release = release
        self.makeup_gain = makeup_gain
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_input("sidechain")  # Optional: external key signal
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        # Use sidechain for envelope detection if connected, else use main
        key_signal = inputs.get("sidechain", signal)

        # Envelope follower
        threshold_linear = 10 ** (self.threshold / 20)
        attack_coef = np.exp(-1 / (self.attack * sample_rate))
        release_coef = np.exp(-1 / (self.release * sample_rate))

        envelope = np.abs(key_signal)
        smooth_env = np.zeros(num_samples)
        smooth_env[0] = envelope[0]
        for i in range(1, num_samples):
            if envelope[i] > smooth_env[i - 1]:
                smooth_env[i] = attack_coef * smooth_env[i - 1] + (1 - attack_coef) * envelope[i]
            else:
                smooth_env[i] = release_coef * smooth_env[i - 1] + (1 - release_coef) * envelope[i]

        # Gain calculation
        gain = np.ones(num_samples)
        above = smooth_env > threshold_linear
        gain[above] = (
            threshold_linear +
            (smooth_env[above] - threshold_linear) / self.ratio
        ) / smooth_env[above]

        output = signal * gain * (10 ** (self.makeup_gain / 20))
        return {"main": output}


# ---------------------------------------------------------------------------
# Section 5: Combiner Nodes — Where Signals Converge
# ---------------------------------------------------------------------------

class MixNode(SignalNode):
    """
    Weighted sum of multiple input signals.

    Input ports are named input_0, input_1, ..., input_N-1.
    Each can have a weight (default: equal weighting).
    """

    def __init__(self, num_inputs: int = 2,
                 weights: Optional[List[float]] = None,
                 name: str = "mix"):
        self.num_inputs = num_inputs
        self.weights = weights or [1.0 / num_inputs] * num_inputs
        super().__init__(name=name)

    def _setup_ports(self):
        for i in range(self.num_inputs):
            self._add_input(f"input_{i}")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        output = np.zeros(num_samples)
        for i in range(self.num_inputs):
            port_name = f"input_{i}"
            if port_name in inputs:
                weight = self.weights[i] if i < len(self.weights) else 1.0
                signal = inputs[port_name]
                length = min(len(signal), num_samples)
                output[:length] += signal[:length] * weight
        return {"main": output}


class MultiplyNode(SignalNode):
    """
    Element-wise multiplication of two signals.

    This is the fundamental building block for:
    - Ring modulation (two audio-rate signals)
    - Amplitude modulation (audio × envelope)
    - VCA (audio × control signal)
    """

    def __init__(self, name: str = "multiply"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("a")
        self._add_input("b")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        a = inputs.get("a", np.zeros(num_samples))
        b = inputs.get("b", np.zeros(num_samples))
        return {"main": a * b}


class CrossfadeNode(SignalNode):
    """
    Blend between two signals with a mix parameter.

    mix=0.0 outputs signal a, mix=1.0 outputs signal b.
    If a mix_cv signal is connected, it overrides the static mix.
    """

    def __init__(self, mix: float = 0.5, name: str = "crossfade"):
        self.mix = mix
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("a")
        self._add_input("b")
        self._add_input("mix_cv")  # Optional: per-sample mix control
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        a = inputs.get("a", np.zeros(num_samples))
        b = inputs.get("b", np.zeros(num_samples))

        if "mix_cv" in inputs:
            mix = np.clip(inputs["mix_cv"], 0.0, 1.0)
        else:
            mix = self.mix

        return {"main": a * (1 - mix) + b * mix}


# ---------------------------------------------------------------------------
# Section 6: Analyzer Nodes — The Perceiving Eye
# ---------------------------------------------------------------------------

class EnvelopeFollower(SignalNode):
    """
    Extracts the amplitude envelope of a signal.

    Produces a slowly-varying control signal that traces
    the loudness contour of the input — the shape of the sound
    made visible. Essential for vocoders, auto-wah, and
    dynamic processing.
    """

    def __init__(self, attack: float = 0.005, release: float = 0.02,
                 name: str = "envelope_follower"):
        self.attack = attack
        self.release = release
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("envelope")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))

        # Rectify
        rectified = np.abs(signal)

        # Smooth with attack/release
        attack_coef = np.exp(-1.0 / (self.attack * sample_rate)) if self.attack > 0 else 0.0
        release_coef = np.exp(-1.0 / (self.release * sample_rate)) if self.release > 0 else 0.0

        envelope = np.zeros(num_samples)
        envelope[0] = rectified[0]

        for i in range(1, num_samples):
            if rectified[i] > envelope[i - 1]:
                envelope[i] = attack_coef * envelope[i - 1] + (1 - attack_coef) * rectified[i]
            else:
                envelope[i] = release_coef * envelope[i - 1] + (1 - release_coef) * rectified[i]

        return {"envelope": envelope}


# ---------------------------------------------------------------------------
# Section 7: Splitter Nodes — The Prism That Separates Light
# ---------------------------------------------------------------------------

class FilterBankNode(SignalNode):
    """
    Splits a signal into frequency bands using cascaded bandpass filters.

    Given N-1 crossover frequencies, produces N bands:
    band_0 (below lowest freq) through band_N-1 (above highest freq).

    This is the essential building block for vocoders,
    multiband compressors, and spectral processing.
    """

    def __init__(self, crossover_freqs: List[float],
                 resonance: float = 0.3,
                 name: str = "filterbank"):
        self.crossover_freqs = sorted(crossover_freqs)
        self.resonance = resonance
        self.num_bands = len(crossover_freqs) + 1
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        for i in range(self.num_bands):
            self._add_output(f"band_{i}")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        outputs = {}

        for i in range(self.num_bands):
            if i == 0:
                # Lowest band: lowpass at first crossover
                filt = Filter(
                    cutoff=self.crossover_freqs[0],
                    resonance=self.resonance,
                    filter_type='lowpass'
                )
                outputs[f"band_{i}"] = filt.process(signal.copy(), sample_rate)
            elif i == self.num_bands - 1:
                # Highest band: highpass at last crossover
                filt = Filter(
                    cutoff=self.crossover_freqs[-1],
                    resonance=self.resonance,
                    filter_type='highpass'
                )
                outputs[f"band_{i}"] = filt.process(signal.copy(), sample_rate)
            else:
                # Middle bands: bandpass between adjacent crossovers
                low_freq = self.crossover_freqs[i - 1]
                high_freq = self.crossover_freqs[i]
                center_freq = np.sqrt(low_freq * high_freq)

                # Bandpass via lowpass then highpass
                lp = Filter(
                    cutoff=high_freq,
                    resonance=self.resonance,
                    filter_type='lowpass'
                )
                hp = Filter(
                    cutoff=low_freq,
                    resonance=self.resonance,
                    filter_type='highpass'
                )
                band = lp.process(signal.copy(), sample_rate)
                band = hp.process(band, sample_rate)
                outputs[f"band_{i}"] = band

        return outputs


class ChannelSplitNode(SignalNode):
    """Split a stereo signal into left and right mono channels."""

    def __init__(self, name: str = "channel_split"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("main")
        self._add_output("left")
        self._add_output("right")

    def process_graph(self, inputs, sample_rate, num_samples):
        signal = inputs.get("main", np.zeros(num_samples))
        # If signal is 1D (mono), duplicate to both outputs
        return {
            "left": signal.copy(),
            "right": signal.copy(),
        }


class StereoMergeNode(SignalNode):
    """Combine left and right mono signals into stereo."""

    def __init__(self, name: str = "stereo_merge"):
        super().__init__(name=name)

    def _setup_ports(self):
        self._add_input("left")
        self._add_input("right")
        self._add_output("main")

    def process_graph(self, inputs, sample_rate, num_samples):
        left = inputs.get("left", np.zeros(num_samples))
        right = inputs.get("right", np.zeros(num_samples))
        # Return interleaved stereo (note: render currently outputs mono)
        # For now, return the mean for mono compatibility
        return {"main": (left + right) * 0.5}


# ---------------------------------------------------------------------------
# Section 8: GraphEffect Adapter — The Bridge Between Worlds
# ---------------------------------------------------------------------------

class GraphEffect(AudioEffect):
    """
    Wraps a SignalGraph as a standard AudioEffect.

    This adapter allows any signal graph to be used wherever an
    AudioEffect is expected: in Track.effects, EffectChain, or
    Song.master_effects.

    The process() input audio is fed into the graph's designated
    AudioInput node. Additional fixed audio sources (e.g., a carrier
    signal for a vocoder) are set via fixed_sources.

    Example:
        graph = build_my_vocoder_graph()
        effect = graph.to_effect(
            input_node_name="voice",
            synth=carrier_audio
        )
        track.add_effect(effect)  # Now the track audio is vocoded!
    """

    def __init__(self, graph: SignalGraph,
                 input_node_name: str = "input",
                 fixed_sources: Optional[Dict[str, AudioData]] = None):
        self._graph = graph
        self._input_node_name = input_node_name
        self._fixed_sources = fixed_sources or {}

    def _find_audio_input(self, name: str) -> Optional[AudioInput]:
        """Find an AudioInput node by name."""
        for node in self._graph.nodes:
            if isinstance(node, AudioInput) and node.name == name:
                return node
        return None

    def process(self, audio: AudioData) -> AudioData:
        """Apply the graph as an effect to the input audio."""
        # Set the main input
        input_node = self._find_audio_input(self._input_node_name)
        if input_node is not None:
            input_node.set_audio(audio)

        # Set fixed sources
        for name, source_audio in self._fixed_sources.items():
            source_node = self._find_audio_input(name)
            if source_node is not None:
                source_node.set_audio(source_audio)

        # Render the graph for the duration of the input
        result = self._graph.render(audio.duration, audio.sample_rate)

        # Match output channels to input
        if audio.channels == 2 and result.channels == 1:
            result = result.to_stereo()
        elif audio.channels == 1 and result.channels == 2:
            result = result.to_mono()

        return result
