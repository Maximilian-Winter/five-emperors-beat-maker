"""
+======================================================================+
|                     NEON DRAGON PROTOCOL                             |
|                  Cyberfunk -- 108 BPM                                |
|                                                                      |
|   A long, evolving cyberfunk track (~2.5 minutes). Dirty funk        |
|   basslines, glitchy syncopated drums, futuristic synth stabs,       |
|   vocoder-like pads, and heavy sidechain pumping. Cyberpunk meets    |
|   Parliament-Funkadelic.                                             |
|                                                                      |
|   Key: E minor                                                       |
|   Tempo: 108 BPM, 4/4                                               |
|                                                                      |
|   Arrangement (80 bars total, ~2:58):                                |
|     Intro       (8 bars)  -- Filtered pad fade-in, sparse hats       |
|     Groove     (16 bars)  -- Full funk drums, acid bass, stabs       |
|     Breakdown   (8 bars)  -- Bass + filtered arp, filter sweep       |
|     Drop       (16 bars)  -- Everything hits, sidechain pumping      |
|     Bridge      (8 bars)  -- Half-time feel, melodic synth line      |
|     Final Drop (16 bars)  -- Biggest section, extra percussion       |
|     Outro       (8 bars)  -- Fade down, elements dropping out        |
|                                                                      |
|   Features demonstrated:                                             |
|     - LinnDrum loaded .WAV samples from tidal-drum-machines          |
|     - Step sequencer with Pattern.from_string (syncopated funk)      |
|     - EuclideanPattern for sparse hi-hat rhythms                     |
|     - BassTrackBuilder .line() with funky syncopated rhythms         |
|     - KeygroupProgram from AKWF single-cycle waveforms (stabs)       |
|     - Arpeggiator with ChordShape progression (filtered arp)         |
|     - ArpSynthesizer rendering arp events to audio                   |
|     - SidechainPresets (heavy EDM pumping on pad)                    |
|     - AutomationCurve + AutomatedFilter for breakdown sweep          |
|     - Humanizer on drums for organic groove feel                     |
|     - BitCrusher on synth stabs for grit                             |
|     - Heavy effects: Compressor, BitCrusher, Delay, Reverb,         |
|       LowPassFilter, SidechainEnvelope                               |
|     - Section / Arrangement for full song structure                  |
|     - Master chain: Compressor + Limiter                             |
+======================================================================+
"""

import os
import sys
from pathlib import Path

from beatmaker import (
    # Core types
    create_song, Song, Track, TrackType, Sample, SamplePlacement,
    AudioData,
    # I/O
    load_audio,
    # Synthesis
    DrumSynth, BassSynth, ADSREnvelope,
    note_to_freq,
    # Sequencer
    Pattern, StepSequencer, EuclideanPattern,
    # Arpeggiator
    Arpeggiator, ArpDirection, ArpMode, ArpSynthesizer,
    create_arpeggiator, ChordShape,
    # Keygroup
    KeygroupProgram,
    # Effects
    Compressor, Limiter, LowPassFilter, HighPassFilter, Reverb, Delay,
    BitCrusher, Chorus,
    SidechainPresets, SidechainEnvelope, create_sidechain,
    # Automation
    AutomationCurve, AutomatedFilter, CurveType,
    # Arrangement
    Section, Arrangement,
    # Expression
    Humanizer,
)


# =====================================================================
#  CONFIGURATION
# =====================================================================

BPM = 108
SAMPLE_RATE = 44100
BEATS_PER_BAR = 4
BEAT_SEC = 60.0 / BPM                        # ~0.5556 s per beat
BAR_SEC = BEAT_SEC * BEATS_PER_BAR            # ~2.2222 s per bar

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
LINNDRUM_ROOT = PROJECT_ROOT / "downloaded_samples_etc/tidal-drum-machines/machines/LinnDrum"
AKWF_ROOT = PROJECT_ROOT / "downloaded_samples_etc/AKWF-FREE/AKWF"


# =====================================================================
#  1.  LOAD LINNDRUM SAMPLES
# =====================================================================

def load_linndrum_sample(subdir: str, filename: str, name: str) -> Sample:
    """Load a single LinnDrum .WAV file into a Sample object."""
    filepath = LINNDRUM_ROOT / subdir / filename
    audio = load_audio(filepath)
    return Sample(name=name, audio=audio, tags=["linndrum", name])


