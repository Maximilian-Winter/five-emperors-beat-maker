"""
╔══════════════════════════════════════════════════════════════════╗
║            The Enchantress of Numbers — Version II              ║
║     A Victorian Portrait Through the Gaussian Loom              ║
║                                                                  ║
║     The same poetical science, now woven through the SPC700     ║
║     S-DSP: BRR compression, Gaussian interpolation, hardware    ║
║     ADSR, and the legendary 8-tap FIR echo that gave the       ║
║     Super Nintendo its unmistakable spatial warmth.             ║
║                                                                  ║
║     8 voices. 64 kilobytes. One soul.                           ║
║     by A.A.L.                                                   ║
╚══════════════════════════════════════════════════════════════════╝

The piece remains in D minor — 108 BPM — but now every note passes through
actual hardware emulation. The AKWF single-cycle waveforms provide the
harmonic material; the SPC700 DSP shapes it with Gaussian interpolation,
BRR compression artifacts, and that echo unit which made the SNES sing.

Voice allocation (8 voices, the full orchestra):
    0 — Kick drum       (beatmaker DrumSynth → BRR)
    1 — Snare drum      (beatmaker DrumSynth → BRR)
    2 — Hi-hat / Bell   (beatmaker DrumSynth → BRR, instrument switch)
    3 — Bass            (AKWF cello waveform, 'bass' preset)
    4 — Lead melody     (AKWF violin waveform, 'lead' preset)
    5 — Pad voice I     (AKWF sine waveform, 'pad' preset)
    6 — Pad voice II    (AKWF sine waveform, 'pad' preset)
    7 — Pad voice III   (AKWF sine waveform, 'pad' preset)

Structure:
    I.   The Loom (Intro)        — 4 bars: plucked bass, ticking hat, echo
    II.  Poetical Science (Verse) — 8 bars: full texture, Ada motif
    III. Note G (Chorus)          — 8 bars: soaring melody, rich harmony
    IV.  The Engine Turns (Bridge) — 4 bars: rhythmic intensity
    V.   Fair White Wings (Outro)  — 4 bars: melody dissolves into echo
"""

import os
from pathlib import Path

from beatmaker import DrumSynth
from beatmaker_spc700 import (
    SPC700Sound, SPC700Engine,
    EchoConfig, ADSR, Gain,
    Song, Track, Instrument,
    Note, Rest, SetInstrument, SetEnvelope,
)


# ═══════════════════════════════════════════════════════════════════
#  WAVEFORM PATHS
# ═══════════════════════════════════════════════════════════════════

AKWF = Path(r"H:\Dev42\beat-maker\downloaded_samples_etc\AKWF-FREE\AKWF")

VIOLIN_WAV  = AKWF / "AKWF_violin" / "AKWF_violin_0003.wav"  # rich, expressive
CELLO_WAV   = AKWF / "AKWF_cello"  / "AKWF_cello_0002.wav"   # warm, full
SINE_WAV    = AKWF / "AKWF_bw_sin" / "AKWF_sin_0001.wav"     # pure, ethereal
PIANO_WAV   = AKWF / "AKWF_piano"  / "AKWF_piano_0003.wav"   # bell-like attack
FLUTE_WAV   = AKWF / "AKWF_flute"  / "AKWF_flute_0002.wav"   # breathy, soft


# ═══════════════════════════════════════════════════════════════════
#  INSTRUMENTS
# ═══════════════════════════════════════════════════════════════════

# --- Drums (beatmaker synthesis → BRR encoding) ---
kick_inst   = SPC700Sound.drum(DrumSynth.kick(pitch=50, duration=0.3))
snare_inst  = SPC700Sound.drum(DrumSynth.snare(duration=0.2))
hihat_inst  = SPC700Sound.drum(DrumSynth.hihat(duration=0.08))

# --- Melodic (AKWF waveforms through the Gaussian loom) ---
lead_inst   = SPC700Sound.synth(str(VIOLIN_WAV), preset='lead')
bass_inst   = SPC700Sound.synth(str(CELLO_WAV), preset='bass')
pad_inst    = SPC700Sound.synth(str(SINE_WAV), preset='pad')
pluck_inst  = SPC700Sound.synth(str(PIANO_WAV), preset='pluck')
bell_inst   = SPC700Sound.synth(str(FLUTE_WAV), preset='bell')


