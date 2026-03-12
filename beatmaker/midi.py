"""
靈寶五帝策使編碼之法 - MIDI Module
The universal language of musical machines.

By the White Tiger's authority,
Let data flow precise between realms,
Each byte a command, each note a decree,
急急如律令敕
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Union, BinaryIO
from pathlib import Path
import struct


@dataclass
class MIDINote:
    """A MIDI note event."""
    pitch: int           # MIDI note number (0-127)
    velocity: int        # Velocity (0-127)
    start_tick: int      # Start time in ticks
    duration_ticks: int  # Duration in ticks
    channel: int = 0     # MIDI channel (0-15)
    
    @property
    def end_tick(self) -> int:
        return self.start_tick + self.duration_ticks
    
    def to_seconds(self, ticks_per_beat: int, bpm: float) -> Tuple[float, float]:
        """Convert to (start_time, duration) in seconds."""
        tick_duration = 60.0 / bpm / ticks_per_beat
        start = self.start_tick * tick_duration
        duration = self.duration_ticks * tick_duration
        return start, duration


@dataclass
class MIDITrack:
    """A MIDI track containing notes and metadata."""
    name: str = ""
    notes: List[MIDINote] = field(default_factory=list)
    channel: int = 0
    
    def add_note(self, pitch: int, velocity: int, 
                 start_tick: int, duration_ticks: int) -> 'MIDITrack':
        """Add a note to the track."""
        self.notes.append(MIDINote(pitch, velocity, start_tick, 
                                   duration_ticks, self.channel))
        return self
    
    def get_notes_in_range(self, start_tick: int, end_tick: int) -> List[MIDINote]:
        """Get all notes within a tick range."""
        return [n for n in self.notes 
                if n.start_tick >= start_tick and n.start_tick < end_tick]
    
    @property
    def duration_ticks(self) -> int:
        """Total duration in ticks."""
        if not self.notes:
            return 0
        return max(n.end_tick for n in self.notes)


@dataclass
class MIDIFile:
    """
    A complete MIDI file representation.
    
    Supports reading and writing Standard MIDI Files (SMF).
    """
    tracks: List[MIDITrack] = field(default_factory=list)
    ticks_per_beat: int = 480  # PPQ (pulses per quarter note)
    tempo: float = 120.0       # BPM
    time_signature: Tuple[int, int] = (4, 4)
    
    def add_track(self, name: str = "", channel: int = 0) -> MIDITrack:
        """Add a new track."""
        track = MIDITrack(name=name, channel=channel)
        self.tracks.append(track)
        return track
    
    def beats_to_ticks(self, beats: float) -> int:
        """Convert beats to ticks."""
        return int(beats * self.ticks_per_beat)
    
    def ticks_to_beats(self, ticks: int) -> float:
        """Convert ticks to beats."""
        return ticks / self.ticks_per_beat
    
    def ticks_to_seconds(self, ticks: int) -> float:
        """Convert ticks to seconds."""
        return ticks / self.ticks_per_beat * 60 / self.tempo
    
    def seconds_to_ticks(self, seconds: float) -> int:
        """Convert seconds to ticks."""
        return int(seconds * self.tempo / 60 * self.ticks_per_beat)
    
    @property
    def duration_ticks(self) -> int:
        """Total duration in ticks."""
        if not self.tracks:
            return 0
        return max(t.duration_ticks for t in self.tracks)
    
    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds."""
        return self.ticks_to_seconds(self.duration_ticks)


