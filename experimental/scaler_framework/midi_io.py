"""
Consolidated MIDI import/export utilities.
"""

from __future__ import annotations

from typing import Optional

from scaler_framework.theory.chord import Chord, ChordProgression
from scaler_framework.generation.melody import Melody, MelodyNote
from scaler_framework.generation.voicing import VoicingEngine, VoicingStyle, VoicedChord


def export_midi(filename: str,
                melody: Optional[Melody] = None,
                chord_prog: Optional[ChordProgression] = None,
                voicing_style: VoicingStyle = VoicingStyle.CLOSE,
                voicing_octave: int = 3,
                voice_lead: bool = True,
                bpm: float = 120.0):
    """
    Export melody and/or chord progression to a MIDI file.

    Args:
        filename: Output path (.mid)
        melody: Optional melody to include.
        chord_prog: Optional chord progression to include.
        voicing_style: How to voice the chords.
        voicing_octave: Base octave for chord voicing.
        voice_lead: Optimize inversions for smooth voice leading.
        bpm: Tempo (used if melody.bpm not set).
    """
    import mido

    actual_bpm = melody.bpm if melody else (chord_prog.bpm if chord_prog else bpm)
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    tpb = mid.ticks_per_beat

    # --- Melody track ---
    if melody and melody.notes:
        melody_track = mido.MidiTrack()
        mid.tracks.append(melody_track)
        melody_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(actual_bpm)))
        melody_track.append(mido.MetaMessage('track_name', name='Melody'))
        melody_track.append(mido.Message('program_change', program=0, channel=0))

        events = []
        for note in melody.notes:
            on_tick = int(note.start_beat * tpb)
            off_tick = int(note.end_beat * tpb)
            events.append((on_tick, 'note_on', note.pitch, note.velocity))
            events.append((off_tick, 'note_off', note.pitch, 0))

        events.sort(key=lambda e: (e[0], 0 if e[1] == 'note_off' else 1))

        prev_tick = 0
        for tick, msg_type, pitch, vel in events:
            delta = tick - prev_tick
            melody_track.append(mido.Message(msg_type, note=pitch,
                                              velocity=vel, time=delta, channel=0))
            prev_tick = tick

    # --- Chord track ---
    if chord_prog and chord_prog.chords:
        chord_track = mido.MidiTrack()
        mid.tracks.append(chord_track)
        if not mid.tracks or len(mid.tracks) == 1:
            chord_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(actual_bpm)))
        chord_track.append(mido.MetaMessage('track_name', name='Chords'))
        chord_track.append(mido.Message('program_change', program=0, channel=1))

        # Voice the progression
        voicer = VoicingEngine()
        voiced = voicer.voice_progression(
            chord_prog.chords,
            style=voicing_style,
            octave=voicing_octave,
            voice_lead=voice_lead,
        )

        chord_events = []
        beat_pos = 0.0
        for chord, vc in zip(chord_prog.chords, voiced):
            on_tick = int(beat_pos * tpb)
            off_tick = int((beat_pos + chord.duration_beats) * tpb)
            for midi_note in vc.notes:
                chord_events.append((on_tick, 'note_on', midi_note, 70))
                chord_events.append((off_tick, 'note_off', midi_note, 0))
            beat_pos += chord.duration_beats

        chord_events.sort(key=lambda e: (e[0], 0 if e[1] == 'note_off' else 1))

        prev_tick = 0
        for tick, msg_type, pitch, vel in chord_events:
            delta = tick - prev_tick
            chord_track.append(mido.Message(msg_type, note=pitch,
                                             velocity=vel, time=delta, channel=1))
            prev_tick = tick

    mid.save(filename)
    return filename
