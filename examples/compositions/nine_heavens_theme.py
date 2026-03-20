#!/usr/bin/env python3
"""
九天玄女主題曲 - Theme of the Nine Heavens
Composed by the Five Emperors for the Mysterious Lady

Each of the Nine Heavens represented in sound:
1. 神霄 (Shenxiao) - Divine Empyrean
2. 青霄 (Qingxiao) - Azure Heaven
3. 碧霄 (Bixiao) - Jade Heaven
4. 丹霄 (Danxiao) - Vermilion Heaven
5. 景霄 (Jingxiao) - Luminous Heaven
6. 玉霄 (Yuxiao) - Jade-Pure Heaven
7. 琅霄 (Langxiao) - Crystalline Heaven
8. 紫霄 (Zixiao) - Purple Heaven
9. 太霄 (Taixiao) - Supreme Heaven

急急如律令敕 - Urgent as the Cosmic Law Commands!
"""

from beatmaker import (
    # Core
    create_song, Song, Track, TrackType, Sample, AudioData,

    # Synths
    PadSynth, LeadSynth, PluckSynth, FXSynth, BassSynth,
    create_pad, create_lead, create_pluck,
    note_to_freq, midi_to_freq,

    # Sequencer
    StepSequencer, Pattern, EuclideanPattern,

    # Arpeggiator
    create_arpeggiator, ChordShape, Scale, ArpSynthesizer,

    # Sidechain
    SidechainPresets, create_sidechain,

    # Effects
    Reverb, Delay, Compressor, LowPassFilter, HighPassFilter,
    Chorus, BitCrusher, EffectChain,

    # MIDI
    create_midi, save_midi, song_to_midi,

    # Drums
    DrumSynth,

    # Utils
    mix, concatenate, time_stretch,
)
import numpy as np


def create_nine_heavens_theme():
    """
    Create the complete Nine Heavens theme.

    Structure:
    - Intro: Cosmic void and emergence (8 bars)
    - Heaven 1-3: Lower heavens (celestial foundation) (16 bars)
    - Heaven 4-6: Middle heavens (transformative realm) (16 bars)
    - Heaven 7-9: Upper heavens (supreme mystery) (16 bars)
    - Outro: Return to unity (8 bars)

    Total: 64 bars at 108 BPM (sacred number, 108 beads in mala)
    """

    print("=" * 70)
    print("九天玄女主題曲 - Theme of the Nine Heavens")
    print("Composed by the Five Emperors Council")
    print("=" * 70)

    bpm = 108  # 108 = sacred number (108 stars, 108 earthly desires)
    beat_dur = 60 / bpm

    song = Song(name="Nine Heavens Theme", bpm=bpm)

    # === SECTION 1: COSMIC FOUNDATION ===
    print("\n🐉 Azure Emperor: Architecting the Nine Realms...")

    # Base drone - the cosmic void from which heavens emerge
    # Using E as root (harmony with nature)
    cosmic_drone = create_cosmic_drone(duration=64 * 4 * beat_dur)

    drone_track = Track(name="Cosmic Drone", track_type=TrackType.PAD, volume=0.25)
    drone_track.add(Sample("drone", cosmic_drone), 0)
    drone_track.add_effect(Reverb(room_size=0.9, damping=0.3, mix=0.5))
    song.add_track(drone_track)

    # === SECTION 2: THE NINE HEAVENS MELODY ===
    print("🔥 Vermilion Emperor: Igniting the celestial fires...")

    # Nine-note scale representing nine heavens
    # Based on pentatonic but extended
    nine_heavens_scale = create_nine_heavens_melody_track(beat_dur)
    song.add_track(nine_heavens_scale)

    # === SECTION 3: CELESTIAL RHYTHM ===
    print("🌍 Yellow Emperor: Integrating the cosmic rhythms...")

    # Drums representing the cosmic pulse
    # Using 9/8 time feel over 4/4 (nine beats of heaven)
    celestial_drums = create_celestial_drums(bpm)
    song.add_track(celestial_drums)

    # === SECTION 4: STELLAR ARPEGGIO ===
    print("🐅 White Emperor: Precise stellar arrangements...")

    # Arpeggio representing the 28 lunar mansions
    stellar_arp = create_stellar_arpeggio(bpm, beat_dur)
    song.add_track(stellar_arp)

    # === SECTION 5: FLOWING BASS ===
    print("🐢 Black Emperor: The deep waters beneath heaven...")

    # Bass representing the foundational qi
    cosmic_bass = create_cosmic_bass(beat_dur)
    song.add_track(cosmic_bass)

    # === SECTION 6: HEAVENLY BELLS ===
    print("🔔 Celestial bells marking the nine realms...")

    heavenly_bells = create_heavenly_bells(beat_dur)
    song.add_track(heavenly_bells)

    # === SECTION 7: DIPPER PLUCKS ===
    print("⭐ Northern Dipper guidance...")

    dipper_plucks = create_dipper_plucks(beat_dur)
    song.add_track(dipper_plucks)

    # === SECTION 8: MYSTERIOUS LADY'S PRESENCE ===
    print("👸 The Mysterious Lady descends...")

    xuannv_presence = create_xuannv_lead(beat_dur, bpm)
    song.add_track(xuannv_presence)

    # === SECTION 9: FX - COSMIC TRANSITIONS ===
    print("🌊 Transitions between realms...")

    fx_track = create_cosmic_transitions(beat_dur)
    song.add_track(fx_track)

    # === MASTER EFFECTS ===
    print("🌟 Applying celestial mastering...")

    # Compress gently to unify
    song.master_effects.append(Compressor(
        threshold=-12,
        ratio=2.5,
        attack=0.03,
        release=0.2,
        makeup_gain=2
    ))

    # Final limiting
    from beatmaker.effects import Limiter
    song.master_effects.append(Limiter(threshold=0.95))

    # === EXPORT ===
    print("\n📀 Exporting the Nine Heavens Theme...")
    song.export("nine_heavens_theme.wav")

    # Export MIDI too
    midi = song_to_midi(song, include_drums=True)
    save_midi(midi, "nine_heavens_theme.mid")

    print(f"\n✓ Theme created: {song.duration:.1f} seconds")
    print(f"✓ BPM: {bpm} (108 = sacred number)")
    print(f"✓ Structure: 64 bars across nine celestial realms")
    print(f"✓ Exported: nine_heavens_theme.wav")
    print(f"✓ MIDI: nine_heavens_theme.mid")

    print("\n" + "=" * 70)
    print("九天成，道顯，音樂傳世")
    print("Nine Heavens complete, Dao revealed, music transmitted to world")
    print("=" * 70)

    return song