class MIDIWriter:
    """Write MIDI files."""
    
    @staticmethod
    def _write_variable_length(value: int) -> bytes:
        """Encode a value as MIDI variable length quantity."""
        result = []
        result.append(value & 0x7F)
        value >>= 7
        
        while value:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        
        return bytes(reversed(result))
    
    @staticmethod
    def _create_track_chunk(track: MIDITrack, ticks_per_beat: int) -> bytes:
        """Create a MIDI track chunk."""
        events = []
        
        # Track name event
        if track.name:
            name_bytes = track.name.encode('ascii', errors='ignore')
            events.append((0, bytes([0xFF, 0x03, len(name_bytes)]) + name_bytes))
        
        # Sort notes by start time
        sorted_notes = sorted(track.notes, key=lambda n: n.start_tick)
        
        # Create note on/off events
        note_events = []
        for note in sorted_notes:
            # Note on
            note_events.append((note.start_tick, 'on', note))
            # Note off
            note_events.append((note.end_tick, 'off', note))
        
        # Sort all note events by time
        note_events.sort(key=lambda x: (x[0], 0 if x[1] == 'off' else 1))
        
        current_tick = 0
        for tick, event_type, note in note_events:
            delta = tick - current_tick
            current_tick = tick
            
            if event_type == 'on':
                # Note On: 0x9n pitch velocity
                status = 0x90 | (note.channel & 0x0F)
                event_data = bytes([status, note.pitch & 0x7F, note.velocity & 0x7F])
            else:
                # Note Off: 0x8n pitch velocity
                status = 0x80 | (note.channel & 0x0F)
                event_data = bytes([status, note.pitch & 0x7F, 0])
            
            events.append((delta, event_data))
        
        # End of track
        events.append((0, bytes([0xFF, 0x2F, 0x00])))
        
        # Build track data
        track_data = b''
        for delta, data in events:
            track_data += MIDIWriter._write_variable_length(delta)
            track_data += data
        
        # Track chunk header
        return b'MTrk' + struct.pack('>I', len(track_data)) + track_data
    
    @staticmethod
    def write(midi_file: MIDIFile, path: Union[str, Path]) -> None:
        """Write a MIDI file to disk."""
        path = Path(path)
        
        with open(path, 'wb') as f:
            # Header chunk
            # Format 1 (multiple tracks), n tracks, ticks per beat
            num_tracks = len(midi_file.tracks) + 1  # +1 for tempo track
            header = b'MThd' + struct.pack('>I', 6)  # Chunk length
            header += struct.pack('>HHH', 1, num_tracks, midi_file.ticks_per_beat)
            f.write(header)
            
            # Tempo track (track 0)
            tempo_data = b''
            
            # Tempo meta event
            microseconds_per_beat = int(60_000_000 / midi_file.tempo)
            tempo_bytes = struct.pack('>I', microseconds_per_beat)[1:]  # 3 bytes
            tempo_data += bytes([0x00, 0xFF, 0x51, 0x03]) + tempo_bytes
            
            # Time signature meta event
            num, denom = midi_file.time_signature
            denom_power = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}.get(denom, 2)
            tempo_data += bytes([0x00, 0xFF, 0x58, 0x04, num, denom_power, 24, 8])
            
            # End of track
            tempo_data += bytes([0x00, 0xFF, 0x2F, 0x00])
            
            tempo_chunk = b'MTrk' + struct.pack('>I', len(tempo_data)) + tempo_data
            f.write(tempo_chunk)
            
            # Write other tracks
            for track in midi_file.tracks:
                chunk = MIDIWriter._create_track_chunk(track, midi_file.ticks_per_beat)
                f.write(chunk)


