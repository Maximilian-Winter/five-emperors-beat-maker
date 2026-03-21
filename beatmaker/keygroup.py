"""
Keygroup Module — MPC-style sample-based chromatic instrument.

Provides KeygroupProgram (the instrument) and KeygroupTrackBuilder
(the builder for use in the song builder chain).

Usage:

    from beatmaker import load_audio, create_song
    from beatmaker.keygroup import KeygroupProgram

    # From a loaded sample
    piano = KeygroupProgram.from_sample(
        load_audio("piano_C4.wav"),
        root_note='C4',
    )

    # From any Sample or synth output
    pad_sample = PadSynth.warm_pad(note_to_freq('C3'), duration=2.0)
    pad_keys = KeygroupProgram.from_sample(pad_sample, root_note='C3')

    # In a song
    song = (create_song("Sampled")
        .tempo(120).bars(4)
        .add_keygroup("Sampled Piano", piano, lambda k: k
            .note('C4', beat=0, duration=1)
            .note('E4', beat=1, duration=1)
            .chord(['C4', 'E4', 'G4'], beat=2, duration=2)
            .phrase(some_phrase)
            .volume(0.7)
            .effect(Reverb(room_size=0.4, mix=0.3))
        )
        .build()
    )

Modules:
    beatmaker/keygroup.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union, List, Tuple, TYPE_CHECKING

import numpy as np

from beatmaker.core import AudioData, Sample, Track, TrackType, AudioEffect
from beatmaker.music import (
    note_to_freq,
    note_name_to_midi,
    midi_to_freq,
    midi_to_note_name,
)
from beatmaker.synthesis.oscillator import ADSREnvelope

if TYPE_CHECKING:
    from beatmaker.melody import Phrase
    from beatmaker.builder import SongBuilder
    from beatmaker.automation import AutomationCurve
    from beatmaker.expression import Humanizer, GrooveTemplate


# ═══════════════════════════════════════════════════════════════════
#  KeygroupProgram — The Instrument
# ═══════════════════════════════════════════════════════════════════


@dataclass
class KeygroupZone:
    """A single sample mapped to a root note within a keygroup.

    For multi-sample keygroups, multiple zones can cover different
    pitch ranges (e.g., a piano sampled every minor third). The
    keygroup engine picks the closest zone for each requested note.
    """
    sample: Sample
    root_midi: int
    low_midi: int = 0
    high_midi: int = 127
    volume: float = 1.0


@dataclass
class KeygroupProgram:
    """MPC-style keygroup instrument — maps samples across the keyboard
    via pitched resampling.

    A KeygroupProgram holds one or more sample zones, each with a root
    note. When you request a note, the program finds the nearest zone
    and resamples it to the target pitch.

    The resampling is simple ratio-based interpolation (the classic
    sampler approach): higher notes produce shorter, faster playback;
    lower notes produce longer, slower playback. This is authentic
    to hardware samplers — the characteristic artifacts (chipmunk
    highs, slowed-tape lows) are part of the sound.

    For duration-preserving pitch shifting, combine with the signal
    graph or use time_stretch + pitch_shift from beatmaker.utils.
    """

    name: str = "keygroup"
    zones: List[KeygroupZone] = field(default_factory=list)
    envelope: Optional[ADSREnvelope] = None
    sample_rate: int = 44100

    # ── Factory Methods ───────────────────────────────────────────

    @classmethod
    def from_sample(
        cls,
        sample: Union[Sample, AudioData],
        root_note: Union[str, int] = 'C4',
        name: str = "keygroup",
        envelope: Optional[ADSREnvelope] = None,
    ) -> KeygroupProgram:
        """Create a keygroup from a single sample.

        This is the most common case — one sample mapped across the
        entire MIDI range, like loading a single hit into an MPC
        keygroup program.

        Parameters
        ----------
        sample : Sample or AudioData
            The source audio. If AudioData, it is wrapped in a Sample.
        root_note : str or int
            The note at which the sample plays back at original pitch.
            Accepts note names ('C4', 'F#3') or MIDI numbers (60).
        name : str
            Name for the keygroup program.
        envelope : ADSREnvelope, optional
            Amplitude envelope applied to every generated note. If None,
            notes use a minimal fade-out to avoid clicks.

        Returns
        -------
        KeygroupProgram
        """
        if isinstance(sample, AudioData):
            sample = Sample(name=name, audio=sample)

        if isinstance(root_note, str):
            root_midi = note_name_to_midi(root_note)
        else:
            root_midi = root_note

        zone = KeygroupZone(
            sample=sample,
            root_midi=root_midi,
            low_midi=0,
            high_midi=127,
        )
        return cls(
            name=name,
            zones=[zone],
            envelope=envelope,
            sample_rate=sample.audio.sample_rate,
        )

    @classmethod
    def from_multi_sample(
        cls,
        samples: List[Tuple[Union[Sample, AudioData], Union[str, int]]],
        name: str = "keygroup",
        envelope: Optional[ADSREnvelope] = None,
    ) -> KeygroupProgram:
        """Create a keygroup from multiple samples at different root notes.

        The keyboard range is automatically split so each zone covers
        the notes closest to its root. Like an MPC keygroup with
        multiple layers, or a SoundFont with samples every minor third.

        Parameters
        ----------
        samples : list of (Sample/AudioData, root_note) tuples
            Each entry is a sample and its root note (name or MIDI).
        name : str
            Name for the keygroup program.
        envelope : ADSREnvelope, optional
            Shared amplitude envelope.

        Returns
        -------
        KeygroupProgram
        """
        # Parse and sort by root MIDI
        parsed = []
        sr = 44100
        for samp, root in samples:
            if isinstance(samp, AudioData):
                samp = Sample(name=f"{name}_zone", audio=samp)
            midi = note_name_to_midi(root) if isinstance(root, str) else root
            parsed.append((samp, midi))
            sr = samp.audio.sample_rate

        parsed.sort(key=lambda x: x[1])

        # Compute zone boundaries — split at midpoints between roots
        zones = []
        for i, (samp, root_midi) in enumerate(parsed):
            if i == 0:
                low = 0
            else:
                low = (parsed[i - 1][1] + root_midi) // 2 + 1

            if i == len(parsed) - 1:
                high = 127
            else:
                high = (root_midi + parsed[i + 1][1]) // 2

            zones.append(KeygroupZone(
                sample=samp,
                root_midi=root_midi,
                low_midi=low,
                high_midi=high,
            ))

        return cls(
            name=name,
            zones=zones,
            envelope=envelope,
            sample_rate=sr,
        )

    # ── Core: Generate a Note ─────────────────────────────────────

    def generate(
        self,
        note: Union[str, int],
        duration: Optional[float] = None,
        velocity: float = 1.0,
    ) -> Sample:
        """Generate a pitched sample for the given note.

        Parameters
        ----------
        note : str or int
            Target note as a name ('E4') or MIDI number (64).
        duration : float, optional
            Desired duration in seconds. If None, the natural resampled
            duration is used (shorter for higher notes, longer for lower).
            If specified, the output is trimmed or zero-padded, with
            the envelope's release applied at the end.
        velocity : float
            Amplitude multiplier (0.0 to 1.0).

        Returns
        -------
        Sample
            A new Sample containing the pitched audio.
        """
        if isinstance(note, str):
            target_midi = note_name_to_midi(note)
        else:
            target_midi = note

        target_midi = max(0, min(127, target_midi))

        # Find the best zone for this note
        zone = self._find_zone(target_midi)

        # Compute pitch ratio
        semitone_diff = target_midi - zone.root_midi
        ratio = 2.0 ** (semitone_diff / 12.0)

        # Resample
        source = zone.sample.audio
        resampled = self._resample(source, ratio)

        # Apply duration constraint
        if duration is not None:
            target_samples = int(duration * self.sample_rate)
            resampled = self._fit_duration(resampled, target_samples)

        # Apply envelope
        if self.envelope is not None:
            resampled = self.envelope.apply(resampled)
        elif duration is not None:
            # Minimal fade-out to avoid clicks (5ms or 5% of duration)
            resampled = self._apply_fade_out(resampled)

        # Apply velocity and zone volume
        if resampled.samples.size > 0:
            resampled = AudioData(
                samples=resampled.samples * velocity * zone.volume,
                sample_rate=resampled.sample_rate,
            )

        note_name = midi_to_note_name(target_midi)
        return Sample(
            name=f"{self.name}_{note_name}",
            audio=resampled,
        )

    # ── Convenience ───────────────────────────────────────────────

    def generate_chord(
        self,
        notes: List[Union[str, int]],
        duration: Optional[float] = None,
        velocity: float = 1.0,
    ) -> Sample:
        """Generate a chord by mixing multiple pitched samples.

        Parameters
        ----------
        notes : list of str or int
            Notes to layer.
        duration : float, optional
            Duration for each note.
        velocity : float
            Shared velocity.

        Returns
        -------
        Sample
        """
        if not notes:
            raise ValueError("Chord requires at least one note")

        audios = []
        max_len = 0
        for n in notes:
            s = self.generate(n, duration=duration, velocity=velocity)
            audios.append(s.audio.samples)
            max_len = max(max_len, len(s.audio.samples))

        # Pad to equal length and sum
        mixed = np.zeros(max_len, dtype=np.float64)
        for a in audios:
            mixed[:len(a)] += a

        # Normalize to avoid clipping
        peak = np.max(np.abs(mixed))
        if peak > 1.0:
            mixed /= peak

        return Sample(
            name=f"{self.name}_chord",
            audio=AudioData(samples=mixed, sample_rate=self.sample_rate),
        )

    def preview_range(
        self,
        low: Union[str, int] = 'C2',
        high: Union[str, int] = 'C6',
        step: int = 12,
        note_duration: float = 0.5,
        gap: float = 0.1,
    ) -> AudioData:
        """Generate a preview: ascending notes across a range.

        Useful for auditioning how the sample sounds at different pitches.

        Parameters
        ----------
        low, high : str or int
            Range boundaries.
        step : int
            Interval in semitones between preview notes.
        note_duration : float
            Duration of each note in seconds.
        gap : float
            Silence between notes in seconds.

        Returns
        -------
        AudioData
        """
        low_midi = note_name_to_midi(low) if isinstance(low, str) else low
        high_midi = note_name_to_midi(high) if isinstance(high, str) else high

        gap_samples = int(gap * self.sample_rate)
        gap_audio = np.zeros(gap_samples, dtype=np.float64)

        segments = []
        for midi in range(low_midi, high_midi + 1, step):
            s = self.generate(midi, duration=note_duration)
            segments.append(s.audio.samples)
            segments.append(gap_audio)

        if segments:
            segments.pop()  # remove trailing gap

        combined = np.concatenate(segments) if segments else np.zeros(1)
        return AudioData(samples=combined, sample_rate=self.sample_rate)

    # ── Internal ──────────────────────────────────────────────────

    def _find_zone(self, target_midi: int) -> KeygroupZone:
        """Find the zone whose range contains the target note.

        Falls back to the zone with the closest root if no range
        matches exactly.
        """
        # First: try to find a zone whose range includes the note
        for zone in self.zones:
            if zone.low_midi <= target_midi <= zone.high_midi:
                return zone

        # Fallback: closest root
        return min(self.zones, key=lambda z: abs(z.root_midi - target_midi))

    @staticmethod
    def _resample(audio: AudioData, ratio: float) -> AudioData:
        """Resample audio by a pitch ratio.

        ratio > 1.0 = higher pitch, shorter duration
        ratio < 1.0 = lower pitch, longer duration
        ratio == 1.0 = unchanged

        Uses linear interpolation for simplicity and speed.
        """
        if abs(ratio - 1.0) < 1e-6:
            return AudioData(
                samples=audio.samples.copy(),
                sample_rate=audio.sample_rate,
            )

        source = audio.samples
        n_source = len(source)

        # New length after resampling
        n_target = int(n_source / ratio)
        if n_target < 1:
            n_target = 1

        # Generate target indices mapped back to source positions
        target_indices = np.arange(n_target) * ratio

        # Linear interpolation
        source_indices = np.arange(n_source)
        resampled = np.interp(target_indices, source_indices, source)

        return AudioData(
            samples=resampled.astype(np.float64),
            sample_rate=audio.sample_rate,
        )

    @staticmethod
    def _fit_duration(audio: AudioData, target_samples: int) -> AudioData:
        """Trim or zero-pad audio to exactly target_samples length."""
        current = len(audio.samples)
        if current >= target_samples:
            return AudioData(
                samples=audio.samples[:target_samples].copy(),
                sample_rate=audio.sample_rate,
            )
        else:
            padded = np.zeros(target_samples, dtype=np.float64)
            padded[:current] = audio.samples
            return AudioData(samples=padded, sample_rate=audio.sample_rate)

    @staticmethod
    def _apply_fade_out(audio: AudioData, fade_ms: float = 5.0) -> AudioData:
        """Apply a short fade-out to prevent clicks at the end."""
        samples = audio.samples.copy()
        fade_len = min(
            int(fade_ms / 1000.0 * audio.sample_rate),
            len(samples) // 20,  # at most 5% of total length
        )
        if fade_len > 0:
            fade = np.linspace(1.0, 0.0, fade_len)
            samples[-fade_len:] *= fade
        return AudioData(samples=samples, sample_rate=audio.sample_rate)


# ═══════════════════════════════════════════════════════════════════
#  KeygroupTrackBuilder — Builder for the Song Builder Chain
# ═══════════════════════════════════════════════════════════════════


class KeygroupTrackBuilder:
    """Fluent builder for creating a track from a KeygroupProgram.

    Follows the same patterns as DrumTrackBuilder, BassTrackBuilder,
    and MelodyTrackBuilder — designed to be used inside the song
    builder chain via `.add_keygroup()`.

    Example::

        .add_keygroup("Piano", piano_program, lambda k: k
            .note('C4', beat=0, duration=1)
            .note('E4', beat=1, duration=0.5)
            .note('G4', beat=2, duration=0.5)
            .note('C5', beat=3, duration=2)
            .chord(['C4', 'E4', 'G4'], beat=4, duration=2)
            .phrase(my_phrase, start_beat=8)
            .line([('C4', 0, 1), ('E4', 1, 0.5), ('G4', 1.5, 0.5)])
            .volume(0.7)
            .pan(-0.1)
            .effect(Reverb(room_size=0.4, mix=0.3))
        )
    """

    def __init__(
        self,
        track: Track,
        song: 'SongBuilder',
        program: KeygroupProgram,
    ):
        self._track = track
        self._song = song
        self._program = program
        self._placements: List[Tuple[float, Sample]] = []

    # ── Note Placement ────────────────────────────────────────────

    def note(
        self,
        note: Union[str, int],
        beat: float,
        duration: float = 1.0,
        velocity: float = 1.0,
    ) -> 'KeygroupTrackBuilder':
        """Place a single note at a beat position.

        Parameters
        ----------
        note : str or int
            Note name ('C4') or MIDI number (60).
        beat : float
            Beat position (0-indexed from the start of the section/pattern).
        duration : float
            Duration in beats.
        velocity : float
            Note velocity (0.0 to 1.0).

        Returns
        -------
        self
        """
        beat_dur = 60.0 / self._song.bpm
        dur_seconds = duration * beat_dur
        time_seconds = beat * beat_dur

        sample = self._program.generate(note, duration=dur_seconds, velocity=velocity)
        self._track.add(sample, time_seconds)
        return self

    def chord(
        self,
        notes: List[Union[str, int]],
        beat: float,
        duration: float = 1.0,
        velocity: float = 1.0,
    ) -> 'KeygroupTrackBuilder':
        """Place a chord (multiple notes layered) at a beat position.

        Parameters
        ----------
        notes : list of str or int
            Notes to play simultaneously.
        beat : float
            Beat position.
        duration : float
            Duration in beats.
        velocity : float
            Velocity for all notes in the chord.

        Returns
        -------
        self
        """
        beat_dur = 60.0 / self._song.bpm
        dur_seconds = duration * beat_dur
        time_seconds = beat * beat_dur

        chord_sample = self._program.generate_chord(
            notes, duration=dur_seconds, velocity=velocity
        )
        self._track.add(chord_sample, time_seconds)
        return self

    def line(
        self,
        notes: List[Tuple[Union[str, int], float, float]],
        velocity: float = 1.0,
    ) -> 'KeygroupTrackBuilder':
        """Place a sequence of notes from a list of tuples.

        Mirrors the BassTrackBuilder.line() pattern.

        Parameters
        ----------
        notes : list of (note, beat, duration) tuples
            Each entry is (note_name_or_midi, beat_position, duration_beats).
        velocity : float
            Default velocity for all notes.

        Returns
        -------
        self
        """
        for entry in notes:
            if len(entry) == 3:
                n, b, d = entry
                v = velocity
            elif len(entry) == 4:
                n, b, d, v = entry
            else:
                raise ValueError(
                    f"Expected (note, beat, duration) or "
                    f"(note, beat, duration, velocity), got {entry!r}"
                )
            self.note(n, beat=b, duration=d, velocity=v)
        return self

    def phrase(
        self,
        phrase: 'Phrase',
        start_beat: float = 0.0,
        velocity_scale: float = 1.0,
    ) -> 'KeygroupTrackBuilder':
        """Place a Phrase (from beatmaker.melody) using the keygroup sound.

        Each note in the phrase is rendered through the KeygroupProgram.
        Rests are honored as silence.

        Parameters
        ----------
        phrase : Phrase
            A melodic phrase to render.
        start_beat : float
            Beat offset for the phrase.
        velocity_scale : float
            Multiplier applied to each note's velocity.

        Returns
        -------
        self
        """
        events = phrase.to_events(start_beat=start_beat)
        for beat, midi_note, vel, dur in events:
            self.note(
                midi_note,
                beat=beat,
                duration=dur,
                velocity=min(1.0, vel * velocity_scale),
            )
        return self

    def melody(
        self,
        melody: 'Melody',
        velocity_scale: float = 1.0,
    ) -> 'KeygroupTrackBuilder':
        """Render a full Melody object through the keygroup.

        Parameters
        ----------
        melody : Melody
            A Melody containing placed phrases.
        velocity_scale : float
            Multiplier for all velocities.

        Returns
        -------
        self
        """
        events = melody.to_events()
        for beat, midi_note, vel, dur in events:
            self.note(
                midi_note,
                beat=beat,
                duration=dur,
                velocity=min(1.0, vel * velocity_scale),
            )
        return self

    def arp_events(
        self,
        events: List[Tuple[float, int, float, float]],
    ) -> 'KeygroupTrackBuilder':
        """Render arpeggiator events through the keygroup.

        Parameters
        ----------
        events : list of (beat, midi_note, velocity, duration) tuples
            As produced by Arpeggiator.generate_from_chord() etc.

        Returns
        -------
        self
        """
        for beat, midi_note, vel, dur in events:
            self.note(midi_note, beat=beat, duration=dur, velocity=vel)
        return self

    # ── Track Configuration ───────────────────────────────────────

    def volume(self, level: float) -> 'KeygroupTrackBuilder':
        """Set the track volume.

        Parameters
        ----------
        level : float
            Volume level (0.0 to 1.0).
        """
        self._track.volume = level
        return self

    def pan(self, value: float) -> 'KeygroupTrackBuilder':
        """Set the track pan position.

        Parameters
        ----------
        value : float
            Pan position (-1.0 = full left, 0.0 = center, 1.0 = full right).
        """
        self._track.pan = value
        return self

    def effect(self, effect: AudioEffect) -> 'KeygroupTrackBuilder':
        """Add an effect to the track's effect chain.

        Parameters
        ----------
        effect : AudioEffect
            Any beatmaker effect (Reverb, Delay, Compressor, etc.).
        """
        self._track.add_effect(effect)
        return self

    def humanize(
        self,
        timing: float = 0.01,
        velocity: float = 0.1,
        seed: Optional[int] = None,
    ) -> 'KeygroupTrackBuilder':
        """Apply humanization to the track.

        Parameters
        ----------
        timing : float
            Maximum timing jitter in seconds.
        velocity : float
            Maximum velocity variation.
        seed : int, optional
            Random seed for reproducibility.
        """
        from beatmaker.expression import Humanizer
        h = Humanizer(timing_jitter=timing, velocity_variation=velocity, seed=seed)
        h.apply_to_track(self._track)
        return self

    def groove(self, template: 'GrooveTemplate') -> 'KeygroupTrackBuilder':
        """Apply a groove template to the track.

        Parameters
        ----------
        template : GrooveTemplate
            Groove template to apply.
        """
        template.apply_to_track(self._track, bpm=self._song.bpm)
        return self

    def automate_volume(self, curve: 'AutomationCurve') -> 'KeygroupTrackBuilder':
        """Apply volume automation to the track.

        Parameters
        ----------
        curve : AutomationCurve
            Automation curve for volume.
        """
        from beatmaker.automation import AutomatedGain
        self._track.add_effect(AutomatedGain(curve, self._song.bpm))
        return self

    def automate_filter(
        self,
        curve: 'AutomationCurve',
        filter_type: str = 'lowpass',
    ) -> 'KeygroupTrackBuilder':
        """Apply filter automation to the track.

        Parameters
        ----------
        curve : AutomationCurve
            Automation curve for filter cutoff frequency.
        filter_type : str
            Filter type ('lowpass' or 'highpass').
        """
        from beatmaker.automation import AutomatedFilter
        self._track.add_effect(
            AutomatedFilter(curve, self._song.bpm, filter_type=filter_type)
        )
        return self


# ═══════════════════════════════════════════════════════════════════
#  SongBuilder Integration
# ═══════════════════════════════════════════════════════════════════
#
#  To integrate with the existing builder chain, add this method
#  to the SongBuilder class (in beatmaker/builder.py):
#
#      def add_keygroup(
#          self,
#          name: str,
#          program: KeygroupProgram,
#          builder_fn: Callable[[KeygroupTrackBuilder], KeygroupTrackBuilder],
#      ) -> 'SongBuilder':
#          """Add a keygroup-based track to the song.
#
#          Parameters
#          ----------
#          name : str
#              Track name.
#          program : KeygroupProgram
#              The keygroup instrument to use.
#          builder_fn : callable
#              A function that receives a KeygroupTrackBuilder and
#              configures it (placing notes, setting effects, etc.).
#
#          Returns
#          -------
#          self
#          """
#          from beatmaker.keygroup import KeygroupTrackBuilder
#          track = Track(name=name, track_type=TrackType.LEAD)
#          builder = KeygroupTrackBuilder(track, self, program)
#          builder_fn(builder)
#          self._tracks.append(track)
#          return self
#
#  And for the SectionBuilder (used by create_song().section()):
#
#      def add_keygroup(
#          self,
#          name: str,
#          program: KeygroupProgram,
#          builder_fn: Callable[[KeygroupTrackBuilder], KeygroupTrackBuilder],
#      ) -> 'SectionBuilder':
#          from beatmaker.keygroup import KeygroupTrackBuilder
#          track = Track(name=name, track_type=TrackType.LEAD)
#          builder = KeygroupTrackBuilder(track, self._song_builder, program)
#          builder_fn(builder)
#          self._section.add_track(track)
#          return self
#
#  Then export from beatmaker/__init__.py:
#
#      from beatmaker.keygroup import KeygroupProgram, KeygroupTrackBuilder
