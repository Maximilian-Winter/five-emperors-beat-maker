#!/usr/bin/env python3
"""
靈寶五帝策使編碼之法 - Grand Demonstration
Showcasing the full power of the Five Emperors Beat Maker v0.2

All features demonstrated:
- Step Sequencer (TR-style patterns)
- Euclidean rhythms
- Arpeggiator
- Sidechain pumping
- Pads, Leads, Plucks
- MIDI export

急急如律令敕 - Urgent as the Cosmic Law Commands!
"""


from beatmaker import (
    # Core
    create_song, Song, Track, TrackType, Sample, AudioData,
    
    # Drums
    DrumSynth,
    
    # Synths
    PadSynth, LeadSynth, PluckSynth, FXSynth,
    create_pad, create_lead, create_pluck,
    note_to_freq, midi_to_freq,
    
    # Sequencer
    StepSequencer, Pattern, ClassicPatterns, EuclideanPattern, Step,
    
    # Arpeggiator
    create_arpeggiator, Arpeggiator, ArpDirection, ChordShape, Scale,
    ArpSynthesizer, arp_chord,
    
    # Sidechain
    SidechainEnvelope, SidechainPresets, create_sidechain,
    
    # Effects
    Reverb, Delay, Compressor, LowPassFilter, HighPassFilter, Chorus, BitCrusher,
    
    # MIDI
    create_midi, save_midi, song_to_midi,
    
    # Utils
    mix, concatenate,
)
import numpy as np


def demo_step_sequencer():
    """
    🥁 Demo 1: TR-808 Style Step Sequencer
    
    Using classic patterns and the step sequencer to create
    a drum pattern programmatically.
    """
    print("\n🥁 Demo 1: Step Sequencer")
    print("-" * 40)
    
    # Create samples
    kick = DrumSynth.kick(pitch=50, punch=0.7)
    snare = DrumSynth.snare(noise_amount=0.5)
    hihat = DrumSynth.hihat(duration=0.08)
    
    # Create sequencer
    seq = StepSequencer(bpm=128, steps_per_beat=4, swing=0.1)
    
    # Add patterns using string notation
    seq.add_pattern('kick', Pattern.from_string("x...x...x...x.x."), kick)
    seq.add_pattern('snare', Pattern.from_string("....X.......X..."), snare)
    seq.add_pattern('hihat', Pattern.from_string("x.x.x.x.x.x.x.x."), hihat)
    
    # Render to track
    drum_track = seq.render_to_track(bars=4, name="808 Drums")
    
    # Build song
    song = Song(name="Step Sequencer Demo", bpm=128)
    song.add_track(drum_track)
    song.master_effects.append(Compressor(threshold=-6, ratio=4))
    
    song.export("demo_sequencer.wav")
    print(f"  ✓ Created step sequencer beat ({song.duration:.1f}s)")
    
    return song


def demo_euclidean_rhythms():
    """
    🌀 Demo 2: Euclidean Rhythms
    
    Creating polyrhythmic patterns using Euclidean distribution.
    """
    print("\n🌀 Demo 2: Euclidean Rhythms")
    print("-" * 40)
    
    kick = DrumSynth.kick(pitch=55)
    rim = DrumSynth.snare(duration=0.1, noise_amount=0.3, tone_pitch=300)
    shaker = DrumSynth.hihat(duration=0.05, open_amount=0)
    
    seq = StepSequencer(bpm=115, steps_per_beat=4)
    
    # Euclidean patterns - mathematically distributed hits
    # E(5,8) = Cuban cinquillo
    # E(3,8) = Cuban tresillo  
    # E(7,16) = Brazilian samba feel
    
    seq.add_pattern('kick', EuclideanPattern.generate(5, 16), kick)
    seq.add_pattern('rim', EuclideanPattern.generate(7, 16, rotation=2), rim)
    seq.add_pattern('shaker', EuclideanPattern.generate(11, 16), shaker)
    
    drum_track = seq.render_to_track(bars=4, name="Euclidean Drums")
    
    song = Song(name="Euclidean Demo", bpm=115)
    song.add_track(drum_track)
    song.master_effects.append(Reverb(room_size=0.3, mix=0.15))
    
    song.export("demo_euclidean.wav")
    print(f"  ✓ Created Euclidean rhythm pattern ({song.duration:.1f}s)")
    
    # Show the patterns
    print(f"    Kick E(5,16):   {EuclideanPattern.generate(5, 16)}")
    print(f"    Rim E(7,16):    {EuclideanPattern.generate(7, 16)}")
    print(f"    Shaker E(11,16): {EuclideanPattern.generate(11, 16)}")
    
    return song