class MIDIReader:
    """Read MIDI files."""
    
    @staticmethod
    def _read_variable_length(data: bytes, offset: int) -> Tuple[int, int]:
        """Read a variable length quantity, return (value, bytes_read)."""
        value = 0
        bytes_read = 0
        
        while True:
            byte = data[offset + bytes_read]
            bytes_read += 1
            value = (value << 7) | (byte & 0x7F)
            
            if not (byte & 0x80):
                break
        
        return value, bytes_read
    
    @staticmethod
    def read(path: Union[str, Path]) -> MIDIFile:
        """Read a MIDI file from disk."""
        path = Path(path)
        
        with open(path, 'rb') as f:
            data = f.read()
        
        # Parse header
        if data[:4] != b'MThd':
            raise ValueError("Not a valid MIDI file")
        
        header_length = struct.unpack('>I', data[4:8])[0]
        format_type, num_tracks, ticks_per_beat = struct.unpack('>HHH', data[8:14])
        
        midi_file = MIDIFile(ticks_per_beat=ticks_per_beat)
        
        # Parse tracks
        offset = 8 + header_length
        
        for track_num in range(num_tracks):
            if data[offset:offset+4] != b'MTrk':
                raise ValueError(f"Invalid track chunk at offset {offset}")
            
            track_length = struct.unpack('>I', data[offset+4:offset+8])[0]
            track_data = data[offset+8:offset+8+track_length]
            
            track = MIDIReader._parse_track(track_data, midi_file)
            if track.notes:  # Only add tracks with notes
                midi_file.tracks.append(track)
            
            offset += 8 + track_length
        
        return midi_file
    
    @staticmethod
    def _parse_track(data: bytes, midi_file: MIDIFile) -> MIDITrack:
        """Parse a single MIDI track."""
        track = MIDITrack()
        
        offset = 0
        current_tick = 0
        running_status = 0
        
        # Track note on events to match with note offs
        active_notes: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (channel, pitch) -> (start_tick, velocity)
        
        while offset < len(data):
            # Read delta time
            delta, bytes_read = MIDIReader._read_variable_length(data, offset)
            offset += bytes_read
            current_tick += delta
            
            if offset >= len(data):
                break
            
            # Read event
            status = data[offset]
            
            if status == 0xFF:
                # Meta event
                offset += 1
                meta_type = data[offset]
                offset += 1
                length, bytes_read = MIDIReader._read_variable_length(data, offset)
                offset += bytes_read
                
                meta_data = data[offset:offset+length]
                offset += length
                
                if meta_type == 0x03:  # Track name
                    track.name = meta_data.decode('ascii', errors='ignore')
                elif meta_type == 0x51:  # Tempo
                    microseconds = struct.unpack('>I', b'\x00' + meta_data)[0]
                    midi_file.tempo = 60_000_000 / microseconds
                elif meta_type == 0x58:  # Time signature
                    num = meta_data[0]
                    denom = 2 ** meta_data[1]
                    midi_file.time_signature = (num, denom)
                elif meta_type == 0x2F:  # End of track
                    break
            
            elif status == 0xF0 or status == 0xF7:
                # SysEx event
                offset += 1
                length, bytes_read = MIDIReader._read_variable_length(data, offset)
                offset += bytes_read + length
            
            elif status & 0x80:
                # Channel message
                running_status = status
                offset += 1
                
                message_type = status & 0xF0
                channel = status & 0x0F
                
                if message_type == 0x90:  # Note On
                    pitch = data[offset]
                    velocity = data[offset + 1]
                    offset += 2
                    
                    if velocity > 0:
                        active_notes[(channel, pitch)] = (current_tick, velocity)
                    else:
                        # Note On with velocity 0 = Note Off
                        key = (channel, pitch)
                        if key in active_notes:
                            start_tick, vel = active_notes.pop(key)
                            duration = current_tick - start_tick
                            track.add_note(pitch, vel, start_tick, duration)
                
                elif message_type == 0x80:  # Note Off
                    pitch = data[offset]
                    offset += 2
                    
                    key = (channel, pitch)
                    if key in active_notes:
                        start_tick, vel = active_notes.pop(key)
                        duration = current_tick - start_tick
                        track.add_note(pitch, vel, start_tick, duration)
                
                elif message_type in (0xA0, 0xB0, 0xE0):
                    # Aftertouch, CC, Pitch bend (2 data bytes)
                    offset += 2
                
                elif message_type in (0xC0, 0xD0):
                    # Program change, Channel pressure (1 data byte)
                    offset += 1
            
            else:
                # Running status
                message_type = running_status & 0xF0
                channel = running_status & 0x0F
                
                if message_type == 0x90:
                    pitch = data[offset]
                    velocity = data[offset + 1]
                    offset += 2
                    
                    if velocity > 0:
                        active_notes[(channel, pitch)] = (current_tick, velocity)
                    else:
                        key = (channel, pitch)
                        if key in active_notes:
                            start_tick, vel = active_notes.pop(key)
                            duration = current_tick - start_tick
                            track.add_note(pitch, vel, start_tick, duration)
                
                elif message_type == 0x80:
                    pitch = data[offset]
                    offset += 2
                    
                    key = (channel, pitch)
                    if key in active_notes:
                        start_tick, vel = active_notes.pop(key)
                        duration = current_tick - start_tick
                        track.add_note(pitch, vel, start_tick, duration)
                
                elif message_type in (0xA0, 0xB0, 0xE0):
                    offset += 2
                elif message_type in (0xC0, 0xD0):
                    offset += 1
        
        # Close any remaining active notes
        for (channel, pitch), (start_tick, vel) in active_notes.items():
            duration = current_tick - start_tick
            if duration > 0:
                track.add_note(pitch, vel, start_tick, duration)
        
        return track