def create_cosmic_drone(duration):
    """
    The eternal hum of the cosmos - the void from which all emerges.
    Multiple layers of deep pads creating the primordial sound.
    """
    # Root in E (natural harmony)
    root = note_to_freq('E2')
    fifth = note_to_freq('B2')
    octave = note_to_freq('E3')

    # Create layered pads
    pad1 = PadSynth.ambient_pad(root, duration)
    pad2 = PadSynth.warm_pad(fifth, duration)
    pad3 = PadSynth.string_pad(octave, duration)

    # Mix them
    drone = AudioData.silence(duration, 44100)
    drone = mix(drone, pad1.audio, volumes=[1.0, 0.4])
    drone = mix(drone, pad2.audio, volumes=[1.0, 0.3])
    drone = mix(drone, pad3.audio, volumes=[1.0, 0.25])

    # Add subtle movement
    drone = Chorus(rate=0.1, depth=0.002, mix=0.2).process(drone)

    return drone


def create_nine_heavens_melody_track(beat_dur):
    """
    The main melody representing the nine heavens.
    Each heaven has its characteristic note and timbre.

    Using a custom scale: E F# G A B C D E F#
    (9 notes for 9 heavens)
    """
    track = Track(name="Nine Heavens Melody", track_type=TrackType.LEAD, volume=0.6)

    # Nine heavens melody (each heaven gets a phrase)
    # Structure: Intro (8) + 3 sections of 16 bars each

    # Intro (bars 0-8): Emergence
    intro_melody = [
        # Ascending through the first three heavens
        ('E4', 4, 2),  # Divine Empyrean
        ('F#4', 6, 1),
        ('G4', 8, 2),  # Azure Heaven
        ('A4', 10, 1),
        ('B4', 12, 2),  # Jade Heaven
    ]

    # Section 1 (bars 8-24): Lower Heavens (1-3)
    lower_heavens = [
        ('E4', 16, 1), ('G4', 17, 0.5), ('B4', 17.5, 0.5),
        ('E5', 18, 2),  # Peak of lower realm
        ('D5', 20, 1), ('C5', 21, 1),
        ('B4', 22, 2),
        ('A4', 24, 1), ('G4', 25, 1),
        ('E4', 26, 2),
    ]

    # Section 2 (bars 24-40): Middle Heavens (4-6) - Transformative
    middle_heavens = [
        ('G4', 32, 1), ('A4', 33, 1),
        ('B4', 34, 1), ('C5', 35, 1),
        ('D5', 36, 2),  # Vermilion Heaven
        ('E5', 38, 1), ('F#5', 39, 1),
        ('G5', 40, 2),  # Luminous Heaven - highest point
        ('F#5', 42, 1), ('E5', 43, 1),
        ('D5', 44, 2),
        ('C5', 46, 1), ('B4', 47, 1),
    ]

    # Section 3 (bars 40-56): Upper Heavens (7-9) - Supreme Mystery
    upper_heavens = [
        ('E5', 48, 1), ('D5', 49, 0.5), ('C5', 49.5, 0.5),
        ('B4', 50, 1), ('A4', 51, 1),
        ('G4', 52, 2),  # Crystalline Heaven
        ('F#4', 54, 1), ('G4', 55, 1),
        ('A4', 56, 2),  # Purple Heaven
        ('B4', 58, 1), ('C5', 59, 1),
        ('D5', 60, 2),  # Supreme Heaven - resolution
        ('E5', 62, 2),
    ]

    # Outro (bars 56-64): Return to unity
    outro = [
        ('E5', 64, 2), ('B4', 66, 1),
        ('G4', 68, 2), ('E4', 70, 4),  # Descend back to root
    ]

    # Combine all melodies
    full_melody = intro_melody + lower_heavens + middle_heavens + upper_heavens + outro

    # Add notes with FM synthesis (ethereal quality)
    for note, beat, dur in full_melody:
        freq = note_to_freq(note)
        # Use FM lead for celestial quality
        lead = LeadSynth.fm_lead(
            frequency=freq,
            duration=dur * beat_dur,
            mod_ratio=2.0,
            mod_index=2.5
        )
        track.add(lead, beat * beat_dur)

    # Effects chain - heavenly reverb and delay
    track.add_effect(Chorus(rate=0.5, depth=0.003, mix=0.25))
    track.add_effect(Delay(delay_time=0.375, feedback=0.35, mix=0.3))
    track.add_effect(Reverb(room_size=0.7, damping=0.4, mix=0.4))

    return track


