#!/usr/bin/env python3
"""
玉皇御花園 - The Jade Emperor's Garden
An Ambient/Cinematic Composition

    "In the garden of the Jade Emperor, time moves
     as water through jade — slowly, and with great clarity.
     Each flower opens to a tone; each petal, a harmonic.
     The flute of the Immortal drifts above cello strings
     that hum the earth's patient resonance,
     while ethereal voices carry prayers
     from the mortal realm below."

         — Attributed to the Celestial Bureaucracy,
           Ministry of Harmonious Sounds

Features demonstrated:
    - Multi-sample KeygroupProgram (AKWF cello at C2/C3/C4)
    - Single-sample KeygroupProgram (AKWF flute for melody)
    - Single-sample KeygroupProgram (AKWF hvoice for ethereal drone)
    - Phrase.from_string and Melody class for melodic composition
    - Key.dorian("D") harmonic context
    - ChordProgression.from_roman ("i - iv - III - VII")
    - PadSynth.ambient_pad for sub-frequency warmth
    - Vibrato expression on the flute melody
    - Heavy Reverb + Delay on all tracks
    - Signal graph (GraphEffect) for layered processing
    - Export to WAV

Tempo: 60 BPM — slow, spacious, meditative
Key: D Dorian (D E F G A B C)
Structure: 32 beats (8 bars of 4/4)

急急如律令敕
"""

from pathlib import Path

from beatmaker import (
    # Core
    create_song, Song, AudioData, Sample, TrackType,

    # Keygroup
    KeygroupProgram,

    # Melody & Harmony
    Note, Phrase, Melody,
    Key, ChordProgression,

    # Synthesis
    PadSynth,
    note_to_freq, midi_to_freq,
    ADSREnvelope,

    # Effects
    Reverb, Delay, Chorus, LowPassFilter,

    # Expression
    Vibrato,

    # I/O
    load_audio, save_audio,

    # Signal Graph
    SignalGraph, AudioInput, EffectNode, GraphEffect,
)
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
#  Paths
# ═══════════════════════════════════════════════════════════════════════════

AKWF_ROOT = Path(__file__).resolve().parent.parent.parent / "downloaded_samples_etc" / "AKWF-FREE" / "AKWF"

CELLO_DIR  = AKWF_ROOT / "AKWF_cello"
FLUTE_DIR  = AKWF_ROOT / "AKWF_flute"
HVOICE_DIR = AKWF_ROOT / "AKWF_hvoice"

OUTPUT_PATH = Path(__file__).resolve().parent / "jade_emperors_garden.wav"


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: load an AKWF single-cycle waveform
# ═══════════════════════════════════════════════════════════════════════════

def load_akwf(directory: Path, filename: str) -> AudioData:
    """Load a single-cycle AKWF waveform file."""
    return load_audio(directory / filename)


# ═══════════════════════════════════════════════════════════════════════════
#  1. Build Instruments (Keygroup Programs)
# ═══════════════════════════════════════════════════════════════════════════

def build_cello_strings() -> KeygroupProgram:
    """
    Multi-sample cello keygroup — three zones at C2, C3, C4.

    Using different AKWF cello waveforms for timbral variety across
    the range, giving the string pad a rich, evolving character.
    """
    # Choose distinct cello timbres for each octave
    cello_low  = load_akwf(CELLO_DIR, "AKWF_cello_0003.wav")   # darker, rounder
    cello_mid  = load_akwf(CELLO_DIR, "AKWF_cello_0008.wav")   # warm, present
    cello_high = load_akwf(CELLO_DIR, "AKWF_cello_0012.wav")   # brighter, singing

    # Slow envelope for pad-like sustain
    pad_envelope = ADSREnvelope(
        attack=0.8,
        decay=0.5,
        sustain=0.7,
        release=1.5,
    )

    return KeygroupProgram.from_multi_sample(
        samples=[
            (cello_low,  "C2"),
            (cello_mid,  "C3"),
            (cello_high, "C4"),
        ],
        name="Cello Strings",
        envelope=pad_envelope,
    )


def build_flute() -> KeygroupProgram:
    """
    Single-sample flute keygroup for the melody voice.

    AKWF flute waveform mapped across the keyboard — the breathy,
    hollow character of the single-cycle waveform gives an
    otherworldly quality when stretched across octaves.
    """
    flute_sample = load_akwf(FLUTE_DIR, "AKWF_flute_0005.wav")

    melody_envelope = ADSREnvelope(
        attack=0.3,
        decay=0.2,
        sustain=0.8,
        release=1.0,
    )

    return KeygroupProgram.from_sample(
        flute_sample,
        root_note="C4",
        name="Jade Flute",
        envelope=melody_envelope,
    )