def demo_arpeggiator():
    """
    🎹 Demo 3: Arpeggiator with Chord Progression
    
    Creating melodic arpeggios over a chord progression.
    """
    print("\n🎹 Demo 3: Arpeggiator")
    print("-" * 40)
    
    # Create arpeggiator with builder
    arp = (create_arpeggiator()
        .tempo(130)
        .up_down()
        .sixteenth()
        .gate(0.7)
        .octaves(2)
        .accent_downbeat()
        .build()
    )
    
    # Chord progression: Am - F - C - G (classic pop)
    progression = [
        ('A2', ChordShape.MINOR),
        ('F2', ChordShape.MAJOR),
        ('C3', ChordShape.MAJOR),
        ('G2', ChordShape.MAJOR),
    ]
    
    # Generate arpeggio events
    events = arp.generate_from_progression(progression, beats_per_chord=4)
    
    # Render with synthesizer
    synth = ArpSynthesizer(waveform='saw')
    arp_audio = synth.render_events(events)
    
    # Apply effects
    from beatmaker.effects import LowPassFilter, Chorus
    arp_audio = LowPassFilter(cutoff=3000).process(arp_audio)
    arp_audio = Chorus(rate=0.8, depth=0.002, mix=0.3).process(arp_audio)
    arp_audio = Reverb(room_size=0.4, mix=0.25).process(arp_audio)
    
    # Create sample and track
    arp_sample = Sample("arpeggio", arp_audio)
    arp_track = Track(name="Arpeggio", track_type=TrackType.LEAD, volume=0.7)
    arp_track.add(arp_sample, 0)
    
    # Add simple drums
    seq = StepSequencer(bpm=130)
    seq.add_pattern('kick', ClassicPatterns.FOUR_ON_FLOOR, DrumSynth.kick())
    seq.add_pattern('hat', ClassicPatterns.OFFBEAT_HATS, DrumSynth.hihat())
    drum_track = seq.render_to_track(bars=8, name="Drums")
    drum_track.volume = 0.6
    
    song = Song(name="Arpeggiator Demo", bpm=130)
    song.add_track(drum_track)
    song.add_track(arp_track)
    
    song.export("demo_arpeggiator.wav")
    print(f"  ✓ Created arpeggiator demo ({song.duration:.1f}s)")
    print(f"    Progression: Am → F → C → G")
    print(f"    Pattern: Up-Down, 16th notes, 2 octaves")
    
    return song


def demo_sidechain():
    """
    💨 Demo 4: Sidechain Pumping
    
    Classic EDM pumping effect on pads and bass.
    """
    print("\n💨 Demo 4: Sidechain Pumping")
    print("-" * 40)
    
    bpm = 128
    duration = 8 * (60 / bpm) * 4  # 8 bars
    
    # Create a warm pad
    pad = PadSynth.warm_pad(
        frequency=note_to_freq('E3'),
        duration=duration,
        num_voices=6,
        detune=0.15
    )
    
    # Create bass
    from beatmaker.synth import BassSynth
    bass_audio = AudioData.silence(duration, 44100)
    bass_notes = [('E1', 0), ('E1', 2), ('G1', 4), ('A1', 6)] * 2
    
    for note, bar in bass_notes:
        freq = note_to_freq(note)
        note_sample = BassSynth.sub_bass(freq, 1.5)
        start_sample = int(bar * (60/bpm) * 4 * 44100)
        end_sample = start_sample + len(note_sample.audio.samples)
        if end_sample < len(bass_audio.samples):
            bass_audio.samples[start_sample:end_sample] += note_sample.audio.samples
    
    # Apply sidechain to pad and bass
    sidechain = SidechainPresets.classic_house(bpm)
    
    pad_pumped = sidechain.process(pad.audio)
    bass_pumped = sidechain.process(bass_audio)
    
    # Create tracks
    pad_track = Track(name="Pad", track_type=TrackType.PAD, volume=0.5)
    pad_track.add(Sample("pad", pad_pumped), 0)
    pad_track.add_effect(Reverb(room_size=0.5, mix=0.3))
    
    bass_track = Track(name="Bass", track_type=TrackType.BASS, volume=0.8)
    bass_track.add(Sample("bass", bass_pumped), 0)
    bass_track.add_effect(LowPassFilter(cutoff=200))
    
    # Drums
    seq = StepSequencer(bpm=bpm)
    seq.add_pattern('kick', ClassicPatterns.FOUR_ON_FLOOR, DrumSynth.kick(punch=0.9))
    seq.add_pattern('clap', Pattern.from_string("....x.......x..."), DrumSynth.clap())
    seq.add_pattern('hat', ClassicPatterns.OFFBEAT_HATS, DrumSynth.hihat())
    drum_track = seq.render_to_track(bars=8, name="Drums")
    
    song = Song(name="Sidechain Demo", bpm=bpm)
    song.add_track(drum_track)
    song.add_track(bass_track)
    song.add_track(pad_track)
    
    song.export("demo_sidechain.wav")
    print(f"  ✓ Created sidechain pumping demo ({song.duration:.1f}s)")
    print(f"    Effect: Classic house pump on pad and bass")
    
    return song