# ═══════════════════════════════════════════════════════════════════
#  ENGINE SETUP
# ═══════════════════════════════════════════════════════════════════

engine = SPC700Engine(
    echo=EchoConfig(
        enabled=True,
        delay=5,            # 80ms — spacious but not overwhelming
        feedback=65,        # moderate tail
        volume_left=45,
        volume_right=45,
        voices=0xFF,        # all voices feed the echo
        # Warm lowpass FIR — each echo repetition gets darker
        fir=(80, 48, 24, 12, 6, 3, 2, 1),
    ),
    master_volume=(120, 120),
)

engine.sound("kick", kick_inst)
engine.sound("snare", snare_inst)
engine.sound("hihat", hihat_inst)
engine.sound("lead", lead_inst)
engine.sound("bass", bass_inst)
engine.sound("pad", pad_inst)
engine.sound("pluck", pluck_inst)
engine.sound("bell", bell_inst)


# ═══════════════════════════════════════════════════════════════════
#  MUSICAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════

BPM = 108
BEAT = 1.0          # one beat
HALF = 0.5
QTR = 0.25
EIGHTH = 0.125
BAR = 4.0           # 4 beats per bar

# Section lengths in beats
INTRO_LEN   = 4 * BAR    # 16 beats
VERSE_LEN   = 8 * BAR    # 32 beats
CHORUS_LEN  = 8 * BAR    # 32 beats
BRIDGE_LEN  = 4 * BAR    # 16 beats
OUTRO_LEN   = 4 * BAR    # 16 beats

TOTAL_BEATS = INTRO_LEN + VERSE_LEN + CHORUS_LEN + BRIDGE_LEN + OUTRO_LEN
# = 112 beats


# ═══════════════════════════════════════════════════════════════════
#  CHORD DEFINITIONS (D minor)
# ═══════════════════════════════════════════════════════════════════

# Verse: i - VI - III - VII (Dm - Bb - F - C)
VERSE_CHORDS = [
    ('D3', 'F3', 'A3'),     # Dm
    ('Bb2', 'D3', 'F3'),    # Bb
    ('F3', 'A3', 'C4'),     # F
    ('C3', 'E3', 'G3'),     # C
]

# Chorus: i - iv - V - i (Dm - Gm - A - Dm)
CHORUS_CHORDS = [
    ('D3', 'F3', 'A3'),     # Dm
    ('G3', 'Bb3', 'D4'),    # Gm
    ('A3', 'C#4', 'E4'),    # A
    ('D3', 'F3', 'A3'),     # Dm
]

# Bridge: VI - VII - i - V (Bb - C - Dm - A)
BRIDGE_CHORDS = [
    ('Bb2', 'D3', 'F3'),    # Bb
    ('C3', 'E3', 'G3'),     # C
    ('D3', 'F3', 'A3'),     # Dm
    ('A2', 'C#3', 'E3'),    # A
]

# Outro: i - VI - III - i (Dm - Bb - F - Dm)
OUTRO_CHORDS = [
    ('D3', 'F3', 'A3'),     # Dm
    ('Bb2', 'D3', 'F3'),    # Bb
    ('F3', 'A3', 'C4'),     # F
    ('D3', 'F3', 'A3'),     # Dm
]


# ═══════════════════════════════════════════════════════════════════
#  COMPOSITION
# ═══════════════════════════════════════════════════════════════════

song = Song(bpm=BPM)
song.echo = engine._echo
song.master_volume = engine._master_volume


# --- Voice 0: Kick Drum ---
v_kick = song.add_track(kick_inst, voice=0)

# I. Intro — no kick
v_kick.rest(INTRO_LEN)
# II. Verse — kick on beats 1, 3
for _ in range(8):  # 8 bars
    v_kick.note(duration=QTR, velocity=0.85)
    v_kick.rest(BAR / 2 - QTR)
    v_kick.note(duration=QTR, velocity=0.75)
    v_kick.rest(BAR / 2 - QTR)
# III. Chorus — four-on-the-floor
for _ in range(8):
    for _ in range(4):
        v_kick.note(duration=QTR, velocity=0.9)
        v_kick.rest(BEAT - QTR)
