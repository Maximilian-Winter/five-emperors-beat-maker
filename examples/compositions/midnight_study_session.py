"""
╔══════════════════════════════════════════════════════════════════╗
║           Midnight Study Session                                ║
║     Lo-fi Hip-Hop for Late Night Focus                          ║
║                                                                  ║
║     This composition demonstrates:                               ║
║       1. KeygroupProgram — AKWF single-cycle waveforms as        ║
║          chromatic instruments (e-piano chords + guitar melody)   ║
║       2. EuclideanPattern — Algorithmic hi-hat rhythms            ║
║       3. Humanizer — Timing jitter and velocity variation         ║
║          for organic, lo-fi feel                                  ║
║       4. GrooveTemplate — MPC-style swing on the drums            ║
║       5. Loaded drum samples — Real one-shots from the            ║
║          Libre Sample Pack (kick, snare, hi-hat, 808 bass)        ║
║       6. Effects — BitCrusher (subtle grit), Reverb (space),      ║
║          Delay (depth), LowPassFilter (warmth)                    ║
║                                                                  ║
║     ~85 BPM, 4 bars, key of C minor                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

from pathlib import Path

from beatmaker import (
    # Core & building
    create_song, load_audio, Sample,
    # Keygroup
    KeygroupProgram,
    # Sequencer
    EuclideanPattern,
    # Expression
    Humanizer, GrooveTemplate,
    # Melody
    Phrase,
    # Effects
    BitCrusher, Reverb, Delay, LowPassFilter,
    # Synthesis (for envelope shaping)
    ADSREnvelope,
)


# ═══════════════════════════════════════════════════════════════════
#  I.  SAMPLE PATHS — Libre Sample Pack & AKWF Waveforms
# ═══════════════════════════════════════════════════════════════════

SAMPLES_BASE = Path(r"H:\Dev42\beat-maker\downloaded_samples_etc")

# -- Drum one-shots from the Libre Sample Pack --
KICK_PATH    = SAMPLES_BASE / "the-libre-sample-pack/drums/one shot/kicks/Deep Kick @TeaBoi.wav"
SNARE_PATH   = SAMPLES_BASE / "the-libre-sample-pack/drums/one shot/snares/snare 3 @TeaBoi.wav"
HIHAT_PATH   = SAMPLES_BASE / "the-libre-sample-pack/drums/one shot/hi hats/Ringing Hat @TeaBoi.wav"
OPEN_HAT_PATH = SAMPLES_BASE / "the-libre-sample-pack/drums/one shot/hi hats/Open Hat 1 @TeaBoi.wav"
BASS_808_PATH = SAMPLES_BASE / "the-libre-sample-pack/drums/one shot/808/fat 808 c 1 @TeaBoi.wav"

# -- AKWF single-cycle waveforms (great for KeygroupProgram) --
EPIANO_WAV = SAMPLES_BASE / "AKWF-FREE/AKWF/AKWF_epiano/AKWF_epiano_0003.wav"
GUITAR_WAV = SAMPLES_BASE / "AKWF-FREE/AKWF/AKWF_aguitar/AKWF_aguitar_0005.wav"


# ═══════════════════════════════════════════════════════════════════
#  II.  LOAD SAMPLES
# ═══════════════════════════════════════════════════════════════════

# Drum samples loaded and wrapped as Sample objects
kick_sample   = Sample("kick", load_audio(str(KICK_PATH)), tags=["drums", "kick"])
snare_sample  = Sample("snare", load_audio(str(SNARE_PATH)), tags=["drums", "snare"])
hihat_sample  = Sample("hihat", load_audio(str(HIHAT_PATH)), tags=["drums", "hihat"])
open_hat      = Sample("open_hat", load_audio(str(OPEN_HAT_PATH)), tags=["drums", "hihat"])
bass_808      = Sample("808", load_audio(str(BASS_808_PATH)), tags=["bass", "808"])

# AKWF waveforms for keygroup instruments
epiano_wav = load_audio(str(EPIANO_WAV))
guitar_wav = load_audio(str(GUITAR_WAV))


# ═══════════════════════════════════════════════════════════════════
#  III.  KEYGROUP INSTRUMENTS — Chromatic from Single-Cycle Waveforms
# ═══════════════════════════════════════════════════════════════════

# E-piano keygroup — warm Rhodes-like chords
# The ADSR envelope gives each note a soft attack and gentle release,
# perfect for lo-fi chord stabs.
epiano_keys = KeygroupProgram.from_sample(
    epiano_wav,
    root_note='C4',
    name="Lo-fi Rhodes",
    envelope=ADSREnvelope(
        attack=0.02,
        decay=0.3,
        sustain=0.6,
        release=0.4,
    ),
)

# Guitar keygroup — mellow nylon-string tone for the melody line
guitar_keys = KeygroupProgram.from_sample(
    guitar_wav,
    root_note='C4',
    name="Nylon Guitar",
    envelope=ADSREnvelope(
        attack=0.01,
        decay=0.2,
        sustain=0.5,
        release=0.3,
    ),
)


# ═══════════════════════════════════════════════════════════════════
#  IV.  EUCLIDEAN HI-HAT PATTERN
# ═══════════════════════════════════════════════════════════════════

# E(7, 16) distributes 7 hits across 16 steps — a syncopated,
# off-kilter rhythm that feels natural in lo-fi contexts.
hat_pattern = EuclideanPattern.generate(hits=7, steps=16, rotation=1)

# Convert the Pattern object to a boolean list for the drum builder
hat_bool = [step.active for step in hat_pattern.steps]


# ═══════════════════════════════════════════════════════════════════
#  V.  GROOVE TEMPLATE — MPC-style Swing
# ═══════════════════════════════════════════════════════════════════

# Push every other 16th note slightly late for that head-nod swing.
# Timing offsets are fractions of a step duration; velocity scales
# add ghost-note dynamics on off-beats.
lofi_groove = GrooveTemplate(
    name="Lo-fi Swing",
    timing_offsets=[
        0.0,  0.06,  0.0,  0.08,   # beat 1: slight push on &'s
        0.0,  0.05,  0.0,  0.07,   # beat 2
        0.0,  0.06,  0.0,  0.09,   # beat 3
        0.0,  0.05,  0.0,  0.07,   # beat 4
    ],
    velocity_scales=[
        1.0,  0.7,  0.85, 0.65,    # beat 1: accented downbeat
        0.9,  0.6,  0.8,  0.6,     # beat 2: slightly softer
        1.0,  0.7,  0.85, 0.65,    # beat 3
        0.9,  0.6,  0.8,  0.6,     # beat 4
    ],
)


# ═══════════════════════════════════════════════════════════════════
#  VI.  MELODY — A Pensive Late-Night Line
# ═══════════════════════════════════════════════════════════════════

# Simple, spacious melody in C minor — the kind that floats over
# lo-fi beats while you stare at a textbook at 2 AM.
melody_phrase = Phrase.from_string(
    "Eb4:1.5 D4:0.5 C4:1 R:1 "       # bars 1-2: descending motif
    "Bb3:1 C4:0.5 Eb4:0.5 G4:2 "     # bars 2-3: upward reach
    "F4:1 Eb4:1 D4:1 C4:1 "          # bars 3-4: gentle descent
    "R:1 Bb3:1.5 C4:1.5 R:1",        # bar 4: resolving rest
    name="midnight_melody"
)


# ═══════════════════════════════════════════════════════════════════
#  VII.  CHORD PROGRESSION — Cm  Ab  Eb  Bb (i  VI  III  VII)
# ═══════════════════════════════════════════════════════════════════

# Classic lo-fi progression: four chords, each lasting one bar (4 beats).
# Voiced in the middle register for warmth.
chords = [
    (['C3', 'Eb3', 'G3', 'Bb3'],  0.0, 3.5),   # Cm7    bar 1
    (['Ab2', 'C3', 'Eb3', 'G3'],  4.0, 3.5),    # AbMaj7 bar 2
    (['Eb3', 'G3', 'Bb3', 'D4'],  8.0, 3.5),    # EbMaj7 bar 3
    (['Bb2', 'D3', 'F3', 'A3'],  12.0, 3.5),    # BbMaj7 bar 4
]


# ═══════════════════════════════════════════════════════════════════
#  VIII.  BUILD THE SONG
# ═══════════════════════════════════════════════════════════════════

song = (create_song("Midnight Study Session")
    .tempo(85)
    .time_signature(4, 4)
    .bars(4)

    # ── Drums: loaded libre samples with Euclidean hat pattern ──
    .add_drums(lambda d: d
        .use_kit(kick=kick_sample, snare=snare_sample, hihat=hihat_sample)
        # Kick: beat 1 and the "and" of beat 3 — relaxed boom-bap
        .kick(beats=[0, 2.5])
        # Snare: beats 2 and 4 — classic backbeat
        .snare(beats=[1, 3])
        # Hi-hat: Euclidean E(7,16) pattern for organic rhythm
        .hihat(pattern=hat_bool, velocity=0.6)
        # Apply the lo-fi groove template for swing
        .groove(lofi_groove)
        # Humanize — add subtle imperfections
        .humanize(timing=0.012, velocity=0.15, seed=42)
        .volume(0.75)
        # Subtle bit-crush for tape-like texture
        .effect(BitCrusher(bit_depth=12, sample_hold=1))
        .effect(Reverb(room_size=0.3, damping=0.6, mix=0.15))
    )

    # ── E-Piano Chords: KeygroupProgram from AKWF waveform ──
    .add_keygroup("Lo-fi Rhodes", epiano_keys, lambda k: k
        # Place the four-chord progression
        .chord(chords[0][0], beat=chords[0][1], duration=chords[0][2], velocity=0.65)
        .chord(chords[1][0], beat=chords[1][1], duration=chords[1][2], velocity=0.60)
        .chord(chords[2][0], beat=chords[2][1], duration=chords[2][2], velocity=0.65)
        .chord(chords[3][0], beat=chords[3][1], duration=chords[3][2], velocity=0.60)
        .volume(0.55)
        .pan(-0.15)
        # Warm it up: low-pass filter rolls off highs
        .effect(LowPassFilter(cutoff=2500.0))
        # Spacious reverb — like playing in a bedroom at midnight
        .effect(Reverb(room_size=0.5, damping=0.4, mix=0.35))
        # Subtle delay — eighth-note echoes
        .effect(Delay(
            delay_time=60.0 / 85.0 / 2,  # eighth note at 85 BPM
            feedback=0.25,
            mix=0.2,
        ))
        # Gentle humanization on the chords
        .humanize(timing=0.008, velocity=0.08, seed=7)
    )

    # ── Guitar Melody: KeygroupProgram from AKWF guitar waveform ──
    .add_keygroup("Nylon Melody", guitar_keys, lambda k: k
        .phrase(melody_phrase, start_beat=0.0, velocity_scale=0.7)
        .volume(0.45)
        .pan(0.2)
        .effect(LowPassFilter(cutoff=3000.0))
        .effect(Reverb(room_size=0.45, damping=0.5, mix=0.3))
        .effect(Delay(
            delay_time=60.0 / 85.0 * 0.75,  # dotted eighth
            feedback=0.2,
            mix=0.15,
        ))
        .humanize(timing=0.015, velocity=0.1, seed=13)
    )

    .build()
)


# ═══════════════════════════════════════════════════════════════════
#  IX.  EXPORT
# ═══════════════════════════════════════════════════════════════════

output_path = Path(__file__).parent / "midnight_study_session.wav"
song.export(output_path)
print(f"Exported: {output_path}")
print(f"  BPM:      85")
print(f"  Duration: {song.duration:.1f}s ({song.duration_bars:.1f} bars)")
print(f"  Tracks:   {len(song.tracks)}")
for t in song.tracks:
    print(f"    - {t.name}: {len(t.placements)} placements, "
          f"{len(t.effects)} effects")