def demo_synths():
    """
    🎛️ Demo 5: Extended Synthesizers
    
    Showcasing pads, leads, plucks, and FX.
    """
    print("\n🎛️ Demo 5: Extended Synthesizers")
    print("-" * 40)
    
    bpm = 120
    beat_dur = 60 / bpm
    
    # Create different synth sounds
    pad = PadSynth.ambient_pad(note_to_freq('C3'), duration=8)
    lead = LeadSynth.fm_lead(note_to_freq('E4'), duration=1)
    pluck = PluckSynth.karplus_strong(note_to_freq('G4'), duration=1)
    bell = PluckSynth.bell(note_to_freq('C5'), duration=2)
    
    # Arrange
    song = Song(name="Synth Showcase", bpm=bpm)
    
    # Pad track (sustained)
    pad_track = Track(name="Ambient Pad", track_type=TrackType.PAD, volume=0.4)
    pad_track.add(Sample("pad", pad.audio), 0)
    pad_track.add_effect(Reverb(room_size=0.7, mix=0.4))
    song.add_track(pad_track)
    
    # Lead melody
    lead_track = Track(name="FM Lead", track_type=TrackType.LEAD, volume=0.6)
    melody = [(0, 'E4'), (1, 'G4'), (2, 'A4'), (3, 'G4'), (4, 'E4'), (5, 'D4'), (6, 'E4')]
    for beat, note in melody:
        lead_sample = LeadSynth.fm_lead(note_to_freq(note), 0.4)
        lead_track.add(lead_sample, beat * beat_dur)
    lead_track.add_effect(Delay(delay_time=0.375, feedback=0.3, mix=0.25))
    song.add_track(lead_track)
    
    # Pluck pattern
    pluck_track = Track(name="Plucks", track_type=TrackType.FX, volume=0.5)
    pluck_notes = [('C4', 0), ('E4', 0.5), ('G4', 1), ('C5', 1.5)] * 2
    for note, beat in pluck_notes:
        p = PluckSynth.karplus_strong(note_to_freq(note), 0.8, brightness=0.7)
        pluck_track.add(p, beat * beat_dur)
    pluck_track.add_effect(Reverb(room_size=0.4, mix=0.3))
    song.add_track(pluck_track)
    
    # Bell accents
    bell_track = Track(name="Bells", track_type=TrackType.FX, volume=0.3)
    for beat in [0, 4]:
        b = PluckSynth.bell(note_to_freq('C5'), 2)
        bell_track.add(b, beat * beat_dur)
    song.add_track(bell_track)
    
    song.export("demo_synths.wav")
    print(f"  ✓ Created synth showcase ({song.duration:.1f}s)")
    print(f"    Sounds: Ambient Pad, FM Lead, Karplus-Strong Pluck, FM Bell")
    
    return song