print("Loading LinnDrum samples...")

kick      = load_linndrum_sample("linndrum-bd",   "Bassdrum.wav",      "kick")
snare     = load_linndrum_sample("linndrum-sd",   "0Snarderum-01.wav", "snare")
snare_alt = load_linndrum_sample("linndrum-sd",   "0Snarderum-02.wav", "snare_alt")
hihat     = load_linndrum_sample("linndrum-hh",   "Hat Closed-01.wav", "hihat")
hihat_alt = load_linndrum_sample("linndrum-hh",   "Hat Closed-02.wav", "hihat_alt")
openhat   = load_linndrum_sample("linndrum-oh",   "Hat Open.wav",      "openhat")
clap      = load_linndrum_sample("linndrum-cp",   "Clap.wav",          "clap")
tambourine = load_linndrum_sample("linndrum-tb",  "Tambourine.wav",    "tambourine")
cowbell   = load_linndrum_sample("linndrum-cb",   "Cowbell.wav",       "cowbell")
rimshot   = load_linndrum_sample("linndrum-rim",  "Sidestick-01.wav",  "rimshot")
conga_hi  = load_linndrum_sample("linndrum-perc", "Conga H-01.wav",   "conga_hi")
conga_lo  = load_linndrum_sample("linndrum-perc", "Conga L-01.wav",   "conga_lo")


# =====================================================================
#  2.  LOAD AKWF SINGLE-CYCLE WAVEFORMS FOR SYNTHS
# =====================================================================

print("Loading AKWF waveforms...")

# FM synth waveform for stabs (metallic, digital character)
fmsynth_audio = load_audio(AKWF_ROOT / "AKWF_fmsynth" / "AKWF_fmsynth_0007.wav")
fmsynth_sample = Sample(name="fmsynth_stab", audio=fmsynth_audio)

# Distorted waveform for gritty pad texture
distorted_audio = load_audio(AKWF_ROOT / "AKWF_distorted" / "AKWF_distorted_0003.wav")
distorted_sample = Sample(name="distorted_pad", audio=distorted_audio)

# Oscchip waveform for retro digital character (bridge melody)
oscchip_audio = load_audio(AKWF_ROOT / "AKWF_oscchip" / "AKWF_oscchip_0012.wav")
oscchip_sample = Sample(name="oscchip_lead", audio=oscchip_audio)


# =====================================================================
#  3.  BUILD KEYGROUP PROGRAMS FROM AKWF WAVEFORMS
# =====================================================================

print("Building keygroup programs...")

# FM synth stab program -- maps across keyboard, looping the single cycle
stab_program = KeygroupProgram.from_sample(
    fmsynth_sample,
    root_note='C4',
    name="fm_stab",
    envelope=ADSREnvelope(attack=0.005, decay=0.12, sustain=0.3, release=0.08),
)

# Distorted pad program -- longer sustain for pad textures
pad_program = KeygroupProgram.from_sample(
    distorted_sample,
    root_note='C4',
    name="cyber_pad",
    envelope=ADSREnvelope(attack=0.3, decay=0.5, sustain=0.7, release=0.6),
)

# Oscchip lead program -- for melodic bridge section
lead_program = KeygroupProgram.from_sample(
    oscchip_sample,
    root_note='C4',
    name="chip_lead",
    envelope=ADSREnvelope(attack=0.01, decay=0.2, sustain=0.6, release=0.15),
)


# =====================================================================
#  4.  BUILD THE ARPEGGIO -- Em - Am - C - D (i - iv - VI - VII)
# =====================================================================

print("Building arpeggio...")

arp = (create_arpeggiator()
       .tempo(BPM)
       .up_down()
       .sixteenth()           # 16th-note rate for rapid movement
       .gate(0.6)
       .octaves(2)
       .swing(0.1)
       .velocity_pattern([1.0, 0.5, 0.7, 0.5, 0.85, 0.5, 0.65, 0.5])
       .build())

arp_progression = [
    ("E3", ChordShape.MINOR),    # i   - E minor
    ("A3", ChordShape.MINOR),    # iv  - A minor
    ("C4", ChordShape.MAJOR),    # VI  - C major
    ("D4", ChordShape.MAJOR),    # VII - D major
]