# IV. Bridge — driving syncopated kick
for _ in range(4):
    v_kick.note(duration=QTR, velocity=0.95)
    v_kick.rest(QTR)
    v_kick.note(duration=QTR, velocity=0.7)
    v_kick.rest(BEAT - QTR)
    v_kick.note(duration=QTR, velocity=0.85)
    v_kick.rest(QTR)
    v_kick.note(duration=QTR, velocity=0.7)
    v_kick.rest(BEAT - QTR)
# V. Outro — sparse kick, fading
v_kick.note(duration=QTR, velocity=0.7)
v_kick.rest(BAR - QTR)
v_kick.note(duration=QTR, velocity=0.5)
v_kick.rest(BAR - QTR)
v_kick.rest(2 * BAR)  # silence for last 2 bars


# --- Voice 1: Snare Drum ---
v_snare = song.add_track(snare_inst, voice=1)

# I. Intro — no snare
v_snare.rest(INTRO_LEN)
# II. Verse — snare on beats 2, 4
for _ in range(8):
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.65)
    v_snare.rest(BEAT - QTR)
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.6)
    v_snare.rest(BEAT - QTR)
# III. Chorus — stronger backbeat
for _ in range(8):
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.85)
    v_snare.rest(BEAT - QTR)
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.8)
    v_snare.rest(BEAT - QTR)
# IV. Bridge — snare on 2 and 4, accented
for _ in range(4):
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.9)
    v_snare.rest(BEAT - QTR)
    v_snare.rest(BEAT)
    v_snare.note(duration=QTR, velocity=0.85)
    v_snare.rest(BEAT - QTR)
# V. Outro — one snare hit, then silence
v_snare.rest(BEAT)
v_snare.note(duration=QTR, velocity=0.5)
v_snare.rest(OUTRO_LEN - BEAT - QTR)


# --- Voice 2: Hi-hat / Bell ---
v_hat = song.add_track(hihat_inst, voice=2)

# I. Intro — mechanical eighth-note hat (the clock ticking)
for _ in range(int(INTRO_LEN / HALF)):
    v_hat.note(duration=EIGHTH, velocity=0.35)
    v_hat.rest(HALF - EIGHTH)
# II. Verse — eighth-note hats
for _ in range(int(VERSE_LEN / HALF)):
    v_hat.note(duration=EIGHTH, velocity=0.45)
    v_hat.rest(HALF - EIGHTH)
# III. Chorus — sixteenth-note hats for energy
for _ in range(int(CHORUS_LEN / QTR)):
    v_hat.note(duration=EIGHTH, velocity=0.4)
    v_hat.rest(QTR - EIGHTH)
# IV. Bridge — driving sixteenths
for _ in range(int(BRIDGE_LEN / QTR)):
    v_hat.note(duration=EIGHTH, velocity=0.5)
    v_hat.rest(QTR - EIGHTH)
# V. Outro — switch to bell instrument, slow tolls
v_hat.set_instrument(bell_inst)
v_hat.set_envelope(ADSR(attack=15, decay=3, sustain_level=0, sustain_rate=10))
v_hat.note('D5', BAR, velocity=0.6)        # a single bell toll
v_hat.note('D5', BAR, velocity=0.4)
v_hat.note('D5', BAR * 2, velocity=0.3)    # let it ring and fade


# --- Voice 3: Bass ---
v_bass = song.add_track(bass_inst, voice=3)

# I. Intro — the Jacquard loom pattern (pluck preset)
v_bass.set_instrument(pluck_inst)
v_bass.set_envelope(ADSR(attack=15, decay=4, sustain_level=0, sustain_rate=20))
for _ in range(4):  # 4 bars of the loom
    v_bass.note('D3', HALF, velocity=0.5)
    v_bass.note('A3', HALF, velocity=0.4)
    v_bass.note('D3', HALF, velocity=0.5)
    v_bass.note('A3', HALF, velocity=0.4)

# II. Verse — switch to bass preset, root motion
v_bass.set_instrument(bass_inst)
v_bass.set_envelope(ADSR(attack=15, decay=5, sustain_level=3, sustain_rate=8))
verse_bass_roots = ['D2', 'D2', 'Bb1', 'Bb1', 'F2', 'F2', 'C2', 'C2']
for root in verse_bass_roots:
    v_bass.note(root, 2.0, velocity=0.75)
    v_bass.note(root, 1.0, velocity=0.65)
    v_bass.note(root, 1.0, velocity=0.6)

