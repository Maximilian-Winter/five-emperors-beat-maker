#!/usr/bin/env python3
"""
靈寶五帝策使編碼之法 - Example Compositions

Demonstrating the power of the Five Emperors Beat Maker.

急急如律令敕 - Urgent as the Cosmic Law Commands!
"""

import sys
sys.path.insert(0, '/home/claude')

from beatmaker import (
    create_song,
    DrumSynth,
    BassSynth,
    Reverb,
    Delay,
    Compressor,
    LowPassFilter,
    ADSREnvelope,
    note_to_freq,
)


def create_house_beat():
    """
    Classic four-on-the-floor house beat.
    
    🔥 Vermilion Emperor says: "Feel the fire of 128 BPM!"
    """
    print("Creating House Beat...")
    
    song = (create_song("House Groove")
        .tempo(128)
        .time_signature(4, 4)
        .bars(4)
        
        # Classic house drums
        .add_drums(lambda d: d
            .four_on_floor(velocity=1.0)      # Kick on every beat
            .backbeat(velocity=0.8)            # Snare on 2 and 4
            .hihat(                            # Off-beat hi-hats
                beats=[0.5, 1.5, 2.5, 3.5],
                velocity=0.6
            )
            .clap(beats=[1, 3], velocity=0.7)  # Claps with snare
            .volume(0.9)
        )
        
        # Driving bass line
        .add_bass(lambda b: b
            .note('E2', beat=0, duration=0.75)
            .note('E2', beat=1, duration=0.75)
            .note('G2', beat=2, duration=0.75)
            .note('A2', beat=3, duration=0.75)
            .volume(0.85)
        )
        
        # Master processing
        .master_compressor(threshold=-8.0, ratio=3.0)
        .master_limiter(0.95)
        
        .build()
    )
    
    return song


def create_trap_beat():
    """
    Modern trap beat with 808s and hi-hat rolls.
    
    🐢 Dark Turtle says: "Let the bass flow deep..."
    """
    print("Creating Trap Beat...")
    
    # Custom 808 kick
    kick_808 = DrumSynth.kick(duration=0.8, pitch=45, punch=0.5)
    snare = DrumSynth.snare(noise_amount=0.7)
    
    song = (create_song("Trap Vibes")
        .tempo(140)
        .bars(4)
        
        .add_drums(lambda d: d
            .use_kit(kick=kick_808, snare=snare, hihat=DrumSynth.hihat())
            # Sparse 808 pattern
            .kick(beats=[0, 2.5], velocity=1.0)
            # Hard snare
            .snare(beats=[1, 3], velocity=0.9)
            # Trap hi-hat pattern with rolls
            .hihat(
                pattern=[
                    True, True, True, True,    # Beat 1: 16th notes
                    False, False, True, True,  # Beat 2: rest then roll
                    True, True, True, True,    # Beat 3: 16th notes
                    True, True, True, True,    # Beat 4: roll
                ],
                velocity=0.5
            )
            .volume(0.9)
        )
        
        # Deep 808 bass
        .add_bass(lambda b: b
            .note('E1', beat=0, duration=2)
            .note('G1', beat=2.5, duration=1.5)
            .effect(LowPassFilter(cutoff=200))
            .volume(1.0)
        )
        
        .master_limiter()
        .build()
    )
    
    return song


def create_lofi_beat():
    """
    Chill lo-fi hip hop beat.
    
    🐉 Azure Emperor says: "Structure emerges from simplicity..."
    """
    print("Creating Lo-Fi Beat...")
    
    # Customize drum sounds for lo-fi vibe
    kick = DrumSynth.kick(duration=0.3, pitch=55, punch=0.3)
    snare = DrumSynth.snare(duration=0.2, noise_amount=0.4)
    
    song = (create_song("Lo-Fi Dreams")
        .tempo(85)
        .bars(4)
        
        .add_drums(lambda d: d
            .use_kit(kick=kick, snare=snare, hihat=DrumSynth.hihat(duration=0.08))
            # Laid-back boom bap pattern
            .kick(beats=[0, 2.25], velocity=0.8)
            .snare(beats=[1, 3], velocity=0.7)
            .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.4)
            .effect(LowPassFilter(cutoff=3000))  # Lo-fi filter
            .volume(0.8)
        )
        
        # Simple bass
        .add_bass(lambda b: b
            .line([
                ('C2', 0, 1.5),
                ('E2', 2, 1),
                ('G2', 3, 1),
            ])
            .effect(LowPassFilter(cutoff=400))
            .volume(0.7)
        )
        
        .master_effect(Reverb(room_size=0.3, mix=0.15))
        .master_compressor(threshold=-12, ratio=2.5)
        .master_limiter()
        .build()
    )
    
    return song