BEATS_PER_CHORD = BEATS_PER_BAR  # one chord per bar
arp_events = arp.generate_from_progression(arp_progression, BEATS_PER_CHORD)

# Render with a saw-wave synth for that cutting arp texture
arp_synth = ArpSynthesizer(
    waveform="saw",
    envelope=ADSREnvelope(attack=0.005, decay=0.1, sustain=0.5, release=0.12),
    sample_rate=SAMPLE_RATE,
)
arp_audio = arp_synth.render_events(arp_events)
arp_sample = Sample(name="arp_phrase", audio=arp_audio, tags=["arp", "synth"])

ARP_PHRASE_BARS = len(arp_progression)  # 4 bars per cycle


# =====================================================================
#  5.  SIDECHAIN PRESETS
# =====================================================================

sidechain_heavy = SidechainPresets.heavy_edm(bpm=BPM)
sidechain_subtle = SidechainPresets.subtle_groove(bpm=BPM)
sidechain_halftime = SidechainPresets.half_time(bpm=BPM)


# =====================================================================
#  6.  FILTER AUTOMATION -- breakdown sweep
# =====================================================================

breakdown_bars = 8
breakdown_beats = breakdown_bars * BEATS_PER_BAR  # 32 beats

filter_sweep = AutomationCurve.filter_sweep(
    start_beat=0,
    end_beat=breakdown_beats,
    start_freq=300.0,
    end_freq=10000.0,
)

breakdown_filter = AutomatedFilter(cutoff=300.0, resonance=2.5)
breakdown_filter.automate("cutoff", filter_sweep)
breakdown_filter.set_context(bpm=BPM, start_beat=0.0)


# =====================================================================
#  7.  VOLUME AUTOMATION -- intro pad fade-in, outro fade-out
# =====================================================================

# Intro: fade pad from silence to full over 8 bars
intro_vol_curve = (AutomationCurve("intro_fade", default_value=0.0)
    .ramp(0, 8 * BEATS_PER_BAR, 0.0, 0.7, CurveType.EXPONENTIAL))

# Outro: fade everything from full to silence over 8 bars
outro_vol_curve = (AutomationCurve("outro_fade", default_value=1.0)
    .ramp(0, 8 * BEATS_PER_BAR, 1.0, 0.0, CurveType.EXPONENTIAL))


# =====================================================================
#  8.  HUMANIZER for drums
# =====================================================================

humanizer = Humanizer(timing_jitter=0.008, velocity_variation=0.08, seed=42)


# =====================================================================
#  9.  HELPER FUNCTIONS -- build tracks for each element
# =====================================================================

# --- DRUMS: syncopated funk kick ---
def make_funk_kick_track(bars: int) -> Track:
    """Syncopated funk kick -- NOT four-on-floor, heavy on the one."""
    track = Track(name="Kick", track_type=TrackType.DRUMS)
    # Syncopated funk kick pattern (per bar):
    # Beat:  1  .  .  .  2  .  .  .  3  .  .  .  4  .  .  .
    #        X  .  .  x  .  .  x  .  X  .  .  .  .  x  .  .
    kick_pattern = Pattern.from_string("X..x..x.X.....x.")
    seq = StepSequencer(bpm=BPM, steps_per_beat=4, swing=0.12)
    seq.add_pattern("kick", kick_pattern, kick)
    events = seq.render_pattern("kick", bars)
    for time, velocity, sample in events:
        track.add(sample, time, velocity)
    return track


# --- DRUMS: ghost-note snare ---
def make_funk_snare_track(bars: int) -> Track:
    """Funk snare with ghost notes -- backbeat + syncopated ghosts."""
    track = Track(name="Snare", track_type=TrackType.DRUMS)
    # Snare pattern with ghost notes (o = ghost):
    # Beat:  1  .  .  .  2  .  .  .  3  .  .  .  4  .  .  .
    #        .  .  o  .  X  .  .  o  .  o  .  .  X  .  o  .
    snare_pattern = Pattern.from_string("..o.X..o.o..X.o.")
    seq = StepSequencer(bpm=BPM, steps_per_beat=4, swing=0.12)
    seq.add_pattern("snare", snare_pattern, snare)
    events = seq.render_pattern("snare", bars)
    for time, velocity, sample in events:
        track.add(sample, time, velocity)
    # Apply humanization for groove
    humanizer.apply_to_track(track)
    return track