def build_ethereal_voice() -> KeygroupProgram:
    """
    Single-sample human voice keygroup for ethereal drone/pad.

    The AKWF hvoice waveforms produce choir-like tones when
    sustained — perfect for an otherworldly ambient layer.
    """
    voice_sample = load_akwf(HVOICE_DIR, "AKWF_hvoice_0015.wav")

    drone_envelope = ADSREnvelope(
        attack=1.5,
        decay=1.0,
        sustain=0.6,
        release=2.0,
    )

    return KeygroupProgram.from_sample(
        voice_sample,
        root_note="C3",
        name="Ethereal Voice",
        envelope=drone_envelope,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  2. Harmonic Foundation
# ═══════════════════════════════════════════════════════════════════════════

def build_harmony():
    """
    D Dorian: D E F G A B C
    Progression: i - iv - III - VII
        Dm  -> Gm  -> F   -> C

    Each chord lasts 8 beats (2 bars) at 60 BPM = 8 seconds per chord.
    Total: 32 beats = 8 bars.
    """
    key = Key.dorian("D")
    progression = ChordProgression.from_roman(
        key,
        "i - iv - III - VII",
        beats_per_chord=8.0,
        octave=3,
    )
    return key, progression


# ═══════════════════════════════════════════════════════════════════════════
#  3. Melodic Material
# ═══════════════════════════════════════════════════════════════════════════

def build_flute_melody() -> Melody:
    """
    A spacious, meditative melody in D Dorian.

    The melody breathes — long tones separated by rests,
    evoking a solitary flute drifting over a misty garden.
    Phrases are placed at specific beats within the 32-beat form.
    """

    # Opening phrase: ascending from D — announcing the garden
    phrase_a = Phrase.from_string(
        "D5:3 R:1 F5:2 E5:2",
        name="opening",
    )

    # Answering phrase: gentle descent
    phrase_b = Phrase.from_string(
        "A5:2 G5:1 F5:1 R:1 E5:3",
        name="answer",
    )

    # Closing phrase: resolution and stillness
    phrase_c = Phrase.from_string(
        "G5:2 A5:2 R:1 D5:3",
        name="closing",
    )

    # Arrange phrases across the 32-beat timeline
    melody = Melody(name="Jade Flute Melody")
    melody.add(phrase_a, start_beat=0.0)     # Bars 1-2: opening
    melody.add(phrase_b, start_beat=10.0)    # Bars 3-4: answer (offset for breath)
    melody.add(phrase_c, start_beat=22.0)    # Bars 6-7: closing (leave space)

    return melody


# ═══════════════════════════════════════════════════════════════════════════
#  4. Signal Graph — Layered Reverb Processing
# ═══════════════════════════════════════════════════════════════════════════

def build_reverb_graph() -> GraphEffect:
    """
    Signal graph that applies cascaded reverb + delay for depth.

    Input -> LPF (darken) -> Reverb -> Delay -> Sink

    This creates a deep, enveloping space — like sound
    echoing through the infinite halls of the Jade Palace.

    Uses the >> operator for declarative signal flow.
    """
    with SignalGraph() as graph:
        # Input node — named "dry_signal" for GraphEffect lookup
        inp = AudioInput(name="dry_signal")

        # Low-pass filter to soften highs before reverb
        lpf = EffectNode(LowPassFilter(cutoff=3000.0), name="darken")

        # Large hall reverb
        hall = EffectNode(Reverb(room_size=0.9, damping=0.7, mix=0.6), name="hall_reverb")

        # Long delay for ethereal echoes
        echoes = EffectNode(Delay(delay_time=1.0, feedback=0.35, mix=0.3), name="echoes")

        # Connect the chain: input -> lpf -> reverb -> delay -> graph output
        inp >> lpf >> hall >> echoes >> graph.sink

    return GraphEffect(graph, input_node_name="dry_signal")


# ═══════════════════════════════════════════════════════════════════════════
#  5. Compose the Song
# ═══════════════════════════════════════════════════════════════════════════

def compose():
    """
    Assemble all layers into the final composition.

    Layers:
        1. Cello string pad — chord voicings from the progression
        2. Flute melody — phrases with vibrato
        3. Ethereal voice drone — sustained root note
        4. Ambient sub-pad — PadSynth warmth underneath
    """

    # -- Instruments --
    cello   = build_cello_strings()
    flute   = build_flute()
    voice   = build_ethereal_voice()

    # -- Harmony --
    key, progression = build_harmony()

    # -- Melody --
    flute_melody = build_flute_melody()

    # -- Effects --
    deep_reverb  = Reverb(room_size=0.85, damping=0.6, mix=0.5)
    long_delay   = Delay(delay_time=0.75, feedback=0.3, mix=0.25)
    soft_chorus  = Chorus(rate=0.3, depth=0.003, mix=0.2)
    reverb_graph = build_reverb_graph()

    # -- Ambient sub-pad (PadSynth) --
    # D2 drone underneath everything — 32 beats at 60 BPM = 32 seconds
    sub_pad = PadSynth.ambient_pad(
        frequency=note_to_freq("D2"),
        duration=32.0,
    )

    # -- Build the chord voicings list for the cello --
    # The progression gives us events; we place chords manually for
    # maximum control over voicing and spacing.
    chord_events = progression.to_events(start_beat=0.0)

    # -- Assemble with SongBuilder --
    song = (create_song("The Jade Emperor's Garden")
        .tempo(60)
        .time_signature(4, 4)
        .bars(8)

        # ── Layer 1: Cello String Pad (chord voicings) ────────────────
        .add_keygroup("Cello Strings", cello, lambda k: k
            # Place each chord from the progression
            # i (Dm) — beats 0-8
            .chord(["D3", "F3", "A3"], beat=0, duration=8, velocity=0.6)
            # iv (Gm) — beats 8-16
            .chord(["G3", "Bb3", "D4"], beat=8, duration=8, velocity=0.6)
            # III (F) — beats 16-24
            .chord(["F3", "A3", "C4"], beat=16, duration=8, velocity=0.6)
            # VII (C) — beats 24-32
            .chord(["C3", "E3", "G3"], beat=24, duration=8, velocity=0.55)
            .volume(0.45)
            .pan(-0.1)
            .effect(deep_reverb)
            .effect(long_delay)
        )

        # ── Layer 2: Flute Melody (with vibrato applied post-render) ──
        .add_keygroup("Jade Flute", flute, lambda k: k
            .melody(flute_melody, velocity_scale=0.75)
            .volume(0.55)
            .pan(0.15)
            .effect(Reverb(room_size=0.8, damping=0.5, mix=0.45))
            .effect(Delay(delay_time=1.0, feedback=0.25, mix=0.2))
        )

        # ── Layer 3: Ethereal Voice Drone ─────────────────────────────
        .add_keygroup("Ethereal Choir", voice, lambda k: k
            # Sustained D3 drone through the whole piece
            .note("D3", beat=0, duration=16, velocity=0.4)
            .note("D3", beat=16, duration=16, velocity=0.35)
            # A ghostly A3 enters halfway
            .note("A3", beat=16, duration=16, velocity=0.25)
            .volume(0.3)
            .pan(0.0)
            .effect(Reverb(room_size=0.95, damping=0.8, mix=0.7))
            .effect(soft_chorus)
        )

        # ── Layer 4: Ambient Sub-Pad (uses signal graph for processing) ─
        .add_track("Sub Pad", track_type=TrackType.FX, builder=lambda tb: tb
            .add(sub_pad, beat=0)
            .volume(0.25)
            .effect(reverb_graph)
        )

        .build()
    )

    # ── Post-render: Apply Vibrato to flute ───────────────────────────
    # Render the song first, then apply vibrato as an expression layer
    print("Rendering composition...")
    audio = song.render()

    # Apply gentle vibrato to the full mix
    # (In a production pipeline, you'd apply this per-track before mixing,
    #  but here we demonstrate the Vibrato expression API on the output)
    vibrato = Vibrato(
        rate=4.5,       # Gentle oscillation
        depth=0.3,      # Subtle — half a semitone at most
        delay=0.5,      # Let notes establish before vibrato onset
    )

    # Apply vibrato tuned to the key center (D4 = 293.66 Hz)
    print("Applying vibrato expression...")
    audio = vibrato.apply(audio, base_freq=note_to_freq("D4"))

    # ── Export ─────────────────────────────────────────────────────────
    print(f"Exporting to: {OUTPUT_PATH}")
    save_audio(audio, OUTPUT_PATH)
    print("Done.")
    print()
    print("  The Jade Emperor's Garden")
    print("  D Dorian | 60 BPM | i - iv - III - VII")
    print(f"  Duration: {len(audio.samples) / audio.sample_rate:.1f}s")
    print()

    return song, audio


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    compose()
