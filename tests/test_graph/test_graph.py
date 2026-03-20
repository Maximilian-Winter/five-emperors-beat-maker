"""
Tests for the beatmaker.graph subpackage.
"""

import numpy as np
import pytest

from beatmaker.graph import (
    PortDirection,
    Port,
    SignalNode,
    Connection,
    SignalGraph,
    AudioInput,
    OscillatorNode,
    NoiseNode,
    GainNode,
    FilterNode,
    CompressorNode,
    MixNode,
    MultiplyNode,
    CrossfadeNode,
    EnvelopeFollower,
    FilterBankNode,
    ChannelSplitNode,
    StereoMergeNode,
    GraphEffect,
    EffectNode,
)
from beatmaker.core import AudioData


# ---------------------------------------------------------------------------
# Port tests
# ---------------------------------------------------------------------------

class TestPort:
    def test_port_direction(self):
        assert PortDirection.INPUT != PortDirection.OUTPUT

    def test_port_rshift_output_to_input(self):
        """Output >> Input should work inside a graph context."""
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            gain = GainNode(level=0.5)
            result = osc.output("main") >> gain.input("main")
            assert result is gain

    def test_port_rshift_input_to_input_raises(self):
        """Input >> Input should raise ValueError."""
        with SignalGraph() as g:
            gain1 = GainNode(level=1.0, name="g1")
            gain2 = GainNode(level=1.0, name="g2")
            with pytest.raises(ValueError, match="output port"):
                gain1.input("main") >> gain2.input("main")

    def test_port_repr(self):
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            port = osc.output("main")
            assert "osc_440hz" in repr(port)


# ---------------------------------------------------------------------------
# SignalNode tests
# ---------------------------------------------------------------------------

class TestSignalNode:
    def test_node_rshift_chaining(self):
        """Node >> Node >> Node should chain connections."""
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            gain = GainNode(level=0.5)
            filt = FilterNode(cutoff=1000)
            result = osc >> gain >> filt
            assert result is filt
            # Graph should have 3 nodes and 2 connections
            assert len(g.nodes) == 3
            assert len(g.connections) == 2

    def test_node_input_keyerror(self):
        osc = OscillatorNode(frequency=440)
        with pytest.raises(KeyError, match="no input port"):
            osc.input("nonexistent")

    def test_node_output_keyerror(self):
        gain = GainNode()
        with pytest.raises(KeyError, match="no output port"):
            gain.output("nonexistent")


# ---------------------------------------------------------------------------
# SignalGraph tests
# ---------------------------------------------------------------------------

class TestSignalGraph:
    def test_render_silence(self):
        """Empty graph should render silence."""
        g = SignalGraph()
        audio = g.render(duration=0.1, sample_rate=44100)
        assert isinstance(audio, AudioData)
        assert audio.sample_rate == 44100
        assert np.allclose(audio.samples, 0.0)

    def test_render_oscillator(self):
        """Oscillator connected to sink should produce non-silent audio."""
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440, amplitude=1.0)
            osc >> g.sink
        audio = g.render(duration=0.1, sample_rate=44100)
        assert audio.sample_rate == 44100
        assert not np.allclose(audio.samples, 0.0)
        # Check length
        expected_samples = int(0.1 * 44100)
        assert len(audio.samples) == expected_samples

    def test_render_gain(self):
        """GainNode should scale the signal."""
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440, amplitude=1.0)
            gain = GainNode(level=0.5)
            osc >> gain >> g.sink
        audio_half = g.render(duration=0.05, sample_rate=22050)

        with SignalGraph() as g2:
            osc2 = OscillatorNode(frequency=440, amplitude=1.0)
            osc2 >> g2.sink
        audio_full = g2.render(duration=0.05, sample_rate=22050)

        # Half-gain signal should have roughly half the amplitude
        ratio = np.max(np.abs(audio_half.samples)) / np.max(np.abs(audio_full.samples))
        assert 0.45 < ratio < 0.55

    def test_context_manager_nesting(self):
        """Nested graph contexts should restore correctly."""
        with SignalGraph() as outer:
            from beatmaker.graph.core import _get_current_graph
            assert _get_current_graph() is outer
            with SignalGraph() as inner:
                assert _get_current_graph() is inner
            assert _get_current_graph() is outer
        assert _get_current_graph() is None

    def test_cycle_detection(self):
        """Graph with a cycle should raise ValueError."""
        g = SignalGraph()
        gain1 = GainNode(level=1.0, name="g1")
        gain2 = GainNode(level=1.0, name="g2")
        g.add(gain1)
        g.add(gain2)
        g.connect(gain1.output(), gain2.input())
        g.connect(gain2.output(), gain1.input())
        with pytest.raises(ValueError, match="Cycle detected"):
            g.render(duration=0.01)

    def test_add_node(self):
        g = SignalGraph()
        osc = OscillatorNode(frequency=220)
        g.add(osc)
        assert osc in g.nodes
        # Adding again should not duplicate
        g.add(osc)
        assert g.nodes.count(osc) == 1

    def test_audio_input(self):
        """AudioInput should inject audio data into the graph."""
        samples = np.sin(2 * np.pi * 440 * np.arange(4410) / 44100).astype(np.float64)
        audio_data = AudioData(samples, 44100, 1)

        with SignalGraph() as g:
            inp = AudioInput(audio=audio_data)
            inp >> g.sink
        result = g.render(duration=0.1, sample_rate=44100)
        assert not np.allclose(result.samples, 0.0)