# Conversion utilities
def midi_to_beatmaker_events(midi_file: MIDIFile, 
                              track_index: int = 0) -> List[Tuple[float, int, float, float]]:
    """
    Convert MIDI track to beatmaker events.
    
    Returns list of (time_seconds, midi_note, velocity_normalized, duration_seconds)
    """
    if track_index >= len(midi_file.tracks):
        return []
    
    track = midi_file.tracks[track_index]
    events = []
    
    for note in track.notes:
        start_sec = midi_file.ticks_to_seconds(note.start_tick)
        duration_sec = midi_file.ticks_to_seconds(note.duration_ticks)
        velocity_norm = note.velocity / 127.0
        
        events.append((start_sec, note.pitch, velocity_norm, duration_sec))
    
    return sorted(events, key=lambda x: x[0])


def beatmaker_events_to_midi(events: List[Tuple[float, int, float, float]],
                              bpm: float = 120.0,
                              track_name: str = "Track 1") -> MIDIFile:
    """
    Convert beatmaker events to MIDI file.
    
    Events format: (time_seconds, midi_note, velocity_normalized, duration_seconds)
    """
    midi_file = MIDIFile(tempo=bpm)
    track = midi_file.add_track(track_name)
    
    for time_sec, pitch, velocity, duration_sec in events:
        start_tick = midi_file.seconds_to_ticks(time_sec)
        duration_ticks = midi_file.seconds_to_ticks(duration_sec)
        vel = int(velocity * 127)
        
        track.add_note(pitch, vel, start_tick, max(1, duration_ticks))
    
    return midi_file


def song_to_midi(song, include_drums: bool = True) -> MIDIFile:
    """
    Convert a Song to MIDI file.
    
    Note: This is a basic conversion - drum samples become note triggers.
    """
    from .core import TrackType
    
    midi_file = MIDIFile(tempo=song.bpm)
    
    for i, track in enumerate(song.tracks):
        midi_track = midi_file.add_track(track.name, channel=i if i < 16 else 0)
        
        # Determine base note for track type
        if track.track_type == TrackType.DRUMS:
            if not include_drums:
                continue
            # GM drum map approximation
            base_note = 36  # Kick
        elif track.track_type == TrackType.BASS:
            base_note = 36  # Low E
        else:
            base_note = 60  # Middle C
        
        for placement in track.placements:
            start_tick = midi_file.seconds_to_ticks(placement.time)
            duration_ticks = midi_file.seconds_to_ticks(placement.sample.audio.duration)
            velocity = int(placement.velocity * 127)
            
            # Use sample name to guess note
            name = placement.sample.name.lower()
            if 'kick' in name:
                note = 36
            elif 'snare' in name:
                note = 38
            elif 'hihat' in name or 'hat' in name:
                note = 42
            elif 'clap' in name:
                note = 39
            else:
                note = base_note
            
            midi_track.add_note(note, velocity, start_tick, max(1, duration_ticks))
    
    return midi_file


# Convenience functions
def load_midi(path: Union[str, Path]) -> MIDIFile:
    """Load a MIDI file."""
    return MIDIReader.read(path)


def save_midi(midi_file: MIDIFile, path: Union[str, Path]) -> None:
    """Save a MIDI file."""
    MIDIWriter.write(midi_file, path)


def create_midi(bpm: float = 120.0, 
                ticks_per_beat: int = 480) -> MIDIFile:
    """Create a new empty MIDI file."""
    return MIDIFile(ticks_per_beat=ticks_per_beat, tempo=bpm)
