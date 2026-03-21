#!/usr/bin/env python3
"""
Keygroup Demo — "Jade Echoes"

Demonstrates the KeygroupProgram and KeygroupTrackBuilder by
creating a short piece where a single pad sample is mapped across
the keyboard and played as melody, chords, and arpeggios.

This also shows multi-sample keygroups (a piano sampled at
multiple octaves) and integration with Phrase/Melody objects.
"""

from beatmaker import (
    create_song, Song, Sample,
    PadSynth, PluckSynth, LeadSynth, DrumSynth,
    note_to_freq,
    Reverb, Delay, Chorus, Compressor, LowPassFilter,
    ADSREnvelope,
    create_arpeggiator, ChordShape,
)
from beatmaker.melody import Phrase
from beatmaker.keygroup import KeygroupProgram, KeygroupTrackBuilder


# ═══════════════════════════════════════════════════════════════════
#  1. Create Keygroup Instruments
# ═══════════════════════════════════════════════════════════════════

# --- Single-sample keygroup: warm pad mapped chromatically ---
# One sample at C3, the engine resamples it for all other notes
pad_audio = PadSynth.warm_pad(note_to_freq('C3'), duration=3.0, num_voices=4)
pad_keys = KeygroupProgram.from_sample(
    pad_audio,
    root_note='C3',
    name="warm_pad",
    envelope=ADSREnvelope(attack=0.05, decay=0.3, sustain=0.6, release=0.5),
)

# --- Single-sample keygroup: bell/pluck for arpeggios ---
bell_audio = PluckSynth.bell(note_to_freq('E4'), duration=2.0)
bell_keys = KeygroupProgram.from_sample(
    bell_audio,
    root_note='E4',
    name="bell",
    envelope=ADSREnvelope(attack=0.001, decay=0.2, sustain=0.3, release=0.4),
)

# --- Multi-sample keygroup: lead sampled at 3 octaves ---
# This reduces pitch-shifting artifacts by keeping each zone
# within ±6 semitones of its root
lead_samples = [
    (LeadSynth.saw_lead(note_to_freq('C3'), duration=1.0), 'C3'),
    (LeadSynth.saw_lead(note_to_freq('C4'), duration=1.0), 'C4'),
    (LeadSynth.saw_lead(note_to_freq('C5'), duration=1.0), 'C5'),
]
lead_keys = KeygroupProgram.from_multi_sample(
    lead_samples,
    name="multi_lead",
    envelope=ADSREnvelope(attack=0.01, decay=0.1, sustain=0.7, release=0.2),
)


# ═══════════════════════════════════════════════════════════════════
#  2. Define Melodic Material (reusing the Phrase system)
# ═══════════════════════════════════════════════════════════════════

# Pentatonic melody — will be rendered through the keygroup
jade_melody = Phrase.from_string(
    "C4:1 Eb4:0.5 F4:0.5 G4:1 Eb4:0.5 C4:0.5 "
    "Bb3:1 C4:1 Eb4:2",
    name="jade_melody"
)

jade_answer = Phrase.from_string(
    "G4:1 F4:0.5 Eb4:0.5 C4:1 Eb4:0.5 F4:0.5 "
    "G4:1 Eb4:1 C4:2",
    name="jade_answer"
)


# ═══════════════════════════════════════════════════════════════════
#  3. Build the Song
# ═══════════════════════════════════════════════════════════════════

