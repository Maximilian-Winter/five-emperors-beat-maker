"""
Signal Graph Demo — The Loom of Sound
======================================

Demonstrates the declarative signal graph system by creating
four distinct effects and exporting each as a .wav file:

  1. Ring Modulator  — tremolo / metallic tones
  2. Parallel (NY) Compression — punchy dynamics
  3. Auto-Wah — envelope-controlled filter sweep
  4. Vocoder — the classic robotic voice effect

Each example builds a signal graph with the >> operator,
renders it, and saves the result.

Run:
    python examples/signal_graph_demo.py

Output:
    examples/output/ring_modulator.wav
    examples/output/parallel_compression.wav
    examples/output/auto_wah.wav
    examples/output/vocoder.wav
"""

import sys
from pathlib import Path

# Ensure beatmaker is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from beatmaker import (
    AudioData, save_audio,
    sine_wave, sawtooth_wave, square_wave, white_noise,
    Compressor, Reverb, Delay,
    create_song, DrumSynth, Sample, Track, TrackType,
)
from beatmaker.graph import (
    SignalGraph, AudioInput, OscillatorNode, NoiseNode,
    EffectNode, GainNode, FilterNode, MixNode, MultiplyNode,
    CrossfadeNode, EnvelopeFollower, FilterBankNode, GraphEffect,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLE_RATE = 44100
DURATION = 4.0  # seconds


def make_test_tone(freq=220.0, duration=DURATION):
    """A rich sawtooth tone for testing effects."""
    audio = sawtooth_wave(freq, duration, SAMPLE_RATE, 0.7)
    return audio


def make_voice_signal(duration=DURATION):
    """
    Simulate a voice-like signal: a glottal buzz with formants.
    This approximates a vowel 'ah' sound for vocoder demos.
    """
    sr = SAMPLE_RATE
    t = np.linspace(0, duration, int(duration * sr), False)

    # Glottal pulse train at ~120 Hz (male voice pitch)
    fundamental = 120.0
    pulse = np.zeros_like(t)
    for h in range(1, 20):
        pulse += np.sin(2 * np.pi * fundamental * h * t) / h
    pulse *= 0.5

    # Simple formant emphasis (vowel 'ah': F1~700Hz, F2~1200Hz)
    from beatmaker.synths import Filter
    f1 = Filter(cutoff=700, resonance=0.6, filter_type='bandpass')
    f2 = Filter(cutoff=1200, resonance=0.5, filter_type='bandpass')
    formant1 = f1.process(pulse, sr)
    formant2 = f2.process(pulse, sr)
    voice = pulse * 0.3 + formant1 * 0.5 + formant2 * 0.2

    # Normalize
    peak = np.max(np.abs(voice))
    if peak > 0:
        voice = voice * 0.8 / peak

    return AudioData(voice, sr)


def make_carrier_chord(duration=DURATION):
    """
    A lush sawtooth chord for the vocoder carrier.
    C minor: C3, Eb3, G3
    """
    sr = SAMPLE_RATE
    t = np.linspace(0, duration, int(duration * sr), False)

    from beatmaker import note_to_freq
    freqs = [note_to_freq('C3'), note_to_freq('E3'), note_to_freq('G3')]

    chord = np.zeros_like(t)
    for f in freqs:
        # Two slightly detuned saws per note for richness
        chord += sawtooth_wave(f, duration, sr, 0.3).samples
        chord += sawtooth_wave(f * 1.004, duration, sr, 0.3).samples

    peak = np.max(np.abs(chord))
    if peak > 0:
        chord = chord * 0.7 / peak

    return AudioData(chord, sr)


# ===================================================================
# Example 1: Ring Modulator
# ===================================================================

def demo_ring_modulator():
    """
    Ring modulation: multiply audio by a sine oscillator.

    At low frequencies (< 20 Hz) this creates tremolo.
    At audio frequencies it creates metallic, inharmonic tones.
    We'll do both: a slow tremolo opening into a metallic ring.
    """
    print("\n  [1/4] Ring Modulator")
    audio = make_test_tone(freq=220)

    with SignalGraph() as g:
        source = AudioInput(audio, name="input")

        # Modulator at 80 Hz — creates sidebands
        mod_osc = OscillatorNode(frequency=80, waveform='sine', name="mod")
        ring = MultiplyNode(name="ring")

        source >> ring.input("a")
        mod_osc >> ring.input("b")

        # Add a touch of reverb via EffectNode
        reverb = EffectNode(Reverb(room_size=0.4, mix=0.2), name="reverb")
        ring >> reverb >> g.sink

    result = g.render(DURATION, SAMPLE_RATE)
    result = result.normalize(0.9)
    save_audio(result, OUTPUT_DIR / "ring_modulator.wav")
    print(f"        Saved: ring_modulator.wav ({result.duration:.1f}s)")


# ===================================================================
# Example 2: Parallel (NY) Compression
# ===================================================================

def demo_parallel_compression():
    """
    New York style parallel compression:
    mix the dry signal with a heavily compressed copy.
    Adds punch and energy without killing dynamics.
    """
    print("  [2/4] Parallel Compression")

    # Use a drum loop as source
    sr = SAMPLE_RATE
    kick = DrumSynth.kick(duration=0.3, pitch=55, punch=0.9, sample_rate=sr)
    snare = DrumSynth.snare(duration=0.2, noise_amount=0.7, sample_rate=sr)
    hat = DrumSynth.hihat(duration=0.08, sample_rate=sr)

    # Build a simple 2-bar pattern
    bpm = 128
    beat_dur = 60.0 / bpm
    total_dur = beat_dur * 8  # 2 bars of 4/4

    t_len = int(total_dur * sr)
    drums = np.zeros(t_len)

    # Place kick on beats 1, 2, 3, 4 (four on the floor)
    for beat in range(8):
        pos = int(beat * beat_dur * sr)
        k = kick.audio.samples
        end = min(pos + len(k), t_len)
        drums[pos:end] += k[:end - pos]

    # Snare on beats 2 and 4
    for beat in [1, 3, 5, 7]:
        pos = int(beat * beat_dur * sr)
        s = snare.audio.samples
        end = min(pos + len(s), t_len)
        drums[pos:end] += s[:end - pos]

    # Hats on every 8th note
    for eighth in range(16):
        pos = int(eighth * beat_dur * 0.5 * sr)
        h = hat.audio.samples * 0.4
        end = min(pos + len(h), t_len)
        drums[pos:end] += h[:end - pos]

    # Normalize the drum mix
    peak = np.max(np.abs(drums))
    if peak > 0:
        drums = drums * 0.8 / peak

    drum_audio = AudioData(drums, sr)

    # Now build the parallel compression graph
    blend = 0.4

    with SignalGraph() as g:
        src = AudioInput(drum_audio, name="drums")

        # Dry path
        dry = GainNode(level=1.0 - blend, name="dry")

        # Wet path: heavy compression + makeup gain
        compressed = EffectNode(
            Compressor(threshold=-25.0, ratio=10.0, attack=0.001,
                       release=0.05, makeup_gain=8.0),
            name="squash"
        )
        wet_level = GainNode(level=blend, name="wet_level")

        # Mix
        mixer = MixNode(num_inputs=2, weights=[1.0, 1.0], name="bus")

        src >> dry >> mixer.input("input_0")
        src >> compressed >> wet_level >> mixer.input("input_1")

        mixer >> g.sink

    result = g.render(total_dur, sr)
    result = result.normalize(0.9)
    save_audio(result, OUTPUT_DIR / "parallel_compression.wav")
    print(f"        Saved: parallel_compression.wav ({result.duration:.1f}s)")


# ===================================================================
# Example 3: Auto-Wah
# ===================================================================

def demo_auto_wah():
    """
    Envelope-controlled bandpass filter (auto-wah).

    The louder the input, the higher the filter opens.
    Creates that classic funky 'wah' sweep.
    """
    print("  [3/4] Auto-Wah")

    # Create a rhythmic source: staccato saw notes
    sr = SAMPLE_RATE
    from beatmaker import note_to_freq

    notes = ['E2', 'E2', 'G2', 'A2', 'E2', 'E2', 'B2', 'A2']
    beat_dur = 60.0 / 120  # 120 bpm
    note_dur = beat_dur * 0.6  # Staccato
    total_dur = beat_dur * len(notes)
    t_len = int(total_dur * sr)

    riff = np.zeros(t_len)
    for i, note in enumerate(notes):
        freq = note_to_freq(note)
        t_note = np.linspace(0, note_dur, int(note_dur * sr), False)
        # Saw with quick decay
        tone = np.sin(2 * np.pi * freq * t_note)
        tone += 0.5 * sawtooth_wave(freq, note_dur, sr, 0.5).samples
        envelope = np.exp(-t_note * 4)
        tone *= envelope

        pos = int(i * beat_dur * sr)
        end = min(pos + len(tone), t_len)
        riff[pos:end] += tone[:end - pos]

    peak = np.max(np.abs(riff))
    if peak > 0:
        riff = riff * 0.8 / peak

    riff_audio = AudioData(riff, sr)

    # Build the auto-wah graph
    with SignalGraph() as g:
        source = AudioInput(riff_audio, name="input")

        # Envelope follower detects the dynamics
        env = EnvelopeFollower(attack=0.001, release=0.08, name="env_detect")

        # Scale envelope to filter frequency range (200-3000 Hz offset)
        env_scaled = GainNode(level=3000.0, name="env_to_freq")

        # Resonant bandpass filter with CV modulation
        wah = FilterNode(
            cutoff=200, resonance=0.65,
            filter_type='bandpass', name="wah_filter"
        )

        # Mix dry and filtered for body
        dry_gain = GainNode(level=0.3, name="dry")
        wet_gain = GainNode(level=0.7, name="wet")
        mixer = MixNode(num_inputs=2, weights=[1.0, 1.0], name="mix")

        # Signal flow
        source >> env
        env.output("envelope") >> env_scaled >> wah.input("cutoff_cv")
        source >> wah

        source >> dry_gain >> mixer.input("input_0")
        wah >> wet_gain >> mixer.input("input_1")

        mixer >> g.sink

    result = g.render(total_dur, sr)
    result = result.normalize(0.9)
    save_audio(result, OUTPUT_DIR / "auto_wah.wav")
    print(f"        Saved: auto_wah.wav ({result.duration:.1f}s)")


# ===================================================================
# Example 4: Vocoder
# ===================================================================

def demo_vocoder():
    """
    Classic channel vocoder.

    The modulator (voice) controls the spectral envelope.
    The carrier (synth chord) provides the tonal material.
    Result: the synth 'speaks' with the voice's articulation.

    Architecture:
        voice ──► FilterBank ──► EnvelopeFollower ──► Multiply ──► Mix ──► out
        synth ──► FilterBank ────────────────────────► Multiply ─┘
    """
    print("  [4/4] Vocoder")

    voice = make_voice_signal(duration=DURATION)
    carrier = make_carrier_chord(duration=DURATION)

    num_bands = 16
    # Log-spaced crossover frequencies from 80 Hz to 8000 Hz
    crossover_freqs = np.geomspace(80, 8000, num_bands + 1)[1:-1].tolist()

    with SignalGraph() as g:
        mod_in = AudioInput(voice, name="voice")
        car_in = AudioInput(carrier, name="synth")

        # Split both signals into frequency bands
        mod_bank = FilterBankNode(crossover_freqs, resonance=0.2, name="mod_bank")
        car_bank = FilterBankNode(crossover_freqs, resonance=0.2, name="car_bank")

        mod_in >> mod_bank
        car_in >> car_bank

        # Recombine: for each band, use voice envelope to control carrier amplitude
        recombine = MixNode(num_inputs=num_bands,
                            weights=[1.5 / num_bands] * num_bands,
                            name="recombine")

        for i in range(num_bands):
            # Extract amplitude envelope from modulator band
            env = EnvelopeFollower(
                attack=0.002, release=0.015,
                name=f"env_{i}"
            )
            # VCA: multiply carrier band by modulator envelope
            vca = MultiplyNode(name=f"vca_{i}")

            mod_bank.output(f"band_{i}") >> env
            car_bank.output(f"band_{i}") >> vca.input("a")
            env.output("envelope") >> vca.input("b")
            vca >> recombine.input(f"input_{i}")

        recombine >> g.sink

    result = g.render(DURATION, SAMPLE_RATE)
    result = result.normalize(0.9)
    save_audio(result, OUTPUT_DIR / "vocoder.wav")
    print(f"        Saved: vocoder.wav ({result.duration:.1f}s)")

    # Bonus: demonstrate GraphEffect integration
    # Wrap the vocoder graph as an AudioEffect usable in Track.effects
    vocoder_effect = g.to_effect(
        input_node_name="voice",
        synth=carrier
    )

    # Use it in a SongBuilder
    song = (create_song("Vocoder Demo")
            .tempo(120)
            .bars(4)
            .add_graph_track("vocoder_pad", g, DURATION)
            .build())

    song.export(str(OUTPUT_DIR / "vocoder_in_song.wav"))
    print(f"        Saved: vocoder_in_song.wav (via SongBuilder)")


# ===================================================================
# Main
# ===================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Signal Graph Demo — The Loom of Sound")
    print("=" * 60)
    print(f"\n  Output directory: {OUTPUT_DIR}")

    demo_ring_modulator()
    demo_parallel_compression()
    demo_auto_wah()
    demo_vocoder()

    print("\n" + "=" * 60)
    print("  All demos complete! Open the .wav files to listen.")
    print("=" * 60)