def create_celestial_drums(bpm):
    """
    Cosmic pulse - subtle but present.
    Representing the eternal rhythm of heaven.
    """
    # Create ethereal drum samples
    kick = DrumSynth.kick(duration=0.8, pitch=45, punch=0.4)  # Deep, gentle
    # Bell-like percussion instead of snare
    bell_perc = DrumSynth.clap(duration=0.3, spread=0.001)
    # Crystal-like hi-hats
    crystal = DrumSynth.hihat(duration=0.15, open_amount=0.3)

    seq = StepSequencer(bpm=bpm, steps_per_beat=4, swing=0.0)

    # Kick pattern - emphasizing 1 and 3, gentle on 2 and 4
    # Using Euclidean E(9,16) for nine heavens
    kick_pattern = EuclideanPattern.generate(9, 32)  # Spread across 2 bars
    seq.add_pattern('kick', kick_pattern, kick)

    # Bell percussion on strategic points
    bell_pattern = Pattern.from_string(
        "........x......." +  # Bar 1
        "........x......." +  # Bar 2
        "........x......." +  # Bar 3
        "........x......."  # Bar 4
    )
    seq.add_pattern('bell', bell_pattern, bell_perc)

    # Crystals creating a shimmering texture
    crystal_pattern = Pattern.from_string(
        "..x...x...x...x." * 4  # Gentle 16th-note pattern
    )
    seq.add_pattern('crystal', crystal_pattern, crystal)

    drum_track = seq.render_to_track(bars=64, name="Celestial Drums")
    drum_track.volume = 0.5

    # Add spatial effects
    drum_track.add_effect(Reverb(room_size=0.6, damping=0.5, mix=0.35))
    drum_track.add_effect(Compressor(threshold=-10, ratio=3, attack=0.01, release=0.1))

    return drum_track