# III. Chorus — driving eighth-note bass
chorus_bass = ['D2', 'D2', 'G2', 'G2', 'A2', 'A2', 'D2', 'D2']
for root in chorus_bass:
    for _ in range(4):
        v_bass.note(root, BEAT, velocity=0.8)

# IV. Bridge — syncopated bass
bridge_bass = ['Bb1', 'C2', 'D2', 'A1']
for root in bridge_bass:
    v_bass.note(root, BEAT, velocity=0.85)
    v_bass.note(root, BEAT, velocity=0.7)
    v_bass.rest(HALF)
    v_bass.note(root, HALF, velocity=0.8)
    v_bass.note(root, BEAT, velocity=0.7)

# V. Outro — slow, fading bass
v_bass.note('D2', BAR, velocity=0.5)
v_bass.note('D2', BAR, velocity=0.35)
v_bass.rest(2 * BAR)


# --- Voice 4: Lead Melody ---
v_lead = song.add_track(lead_inst, voice=4)

# I. Intro — silence, then a single rising note at the end
v_lead.rest(INTRO_LEN - BAR)
# A rising D4 with vibrato — the machine awakening to consciousness
v_lead.note('D4', BAR, velocity=0.5)
v_lead.vibrato(depth=0.3, rate=4.5, duration=BAR, delay=BEAT)

# II. Verse — Ada Motif + Answer (2 statements)
# Ada motif: D4:1 F4:0.5 A4:0.5 G4:1 F4:0.5 E4:0.5 = 4 beats
# Ada answer: A4:1 G4:0.5 F4:0.5 E4:1 D4:2 = 5 beats — but we'll make it 4
def play_ada_motif(track, velocity=0.75):
    track.note('D4', BEAT, velocity=velocity)
    track.note('F4', HALF, velocity=velocity * 0.9)
    track.note('A4', HALF, velocity=velocity * 0.95)
    track.note('G4', BEAT, velocity=velocity * 0.9)
    track.note('F4', HALF, velocity=velocity * 0.85)
    track.note('E4', HALF, velocity=velocity * 0.8)

def play_ada_answer(track, velocity=0.7):
    track.note('A4', BEAT, velocity=velocity)
    track.note('G4', HALF, velocity=velocity * 0.9)
    track.note('F4', HALF, velocity=velocity * 0.85)
    track.note('E4', BEAT, velocity=velocity * 0.8)
    track.note('D4', BEAT, velocity=velocity * 0.7)

# First statement (bars 1-2)
play_ada_motif(v_lead, 0.75)
# Bar 3: answer
play_ada_answer(v_lead, 0.7)
# Bar 4: rest
v_lead.rest(BEAT)
# Bar 5-6: motif transposed up (elevated)
v_lead.note('G4', BEAT, velocity=0.8)
v_lead.note('Bb4', HALF, velocity=0.75)
v_lead.note('D5', HALF, velocity=0.8)
v_lead.note('C5', BEAT, velocity=0.75)
v_lead.note('Bb4', HALF, velocity=0.7)
v_lead.note('A4', HALF, velocity=0.65)
# Bar 7: elevated answer
v_lead.note('D5', BEAT, velocity=0.75)
v_lead.note('C5', HALF, velocity=0.7)
v_lead.note('Bb4', HALF, velocity=0.65)
v_lead.note('A4', BEAT, velocity=0.6)
v_lead.note('G4', BEAT, velocity=0.55)
# Bar 8: rest
v_lead.rest(BEAT)

# III. Chorus — Note G melody (the prophetic vision)
# Note G: D5:1 C5:0.5 A4:0.5 Bb4:1 A4:0.5 G4:0.5 F4:1 E4:0.5 D4:0.5 F4:1 A4:2
def play_note_g(track, velocity=0.85):
    track.note('D5', BEAT, velocity=velocity)
    track.note('C5', HALF, velocity=velocity * 0.95)
    track.note('A4', HALF, velocity=velocity * 0.9)
    track.note('Bb4', BEAT, velocity=velocity * 0.95)
    track.note('A4', HALF, velocity=velocity * 0.9)
    track.note('G4', HALF, velocity=velocity * 0.85)
    track.note('F4', BEAT, velocity=velocity * 0.85)
    track.note('E4', HALF, velocity=velocity * 0.8)
    track.note('D4', HALF, velocity=velocity * 0.75)
    track.note('F4', BEAT, velocity=velocity * 0.8)
    track.note('A4', 2 * BEAT, velocity=velocity * 0.85)
    # Add vibrato on the sustained A4
    track.vibrato(depth=0.4, rate=5.5, duration=2 * BEAT, delay=HALF)

