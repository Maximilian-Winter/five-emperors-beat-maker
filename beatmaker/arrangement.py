"""
靈寶五帝策使編碼之法 - Arrangement Module
The architecture of musical form — sections, repetition, and variation.

By the Azure Dragon's authority,
Let songs grow as living structures,
Verse answering chorus, bridge spanning keys,
急急如律令敕

This module provides Section and Arrangement abstractions that
let you compose full songs from reusable, transformable building blocks.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict

from .core import Track, TrackType, SamplePlacement, AudioEffect


# ─── Section ────────────────────────────────────────────────────────────────

@dataclass
class Section:
    """
    A named section of a song (verse, chorus, bridge, intro, etc.).

    Each section has a defined length in bars and contains its own
    collection of tracks.  Sections can be reused, varied, and
    arranged into a complete song structure.
    """
    name: str
    bars: int
    tracks: List[Track] = field(default_factory=list)

    def add_track(self, track: Track) -> 'Section':
        """Add a track to this section."""
        self.tracks.append(track)
        return self

    def get_track(self, name: str) -> Optional[Track]:
        """Get a track by name."""
        for t in self.tracks:
            if t.name == name:
                return t
        return None

    # ── Variation methods (return deep copies) ───────────────────────────

    def variant(self, name: str,
                modifier: Callable[['Section'], 'Section']) -> 'Section':
        """
        Create a variation of this section.

        The modifier function receives a deep copy and can freely
        alter tracks, effects, volume, etc.

        Example:
            verse2 = verse.variant("verse2", lambda s: s.with_volume("Bass", 0.8))
        """
        new_section = copy.deepcopy(self)
        new_section.name = name
        return modifier(new_section)

    def with_added_track(self, track: Track,
                         name: Optional[str] = None) -> 'Section':
        """Return a copy with an additional track."""
        new_section = copy.deepcopy(self)
        new_section.name = name or f"{self.name}_plus"
        new_section.tracks.append(copy.deepcopy(track))
        return new_section

    def without_track(self, track_name: str,
                      name: Optional[str] = None) -> 'Section':
        """Return a copy with a track removed by name."""
        new_section = copy.deepcopy(self)
        new_section.name = name or f"{self.name}_minus"
        new_section.tracks = [t for t in new_section.tracks
                              if t.name != track_name]
        return new_section

    def with_volume(self, track_name: str, volume: float,
                    name: Optional[str] = None) -> 'Section':
        """Return a copy with a track's volume changed."""
        new_section = copy.deepcopy(self)
        new_section.name = name or self.name
        for t in new_section.tracks:
            if t.name == track_name:
                t.volume = volume
        return new_section

    def with_effect(self, track_name: str, effect: AudioEffect,
                    name: Optional[str] = None) -> 'Section':
        """Return a copy with an additional effect on a track."""
        new_section = copy.deepcopy(self)
        new_section.name = name or self.name
        for t in new_section.tracks:
            if t.name == track_name:
                t.effects.append(effect)
        return new_section

    def with_mute(self, track_name: str,
                  name: Optional[str] = None) -> 'Section':
        """Return a copy with a track muted."""
        new_section = copy.deepcopy(self)
        new_section.name = name or self.name
        for t in new_section.tracks:
            if t.name == track_name:
                t.muted = True
        return new_section

    def __repr__(self) -> str:
        track_names = [t.name for t in self.tracks]
        return f"Section('{self.name}', {self.bars} bars, tracks=[{', '.join(track_names)}])"


# ─── Transition ─────────────────────────────────────────────────────────────

@dataclass
class Transition:
    """Configuration for transition between sections."""
    type: str = 'cut'           # 'cut', 'crossfade'
    duration_beats: float = 0.0  # Duration of crossfade (if applicable)


# ─── Arrangement ────────────────────────────────────────────────────────────

@dataclass
class ArrangementEntry:
    """A section placed in the arrangement with repeat count."""
    section: Section
    repeat: int = 1
    transition: Optional[Transition] = None


class Arrangement:
    """
    The full arrangement of a song — an ordered sequence of sections.

    Sections can be added with semantic aliases (intro, verse, chorus, etc.)
    and with repeat counts.  The arrangement is flattened into a Song
    by placing section tracks on the song timeline at computed offsets.
    """

    def __init__(self):
        self._entries: List[ArrangementEntry] = []

    # ── Adding sections ──────────────────────────────────────────────────

    def add(self, section: Section, repeat: int = 1,
            transition: Optional[Transition] = None) -> 'Arrangement':
        """Add a section to the arrangement."""
        self._entries.append(ArrangementEntry(section, repeat, transition))
        return self

    # Semantic aliases
    def intro(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def verse(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def chorus(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def bridge(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def outro(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def breakdown(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    def drop(self, section: Section, repeat: int = 1) -> 'Arrangement':
        return self.add(section, repeat)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def entries(self) -> List[ArrangementEntry]:
        return list(self._entries)

    def total_bars(self) -> int:
        """Total number of bars in the arrangement."""
        return sum(e.section.bars * e.repeat for e in self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    # ── Rendering ────────────────────────────────────────────────────────

    def render_to_song(self, song) -> None:
        """
        Render the arrangement onto a Song object.

        Places all section tracks onto the song timeline at the
        correct bar offsets.  Tracks with the same name are merged
        (placements accumulated).

        Args:
            song: a builder.Song instance (imported at call time to
                  avoid circular imports).
        """
        current_bar = 0

        for entry in self._entries:
            for rep in range(entry.repeat):
                offset_seconds = song.bar_to_seconds(current_bar)
                self._place_section(song, entry.section, offset_seconds)
                current_bar += entry.section.bars

    def _place_section(self, song, section: Section,
                       offset_seconds: float) -> None:
        """Place all tracks from a section onto the song with time offset."""
        for src_track in section.tracks:
            # Find or create matching track in song
            dest_track = song.get_track(src_track.name)
            if dest_track is None:
                dest_track = Track(
                    name=src_track.name,
                    track_type=src_track.track_type,
                    volume=src_track.volume,
                    pan=src_track.pan,
                    effects=list(src_track.effects),
                )
                song.add_track(dest_track)

            # Copy placements with time offset
            for placement in src_track.placements:
                shifted = SamplePlacement(
                    sample=placement.sample,
                    time=placement.time + offset_seconds,
                    velocity=placement.velocity,
                    pan=placement.pan,
                )
                dest_track.placements.append(shifted)

    def __repr__(self) -> str:
        parts = []
        for e in self._entries:
            if e.repeat > 1:
                parts.append(f"{e.section.name} x{e.repeat}")
            else:
                parts.append(e.section.name)
        return f"Arrangement([{' -> '.join(parts)}], {self.total_bars()} bars)"