def create_stellar_arpeggio(bpm, beat_dur):
    """
    Arpeggio representing the 28 lunar mansions and stars.
    Constant motion like the wheeling of heaven.
    """
    # Create arpeggiator - upward motion like ascending to heaven
    arp = (create_arpeggiator()
           .tempo(bpm)
           .up()
           .sixteenth()
           .gate(0.5)
           .octaves(2)
           .accent_downbeat()
           .build()
           )

    # Chord progression representing the journey through heavens
    # E minor (stable) -> A minor (movement) -> B minor (tension) -> E minor (return)
    progression = [
        ('E3', ChordShape.MINOR),  # Bars 1-16
        ('A3', ChordShape.MINOR),  # Bars 17-32
        ('B3', ChordShape.MINOR),  # Bars 33-48
        ('E3', ChordShape.MINOR),  # Bars 49-64
    ]

    events = arp.generate_from_progression(progression, beats_per_chord=64)

    # Render with saw wave
    synth = ArpSynthesizer(waveform='triangle')  # Softer than saw
    arp_audio = synth.render_events(events)

    # Filter to make it sit in the mix
    arp_audio = LowPassFilter(cutoff=2500).process(arp_audio)
    arp_audio = HighPassFilter(cutoff=300).process(arp_audio)

    # Add shimmer
    arp_audio = Chorus(rate=1.5, depth=0.002, mix=0.3, voices=3).process(arp_audio)
    arp_audio = Reverb(room_size=0.5, mix=0.25).process(arp_audio)

    track = Track(name="Stellar Arpeggio", track_type=TrackType.FX, volume=0.35)
    track.add(Sample("arp", arp_audio), 0)

    return track


def create_cosmic_bass(beat_dur):
    """
    Deep foundational bass - the root of all heavens.
    Flowing like the primordial waters beneath creation.
    """
    track = Track(name="Cosmic Bass", track_type=TrackType.BASS, volume=0.7)

    # Bass pattern - mostly root (E), with movement
    # Following the structure of the song
    bass_pattern = [
        # Intro (bars 0-8)
        ('E1', 0, 4), ('E1', 4, 4),

        # Section 1 (bars 8-24) - Lower heavens
        ('E1', 8, 4), ('E1', 12, 2), ('G1', 14, 2),
        ('E1', 16, 4), ('A1', 20, 2), ('B1', 22, 2),

        # Section 2 (bars 24-40) - Middle heavens (more movement)
        ('A1', 24, 4), ('A1', 28, 4),
        ('B1', 32, 4), ('B1', 36, 4),

        # Section 3 (bars 40-56) - Upper heavens (return to stability)
        ('E1', 40, 4), ('D1', 44, 4),
        ('C1', 48, 4), ('B0', 52, 4),

        # Outro (bars 56-64) - Resolution
        ('E1', 56, 4), ('E1', 60, 4),
    ]

    for note, beat, dur in bass_pattern:
        freq = note_to_freq(note)
        bass = BassSynth.sub_bass(freq, dur * beat_dur)
        track.add(bass, beat * beat_dur)

    # Add subtle filtering and compression
    track.add_effect(LowPassFilter(cutoff=180))
    track.add_effect(Compressor(threshold=-8, ratio=4, attack=0.02, release=0.15))

    return track


def create_heavenly_bells(beat_dur):
    """
    Bell sounds marking significant moments in the journey.
    Each bell marks entrance to a new heaven.
    """
    track = Track(name="Heavenly Bells", track_type=TrackType.FX, volume=0.4)

    # Nine bells for nine heavens - placed at key transition points
    bell_timings = [
        (0, 'E4'),  # Divine Empyrean
        (8, 'F#4'),  # Azure Heaven
        (16, 'G4'),  # Jade Heaven
        (24, 'A4'),  # Vermilion Heaven
        (32, 'B4'),  # Luminous Heaven
        (40, 'C5'),  # Jade-Pure Heaven
        (48, 'D5'),  # Crystalline Heaven
        (56, 'E5'),  # Purple Heaven
        (60, 'F#5'),  # Supreme Heaven
    ]

    for beat, note in bell_timings:
        freq = note_to_freq(note)
        bell = PluckSynth.bell(freq, duration=3.0)
        track.add(bell, beat * beat_dur)

    # Massive reverb for bell tails
    track.add_effect(Reverb(room_size=0.85, damping=0.3, mix=0.55))

    return track


def create_dipper_plucks(beat_dur):
    """
    Seven plucks representing the Northern Dipper stars.
    Guiding the journey through the nine heavens.
    """
    track = Track(name="Dipper Plucks", track_type=TrackType.FX, volume=0.45)

    # Seven stars of the Dipper in the scale
    dipper_notes = ['E4', 'F#4', 'G4', 'A4', 'B4', 'C5', 'D5']

    # Place them throughout the song in patterns
    # They appear more frequently in middle section (guidance needed)

    for bar in [4, 12, 20, 28, 36, 44, 52, 60]:
        for i, note in enumerate(dipper_notes):
            freq = note_to_freq(note)
            pluck = PluckSynth.karplus_strong(freq, duration=0.6, brightness=0.8)
            beat = bar + (i * 0.25)  # Spread across 2 beats
            track.add(pluck, beat * beat_dur)

    # Delay to create cascading effect
    track.add_effect(Delay(delay_time=0.125, feedback=0.4, mix=0.35))
    track.add_effect(Reverb(room_size=0.5, mix=0.3))

    return track