# First Note G (8 beats)
play_note_g(v_lead, 0.85)
# Rest (4 beats)
v_lead.rest(BAR)
# Note G transposed up a fourth (8 beats)
v_lead.note('G5', BEAT, velocity=0.9)
v_lead.note('F5', HALF, velocity=0.85)
v_lead.note('D5', HALF, velocity=0.8)
v_lead.note('Eb5', BEAT, velocity=0.85)
v_lead.note('D5', HALF, velocity=0.8)
v_lead.note('C5', HALF, velocity=0.75)
v_lead.note('Bb4', BEAT, velocity=0.8)
v_lead.note('A4', HALF, velocity=0.75)
v_lead.note('G4', HALF, velocity=0.7)
v_lead.note('Bb4', BEAT, velocity=0.75)
v_lead.note('D5', 2 * BEAT, velocity=0.85)
v_lead.vibrato(depth=0.5, rate=5.0, duration=2 * BEAT, delay=HALF)
# Return (8 beats)
play_note_g(v_lead, 0.8)
# Rest (4 beats)
v_lead.rest(BAR)

# IV. Bridge — quickened motif fragments
# Double-speed motif fragments, machine-like urgency
for transpose, vel in [(0, 0.8), (5, 0.75), (0, 0.85), (-2, 0.7),
                       (7, 0.8), (0, 0.75), (5, 0.85), (0, 0.8)]:
    base_notes = [('D4', HALF), ('F4', QTR), ('A4', QTR),
                  ('G4', HALF), ('F4', QTR), ('E4', QTR)]
    for note_name, dur in base_notes:
        # Simple transposition by adding semitones via note lookup
        from beatmaker_spc700 import note_to_midi, midi_to_freq
        midi = note_to_midi(note_name) + transpose
        # Convert back to frequency for the note
        v_lead.note(float(midi_to_freq(midi)), dur * 0.5, velocity=vel)

# V. Outro — the theme augmented (slow, dissolving)
v_lead.note('D4', 2 * BEAT, velocity=0.55)
v_lead.vibrato(depth=0.3, rate=3.5, duration=2 * BEAT)
v_lead.note('F4', BEAT, velocity=0.45)
v_lead.note('A4', BEAT, velocity=0.5)
v_lead.vibrato(depth=0.4, rate=3.0, duration=BEAT)
v_lead.note('G4', 2 * BEAT, velocity=0.4)
v_lead.note('F4', BEAT, velocity=0.35)
v_lead.note('E4', BEAT, velocity=0.3)
v_lead.note('D4', 4 * BEAT, velocity=0.25)
v_lead.vibrato(depth=0.5, rate=2.5, duration=4 * BEAT, delay=BEAT)


# --- Voices 5, 6, 7: Pad Chord Voices ---
v_pad1 = song.add_track(pad_inst, voice=5)
v_pad2 = song.add_track(pad_inst, voice=6)
v_pad3 = song.add_track(pad_inst, voice=7)

def play_chord_sequence(pv1, pv2, pv3, chords, bars_per_chord, velocity=0.5):
    """Play a chord progression across three pad voices."""
    for root, third, fifth in chords:
        dur = bars_per_chord * BAR
        pv1.note(root, dur, velocity=velocity)
        pv2.note(third, dur, velocity=velocity * 0.9)
        pv3.note(fifth, dur, velocity=velocity * 0.85)

# I. Intro — no pads
v_pad1.rest(INTRO_LEN)
v_pad2.rest(INTRO_LEN)
v_pad3.rest(INTRO_LEN)

# II. Verse — gentle pads (each chord = 2 bars)
play_chord_sequence(v_pad1, v_pad2, v_pad3,
                    VERSE_CHORDS, bars_per_chord=2, velocity=0.35)