song = (create_song("Jade Echoes")
    .tempo(88)
    .bars(8)

    # Drums — simple groove
    .add_drums(lambda d: d
        .kick(beats=[0, 2.5], velocity=0.8)
        .snare(beats=[1, 3], velocity=0.6)
        .hihat(beats=[i * 0.5 for i in range(8)], velocity=0.4)
        .volume(0.6)
        .effect(Compressor(threshold=-8, ratio=3))
    )

    # Bass — sub bass through a keygroup (one sample, played low)
    .add_keygroup("Sub Bass", pad_keys, lambda k: k
        .line([
            ('C2', 0, 2), ('Eb2', 2, 2),
            ('F2', 4, 2), ('G2', 6, 2),
            ('C2', 8, 2), ('Eb2', 10, 2),
            ('Ab2', 12, 2), ('G2', 14, 2),
            ('C2', 16, 2), ('Eb2', 18, 2),
            ('F2', 20, 2), ('G2', 22, 2),
            ('Ab2', 24, 2), ('Bb2', 26, 2),
            ('G2', 28, 2), ('C2', 30, 2),
        ])
        .volume(0.7)
        .effect(LowPassFilter(cutoff=300))
    )

    # Lead melody — multi-sample keygroup with phrases
    .add_keygroup("Lead", lead_keys, lambda k: k
        .phrase(jade_melody, start_beat=0)
        .phrase(jade_answer, start_beat=8)
        .phrase(jade_melody.transpose(5), start_beat=16)
        .phrase(jade_answer, start_beat=24)
        .volume(0.55)
        .effect(Reverb(room_size=0.5, mix=0.3))
        .effect(Delay(delay_time=0.341, feedback=0.25, mix=0.2))
        .humanize(timing=0.008, velocity=0.06)
    )

    # Pad chords — single-sample keygroup playing chords
    .add_keygroup("Pad Chords", pad_keys, lambda k: k
        .chord(['C3', 'Eb3', 'G3'], beat=0, duration=4)
        .chord(['Ab3', 'C4', 'Eb4'], beat=4, duration=4)
        .chord(['F3', 'Ab3', 'C4'], beat=8, duration=4)
        .chord(['G3', 'Bb3', 'D4'], beat=12, duration=4)
        .chord(['C3', 'Eb3', 'G3'], beat=16, duration=4)
        .chord(['Ab3', 'C4', 'Eb4'], beat=20, duration=4)
        .chord(['Bb3', 'D4', 'F4'], beat=24, duration=4)
        .chord(['C3', 'Eb3', 'G3', 'Bb3'], beat=28, duration=4)
        .volume(0.25)
        .effect(Chorus(rate=0.4, depth=0.003, mix=0.2))
        .effect(Reverb(room_size=0.7, mix=0.5))
    )

    # Bell arpeggios — keygroup with arp events
    .add_keygroup("Bell Arp", bell_keys, lambda k: k
        .note('C5', beat=0, duration=0.5)
        .note('Eb5', beat=0.5, duration=0.5)
        .note('G5', beat=1, duration=0.5)
        .note('C6', beat=1.5, duration=0.5)
        .note('G5', beat=2, duration=0.5)
        .note('Eb5', beat=2.5, duration=0.5)
        .note('C5', beat=3, duration=0.5)
        .note('G4', beat=3.5, duration=0.5)
        # Repeat with variation
        .note('Ab4', beat=4, duration=0.5)
        .note('C5', beat=4.5, duration=0.5)
        .note('Eb5', beat=5, duration=0.5)
        .note('Ab5', beat=5.5, duration=0.5)
        .note('Eb5', beat=6, duration=0.5)
        .note('C5', beat=6.5, duration=0.5)
        .note('Ab4', beat=7, duration=0.5)
        .note('G4', beat=7.5, duration=1.0)
        .volume(0.3)
        .effect(Reverb(room_size=0.6, mix=0.4))
        .effect(Delay(delay_time=0.682, feedback=0.35, mix=0.3))
    )

    .master_effect(Compressor(threshold=-6, ratio=3))
    .master_limiter(0.95)
    .build()
)


if __name__ == "__main__":
    print("=" * 60)
    print("  Jade Echoes — Keygroup Demo")
    print("  Demonstrating MPC-style sample mapping")
    print("=" * 60)
    print()
    print("  Instruments:")
    print(f"    Pad Keygroup:  warm_pad @ C3 (single sample)")
    print(f"    Bell Keygroup: bell @ E4 (single sample)")
    print(f"    Lead Keygroup: saw_lead @ C3/C4/C5 (multi-sample)")
    print()

    audio = song.render()
    print(f"  Duration: {audio.duration:.1f}s")
    print(f"  Peak:     {max(abs(audio.samples.min()), abs(audio.samples.max())):.3f}")

    song.export("jade_echoes.wav")
    print("  Exported: jade_echoes.wav")