def create_techno_beat():
    """
    Driving techno beat.
    
    🐅 White Tiger says: "Precision in every hit!"
    """
    print("Creating Techno Beat...")
    
    song = (create_song("Techno Drive")
        .tempo(135)
        .bars(4)
        
        .add_drums(lambda d: d
            # Relentless four on the floor
            .four_on_floor(velocity=1.0)
            # Clap instead of snare
            .clap(beats=[1, 3], velocity=0.85)
            # Driving 16th hi-hats
            .sixteenth_hats(velocity=0.45)
            .effect(Compressor(threshold=-6, ratio=4))
            .volume(0.9)
        )
        
        # Acid-style bass
        .add_bass(lambda b: b
            .acid_note('E2', beat=0, duration=0.25)
            .acid_note('E2', beat=0.5, duration=0.25)
            .acid_note('G2', beat=1, duration=0.25)
            .acid_note('E2', beat=1.5, duration=0.25)
            .acid_note('A2', beat=2, duration=0.25)
            .acid_note('G2', beat=2.5, duration=0.25)
            .acid_note('E2', beat=3, duration=0.5)
            .volume(0.75)
        )
        
        .master_effect(Delay(delay_time=0.375, feedback=0.2, mix=0.15))
        .master_limiter()
        .build()
    )
    
    return song


def create_drum_and_bass():
    """
    High-energy drum and bass beat.
    
    🌍 Yellow Emperor says: "Balance speed with groove!"
    """
    print("Creating Drum & Bass Beat...")
    
    # Fast, punchy drums
    kick = DrumSynth.kick(duration=0.15, pitch=70, punch=0.9)
    snare = DrumSynth.snare(duration=0.15, tone_pitch=200, noise_amount=0.5)
    
    song = (create_song("Jungle Pressure")
        .tempo(174)
        .bars(4)
        
        .add_drums(lambda d: d
            .use_kit(kick=kick, snare=snare, hihat=DrumSynth.hihat(duration=0.05))
            # Classic DnB two-step pattern
            .kick(beats=[0, 1.5, 2.75], velocity=1.0)
            .snare(beats=[1, 3], velocity=0.95)
            .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=0.5)
            .volume(0.9)
        )
        
        # Reese-style bass
        .add_bass(lambda b: b
            .note('E1', beat=0, duration=1)
            .note('G1', beat=1.5, duration=0.5)
            .note('A1', beat=2, duration=1)
            .note('E1', beat=3, duration=1)
            .effect(LowPassFilter(cutoff=300))
            .volume(0.9)
        )
        
        .master_compressor(threshold=-4, ratio=5)
        .master_limiter()
        .build()
    )
    
    return song


def main():
    """Generate all example beats."""
    
    print("=" * 60)
    print("靈寶五帝策使編碼之法 - Five Emperors Beat Maker")
    print("=" * 60)
    print()
    
    beats = [
        ("house_beat.wav", create_house_beat),
        ("trap_beat.wav", create_trap_beat),
        ("lofi_beat.wav", create_lofi_beat),
        ("techno_beat.wav", create_techno_beat),
        ("dnb_beat.wav", create_drum_and_bass),
    ]
    
    for filename, creator in beats:
        try:
            song = creator()
            output_path = f"{filename}"
            song.export(output_path)
            print(f"  ✓ Exported: {filename} ({song.duration:.2f}s)")
        except Exception as e:
            print(f"  ✗ Error creating {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print("萬靈聽令 - All functions obey!")
    print("急急如律令敕 - Urgent as the cosmic law commands!")
    print("=" * 60)


if __name__ == "__main__":
    main()