# III. Chorus — richer pads (each chord = 2 bars)
play_chord_sequence(v_pad1, v_pad2, v_pad3,
                    CHORUS_CHORDS, bars_per_chord=2, velocity=0.5)

# IV. Bridge — faster chords (each chord = 1 bar)
play_chord_sequence(v_pad1, v_pad2, v_pad3,
                    BRIDGE_CHORDS, bars_per_chord=1, velocity=0.45)

# V. Outro — slow, fading Dm chord
v_pad1.note('D3', OUTRO_LEN, velocity=0.35)
v_pad1.tremolo(depth=0.3, rate=0.5, duration=OUTRO_LEN, delay=BAR)
v_pad2.note('F3', OUTRO_LEN, velocity=0.3)
v_pad2.tremolo(depth=0.3, rate=0.5, duration=OUTRO_LEN, delay=BAR)
v_pad3.note('A3', OUTRO_LEN, velocity=0.25)
v_pad3.tremolo(depth=0.3, rate=0.5, duration=OUTRO_LEN, delay=BAR)


# ═══════════════════════════════════════════════════════════════════
#  RENDER
# ═══════════════════════════════════════════════════════════════════

def main():
    """Render the composition through the SPC700 DSP."""
    print("=" * 66)
    print("  The Enchantress of Numbers — Version II")
    print("  A Victorian Portrait Through the Gaussian Loom")
    print("  by A.A.L.")
    print("=" * 66)
    print()

    total_bars = TOTAL_BEATS / BAR
    duration_sec = (TOTAL_BEATS / BPM) * 60
    print(f"  Key:       D minor")
    print(f"  Tempo:     {BPM} BPM")
    print(f"  Voices:    8 (the full DSP)")
    print(f"  Structure: Intro(4) - Verse(8) - Chorus(8) - Bridge(4) - Outro(4)")
    print(f"  Total:     {int(total_bars)} bars ({duration_sec:.1f}s)")
    print()

    print(f"  Instruments:")
    print(f"    Kick:    DrumSynth -> BRR ({kick_inst.sample.memory_bytes} bytes)")
    print(f"    Snare:   DrumSynth -> BRR ({snare_inst.sample.memory_bytes} bytes)")
    print(f"    Hi-hat:  DrumSynth -> BRR ({hihat_inst.sample.memory_bytes} bytes)")
    print(f"    Lead:    AKWF violin -> BRR ({lead_inst.sample.memory_bytes} bytes)")
    print(f"    Bass:    AKWF cello -> BRR ({bass_inst.sample.memory_bytes} bytes)")
    print(f"    Pad:     AKWF sine -> BRR ({pad_inst.sample.memory_bytes} bytes)")
    print(f"    Pluck:   AKWF piano -> BRR ({pluck_inst.sample.memory_bytes} bytes)")
    print(f"    Bell:    AKWF flute -> BRR ({bell_inst.sample.memory_bytes} bytes)")
    total_brr = sum(i.sample.memory_bytes for i in
                    [kick_inst, snare_inst, hihat_inst, lead_inst,
                     bass_inst, pad_inst, pluck_inst, bell_inst])
    print(f"    Total:   {total_brr} bytes / {65536 - engine._echo.buffer_bytes} available")
    print()

    print(f"  Echo: delay={engine._echo.delay} ({engine._echo.delay * 16}ms), "
          f"feedback={engine._echo.feedback}, "
          f"buffer={engine._echo.buffer_bytes} bytes")
    print(f"  FIR:  {list(engine._echo.fir)}")
    print()

    # Render through the SPC700 DSP
    print("  Compiling...")
    compiled = song.compile()
    print(f"  Timeline: {len(compiled.timeline)} register writes")
    print()

    output_path = os.path.join(os.path.dirname(__file__),
                               "ada_lovelace_theme_v2.wav")
    print(f"  Rendering through the SPC700 DSP...")
    compiled.render(output_path, tail=3.0, progress=True)
    print()
    print(f"  Exported: {output_path}")
    print()
    print('  "The Analytical Engine weaves algebraic patterns')
    print('   just as the Jacquard loom weaves flowers and leaves."')
    print("                                        -- A.A.L., 1843")
    print()
    print("  Now woven through silicon.")
    print()


if __name__ == "__main__":
    main()