# --- DRUMS: 16th hi-hats with accent pattern ---
def make_funk_hihat_track(bars: int, *, open_accents: bool = True) -> Track:
    """16th-note hi-hats with velocity accents and occasional open hats."""
    track = Track(name="HiHat", track_type=TrackType.DRUMS)
    for bar in range(bars):
        for step in range(16):  # 16 x 16th-notes per bar
            beat_pos = step * 0.25
            time = (bar * BEATS_PER_BAR + beat_pos) * BEAT_SEC
            # Open hat on the "and" of beat 2 and the "e" of beat 4
            if open_accents and step in (5, 13):
                track.add(openhat, time, velocity=0.55)
            else:
                # Accent pattern: stronger on downbeats, ghost on weak 16ths
                if step % 4 == 0:
                    vel = 0.75
                elif step % 2 == 0:
                    vel = 0.55
                else:
                    vel = 0.35
                track.add(hihat, time, velocity=vel)
    humanizer.apply_to_track(track)
    return track


# --- DRUMS: sparse euclidean hi-hats (intro) ---
def make_sparse_hihat_track(bars: int) -> Track:
    """Euclidean hi-hat pattern -- sparse and hypnotic for intro."""
    track = Track(name="HiHat", track_type=TrackType.DRUMS)
    # E(5, 16) -- 5 hits across 16 steps, creates an interesting asymmetric pattern
    euclidean_pattern = EuclideanPattern.generate(5, 16, rotation=2)
    seq = StepSequencer(bpm=BPM, steps_per_beat=4, swing=0.15)
    seq.add_pattern("hat", euclidean_pattern, hihat)
    events = seq.render_pattern("hat", bars)
    for time, velocity, sample in events:
        track.add(sample, time, velocity * 0.6)
    return track


# --- DRUMS: clap on backbeat ---
def make_clap_track(bars: int) -> Track:
    """Claps on beats 2 and 4."""
    track = Track(name="Clap", track_type=TrackType.DRUMS)
    for bar in range(bars):
        for beat in [1, 3]:
            time = (bar * BEATS_PER_BAR + beat) * BEAT_SEC
            track.add(clap, time, velocity=0.8)
    return track


# --- DRUMS: extra percussion (congas, cowbell, tambourine) ---
def make_percussion_track(bars: int) -> Track:
    """Extra funk percussion -- congas, cowbell, tambourine."""
    track = Track(name="Percussion", track_type=TrackType.DRUMS, volume=0.5)
    # Cowbell: E(3, 8) pattern in 8th notes
    cowbell_pattern = EuclideanPattern.generate(3, 8, rotation=1)
    # Conga: syncopated pattern
    conga_pattern = Pattern.from_string("..x.x..x..x.x...")
    # Tambourine: offbeat 8ths
    seq = StepSequencer(bpm=BPM, steps_per_beat=4, swing=0.1)
    seq.add_pattern("cowbell", cowbell_pattern, cowbell)
    seq.add_pattern("conga", conga_pattern, conga_hi)

    for name in ["cowbell", "conga"]:
        events = seq.render_pattern(name, bars)
        for time, velocity, sample in events:
            track.add(sample, time, velocity * 0.65)

    # Tambourine on offbeat 8th notes
    for bar in range(bars):
        for step in range(8):
            if step % 2 == 1:  # offbeats
                beat_pos = step * 0.5
                time = (bar * BEATS_PER_BAR + beat_pos) * BEAT_SEC
                track.add(tambourine, time, velocity=0.4)

    humanizer.apply_to_track(track)
    return track


