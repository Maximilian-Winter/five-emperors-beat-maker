"""
Full Track Demo — Scaler Framework + DAW Core
==============================================
Demonstrates the full pipeline across both frameworks:

  1. Scaler: detect key from chord inspiration, generate progression
  2. Scaler: suggest extensions, generate two melody variations
  3. Scaler: voice the chords with drop-2 voicing + voice leading
  4. Scaler: build a key group from an AKWF epiano waveform
  5. DAW Core: load TR-808 drum samples for the beat
  6. DAW Core: step sequencer with euclidean hihat pattern
  7. DAW Core: synthesize acid bass line
  8. DAW Core: render scaler melody via key group (sample-based)
  9. DAW Core: render second melody with FM synth
  10. DAW Core: render voiced chords with pad synth
  11. DAW Core: add FX riser for transitions
  12. DAW Core: effects chain (reverb, delay, sidechain, compression)
  13. DAW Core: mix, master, and export

Run:
    python full_track_demo.py
"""

import sys
import os
import numpy as np

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
sys.path.insert(0, PROJECT_ROOT)

SAMPLES_ROOT = os.path.join(PROJECT_ROOT, "beat-maker", "downloaded_samples_etc")
TR808 = os.path.join(SAMPLES_ROOT, "tidal-drum-machines", "machines", "RolandTR808")
AKWF = os.path.join(SAMPLES_ROOT, "AKWF-FREE", "AKWF")
LIBRE = os.path.join(SAMPLES_ROOT, "the-libre-sample-pack")

OUTPUT_DIR = SCRIPT_DIR
BPM = 95