# ---------------------------------------------------------------------------
# Node type tests
# ---------------------------------------------------------------------------

class TestNodeTypes:
    def test_noise_node(self):
        with SignalGraph() as g:
            noise = NoiseNode(color='white', amplitude=0.5)
            noise >> g.sink
        audio = g.render(duration=0.05, sample_rate=22050)
        assert not np.allclose(audio.samples, 0.0)

    def test_mix_node(self):
        with SignalGraph() as g:
            osc1 = OscillatorNode(frequency=440)
            osc2 = OscillatorNode(frequency=880)
            mixer = MixNode(num_inputs=2, weights=[0.5, 0.5])
            osc1.output() >> mixer.input("input_0")
            osc2.output() >> mixer.input("input_1")
            mixer >> g.sink
        audio = g.render(duration=0.05, sample_rate=22050)
        assert not np.allclose(audio.samples, 0.0)

    def test_multiply_node(self):
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            mod = OscillatorNode(frequency=5, amplitude=1.0)
            mult = MultiplyNode()
            osc.output() >> mult.input("a")
            mod.output() >> mult.input("b")
            mult >> g.sink
        audio = g.render(duration=0.1, sample_rate=22050)
        assert not np.allclose(audio.samples, 0.0)

    def test_crossfade_node(self):
        with SignalGraph() as g:
            osc1 = OscillatorNode(frequency=440)
            osc2 = OscillatorNode(frequency=880)
            xfade = CrossfadeNode(mix=0.0)  # All signal a
            osc1.output() >> xfade.input("a")
            osc2.output() >> xfade.input("b")
            xfade >> g.sink
        audio_a = g.render(duration=0.05, sample_rate=22050)

        with SignalGraph() as g2:
            osc1 = OscillatorNode(frequency=440)
            osc1 >> g2.sink
        audio_direct = g2.render(duration=0.05, sample_rate=22050)

        # With mix=0, crossfade output should equal signal a
        np.testing.assert_allclose(audio_a.samples, audio_direct.samples, atol=1e-10)

    def test_envelope_follower(self):
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440, amplitude=0.8)
            env = EnvelopeFollower()
            osc >> env
            env.output("envelope") >> g.sink
        audio = g.render(duration=0.1, sample_rate=22050)
        # Envelope should be non-negative
        assert np.all(audio.samples >= 0)

    def test_channel_split_merge(self):
        with SignalGraph() as g:
            osc = OscillatorNode(frequency=440)
            split = ChannelSplitNode()
            merge = StereoMergeNode()
            osc >> split
            split.output("left") >> merge.input("left")
            split.output("right") >> merge.input("right")
            merge >> g.sink
        audio = g.render(duration=0.05, sample_rate=22050)
        assert not np.allclose(audio.samples, 0.0)

    def test_filter_node(self):
        with SignalGraph() as g:
            noise = NoiseNode(color='white')
            filt = FilterNode(cutoff=500, filter_type='lowpass')
            noise >> filt >> g.sink
        audio = g.render(duration=0.05, sample_rate=22050)
        assert not np.allclose(audio.samples, 0.0)


# ---------------------------------------------------------------------------
# GraphEffect (bridge) tests
# ---------------------------------------------------------------------------

class TestGraphEffect:
    def test_to_effect(self):
        """SignalGraph.to_effect should return a GraphEffect."""
        with SignalGraph() as g:
            inp = AudioInput(name="input")
            gain = GainNode(level=0.5)
            inp >> gain >> g.sink

        effect = g.to_effect(input_node_name="input")
        assert isinstance(effect, GraphEffect)

        # Process some audio through the effect
        samples = np.sin(2 * np.pi * 440 * np.arange(4410) / 44100).astype(np.float64)
        audio_in = AudioData(samples, 44100, 1)
        audio_out = effect.process(audio_in)

        assert isinstance(audio_out, AudioData)
        # Output should be roughly half the amplitude
        ratio = np.max(np.abs(audio_out.samples)) / np.max(np.abs(audio_in.samples))
        assert 0.4 < ratio < 0.6