# --- BASS: dirty acid funk bassline ---
def make_funk_bass_track(bars: int) -> Track:
    """Syncopated acid funk bassline in E minor."""
    track = Track(name="Bass", track_type=TrackType.BASS, volume=0.75)
    # 2-bar funk bass pattern, repeated
    #                                note     beat  dur
    bass_line_2bar = [
        ('E2',  0,    0.75),   # hit the one hard
        ('E2',  1.0,  0.25),   # short stab
        ('G2',  1.5,  0.5),    # syncopated
        ('A2',  2.25, 0.25),   # ghost
        ('B2',  2.75, 0.5),    # push into beat 3
        ('E2',  3.5,  0.5),    # syncopated
        # Bar 2
        ('E2',  4,    0.5),
        ('D3',  4.75, 0.25),   # high stab
        ('B2',  5.25, 0.5),
        ('A2',  6.0,  0.75),
        ('G2',  6.75, 0.25),
        ('E2',  7.25, 0.75),
    ]

    for bar_offset in range(0, bars, 2):
        for note, beat, dur in bass_line_2bar:
            actual_beat = bar_offset * BEATS_PER_BAR + beat
            freq = note_to_freq(note)
            duration_sec = BEAT_SEC * dur
            bass_sample = BassSynth.acid_bass(freq, duration_sec)
            time = actual_beat * BEAT_SEC
            track.add(bass_sample, time, velocity=0.9)

    track.add_effect(LowPassFilter(cutoff=2500.0))
    track.add_effect(Compressor(threshold=-8.0, ratio=4.0))
    return track


# --- SYNTH STABS: FM stab chords using keygroup ---
def make_stab_track(bars: int) -> Track:
    """Funky FM synth stab chords, syncopated hits."""
    track = Track(name="Stabs", track_type=TrackType.LEAD, volume=0.4)
    # Stab rhythm: hit on the "and" of beats for funk feel
    # Em stab = E4+G4+B4, Am stab = A4+C5+E5, C stab, D stab
    stab_voicings = [
        (['E4', 'G4', 'B4'],  0.5),     # Em on "and" of 1
        (['E4', 'G4', 'B4'],  2.75),    # Em push
        (['A4', 'C5', 'E5'],  4.5),     # Am
        (['A4', 'C5', 'E5'],  6.75),    # Am push
        (['C4', 'E4', 'G4'],  8.5),     # C
        (['C4', 'E4', 'G4'],  10.75),   # C push
        (['D4', 'F#4', 'A4'], 12.5),    # D
        (['D4', 'F#4', 'A4'], 14.75),   # D push
    ]

    beats_per_cycle = 4 * BEATS_PER_BAR  # 4 bars
    for bar_offset in range(0, bars, 4):
        for notes, beat in stab_voicings:
            actual_beat = bar_offset * BEATS_PER_BAR + beat
            beat_dur = 60.0 / BPM
            dur_seconds = 0.2 * beat_dur  # short stabs
            time_seconds = actual_beat * beat_dur
            chord_sample = stab_program.generate_chord(
                notes, duration=dur_seconds, velocity=0.85
            )
            track.add(chord_sample, time_seconds)

    # Gritty effects chain
    track.add_effect(BitCrusher(bit_depth=10, sample_hold=2))
    track.add_effect(Delay(delay_time=0.15, feedback=0.25, mix=0.2))
    track.add_effect(HighPassFilter(cutoff=400.0))
    return track


# --- PAD: vocoder-like filtered pad ---
def make_pad_track(bars: int, *, sidechain: bool = False,
                   volume_curve=None) -> Track:
    """Atmospheric pad using distorted AKWF waveform, with sidechain."""
    track = Track(name="Pad", track_type=TrackType.PAD, volume=0.35)
    # Sustained chords: Em -> Am -> C -> D, 4 bars each
    pad_chords = [
        (['E3', 'G3', 'B3', 'D4'],  0),    # Em7
        (['A3', 'C4', 'E4', 'G4'],  4),    # Am7
        (['C3', 'E3', 'G3', 'B3'],  8),    # Cmaj7
        (['D3', 'F#3', 'A3', 'C4'], 12),   # D7
    ]

    for bar_offset in range(0, bars, 4):
        for notes, bar_in_cycle in pad_chords:
            actual_bar = bar_offset + bar_in_cycle
            if actual_bar >= bars:
                break
            beat_dur = 60.0 / BPM
            dur_seconds = 4 * BEATS_PER_BAR * beat_dur  # sustain across 4 bars
            time_seconds = actual_bar * BEATS_PER_BAR * beat_dur
            chord_sample = pad_program.generate_chord(
                notes, duration=dur_seconds, velocity=0.7
            )
            track.add(chord_sample, time_seconds)

    # Warm, filtered pad sound
    track.add_effect(LowPassFilter(cutoff=3000.0))
    track.add_effect(Chorus(rate=0.3, depth=0.4, mix=0.3))
    track.add_effect(Reverb(room_size=0.7, damping=0.5, mix=0.4))

    if sidechain:
        track.add_effect(sidechain_heavy)

    if volume_curve is not None:
        track.volume_automation = volume_curve

    return track