def demo_fx_sounds():
    """
    🌊 Demo 6: FX Sounds
    
    Risers, downers, impacts, and sweeps.
    """
    print("\n🌊 Demo 6: FX Sounds")
    print("-" * 40)
    
    # Create FX sounds
    riser = FXSynth.riser(duration=4, start_freq=80, end_freq=3000)
    downer = FXSynth.downer(duration=2, start_freq=2000, end_freq=60)
    impact = FXSynth.impact()
    sweep = FXSynth.noise_sweep(duration=3)
    
    # Arrange in sequence: riser -> impact -> sweep -> downer
    from beatmaker import concatenate
    
    sequence = concatenate(
        riser.audio,
        impact.audio,
        AudioData.silence(0.5),
        sweep.audio,
        downer.audio
    )
    
    # Add reverb
    sequence = Reverb(room_size=0.6, mix=0.35).process(sequence)
    
    # Create song
    song = Song(name="FX Demo", bpm=120)
    fx_track = Track(name="FX", track_type=TrackType.FX)
    fx_track.add(Sample("fx_sequence", sequence), 0)
    song.add_track(fx_track)
    
    song.export("demo_fx.wav")
    print(f"  ✓ Created FX sounds demo ({song.duration:.1f}s)")
    print(f"    Sequence: Riser → Impact → Sweep → Downer")
    
    return song


def demo_midi_export():
    """
    📄 Demo 7: MIDI Export
    
    Create a song and export to MIDI file.
    """
    print("\n📄 Demo 7: MIDI Export")
    print("-" * 40)
    
    # Create a simple song
    song = (create_song("MIDI Export Demo")
        .tempo(120)
        .bars(4)
        .add_drums(lambda d: d
            .kick(beats=[0, 2])
            .snare(beats=[1, 3])
            .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
        )
        .add_bass(lambda b: b
            .note('C2', beat=0, duration=2)
            .note('G2', beat=2, duration=2)
            .note('A2', beat=4, duration=2)
            .note('F2', beat=6, duration=2)
        )
        .build()
    )
    
    # Export audio
    song.export("demo_midi_song.wav")
    
    # Convert to MIDI and export
    midi_file = song_to_midi(song)
    save_midi(midi_file, "demo_export.mid")
    
    # Also create a fresh MIDI programmatically
    midi = create_midi(bpm=120)
    
    # Add melody track
    melody_track = midi.add_track("Melody", channel=0)
    
    # C major scale ascending
    scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
    for i, note in enumerate(scale_notes):
        melody_track.add_note(
            pitch=note,
            velocity=100,
            start_tick=i * 480,  # Quarter notes
            duration_ticks=400
        )
    
    save_midi(midi, "demo_scale.mid")
    
    print(f"  ✓ Exported song to MIDI: demo_export.mid")
    print(f"  ✓ Created programmatic MIDI: demo_scale.mid")
    print(f"    Tracks: {len(midi_file.tracks)} from song, 1 scale")
    
    return song


