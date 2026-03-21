"""
+======================================================================+
|                        SOLAR FLARE                                    |
|                    Deep House -- 124 BPM                              |
|                                                                       |
|   A deep house composition built on TR-808 samples,                   |
|   arpeggiated chords, sidechain pumping, and filter automation.       |
|                                                                       |
|   Key: A minor                                                        |
|   Progression: i - VI - III - VII (Am - F - C - G)                    |
|   Tempo: 124 BPM, 4/4                                                |
|                                                                       |
|   Arrangement:                                                        |
|     Intro      (8 bars)  -- Kick + hi-hats, stripped back             |
|     Verse     (16 bars)  -- Add bass + arpeggio                       |
|     Breakdown  (8 bars)  -- Drop the kick, filter sweep on arp        |
|     Drop      (16 bars)  -- Full energy, add claps                    |
|     Outro      (8 bars)  -- Strip down, fade                          |
|                                                                       |
|   Features demonstrated:                                              |
|     - SampleLibrary with loaded TR-808 .WAV files                     |
|     - SidechainPresets (classic house pumping)                         |
|     - Arpeggiator with ChordShape progression                        |
|     - ArpSynthesizer for rendering arp events to audio                |
|     - AutomationCurve for filter sweep                                |
|     - AutomatedFilter for time-varying cutoff                         |
|     - Section / Arrangement for song structure                        |
|     - Master chain: Compressor + Limiter                              |
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
    load_audio, SampleLibrary,
    # Synthesis
    DrumSynth, ADSREnvelope,
    # Arpeggiator
    Arpeggiator, ArpDirection, ArpMode, ArpSynthesizer,
    create_arpeggiator, ChordShape,
    # Effects
    Compressor, Limiter, LowPassFilter, Reverb, Delay,
    SidechainPresets, SidechainEnvelope, create_sidechain,
    # Automation
    AutomationCurve, AutomatedFilter, CurveType,
    # Arrangement
    Section, Arrangement,
)


# =====================================================================
#  CONFIGURATION
# =====================================================================

BPM = 124
SAMPLE_RATE = 44100
BEATS_PER_BAR = 4
BEAT_SEC = 60.0 / BPM                        # duration of one beat
BAR_SEC = BEAT_SEC * BEATS_PER_BAR            # duration of one bar

# Paths to TR-808 samples
TR808_ROOT = Path(__file__).resolve().parent.parent.parent / (
    "downloaded_samples_etc/tidal-drum-machines/machines/RolandTR808"
)


# =====================================================================
#  1.  LOAD TR-808 SAMPLES
# =====================================================================

def load_808_sample(subdir: str, filename: str, name: str) -> Sample:
    """Load a single TR-808 .WAV file into a Sample object."""
    filepath = TR808_ROOT / subdir / filename
    audio = load_audio(filepath)
    return Sample(name=name, audio=audio, tags=["808", name])


print("Loading TR-808 samples...")

kick    = load_808_sample("rolandtr808-bd", "BD7510.WAV",  "kick")
snare   = load_808_sample("rolandtr808-sd", "SD0010.WAV",  "snare")
hihat   = load_808_sample("rolandtr808-hh", "CH.WAV",      "hihat")
openhat = load_808_sample("rolandtr808-oh", "OH10.WAV",    "openhat")
clap    = load_808_sample("rolandtr808-perc", "CL.WAV",    "clap")
rimshot = load_808_sample("rolandtr808-rim", "RS.WAV",     "rimshot")


# =====================================================================
#  2.  BUILD THE ARPEGGIO -- i-VI-III-VII in A minor
# =====================================================================
#
#   i   = A minor  (A3)   intervals [0, 3, 7]
#   VI  = F major  (F3)   intervals [0, 4, 7]
#   III = C major  (C4)   intervals [0, 4, 7]
#   VII = G major  (G3)   intervals [0, 4, 7]

print("Building arpeggio...")

arp = (create_arpeggiator()
       .tempo(BPM)
       .up_down()
       .eighth()               # 8th-note rate
       .gate(0.75)
       .octaves(2)
       .swing(0.15)
       .velocity_pattern([1.0, 0.55, 0.7, 0.55, 0.85, 0.55, 0.7, 0.55])
       .build())

progression = [
    ("A3", ChordShape.MINOR),   # i   - A minor
    ("F3", ChordShape.MAJOR),   # VI  - F major
    ("C4", ChordShape.MAJOR),   # III - C major
    ("G3", ChordShape.MAJOR),   # VII - G major
]

# Each chord lasts one bar = 4 beats
BEATS_PER_CHORD = BEATS_PER_BAR
arp_events = arp.generate_from_progression(progression, BEATS_PER_CHORD)

# Render arp events to audio using ArpSynthesizer (saw wave, lush envelope)
arp_synth = ArpSynthesizer(
    waveform="saw",
    envelope=ADSREnvelope(attack=0.02, decay=0.15, sustain=0.6, release=0.2),
    sample_rate=SAMPLE_RATE,
)
arp_audio = arp_synth.render_events(arp_events)

# Wrap as a Sample so we can place it on tracks
arp_sample = Sample(name="arp_phrase", audio=arp_audio, tags=["arp", "synth"])

# The arp phrase covers 4 bars (one pass through the progression).
# We will tile it across sections as needed.
ARP_PHRASE_BARS = len(progression)  # 4 bars


# =====================================================================
#  3.  SIDECHAIN PUMP (classic house, keyed to 124 BPM)
# =====================================================================

sidechain_pump = SidechainPresets.classic_house(bpm=BPM)


# =====================================================================
#  4.  FILTER AUTOMATION -- sweep for the breakdown
# =====================================================================
#
#  During the 8-bar breakdown we sweep the arp's lowpass cutoff
#  from 400 Hz up to 8000 Hz (exponential), creating a rising tension.

breakdown_bars  = 8
breakdown_beats = breakdown_bars * BEATS_PER_BAR  # 32 beats

filter_sweep = AutomationCurve.filter_sweep(
    start_beat=0,
    end_beat=breakdown_beats,
    start_freq=400.0,
    end_freq=8000.0,
)

breakdown_filter = AutomatedFilter(cutoff=400.0, resonance=1.8)
breakdown_filter.automate("cutoff", filter_sweep)
breakdown_filter.set_context(bpm=BPM, start_beat=0.0)


# =====================================================================
#  5.  HELPER: build drum/bass/arp tracks for a given bar count
# =====================================================================

def make_kick_track(bars: int, *, four_on_floor: bool = True) -> Track:
    """Four-on-the-floor kick pattern for *bars* bars."""
    track = Track(name="Kick", track_type=TrackType.DRUMS)
    for bar in range(bars):
        for beat in range(BEATS_PER_BAR):
            time = (bar * BEATS_PER_BAR + beat) * BEAT_SEC
            track.add(kick, time, velocity=1.0)
    return track


def make_hihat_track(bars: int) -> Track:
    """Off-beat 8th-note closed hats + open hat every 4th bar."""
    track = Track(name="HiHat", track_type=TrackType.DRUMS)
    for bar in range(bars):
        for step in range(8):  # 8 x 8th-notes per bar
            beat_pos = step * 0.5
            time = (bar * BEATS_PER_BAR + beat_pos) * BEAT_SEC
            # Open hat on the "and" of beat 4, every 4th bar
            if bar % 4 == 3 and step == 7:
                track.add(openhat, time, velocity=0.65)
            else:
                vel = 0.5 if step % 2 == 0 else 0.7  # accented off-beats
                track.add(hihat, time, velocity=vel)
    return track


def make_clap_track(bars: int) -> Track:
    """Claps on beats 2 and 4 (backbeat)."""
    track = Track(name="Claps", track_type=TrackType.DRUMS)
    for bar in range(bars):
        for beat in [1, 3]:
            time = (bar * BEATS_PER_BAR + beat) * BEAT_SEC
            track.add(clap, time, velocity=0.85)
    return track


def make_bass_track(bars: int) -> Track:
    """Deep sub-bass following the chord roots, one note per bar."""
    from beatmaker import BassSynth, note_to_freq
    track = Track(name="Bass", track_type=TrackType.BASS, volume=0.8)
    roots = ["A1", "F1", "C2", "G1"]  # match the progression
    for bar in range(bars):
        root = roots[bar % len(roots)]
        freq = note_to_freq(root)
        duration_sec = BAR_SEC * 0.9
        bass_sample = BassSynth.sub_bass(freq, duration_sec)
        time = bar * BAR_SEC
        track.add(bass_sample, time, velocity=0.9)
    return track


def make_arp_track(bars: int, *, effects: list = None) -> Track:
    """Tile the arp phrase across *bars* bars, with sidechain + optional FX."""
    track = Track(name="Arp", track_type=TrackType.LEAD, volume=0.55)
    phrase_duration_bars = ARP_PHRASE_BARS
    for start_bar in range(0, bars, phrase_duration_bars):
        time = start_bar * BAR_SEC
        track.add(arp_sample, time, velocity=1.0)
    # Always apply sidechain pumping
    track.add_effect(sidechain_pump)
    # Additional per-section effects
    if effects:
        for fx in effects:
            track.add_effect(fx)
    return track


# =====================================================================
#  6.  BUILD SECTIONS using the Arrangement system
# =====================================================================

print("Building arrangement sections...")

# --- Intro: 8 bars -- kick + hi-hats only ----------------------------

intro_section = Section(name="Intro", bars=8)
intro_section.add_track(make_kick_track(8))
intro_section.add_track(make_hihat_track(8))

# --- Verse: 16 bars -- add bass + arp --------------------------------

verse_section = Section(name="Verse", bars=16)
verse_section.add_track(make_kick_track(16))
verse_section.add_track(make_hihat_track(16))
verse_section.add_track(make_bass_track(16))
verse_section.add_track(make_arp_track(16))

# --- Breakdown: 8 bars -- remove kick, filter sweep on arp -----------

breakdown_section = Section(name="Breakdown", bars=8)
# No kick here -- just hats, bass (quieter), and filtered arp
breakdown_hats = make_hihat_track(8)
breakdown_hats.volume = 0.4  # pull back the hats
breakdown_section.add_track(breakdown_hats)

breakdown_bass = make_bass_track(8)
breakdown_bass.volume = 0.5  # quieter bass
breakdown_section.add_track(breakdown_bass)

breakdown_arp = make_arp_track(8, effects=[breakdown_filter])
breakdown_arp.volume = 0.65  # let the filter sweep shine
breakdown_section.add_track(breakdown_arp)

# --- Drop: 16 bars -- everything + claps, full energy ----------------

drop_section = Section(name="Drop", bars=16)
drop_section.add_track(make_kick_track(16))
drop_section.add_track(make_hihat_track(16))
drop_section.add_track(make_clap_track(16))
drop_section.add_track(make_bass_track(16))
drop_section.add_track(make_arp_track(16))

# --- Outro: 8 bars -- strip down, just kick + hats + quiet arp ------

outro_section = Section(name="Outro", bars=8)
outro_section.add_track(make_kick_track(8))

outro_hats = make_hihat_track(8)
outro_hats.volume = 0.5
outro_section.add_track(outro_hats)

outro_arp = make_arp_track(8)
outro_arp.volume = 0.3  # fading presence
outro_section.add_track(outro_arp)


# =====================================================================
#  7.  ARRANGE the sections into a full song
# =====================================================================

arrangement = (Arrangement()
    .intro(intro_section)           #  8 bars
    .verse(verse_section)           # 16 bars
    .breakdown(breakdown_section)   #  8 bars
    .drop(drop_section)             # 16 bars
    .outro(outro_section)           #  8 bars
)

print(f"Arrangement: {arrangement}")
print(f"Total bars: {arrangement.total_bars()}")
print(f"Total duration: {arrangement.total_bars() * BAR_SEC:.1f}s "
      f"({arrangement.total_bars() * BAR_SEC / 60:.1f} min)")


# =====================================================================
#  8.  ASSEMBLE with SongBuilder -- master chain + export
# =====================================================================

print("Rendering song...")

song = (create_song("Solar Flare")
    .tempo(BPM)
    .time_signature(4, 4)
    .sample_rate(SAMPLE_RATE)
    .arrange(arrangement)
    .master_compressor(threshold=-8.0, ratio=3.0)
    .master_limiter(threshold=0.95)
    .build()
)

# Export
output_dir = Path(__file__).resolve().parent
output_path = output_dir / "solar_flare.wav"
song.export(output_path)

print(f"Exported to: {output_path}")
print("Done.")