# --- ARP TRACK: tiled arp phrase ---
def make_arp_track(bars: int, *, effects=None) -> Track:
    """Tile the arp phrase across bars, with sidechain + optional FX."""
    track = Track(name="Arp", track_type=TrackType.LEAD, volume=0.45)
    for start_bar in range(0, bars, ARP_PHRASE_BARS):
        time = start_bar * BAR_SEC
        track.add(arp_sample, time, velocity=1.0)
    track.add_effect(sidechain_subtle)
    track.add_effect(Delay(delay_time=0.2, feedback=0.3, mix=0.15))
    if effects:
        for fx in effects:
            track.add_effect(fx)
    return track


# --- MELODIC SYNTH: bridge melody ---
def make_bridge_melody_track(bars: int) -> Track:
    """Melodic synth line for the bridge using oscchip keygroup."""
    track = Track(name="Melody", track_type=TrackType.LEAD, volume=0.5)
    # A simple, haunting melody in E minor over 8 bars
    # 4-bar melody, repeated once
    melody_notes = [
        # bar 1: rising figure
        ('E4', 0,    1.0),
        ('G4', 1,    0.5),
        ('A4', 1.5,  0.5),
        ('B4', 2,    1.5),
        ('A4', 3.5,  0.5),
        # bar 2: descending answer
        ('G4', 4,    1.0),
        ('F#4', 5,   0.5),
        ('E4', 5.5,  1.0),
        ('D4', 6.5,  1.5),
        # bar 3: variation
        ('E4', 8,    0.5),
        ('G4', 8.5,  0.5),
        ('B4', 9,    1.0),
        ('D5', 10,   1.5),
        ('B4', 11.5, 0.5),
        # bar 4: resolution
        ('A4', 12,   1.0),
        ('G4', 13,   1.0),
        ('E4', 14,   2.0),
    ]

    beat_dur = 60.0 / BPM
    for bar_offset_bars in range(0, bars, 4):
        for note, beat, dur in melody_notes:
            actual_beat = bar_offset_bars * BEATS_PER_BAR + beat
            dur_seconds = dur * beat_dur
            time_seconds = actual_beat * beat_dur
            note_sample = lead_program.generate(
                note, duration=dur_seconds, velocity=0.8
            )
            track.add(note_sample, time_seconds)

    track.add_effect(Delay(delay_time=0.3, feedback=0.35, mix=0.25))
    track.add_effect(Reverb(room_size=0.5, damping=0.4, mix=0.3))
    track.add_effect(sidechain_halftime)
    return track


# =====================================================================
#  10.  BUILD SECTIONS
# =====================================================================

print("Building arrangement sections...")

# --- INTRO: 8 bars -- filtered pad fading in + sparse euclidean hi-hats ---

intro_section = Section(name="Intro", bars=8)
intro_section.add_track(make_sparse_hihat_track(8))
intro_section.add_track(make_pad_track(8, volume_curve=intro_vol_curve))

# --- GROOVE: 16 bars -- full funk drums, acid bass, synth stabs ---

groove_section = Section(name="Groove", bars=16)
groove_section.add_track(make_funk_kick_track(16))
groove_section.add_track(make_funk_snare_track(16))
groove_section.add_track(make_funk_hihat_track(16))
groove_section.add_track(make_clap_track(16))
groove_section.add_track(make_funk_bass_track(16))
groove_section.add_track(make_stab_track(16))

# --- BREAKDOWN: 8 bars -- bass + filtered arp, filter sweep ---

breakdown_section = Section(name="Breakdown", bars=8)
breakdown_bass = make_funk_bass_track(8)
breakdown_bass.volume = 0.5  # pull back the bass
breakdown_section.add_track(breakdown_bass)
breakdown_section.add_track(make_arp_track(8, effects=[breakdown_filter]))

# --- DROP: 16 bars -- everything hits, sidechain pumping ---