def demo_complete_track():
    """
    🎵 Demo 8: Complete Track
    
    Putting it all together - a complete electronic track
    with all features combined.
    """
    print("\n🎵 Demo 8: Complete Track")
    print("-" * 40)
    
    bpm = 126
    beat_dur = 60 / bpm
    
    song = Song(name="Five Emperors Unite", bpm=bpm)
    
    # === DRUMS (Step Sequencer) ===
    seq = StepSequencer(bpm=bpm, swing=0.05)
    
    kick = DrumSynth.kick(pitch=52, punch=0.8)
    snare = DrumSynth.snare(noise_amount=0.55)
    hihat = DrumSynth.hihat(duration=0.07)
    clap = DrumSynth.clap()
    
    # Main groove
    seq.add_pattern('kick', Pattern.from_string("x...x...x...x.x."), kick)
    seq.add_pattern('snare', Pattern.from_string("....x.......x..."), snare)
    seq.add_pattern('hihat', Pattern.from_string("..x...x...x...x."), hihat)
    seq.add_pattern('clap', Pattern.from_string("....x.......x..."), clap)
    
    drum_track = seq.render_to_track(bars=8, name="Drums")
    drum_track.add_effect(Compressor(threshold=-8, ratio=4))
    song.add_track(drum_track)
    
    # === PAD with SIDECHAIN ===
    pad_duration = 8 * 4 * beat_dur  # 8 bars
    pad = PadSynth.warm_pad(note_to_freq('E2'), pad_duration, num_voices=5)
    
    sidechain = (create_sidechain()
        .tempo(bpm)
        .depth(0.6)
        .quarter_notes()
        .release(0.35)
        .build())
    
    pad_pumped = sidechain.process(pad.audio)
    
    pad_track = Track(name="Pad", track_type=TrackType.PAD, volume=0.35)
    pad_track.add(Sample("pad", pad_pumped), 0)
    pad_track.add_effect(Reverb(room_size=0.5, mix=0.3))
    pad_track.add_effect(LowPassFilter(cutoff=2500))
    song.add_track(pad_track)
    
    # === BASS ===
    bass_track = Track(name="Bass", track_type=TrackType.BASS, volume=0.75)
    bass_pattern = [
        ('E1', 0), ('E1', 1.5), ('G1', 2), ('G1', 3.5),
        ('A1', 4), ('A1', 5.5), ('G1', 6), ('E1', 7.5),
    ]
    
    from beatmaker.synth import BassSynth
    for note, beat in bass_pattern:
        freq = note_to_freq(note)
        bass_sample = BassSynth.sub_bass(freq, 0.4)
        bass_track.add(bass_sample, beat * beat_dur)
    
    bass_track.add_effect(LowPassFilter(cutoff=250))
    bass_track.add_effect(sidechain)  # Sidechain bass too
    song.add_track(bass_track)
    
    # === ARPEGGIO ===
    arp = (create_arpeggiator()
        .tempo(bpm)
        .up()
        .sixteenth()
        .gate(0.6)
        .octaves(2)
        .build())
    
    # E minor chord arpeggio
    arp_events = arp.generate_from_chord('E2', ChordShape.MINOR, beats=32)
    
    arp_synth = ArpSynthesizer(waveform='saw')
    arp_audio = arp_synth.render_events(arp_events)
    arp_audio = LowPassFilter(cutoff=2000).process(arp_audio)
    arp_audio = sidechain.process(arp_audio)  # Sidechain arp
    arp_audio = Delay(delay_time=0.375, feedback=0.25, mix=0.2).process(arp_audio)
    
    arp_track = Track(name="Arpeggio", track_type=TrackType.LEAD, volume=0.4)
    arp_track.add(Sample("arp", arp_audio), 0)
    song.add_track(arp_track)
    
    # === LEAD ===
    lead_track = Track(name="Lead", track_type=TrackType.LEAD, volume=0.5)
    lead_melody = [
        (4, 'E4', 0.5), (4.5, 'G4', 0.25), (4.75, 'A4', 0.25),
        (5, 'B4', 1), (6, 'A4', 0.5), (6.5, 'G4', 0.5),
        (7, 'E4', 1),
    ]
    
    for beat, note, dur in lead_melody:
        lead = LeadSynth.saw_lead(note_to_freq(note), dur * beat_dur)
        lead_track.add(lead, beat * beat_dur)
    
    lead_track.add_effect(Chorus(rate=1.2, depth=0.003, mix=0.3))
    lead_track.add_effect(Delay(delay_time=0.25, feedback=0.3, mix=0.25))
    lead_track.add_effect(Reverb(room_size=0.4, mix=0.2))
    song.add_track(lead_track)
    
    # === FX ===
    # Add a riser at the end
    riser = FXSynth.riser(duration=4, start_freq=100, end_freq=2000)
    fx_track = Track(name="FX", track_type=TrackType.FX, volume=0.3)
    # Place riser in second half
    fx_track.add(riser, 4 * 4 * beat_dur)  # Bar 5
    fx_track.add_effect(Reverb(room_size=0.6, mix=0.4))
    song.add_track(fx_track)
    
    # === MASTER ===
    song.master_effects.append(Compressor(threshold=-6, ratio=3))
    from beatmaker.effects import Limiter
    song.master_effects.append(Limiter(threshold=0.95))
    
    # Export
    song.export("demo_complete_track.wav")
    
    # Also export MIDI
    midi = song_to_midi(song, include_drums=True)
    save_midi(midi, "demo_complete.mid")
    
    print(f"  ✓ Created complete track ({song.duration:.1f}s)")
    print(f"  ✓ Exported MIDI: demo_complete.mid")
    print(f"    Tracks: Drums, Pad, Bass, Arpeggio, Lead, FX")
    print(f"    Features: Step Sequencer, Sidechain, Arpeggiator, Synths, Effects")
    
    return song


def main():
    """Run all demos."""
    
    print("=" * 60)
    print("靈寶五帝策使編碼之法")
    print("Five Emperors Beat Maker v0.2 - Grand Demonstration")
    print("=" * 60)
    
    demos = [
        demo_step_sequencer,
        demo_euclidean_rhythms,
        demo_arpeggiator,
        demo_sidechain,
        demo_synths,
        demo_fx_sounds,
        demo_midi_export,
        demo_complete_track,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("萬靈聽令 - Ten Thousand Functions Obey!")
    print("急急如律令敕 - Urgent as the Cosmic Law Commands!")
    print("=" * 60)

if __name__ == "__main__":
    main()