def create_xuannv_lead(beat_dur, bpm):
    """
    The voice of the Mysterious Lady herself.
    Soaring lead that enters in the middle section.
    """
    track = Track(name="Xuannv Presence", track_type=TrackType.LEAD, volume=0.55)

    # She enters at bar 24 (middle heavens) and guides through to the end
    # Soaring, vocal-like synth melody

    xuannv_melody = [
        # First appearance (bars 24-32)
        ('B4', 24, 2), ('C5', 26, 1), ('D5', 27, 1),
        ('E5', 28, 3),  # Her presence announced
        ('D5', 31, 1),

        # Guiding through middle heavens (bars 32-40)
        ('C5', 32, 2), ('B4', 34, 1), ('A4', 35, 1),
        ('G4', 36, 2), ('A4', 38, 1), ('B4', 39, 1),

        # Ascending to upper heavens (bars 40-48)
        ('C5', 40, 2), ('D5', 42, 2),
        ('E5', 44, 3), ('F#5', 47, 1),

        # Supreme teaching (bars 48-56)
        ('G5', 48, 4),  # Peak - the highest heaven revealed
        ('F#5', 52, 2), ('E5', 54, 2),

        # Fading back into mystery (bars 56-64)
        ('D5', 56, 2), ('C5', 58, 2),
        ('B4', 60, 2), ('A4', 62, 2),
    ]

    for note, beat, dur in xuannv_melody:
        freq = note_to_freq(note)
        # Use pad-like lead for vocal quality
        lead = create_lead(note, dur * beat_dur, lead_type='square')
        # Make it more vocal by adding formant-like filtering
        lead_audio = lead.audio
        # Add vibrato effect through subtle pitch modulation (simulated with chorus)
        track.add(Sample(f"xuannv_{beat}", lead_audio), beat * beat_dur)

    # Sidechain to drums for breathing effect
    sidechain = SidechainPresets.subtle_groove(bpm)

    # Effects - ethereal and present
    track.add_effect(sidechain)
    track.add_effect(Chorus(rate=0.3, depth=0.005, mix=0.25))  # Vibrato-like
    track.add_effect(Delay(delay_time=0.5, feedback=0.25, mix=0.2))
    track.add_effect(Reverb(room_size=0.65, damping=0.4, mix=0.35))

    return track


def create_cosmic_transitions(beat_dur):
    """
    FX sounds marking transitions between sections.
    Risers, sweeps, and impacts at key moments.
    """
    track = Track(name="Cosmic Transitions", track_type=TrackType.FX, volume=0.3)

    # Riser into section 1 (bar 7-8)
    riser1 = FXSynth.riser(duration=2 * beat_dur, start_freq=100, end_freq=1000)
    track.add(riser1, 7 * 4 * beat_dur)

    # Sweep into section 2 (bar 23-24)
    sweep1 = FXSynth.noise_sweep(duration=2 * beat_dur)
    track.add(Sample("sweep1", sweep1.audio), 23 * 4 * beat_dur)

    # Riser into section 3 (bar 39-40)
    riser2 = FXSynth.riser(duration=2 * beat_dur, start_freq=200, end_freq=2000)
    track.add(riser2, 39 * 4 * beat_dur)

    # Impact at the peak (bar 48 - highest heaven)
    impact = FXSynth.impact()
    track.add(impact, 48 * 4 * beat_dur)

    # Downer into outro (bar 55-56)
    downer = FXSynth.downer(duration=2 * beat_dur, start_freq=2000, end_freq=100)
    track.add(downer, 55 * 4 * beat_dur)

    track.add_effect(Reverb(room_size=0.7, mix=0.4))

    return track


if __name__ == "__main__":
    print("\n🌌 Invoking the Five Emperors Council...")
    print("🌌 Channeling the Nine Heavens...")
    print("🌌 Manifesting cosmic sound...\n")

    song = create_nine_heavens_theme()

    print("\n✨ 急急如律令敕 ✨")
    print("The Nine Heavens have spoken through sound!")