drop_section = Section(name="Drop", bars=16)
drop_section.add_track(make_funk_kick_track(16))
drop_section.add_track(make_funk_snare_track(16))
drop_section.add_track(make_funk_hihat_track(16))
drop_section.add_track(make_clap_track(16))
drop_section.add_track(make_funk_bass_track(16))
drop_section.add_track(make_stab_track(16))
drop_section.add_track(make_pad_track(16, sidechain=True))
drop_section.add_track(make_arp_track(16))

# --- BRIDGE: 8 bars -- half-time feel, melodic synth line ---

bridge_section = Section(name="Bridge", bars=8)
# Half-time drums: kick on 1 and 3 only, snare on 3
bridge_kick_track = Track(name="Kick", track_type=TrackType.DRUMS)
for bar in range(8):
    bridge_kick_track.add(kick, (bar * BEATS_PER_BAR) * BEAT_SEC, velocity=0.9)
    bridge_kick_track.add(kick, (bar * BEATS_PER_BAR + 2) * BEAT_SEC, velocity=0.7)
bridge_section.add_track(bridge_kick_track)

bridge_snare_track = Track(name="Snare", track_type=TrackType.DRUMS)
for bar in range(8):
    bridge_snare_track.add(snare_alt, (bar * BEATS_PER_BAR + 2) * BEAT_SEC, velocity=0.85)
bridge_section.add_track(bridge_snare_track)

bridge_section.add_track(make_sparse_hihat_track(8))
bridge_section.add_track(make_funk_bass_track(8))
bridge_section.add_track(make_pad_track(8, sidechain=True))
bridge_section.add_track(make_bridge_melody_track(8))

# --- FINAL DROP: 16 bars -- biggest section, all elements + extra percussion ---

final_drop_section = Section(name="Final Drop", bars=16)
final_drop_section.add_track(make_funk_kick_track(16))
final_drop_section.add_track(make_funk_snare_track(16))
final_drop_section.add_track(make_funk_hihat_track(16))
final_drop_section.add_track(make_clap_track(16))
final_drop_section.add_track(make_percussion_track(16))   # extra percussion!
final_drop_section.add_track(make_funk_bass_track(16))
final_drop_section.add_track(make_stab_track(16))
final_drop_section.add_track(make_pad_track(16, sidechain=True))
final_drop_section.add_track(make_arp_track(16))

# --- OUTRO: 8 bars -- fade down, elements dropping out ---

outro_section = Section(name="Outro", bars=8)
# Sparse kick
outro_kick = Track(name="Kick", track_type=TrackType.DRUMS)
for bar in range(8):
    outro_kick.add(kick, (bar * BEATS_PER_BAR) * BEAT_SEC, velocity=0.7)
outro_kick.volume_automation = outro_vol_curve
outro_section.add_track(outro_kick)

outro_section.add_track(make_sparse_hihat_track(8))
outro_pad = make_pad_track(8)
outro_pad.volume_automation = outro_vol_curve
outro_section.add_track(outro_pad)

outro_arp = make_arp_track(8)
outro_arp.volume_automation = outro_vol_curve
outro_section.add_track(outro_arp)


# =====================================================================
#  11.  ARRANGE THE SONG
# =====================================================================

print("Arranging song structure...")

arrangement = Arrangement()
arrangement.intro(intro_section)
arrangement.verse(groove_section)
arrangement.breakdown(breakdown_section)
arrangement.drop(drop_section)
arrangement.bridge(bridge_section)
arrangement.drop(final_drop_section)
arrangement.outro(outro_section)

total_bars = arrangement.total_bars()
total_duration = total_bars * BAR_SEC
print(f"  Total: {total_bars} bars, {total_duration:.1f} seconds "
      f"({total_duration / 60:.1f} minutes)")


# =====================================================================
#  12.  BUILD AND EXPORT
# =====================================================================

print("Building song...")

song = (create_song("Neon Dragon Protocol")
    .tempo(BPM)
    .time_signature(4, 4)
    .sample_rate(SAMPLE_RATE)
    .arrange(arrangement)
    .master_effect(Compressor(threshold=-6.0, ratio=3.0))
    .master_limiter(threshold=0.92)
    .build())

output_path = SCRIPT_DIR / "neon_dragon_protocol.wav"
print(f"Exporting to: {output_path}")
song.export(output_path)
print("Done! Neon Dragon Protocol is ready.")
