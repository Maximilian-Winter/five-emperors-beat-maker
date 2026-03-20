#!/usr/bin/env python3
"""
Chronicle of the Nine Heavens - Complete OST
SNES-style game soundtrack using the Five Emperors Beat Maker

Track 2: Mountain Cultivation (Meditation Theme)
The player sits on a mountain, watching clouds, gathering qi...
"""

from beatmaker import *


def create_mountain_cultivation_theme():
    """
    Peaceful, contemplative, slightly repetitive (meditation loop).
    Simple melody with nature sounds.
    SNES-style: limited channels, clear melodic lines.
    """
    print("🏔️ Creating: Mountain Cultivation Theme")

    bpm = 72  # Slow, meditative
    beat_dur = 60 / bpm

    song = Song(name="Mountain Cultivation", bpm=bpm)

    # SNES had limited channels - keep it simple but effective

    # === MAIN MELODY: Simple pentatonic (peaceful) ===
    melody_track = Track(name="Meditation Melody", track_type=TrackType.LEAD, volume=0.6)

    # 16-bar loop that repeats
    # Pentatonic scale: C D E G A (no half-steps = no tension)
    meditation_melody = [
        ('C5', 0, 2), ('D5', 2, 1), ('E5', 3, 1),
        ('G5', 4, 3), ('E5', 7, 1),
        ('D5', 8, 2), ('C5', 10, 2),
        ('G4', 12, 4),  # Long, peaceful

        # Variation
        ('E5', 16, 2), ('G5', 18, 1), ('A5', 19, 1),
        ('G5', 20, 2), ('E5', 22, 2),
        ('D5', 24, 2), ('C5', 26, 2),
        ('C5', 28, 4),  # Resolution
    ]

    # SNES square wave lead (iconic 16-bit sound)
    for note, beat, dur in meditation_melody:
        freq = note_to_freq(note)
        # Square wave = classic SNES lead sound
        lead = LeadSynth.square_lead(freq, dur * beat_dur, pulse_width=0.25)
        melody_track.add(lead, beat * beat_dur)

    # Light chorus for width (SNES stereo!)
    melody_track.add_effect(Chorus(rate=0.3, depth=0.002, mix=0.15))
    melody_track.add_effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))

    song.add_track(melody_track)

    # === PAD: Sustained background (mountain atmosphere) ===
    pad = PadSynth.warm_pad(note_to_freq('C3'), duration=32 * beat_dur, num_voices=4)
    pad_track = Track(name="Mountain Pad", track_type=TrackType.PAD, volume=0.25)
    pad_track.add(Sample("pad", pad.audio), 0)
    pad_track.add_effect(LowPassFilter(cutoff=1500))
    song.add_track(pad_track)

    # === BASS: Simple root notes ===
    bass_track = Track(name="Bass", track_type=TrackType.BASS, volume=0.5)
    bass_pattern = [('C2', 0, 8), ('G2', 8, 8), ('C2', 16, 8), ('C2', 24, 8)]

    for note, beat, dur in bass_pattern:
        bass = BassSynth.sub_bass(note_to_freq(note), dur * beat_dur)
        bass_track.add(bass, beat * beat_dur)

    song.add_track(bass_track)

    # === BELL ACCENTS: Occasional chimes (wind chimes on mountain) ===
    bell_track = Track(name="Wind Chimes", track_type=TrackType.FX, volume=0.3)
    bell_times = [0, 8, 16, 24]
    bell_notes = ['C5', 'E5', 'G5', 'C6']

    for time, note in zip(bell_times, bell_notes):
        bell = PluckSynth.bell(note_to_freq(note), 2)
        bell_track.add(bell, time * beat_dur)

    bell_track.add_effect(Reverb(room_size=0.7, mix=0.4))
    song.add_track(bell_track)

    song.export("02_mountain_cultivation.wav")
    print("  ✓ Mountain Cultivation theme complete")
    return song