def main():
    # ==================================================================
    # PART 1: SCALER FRAMEWORK — Theory, Detection, Generation
    # ==================================================================

    from scaler_framework import (
        ScalerSession, GeneratorConfig, GenerationStrategy, VoicingStyle,
    )
    from scaler_framework.generation.progression import ProgressionEngine

    print("=" * 70)
    print("  Full Track Demo — Scaler + DAW Core")
    print("=" * 70)

    # --- 1a. Set key and build a jazzy progression ---
    print("\n[Scaler] Setting up key and progression...")

    session = ScalerSession()
    session.set_key(5, "major")  # F major
    print(f"  Key: {session.key.name}")
    print(f"  Scale: {', '.join(session.key.get_scale_notes())}")

    # Use the progression engine to get chord suggestions
    engine = ProgressionEngine(root=5, scale="major")

    print("\n[Scaler] Chord suggestions after I -> vi:")
    suggestions = engine.suggest_next(["I", "vi"], top_n=4)
    for s in suggestions:
        print(f"    {s}")

    # Set a progression (Fmaj7 -> Dm7 -> Bbmaj7 -> C7 — jazzy ii-V feel)
    session.set_progression("Fmaj7 | Dm7 | Bbmaj7 | C7", bpm=BPM)
    print(f"\n[Scaler] Progression: {session.progression}")

    # --- 1b. Generate two different melodies ---
    print("\n[Scaler] Generating melodies...")

    # Melody A: gentle contour (for key group rendering)
    config_a = GeneratorConfig(
        strategy=GenerationStrategy.CONTOUR,
        contour_shape="arch",
        rhythm_pattern="dotted",
        pitch_range=(60, 79),
        rest_probability=0.15,
        repeats=2,
        seed=42,
    )
    session.generate_melody(config=config_a)
    melody_a = session.melody
    print(f"  Melody A (contour/arch): {len(melody_a.notes)} notes")

    # Melody B: jazzy Markov (for FM synth rendering)
    config_b = GeneratorConfig(
        strategy=GenerationStrategy.MARKOV,
        rhythm_pattern="syncopated_2",
        pitch_range=(67, 86),
        rest_probability=0.2,
        repeats=2,
        seed=777,
    )
    session.generate_melody(config=config_b)
    melody_b = session.melody
    print(f"  Melody B (markov/syncopated): {len(melody_b.notes)} notes")

    # --- 1c. Voice the chords with scaler's voicing engine ---
    print("\n[Scaler] Voicing chords (drop-2 with voice leading)...")
    voiced_chords = session.voice_progression(
        style=VoicingStyle.DROP_2, octave=4, voice_lead=True
    )
    for vc in voiced_chords:
        print(f"    {vc.chord.name:>8}: {', '.join(vc.note_names)}")

    # --- 1d. Build a key group from AKWF epiano waveform ---
    print("\n[Scaler] Creating key group from AKWF epiano sample...")
    epiano_sample = os.path.join(AKWF, "AKWF_epiano", "AKWF_epiano_0003.wav")

    if os.path.exists(epiano_sample):
        session.set_key(5, "major")  # re-set to ensure key group uses F major
        session.create_key_group(
            epiano_sample,
            name="epiano_fmaj",
            scale_type="major",
            root=5,  # F
            octave_range=(3, 6),
            output_dir=OUTPUT_DIR,
        )
        print(f"  Key group: {session.key_group}")
    else:
        print(f"  Warning: AKWF sample not found at {epiano_sample}")
        print("  Falling back to synth-only rendering")

    # ==================================================================
    # PART 2: DAW CORE — Audio Engine, Synthesis, Mixing
    # ==================================================================

    from daw_core import (
        AudioData, Sample, Track, TrackType,
        DrumSynth, BassSynth, LeadSynth, PadSynth, FXSynth,
        Reverb, Delay, Chorus, Compressor, Limiter, LowPassFilter,
        SidechainEnvelope,
        StepSequencer, Pattern, EuclideanPattern,
        Humanizer, GrooveTemplate,
    )
    from daw_core.composer import Song, ScalerBridge, SongBuilder
    from daw_core.io import load_audio

    song = Song("Scaler x DAW Demo", bpm=BPM, sample_rate=44100)

    # --- 2a. Load TR-808 drum samples ---
    print("\n[DAW Core] Loading TR-808 samples...")

    kick_path = os.path.join(TR808, "rolandtr808-bd", "BD0050.WAV")
    snare_path = os.path.join(TR808, "rolandtr808-sd", "SD0050.WAV")
    hat_path = os.path.join(TR808, "rolandtr808-hh", "CH.WAV")
    open_hat_path = os.path.join(TR808, "rolandtr808-oh", "OH25.WAV")
    clap_path = os.path.join(TR808, "rolandtr808-cp", "cp2.wav")

    def load_sample(path, name, fallback_fn=None):
        if os.path.exists(path):
            audio = load_audio(path)
            return Sample(name, audio, [name])
        elif fallback_fn:
            print(f"  Warning: {path} not found, using synth fallback")
            return fallback_fn()
        return None

    kick = load_sample(kick_path, "kick", DrumSynth.kick)
    snare = load_sample(snare_path, "snare", DrumSynth.snare)
    hat = load_sample(hat_path, "hat", DrumSynth.hihat)
    open_hat = load_sample(open_hat_path, "open_hat", lambda: DrumSynth.hihat(open_amount=0.7))
    clap = load_sample(clap_path, "clap", DrumSynth.clap)

    print(f"  Loaded: kick, snare, hat, open_hat, clap")

    # --- 2b. Build drum pattern with step sequencer + euclidean hats ---
    print("\n[DAW Core] Building drum patterns...")

    seq = StepSequencer(bpm=BPM, steps_per_beat=4, swing=0.15)

    # Boom-bap style kick
    seq.add_pattern("kick", Pattern.from_string("x.....x.x.......", "kick"), kick)

    # Snare on 2 and 4
    seq.add_pattern("snare", Pattern.from_string("....x.......x...", "snare"), snare)

    # Euclidean hihat: E(7,16) — West African bell pattern feel
    eucl_hat = EuclideanPattern.generate(7, 16, rotation=1)
    seq.add_pattern("hat", eucl_hat, hat)

    # Open hat accents
    seq.add_pattern("open_hat", Pattern.from_string("..............x.", "oh"), open_hat)

    # Clap layered with snare
    seq.add_pattern("clap", Pattern.from_string("....x.......x...", "clap"), clap)

    drum_track = seq.render_to_track(bars=8, name="drums")
    drum_track.volume = 0.85
    drum_track.add_effect(Compressor(threshold=-8, ratio=3, attack=0.005, release=0.05))
    Humanizer(timing_jitter=0.005, velocity_variation=0.08, seed=99).apply_to_track(drum_track)
    song.add_track(drum_track)
    print(f"  Drum track: {len(drum_track.placements)} hits, E(7,16) hats")

    # --- 2c. Acid bass line ---
    print("\n[DAW Core] Synthesizing bass line...")

    bass_track = Track("bass", TrackType.BASS, volume=0.7)

    # Bass follows the chord roots, with some rhythmic variation
    bass_notes = [
        # Bar 1-2: Fmaj7
        ("F1", 0, 1.5), ("F1", 2, 0.5), ("C2", 2.5, 0.5), ("F1", 3, 1.0),
        ("F1", 4, 1.0), ("A1", 5, 0.5), ("F1", 5.5, 0.5), ("F1", 6, 1.5),
        # Bar 3-4: Dm7
        ("D1", 8, 1.5), ("D1", 10, 0.5), ("A1", 10.5, 0.5), ("D1", 11, 1.0),
        ("D1", 12, 1.0), ("F1", 13, 0.5), ("D1", 13.5, 0.5), ("D1", 14, 1.5),
        # Bar 5-6: Bbmaj7
        ("A#1", 16, 1.5), ("A#1", 18, 0.5), ("F1", 18.5, 0.5), ("A#1", 19, 1.0),
        ("A#1", 20, 1.0), ("D2", 21, 0.5), ("A#1", 21.5, 0.5), ("A#1", 22, 1.5),
        # Bar 7-8: C7
        ("C2", 24, 1.5), ("C2", 26, 0.5), ("G1", 26.5, 0.5), ("C2", 27, 1.0),
        ("C2", 28, 1.0), ("E2", 29, 0.5), ("C2", 29.5, 0.5), ("C2", 30, 1.5),
    ]
    from daw_core.music import note_to_freq
    for note_name, beat, dur in bass_notes:
        freq = note_to_freq(note_name)
        dur_sec = dur * 60.0 / BPM
        sample = BassSynth.acid_bass(freq, dur_sec, filter_freq=600, resonance=0.5)
        time = beat * 60.0 / BPM
        bass_track.add(sample, time, velocity=0.8)

    bass_track.add_effect(LowPassFilter(cutoff=400))
    bass_track.add_effect(SidechainEnvelope(bpm=BPM, depth=0.4, release=0.3, shape="exp"))
    song.add_track(bass_track)
    print(f"  Bass track: {len(bass_track.placements)} notes (acid bass)")

    # --- 2d. Render melody A via key group (sample-based) ---
    print("\n[DAW Core] Rendering melody A (key group / epiano)...")

    if session.key_group is not None:
        from scaler_framework.sampling.renderer import KeyGroupRenderer
        # Render to audio, then wrap as a track
        renderer = KeyGroupRenderer(session.key_group)
        melody_a_audio = renderer.render(melody_a, bpm=BPM, tail_seconds=1.5)
        melody_a_sample = Sample("melody_a", AudioData(melody_a_audio, session.key_group.sample_rate))
        melody_a_track = Track("melody_epiano", TrackType.LEAD, volume=0.55)
        melody_a_track.add(melody_a_sample, 0.0)
        melody_a_track.add_effect(Reverb(room_size=0.5, damping=0.4, mix=0.25))
        melody_a_track.add_effect(Chorus(rate=0.8, depth=0.003, mix=0.2))
        song.add_track(melody_a_track)
        print(f"  Melody A rendered via key group ({session.key_group.name})")
    else:
        # Fallback: use ScalerBridge with pluck synth
        bridge = ScalerBridge(bpm=BPM)
        melody_a_track = bridge.melody_to_track(
            melody_a, synth="pluck", name="melody_pluck",
            effects=[Reverb(room_size=0.5, mix=0.25)]
        )
        melody_a_track.volume = 0.55
        song.add_track(melody_a_track)
        print(f"  Melody A rendered via pluck synth (key group unavailable)")

    # --- 2e. Render melody B with FM synth ---
    print("\n[DAW Core] Rendering melody B (FM synth)...")

    bridge = ScalerBridge(bpm=BPM)
    melody_b_track = bridge.melody_to_track(
        melody_b, synth="fm", name="melody_fm",
        effects=[
            Delay(delay_time=60.0 / BPM * 0.75, feedback=0.35, mix=0.2),
            Reverb(room_size=0.4, mix=0.15),
        ]
    )
    melody_b_track.volume = 0.35
    song.add_track(melody_b_track)
    print(f"  Melody B: {len(melody_b.notes)} notes, FM + dotted-eighth delay")

    # --- 2f. Render voiced chords with string pad ---
    print("\n[DAW Core] Rendering chord pad (string, voiced by scaler)...")

    chord_track = Track("chords_pad", TrackType.PAD, volume=0.35)
    from daw_core.music import midi_to_freq as _m2f
    beat = 0.0
    for chord, vc in zip(session.progression.chords, voiced_chords):
        dur_sec = chord.duration_beats * 60.0 / BPM
        time = beat * 60.0 / BPM
        for midi_note in vc.notes:
            freq = _m2f(midi_note)
            sample = PadSynth.string_pad(freq, dur_sec)
            chord_track.add(sample, time, velocity=0.5)
        beat += chord.duration_beats

    # Repeat for 8 bars total (progression is 4 bars)
    prog_dur = session.progression.total_beats * 60.0 / BPM
    for p in list(chord_track.placements):
        chord_track.add(p.sample, p.time + prog_dur, p.velocity)

    chord_track.add_effect(LowPassFilter(cutoff=3000))
    chord_track.add_effect(Reverb(room_size=0.7, damping=0.5, mix=0.4))
    chord_track.add_effect(SidechainEnvelope(bpm=BPM, depth=0.25, release=0.35, shape="exp"))
    song.add_track(chord_track)
    print(f"  Chord pad: {len(chord_track.placements)} note placements")

    # --- 2g. FX: riser at bar 7 leading into potential next section ---
    print("\n[DAW Core] Adding FX riser...")

    riser = FXSynth.riser(duration=4 * 60.0 / BPM, start_freq=200, end_freq=3000)
    fx_track = Track("fx", TrackType.FX, volume=0.25)
    fx_track.add(riser, 6 * 4 * 60.0 / BPM)  # starts at bar 7
    fx_track.add_effect(Reverb(room_size=0.8, mix=0.5))
    song.add_track(fx_track)

    # --- 2h. Master chain ---
    print("\n[DAW Core] Master chain: compressor + limiter")
    song.master_effects.append(Compressor(threshold=-6, ratio=2.5, attack=0.01, release=0.1))
    song.master_effects.append(Limiter(threshold=0.92))

    # ==================================================================
    # PART 3: RENDER & EXPORT
    # ==================================================================

    print("\n[Render] Mixing and exporting...")
    print(f"  Song: {song.name}")
    print(f"  BPM: {song.bpm}")
    print(f"  Tracks: {len(song.tracks)}")
    for t in song.tracks:
        n = len(t.placements) if hasattr(t, 'placements') else '?'
        fx = len(t.effects)
        print(f"    {t.name:<20s}  vol:{t.volume:.2f}  placements:{n}  effects:{fx}")

    # Export WAV
    wav_path = os.path.join(OUTPUT_DIR, "full_track_demo.wav")
    song.export(wav_path)

    # Also export MIDI from scaler
    midi_path = os.path.join(OUTPUT_DIR, "full_track_demo.mid")
    from daw_core.midi import MIDIFile, MIDIWriter
    from daw_core.music import note_name_to_midi, midi_to_freq

    midi = MIDIFile(ticks_per_beat=480, tempo=BPM)

    # Melody A to MIDI
    mel_a_track = midi.add_track("Melody A", channel=0)
    for note in melody_a.notes:
        mel_a_track.add_note(
            note.pitch, min(int(note.velocity), 127),
            int(note.start_beat * 480), int(note.duration_beats * 480)
        )

    # Melody B to MIDI
    mel_b_track = midi.add_track("Melody B", channel=1)
    for note in melody_b.notes:
        mel_b_track.add_note(
            note.pitch, min(int(note.velocity), 127),
            int(note.start_beat * 480), int(note.duration_beats * 480)
        )

    # Chords to MIDI
    chord_midi_track = midi.add_track("Chords", channel=2)
    beat = 0.0
    for chord, vc in zip(session.progression.chords, voiced_chords):
        for midi_note in vc.notes:
            chord_midi_track.add_note(
                midi_note, 80,
                int(beat * 480), int(chord.duration_beats * 480)
            )
        beat += chord.duration_beats

    MIDIWriter.write(midi, midi_path)
    print(f"  MIDI: {midi_path}")

    # ==================================================================
    # SUMMARY
    # ==================================================================

    print(f"\n{'=' * 70}")
    print(f"  Done!")
    print(f"  WAV:  {wav_path}")
    print(f"  MIDI: {midi_path}")
    print(f"{'=' * 70}")
    print(f"""
  What this demo used:

  scaler_framework:
    - Key detection & scale (F major)
    - Chord suggestion engine (ProgressionEngine)
    - Progression: Fmaj7 | Dm7 | Bbmaj7 | C7
    - Two melody strategies: contour/arch + markov/syncopated
    - Drop-2 voicing with voice leading
    - Key group from AKWF epiano waveform

  daw_core:
    - TR-808 drum samples (kick, snare, hat, open hat, clap)
    - Step sequencer with euclidean E(7,16) hihat pattern
    - Swing (15%) + humanization
    - Acid bass synthesis with filter envelope
    - FM lead synthesis with dotted-eighth delay
    - String pad synthesis for voiced chords
    - FX riser for transitions
    - Effects: reverb, delay, chorus, compression, sidechain, low-pass
    - Master chain: compressor + limiter
    - WAV + MIDI export
""")


if __name__ == "__main__":
    main()
