"""
Core graph infrastructure: ports, nodes, connections, and the SignalGraph engine.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..core import AudioData


# ---------------------------------------------------------------------------
# Port and Node Types
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
        arrow = "\u2192" if self.direction == PortDirection.OUTPUT else "\u2190"
        return f"Port({arrow} {self.node.name}.{self.name})"


class SignalNode(ABC):
    """
    Base class for all signal graph nodes.

    A SignalNode is a unit of audio computation with named input
    and output ports. Subclasses implement process_graph() to define
    their transformation of input signals to output signals.
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
            a >> b >> c  (connects a->b->c)
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
# Thread-local context management
# ---------------------------------------------------------------------------

_graph_context = threading.local()


def _get_current_graph() -> Optional['SignalGraph']:
    """Get the current graph from thread-local context."""
    return getattr(_graph_context, 'current', None)


def _set_current_graph(graph: Optional['SignalGraph']):
    """Set the current graph in thread-local context."""
    _graph_context.current = graph


# ---------------------------------------------------------------------------
# Connection and SignalGraph
# ---------------------------------------------------------------------------

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
        Raises ValueError if cycles are detected.
        """
        all_nodes = self.nodes + [self._sink_node]

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
        """
        num_samples = int(duration * sample_rate)
        order = self._topological_sort()

        buffers: Dict[Tuple[int, str], np.ndarray] = {}

        for node in order:
            inputs: Dict[str, np.ndarray] = {}
            for port_name, port in node._inputs.items():
                conns = self._connections_to(port)
                if conns:
                    signals = []
                    for c in conns:
                        key = (id(c.source.node), c.source.name)
                        if key in buffers:
                            signals.append(buffers[key])
                    if signals:
                        result = np.zeros(num_samples)
                        for sig in signals:
                            length = min(len(sig), num_samples)
                            result[:length] += sig[:length]
                        inputs[port_name] = result

            outputs = node.process_graph(inputs, sample_rate, num_samples)

            for port_name, data in outputs.items():
                buffers[(id(node), port_name)] = data

        sink_key = (id(self._sink_node), "_result")
        if sink_key in buffers:
            samples = buffers[sink_key]
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
        """Wrap this graph as a standard AudioEffect."""
        from .bridge import GraphEffect
        return GraphEffect(self, input_node_name, fixed_sources)