def create_demon_battle_theme():
    """
    SNES battle music: Fast, energetic, looping.
    The player is throwing qi balls at demons!
    """
    print("⚔️ Creating: First Demon Battle Theme")

    bpm = 140  # Action-packed!
    beat_dur = 60 / bpm

    song = Song(name="Demon Battle", bpm=bpm)

    # === DRUMS: Punchy SNES drums ===
    kick = DrumSynth.kick(pitch=50, punch=0.9, duration=0.3)
    snare = DrumSynth.snare(duration=0.2, noise_amount=0.6)
    hihat = DrumSynth.hihat(duration=0.06)

    seq = StepSequencer(bpm=bpm)

    # Classic SNES battle rhythm
    seq.add_pattern('kick', Pattern.from_string("x.......x.......x.......x......."), kick)
    seq.add_pattern('snare', Pattern.from_string("....x.......x.......x.......x..."), snare)
    seq.add_pattern('hihat', Pattern.from_string("..x...x...x...x...x...x...x...x."), hihat)

    drum_track = seq.render_to_track(bars=16, name="Battle Drums")
    drum_track.volume = 0.8
    drum_track.add_effect(Compressor(threshold=-6, ratio=4))
    song.add_track(drum_track)

    # === LEAD: Aggressive battle melody ===
    lead_track = Track(name="Battle Lead", track_type=TrackType.LEAD, volume=0.7)

    # Minor scale battle theme (A minor)
    battle_melody = [
        # Aggressive opening
        ('A4', 0, 0.5), ('A4', 0.5, 0.5), ('A4', 1, 0.5), ('C5', 1.5, 0.5),
        ('D5', 2, 1), ('E5', 3, 1),
        ('D5', 4, 0.5), ('C5', 4.5, 0.5), ('A4', 5, 1), ('G4', 6, 1),
        ('A4', 7, 1),

        # Second phrase
        ('C5', 8, 0.5), ('C5', 8.5, 0.5), ('D5', 9, 0.5), ('E5', 9.5, 0.5),
        ('F5', 10, 1), ('E5', 11, 1),
        ('D5', 12, 1), ('C5', 13, 1),
        ('A4', 14, 2),
    ]

    for note, beat, dur in battle_melody:
        freq = note_to_freq(note)
        # Saw wave for aggressive sound
        lead = LeadSynth.saw_lead(freq, dur * beat_dur, filter_env=True)
        lead_track.add(lead, beat * beat_dur)

    lead_track.add_effect(Delay(delay_time=0.1875, feedback=0.2, mix=0.2))
    song.add_track(lead_track)

    # === BASS: Driving bass line ===
    bass_track = Track(name="Battle Bass", track_type=TrackType.BASS, volume=0.75)

    # Sixteenth-note bass (constant energy)
    bass_pattern = [
                       ('A1', 0, 0.25), ('A1', 0.5, 0.25), ('A1', 1, 0.25), ('A1', 1.5, 0.25),
                       ('G1', 2, 0.25), ('G1', 2.5, 0.25), ('F1', 3, 0.25), ('E1', 3.5, 0.25),
                   ] * 4  # Repeat

    for note, beat, dur in bass_pattern:
        bass = BassSynth.acid_bass(note_to_freq(note), dur * beat_dur)
        bass_track.add(bass, beat * beat_dur)

    bass_track.add_effect(LowPassFilter(cutoff=300))
    song.add_track(bass_track)

    # === ARPEGGIO: Background energy ===
    arp = create_arpeggiator().tempo(bpm).up().sixteenth().gate(0.4).build()
    arp_events = arp.generate_from_chord('A2', ChordShape.MINOR, beats=64)

    arp_synth = ArpSynthesizer(waveform='square')
    arp_audio = arp_synth.render_events(arp_events)
    arp_audio = LowPassFilter(cutoff=2000).process(arp_audio)

    arp_track = Track(name="Energy Arp", track_type=TrackType.FX, volume=0.3)
    arp_track.add(Sample("arp", arp_audio), 0)
    song.add_track(arp_track)

    song.master_effects.append(Compressor(threshold=-6, ratio=3))
    song.export("03_demon_battle.wav")
    print("  ✓ Demon Battle theme complete")
    return song


def create_breakthrough_fanfare():
    """
    Short fanfare when player achieves a cultivation breakthrough.
    SNES victory jingle style!
    """
    print("✨ Creating: Breakthrough Fanfare")

    bpm = 120
    beat_dur = 60 / bpm

    song = Song(name="Breakthrough!", bpm=bpm)

    # === LEAD: Triumphant ascending melody ===
    fanfare_track = Track(name="Fanfare", track_type=TrackType.LEAD, volume=0.8)

    # Classic RPG victory progression
    fanfare = [
        ('C5', 0, 0.5), ('E5', 0.5, 0.5), ('G5', 1, 0.5),
        ('C6', 1.5, 1.5),  # Hold the high note
        ('G5', 3, 0.5), ('E5', 3.5, 0.5),
        ('C5', 4, 2),  # Resolution
    ]

    for note, beat, dur in fanfare:
        freq = note_to_freq(note)
        lead = LeadSynth.square_lead(freq, dur * beat_dur, pulse_width=0.5)
        fanfare_track.add(lead, beat * beat_dur)

    song.add_track(fanfare_track)

    # === HARMONY: Support notes ===
    harmony_track = Track(name="Harmony", track_type=TrackType.LEAD, volume=0.5)
    harmony = [
        ('E4', 0, 0.5), ('G4', 0.5, 0.5), ('C5', 1, 0.5),
        ('E5', 1.5, 1.5),
        ('C5', 3, 0.5), ('G4', 3.5, 0.5),
        ('E4', 4, 2),
    ]

    for note, beat, dur in harmony:
        freq = note_to_freq(note)
        lead = LeadSynth.saw_lead(freq, dur * beat_dur)
        harmony_track.add(lead, beat * beat_dur)

    song.add_track(harmony_track)

    # === DRUMS: Accent the fanfare ===
    kick = DrumSynth.kick(pitch=60, punch=0.8)
    cymbal = DrumSynth.hihat(duration=1.0, open_amount=1.0)

    drum_track = Track(name="Fanfare Drums", track_type=TrackType.DRUMS, volume=0.7)
    drum_track.add(kick, 0)
    drum_track.add(cymbal, 1.5 * beat_dur)

    song.add_track(drum_track)

    song.export("04_breakthrough_fanfare.wav")
    print("  ✓ Breakthrough Fanfare complete")
    return song


# Create the expanded OST
if __name__ == "__main__":
    print("=" * 70)
    print("CHRONICLE OF THE NINE HEAVENS - Extended OST")
    print("SNES-Style Game Soundtrack by the Five Emperors")
    print("=" * 70)

    create_mountain_cultivation_theme()
    create_demon_battle_theme()
    create_breakthrough_fanfare()

    print("\n" + "=" * 70)
    print("🎮 Ready to cultivate the Dao and throw energy balls! 🎮")
    print("=" * 70)