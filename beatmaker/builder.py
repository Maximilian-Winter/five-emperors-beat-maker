"""
靈寶五帝策使編碼之法 - Song Builder Module
The fluent interface through which compositions manifest.

By the Azure Dragon's authority,
Let this structure grow strong and flexible,
Roots deep, branches reaching,
急急如律令敕

This module provides a builder pattern for constructing beats and songs
with a clean, chainable API.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Union, Callable, TypeVar
import numpy as np
from tqdm import tqdm

from .core import (
    AudioData, Sample, Track, TrackType,
    TimeSignature, SamplePlacement, AudioEffect
)
from .effects import EffectChain, Limiter, Compressor
from .io import save_audio, load_audio
from .automation import AutomationCurve


@dataclass
class Song:
    """
    A complete song composition.
    
    Contains multiple tracks, global settings, and mixing parameters.
    """
    name: str = "Untitled"
    bpm: float = 120.0
    time_signature: TimeSignature = field(default_factory=TimeSignature)
    sample_rate: int = 44100
    tracks: List[Track] = field(default_factory=list)
    master_effects: List[AudioEffect] = field(default_factory=list)
    
    def add_track(self, track: Track) -> 'Song':
        """Add a track to the song."""
        self.tracks.append(track)
        return self
    
    def get_track(self, name: str) -> Optional[Track]:
        """Get a track by name."""
        for track in self.tracks:
            if track.name == name:
                return track
        return None
    
    @property
    def duration(self) -> float:
        """Total duration of the song in seconds."""
        if not self.tracks:
            return 0.0
        return max(t.duration for t in self.tracks)
    
    @property
    def duration_bars(self) -> float:
        """Duration in bars at current tempo."""
        seconds_per_bar = self.time_signature.bars_to_seconds(1, self.bpm)
        return self.duration / seconds_per_bar if seconds_per_bar > 0 else 0
    
    def beat_to_seconds(self, beat: float) -> float:
        """Convert beat number to seconds."""
        return self.time_signature.beats_to_seconds(beat, self.bpm)
    
    def bar_to_seconds(self, bar: float) -> float:
        """Convert bar number to seconds."""
        return self.time_signature.bars_to_seconds(bar, self.bpm)
    
    def render(self, channels: int = 2) -> AudioData:
        """Render the entire song to audio."""
        if not self.tracks:
            return AudioData.silence(0.0, self.sample_rate, channels)
        
        duration = self.duration
        num_samples = int(duration * self.sample_rate) + self.sample_rate
        
        if channels == 1:
            output = np.zeros(num_samples)
        else:
            output = np.zeros((num_samples, channels))
        
        # Check for solo tracks
        has_solo = any(t.solo for t in self.tracks)
        progress = tqdm(self.tracks)
        for track in progress:
            # Skip muted tracks, or non-solo tracks if any track is soloed
            if track.muted:
                continue
            if has_solo and not track.solo:
                continue
            
            rendered = track.render(self.sample_rate, channels, self.bpm)
            track_length = len(rendered.samples)
            
            if track_length > 0:
                # Ensure we don't exceed output buffer
                copy_length = min(track_length, num_samples)
                output[:copy_length] += rendered.samples[:copy_length]
        
        # Apply master effects
        result = AudioData(output, self.sample_rate, channels)
        for effect in self.master_effects:
            result = effect.process(result)
        
        return result
    
    def export(self, path: Union[str, Path], format: Optional[str] = None) -> Path:
        """Export the song to a file."""
        path = Path(path)
        audio = self.render()
        save_audio(audio, path, format)
        return path


class SongBuilder:
    """
    Fluent builder for creating songs.

    Example:
        song = (SongBuilder("My Beat")
            .tempo(128)
            .time_signature(4, 4)
            .samples(lib)  # optional: attach a SampleLibrary
            .add_drums(lambda drums: drums
                .kick(beats=[0, 2])
                .snare(beats=[1, 3])
                .hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
            )
            .add_bass(lambda bass: bass
                .note('E2', beat=0, duration=1)
                .note('G2', beat=2, duration=1)
            )
            .build())
    """

    def __init__(self, name: str = "Untitled"):
        self._song = Song(name=name)
        self._current_bar_length: int = 4  # Default 4 bars
        self._library = None  # Optional[SampleLibrary]
    
    def tempo(self, bpm: float) -> 'SongBuilder':
        """Set the song tempo in BPM."""
        self._song.bpm = bpm
        return self
    
    def time_signature(self, beats_per_bar: int = 4, 
                       beat_value: int = 4) -> 'SongBuilder':
        """Set the time signature."""
        self._song.time_signature = TimeSignature(beats_per_bar, beat_value)
        return self
    
    def sample_rate(self, rate: int) -> 'SongBuilder':
        """Set the sample rate."""
        self._song.sample_rate = rate
        return self
    
    def bars(self, num_bars: int) -> 'SongBuilder':
        """Set the default pattern length in bars."""
        self._current_bar_length = num_bars
        return self

    def samples(self, library) -> 'SongBuilder':
        """
        Attach a SampleLibrary to the song builder.

        When a library is attached, all track builders gain access to it,
        enabling sample lookup by key or alias::

            lib = SampleLibrary.from_directory("./my_samples")
            song = (create_song("Demo")
                .samples(lib)
                .add_drums(lambda d: d
                    .use_kit_from("drums/808")
                    .four_on_floor()
                )
                .build())
        """
        self._library = library
        return self

    def add_track(self, name: str, track_type: TrackType = TrackType.DRUMS,
                  builder: Optional[Callable[['TrackBuilder'], 'TrackBuilder']] = None
                  ) -> 'SongBuilder':
        """Add a generic track with optional builder configuration."""
        track = Track(name=name, track_type=track_type)
        if builder:
            track_builder = TrackBuilder(track, self._song, library=self._library)
            builder(track_builder)
        self._song.add_track(track)
        return self

    def add_drums(self, builder: Callable[['DrumTrackBuilder'], 'DrumTrackBuilder']
                  ) -> 'SongBuilder':
        """Add a drum track using the drum builder."""
        track = Track(name="Drums", track_type=TrackType.DRUMS)
        drum_builder = DrumTrackBuilder(
            track, self._song, self._current_bar_length, library=self._library)
        builder(drum_builder)
        self._song.add_track(track)
        return self

    def add_bass(self, builder: Callable[['BassTrackBuilder'], 'BassTrackBuilder']
                 ) -> 'SongBuilder':
        """Add a bass track using the bass builder."""
        track = Track(name="Bass", track_type=TrackType.BASS)
        bass_builder = BassTrackBuilder(
            track, self._song, self._current_bar_length, library=self._library)
        builder(bass_builder)
        self._song.add_track(track)
        return self

    def add_keygroup(
        self,
        name: str,
        program: 'KeygroupProgram',
        builder_fn: Callable[['KeygroupTrackBuilder'], 'KeygroupTrackBuilder'],
    ) -> 'SongBuilder':
        """Add a keygroup-based track to the song.

        Parameters
        ----------
        name : str
            Track name (e.g. "Sampled Piano", "Pad Layer").
        program : KeygroupProgram
            The keygroup instrument to use as the sound source.
        builder_fn : callable
            A lambda/function that receives a KeygroupTrackBuilder
            and configures it by placing notes, phrases, effects, etc.

        Returns
        -------
        self
        """
        from beatmaker.keygroup import KeygroupTrackBuilder

        track = Track(name=name, track_type=TrackType.LEAD)
        builder = KeygroupTrackBuilder(track, self._song, program)
        builder_fn(builder)
        self._song.add_track(track)
        return self
    
    def add_vocal(self, path: Union[str, Path], 
                  start_bar: float = 0,
                  volume: float = 1.0) -> 'SongBuilder':
        """Add a vocal track from a file."""
        audio = load_audio(Path(path))
        sample = Sample(name="vocal", audio=audio, tags=["vocal"])
        
        track = Track(name="Vocals", track_type=TrackType.VOCAL, volume=volume)
        start_time = self._song.bar_to_seconds(start_bar)
        track.add(sample, start_time)
        
        self._song.add_track(track)
        return self
    
    def add_backing_track(self, path: Union[str, Path],
                          start_bar: float = 0,
                          volume: float = 0.8) -> 'SongBuilder':
        """Add a backing track from a file."""
        audio = load_audio(Path(path))
        sample = Sample(name="backing", audio=audio, tags=["backing"])
        
        track = Track(name="Backing", track_type=TrackType.BACKING, volume=volume)
        start_time = self._song.bar_to_seconds(start_bar)
        track.add(sample, start_time)
        
        self._song.add_track(track)
        return self
    
    def add_sample_track(self, name: str, 
                         samples: List[tuple],  # [(sample, beat), ...]
                         track_type: TrackType = TrackType.FX
                         ) -> 'SongBuilder':
        """Add a track with pre-defined sample placements."""
        track = Track(name=name, track_type=track_type)
        
        for item in samples:
            if len(item) == 2:
                sample, beat = item
                velocity = 1.0
            else:
                sample, beat, velocity = item
            
            time = self._song.beat_to_seconds(beat)
            track.add(sample, time, velocity)
        
        self._song.add_track(track)
        return self
    
    def master_effect(self, effect: AudioEffect) -> 'SongBuilder':
        """Add an effect to the master bus."""
        self._song.master_effects.append(effect)
        return self
    
    def master_limiter(self, threshold: float = 0.95) -> 'SongBuilder':
        """Add a limiter to the master bus."""
        return self.master_effect(Limiter(threshold))
    
    def master_compressor(self, threshold: float = -10.0,
                          ratio: float = 4.0) -> 'SongBuilder':
        """Add a compressor to the master bus."""
        return self.master_effect(Compressor(threshold=threshold, ratio=ratio))
    
    def add_melody(self, builder: Callable[['MelodyTrackBuilder'], 'MelodyTrackBuilder'],
                   name: str = "Melody",
                   synth_type: str = 'saw') -> 'SongBuilder':
        """
        Add a melodic track using Phrase-based composition.

        Example:
            .add_melody(lambda m: m
                .synth('saw')
                .phrase(motif, start_beat=0)
                .phrase(motif.transpose(5), start_beat=4)
                .volume(0.7)
            )
        """
        track = Track(name=name, track_type=TrackType.LEAD)
        melody_builder = MelodyTrackBuilder(
            track, self._song, self._current_bar_length, synth_type,
            library=self._library)
        builder(melody_builder)
        melody_builder.render_melody()
        self._song.add_track(track)
        return self

    def add_harmony(self, builder: Callable[['HarmonyTrackBuilder'], 'HarmonyTrackBuilder'],
                    name: str = "Harmony",
                    synth_type: str = 'saw') -> 'SongBuilder':
        """
        Add a harmony/chord track using chord progressions.

        Example:
            .add_harmony(lambda h: h
                .key("C", "major")
                .progression("I - V - vi - IV", beats_per_chord=4)
                .voice_lead()
                .volume(0.5)
            , synth_type='warm_pad')
        """
        track = Track(name=name, track_type=TrackType.PAD)
        harmony_builder = HarmonyTrackBuilder(
            track, self._song, self._current_bar_length, synth_type,
            library=self._library)
        builder(harmony_builder)
        harmony_builder.render_harmony()
        self._song.add_track(track)
        return self

    def section(self, name: str, bars: int) -> 'SectionBuilder':
        """
        Create a SectionBuilder for building reusable song sections.

        Example:
            verse = song_builder.section("verse", bars=8).add_drums(...).build()
        """
        return SectionBuilder(name, bars, self._song, library=self._library)

    def arrange(self, arrangement) -> 'SongBuilder':
        """
        Apply an Arrangement to the song.

        Places all section tracks onto the song timeline.
        """
        arrangement.render_to_song(self._song)
        return self

    def add_graph_track(self, name: str, graph, duration: float,
                        track_type=None) -> 'SongBuilder':
        """
        Render a signal graph and add it as a track.

        Args:
            name: Track name.
            graph: A SignalGraph instance to render.
            duration: Duration in seconds.
            track_type: TrackType (default: FX).

        Returns:
            self for chaining.
        """
        from .graph import SignalGraph
        if track_type is None:
            track_type = TrackType.FX
        audio = graph.render(duration, self._song.sample_rate)
        sample = Sample(name, audio)
        track = Track(name=name, track_type=track_type)
        track.add(sample, 0.0)
        self._song.tracks.append(track)
        return self

    def add_spc700(self, engine, builder,
                   name: str = "SPC700",
                   track_type=None,
                   volume: float = 1.0) -> 'SongBuilder':
        """
        Compose and render tracks through the SPC700 DSP, then add the
        resulting audio as a song track.

        The builder callback receives an SPC700SongBuilder and should
        compose tracks using the SPC700's event API (.note(), .rest(),
        .vibrato(), etc.). The result is rendered through the DSP and
        mixed alongside normal beatmaker tracks.

        Args:
            engine:     SPC700Engine with registered sounds.
            builder:    Callback receiving SPC700SongBuilder for composition.
            name:       Track name in the final mix.
            track_type: TrackType (default: BACKING).
            volume:     Track volume multiplier (0.0-1.0).

        Example::

            engine = SPC700Engine(echo=EchoConfig.reverb())
            engine.sound("kick", SPC700Sound.drum("kick.wav"))
            engine.sound("lead", SPC700Sound.synth("AKWF_saw.wav"))

            song = (create_song("SNES Style")
                .tempo(120)
                .add_spc700(engine, lambda s: s
                    .track("kick", lambda t: t
                        .note(duration=0.25).rest(0.75).repeat(7))
                    .track("lead", lambda t: t
                        .note("C4", 2.0).note("E4", 2.0))
                )
                .build())
        """
        from .spc import SPC700SongBuilder
        if track_type is None:
            track_type = TrackType.BACKING

        # Build the SPC700 composition
        spc_builder = SPC700SongBuilder(engine, self._song.bpm)
        builder(spc_builder)

        # Render through the DSP
        audio = spc_builder.render(
            sample_rate=self._song.sample_rate, tail=2.0)

        # Add as a regular track
        sample = Sample(name, audio)
        track = Track(name=name, track_type=track_type, volume=volume)
        track.add(sample, 0.0)
        self._song.tracks.append(track)
        return self

    def master_spc700_echo(self, delay: int = 4, feedback: int = 60,
                           volume: int = 50,
                           fir=None) -> 'SongBuilder':
        """
        Add SPC700 echo/reverb as a master effect.

        Applies the SNES S-DSP's legendary 8-tap FIR echo to the entire
        master bus, imparting that distinctive spatial character.

        Args:
            delay:    Echo delay 0-15 (each unit = 16ms).
            feedback: Echo feedback -128 to 127.
            volume:   Echo wet volume 0-127.
            fir:      8-tap FIR coefficients (default: identity).
        """
        from .spc import SPC700Echo
        if fir is None:
            fir = (127, 0, 0, 0, 0, 0, 0, 0)
        return self.master_effect(SPC700Echo(delay, feedback, volume, fir))

    def build(self) -> Song:
        """Build and return the completed song."""
        return self._song


_TB = TypeVar('_TB', bound='TrackBuilder')


class TrackBuilder:
    """Base builder for track construction."""

    def __init__(self, track: Track, song: Song, library=None):
        self._track = track
        self._song = song
        self._library = library  # Optional[SampleLibrary]

    def volume(self: _TB, level: float) -> _TB:
        """Set track volume (0.0 - 1.0)."""
        self._track.volume = level
        return self

    def pan(self: _TB, value: float) -> _TB:
        """Set track pan (-1.0 left to 1.0 right)."""
        self._track.pan = value
        return self

    def mute(self: _TB) -> _TB:
        """Mute the track."""
        self._track.muted = True
        return self

    def solo(self: _TB) -> _TB:
        """Solo the track."""
        self._track.solo = True
        return self

    def effect(self: _TB, effect: AudioEffect) -> _TB:
        """Add an effect to the track."""
        self._track.add_effect(effect)
        return self

    def add(self: _TB, sample: Sample, beat: float,
            velocity: float = 1.0, pan: float = 0.0) -> _TB:
        """Add a sample at a specific beat."""
        time = self._song.beat_to_seconds(beat)
        self._track.add(sample, time, velocity, pan)
        return self

    def add_at_bar(self: _TB, sample: Sample, bar: float,
                   velocity: float = 1.0, pan: float = 0.0) -> _TB:
        """Add a sample at a specific bar."""
        time = self._song.bar_to_seconds(bar)
        self._track.add(sample, time, velocity, pan)
        return self

    def sample(self: _TB, key: str, beat: float,
               velocity: float = 1.0, pan: float = 0.0) -> _TB:
        """
        Place a sample from the attached library at a beat position.

        Args:
            key:      Library key, alias, or stem name.
            beat:     Beat position to place the sample.
            velocity: Volume multiplier (0.0-1.0).
            pan:      Stereo position (-1.0 left to 1.0 right).

        Raises:
            RuntimeError: If no library is attached.
            KeyError: If the key is not found in the library.

        Example::

            .add_track("FX", TrackType.FX, lambda t: t
                .sample("fx/riser", beat=0)
                .sample("fx/impact", beat=16)
            )
        """
        if self._library is None:
            raise RuntimeError(
                "No SampleLibrary attached. Use .samples(lib) on the "
                "SongBuilder before using .sample() lookups."
            )
        s = self._library[key]
        return self.add(s, beat, velocity, pan)

    def humanize(self: _TB, timing: float = 0.01, velocity: float = 0.1,
                 seed: Optional[int] = None) -> _TB:
        """Apply humanization (timing jitter + velocity variation) to all placements."""
        from .expression import Humanizer
        Humanizer(timing_jitter=timing, velocity_variation=velocity,
                  seed=seed).apply_to_track(self._track)
        return self

    def groove(self: _TB, template) -> _TB:
        """Apply a groove template to all placements."""
        template.apply_to_track(self._track, self._song.bpm)
        return self

    def automate_volume(self: _TB, curve: AutomationCurve) -> _TB:
        """Attach a volume automation curve to this track."""
        if not hasattr(self._track, 'volume_automation'):
            self._track.volume_automation = None
        self._track.volume_automation = curve
        return self

    def automate_pan(self: _TB, curve: AutomationCurve) -> _TB:
        """Attach a pan automation curve to this track."""
        if not hasattr(self._track, 'pan_automation'):
            self._track.pan_automation = None
        self._track.pan_automation = curve
        return self


class DrumTrackBuilder(TrackBuilder):
    """
    Specialized builder for drum tracks.

    Provides convenient methods for common drum patterns.
    """

    # Conventional name fragments for auto-detecting kit pieces
    _KICK_NAMES = ('kick', 'bd', 'bass_drum', 'bassdrum')
    _SNARE_NAMES = ('snare', 'sd', 'snr')
    _HIHAT_NAMES = ('hihat', 'hat', 'hh', 'hi_hat')
    _CLAP_NAMES = ('clap', 'cp', 'handclap')

    def __init__(self, track: Track, song: Song, pattern_bars: int = 4,
                 library=None):
        super().__init__(track, song, library=library)
        self._pattern_bars = pattern_bars
        self._kick_sample: Optional[Sample] = None
        self._snare_sample: Optional[Sample] = None
        self._hihat_sample: Optional[Sample] = None
        self._clap_sample: Optional[Sample] = None

    def use_kit(self, kick: Sample, snare: Sample,
                hihat: Sample, clap: Optional[Sample] = None) -> 'DrumTrackBuilder':
        """Set the drum samples to use."""
        self._kick_sample = kick
        self._snare_sample = snare
        self._hihat_sample = hihat
        self._clap_sample = clap
        return self

    def use_sample(self, role: str, key: str) -> 'DrumTrackBuilder':
        """
        Assign a library sample to a drum role.

        Args:
            role: One of 'kick', 'snare', 'hihat', 'clap'.
            key:  Library key, alias, or stem name.

        Example::

            .use_sample("kick", "drums/808/kick_heavy")
            .use_sample("snare", "drums/vinyl/snare_03")
        """
        if self._library is None:
            raise RuntimeError(
                "No SampleLibrary attached. Use .samples(lib) on the "
                "SongBuilder before using .use_sample()."
            )
        s = self._library[key]
        role = role.lower()
        if role == 'kick':
            self._kick_sample = s
        elif role == 'snare':
            self._snare_sample = s
        elif role in ('hihat', 'hat', 'hh'):
            self._hihat_sample = s
        elif role in ('clap', 'cp'):
            self._clap_sample = s
        else:
            raise ValueError(f"Unknown drum role: '{role}'. "
                             f"Use 'kick', 'snare', 'hihat', or 'clap'.")
        return self

    def use_kit_from(self, prefix: str) -> 'DrumTrackBuilder':
        """
        Auto-detect and assign drum samples from a library prefix.

        Searches the library under the given prefix for samples whose
        names contain common drum terms (kick, snare, hat, clap).

        Args:
            prefix: Library path prefix (e.g. ``"drums/808"``).

        Example::

            .add_drums(lambda d: d
                .use_kit_from("drums/acoustic")
                .four_on_floor()
                .backbeat()
            )
        """
        if self._library is None:
            raise RuntimeError(
                "No SampleLibrary attached. Use .samples(lib) on the "
                "SongBuilder before using .use_kit_from()."
            )
        keys = self._library.list(prefix)

        def _find(names):
            for k in keys:
                stem = k.rsplit('/', 1)[-1].lower()
                for n in names:
                    if n in stem:
                        return self._library[k]
            return None

        found_kick = _find(self._KICK_NAMES)
        if found_kick:
            self._kick_sample = found_kick
        found_snare = _find(self._SNARE_NAMES)
        if found_snare:
            self._snare_sample = found_snare
        found_hihat = _find(self._HIHAT_NAMES)
        if found_hihat:
            self._hihat_sample = found_hihat
        found_clap = _find(self._CLAP_NAMES)
        if found_clap:
            self._clap_sample = found_clap

        return self
    
    def _get_or_create_kick(self) -> Sample:
        if self._kick_sample is None:
            from .synth import DrumSynth
            self._kick_sample = DrumSynth.kick()
        return self._kick_sample
    
    def _get_or_create_snare(self) -> Sample:
        if self._snare_sample is None:
            from .synth import DrumSynth
            self._snare_sample = DrumSynth.snare()
        return self._snare_sample
    
    def _get_or_create_hihat(self) -> Sample:
        if self._hihat_sample is None:
            from .synth import DrumSynth
            self._hihat_sample = DrumSynth.hihat()
        return self._hihat_sample
    
    def _get_or_create_clap(self) -> Sample:
        if self._clap_sample is None:
            from .synth import DrumSynth
            self._clap_sample = DrumSynth.clap()
        return self._clap_sample
    
    def kick(self, beats: Optional[List[float]] = None,
             pattern: Optional[List[bool]] = None,
             velocity: float = 1.0) -> 'DrumTrackBuilder':
        """
        Add kick drum hits.
        
        Args:
            beats: List of beat positions (e.g., [0, 2] for beats 1 and 3)
            pattern: 16-step pattern as boolean list
            velocity: Hit velocity
        """
        sample = self._get_or_create_kick()
        
        if beats is not None:
            # Repeat for pattern length
            beats_per_bar = self._song.time_signature.beats_per_bar
            total_beats = self._pattern_bars * beats_per_bar
            
            for bar in range(self._pattern_bars):
                for beat in beats:
                    actual_beat = bar * beats_per_bar + beat
                    if actual_beat < total_beats:
                        self.add(sample, actual_beat, velocity)
        
        elif pattern is not None:
            step_duration = self._song.beat_to_seconds(0.25)  # 16th notes
            for i, hit in enumerate(pattern):
                if hit:
                    beat = i * 0.25
                    self.add(sample, beat, velocity)
        
        return self
    
    def snare(self, beats: Optional[List[float]] = None,
              pattern: Optional[List[bool]] = None,
              velocity: float = 1.0) -> 'DrumTrackBuilder':
        """Add snare drum hits."""
        sample = self._get_or_create_snare()
        
        if beats is not None:
            beats_per_bar = self._song.time_signature.beats_per_bar
            
            for bar in range(self._pattern_bars):
                for beat in beats:
                    actual_beat = bar * beats_per_bar + beat
                    self.add(sample, actual_beat, velocity)
        
        elif pattern is not None:
            for i, hit in enumerate(pattern):
                if hit:
                    beat = i * 0.25
                    self.add(sample, beat, velocity)
        
        return self
    
    def hihat(self, beats: Optional[List[float]] = None,
              pattern: Optional[List[bool]] = None,
              velocity: float = 0.7,
              open_beats: Optional[List[float]] = None) -> 'DrumTrackBuilder':
        """Add hi-hat hits."""
        sample = self._get_or_create_hihat()
        
        if beats is not None:
            beats_per_bar = self._song.time_signature.beats_per_bar
            open_beats_set = set(open_beats or [])
            
            for bar in range(self._pattern_bars):
                for beat in beats:
                    actual_beat = bar * beats_per_bar + beat
                    
                    # Use open hi-hat if specified
                    if beat in open_beats_set:
                        from .synth import DrumSynth
                        open_sample = DrumSynth.hihat(open_amount=0.8)
                        self.add(open_sample, actual_beat, velocity)
                    else:
                        self.add(sample, actual_beat, velocity)
        
        elif pattern is not None:
            for i, hit in enumerate(pattern):
                if hit:
                    beat = i * 0.25
                    self.add(sample, beat, velocity)
        
        return self
    
    def clap(self, beats: Optional[List[float]] = None,
             velocity: float = 0.9) -> 'DrumTrackBuilder':
        """Add clap hits."""
        sample = self._get_or_create_clap()
        
        if beats is not None:
            beats_per_bar = self._song.time_signature.beats_per_bar
            
            for bar in range(self._pattern_bars):
                for beat in beats:
                    actual_beat = bar * beats_per_bar + beat
                    self.add(sample, actual_beat, velocity)
        
        return self
    
    def four_on_floor(self, velocity: float = 1.0) -> 'DrumTrackBuilder':
        """Classic four-on-the-floor kick pattern."""
        return self.kick(beats=[0, 1, 2, 3], velocity=velocity)
    
    def backbeat(self, velocity: float = 1.0) -> 'DrumTrackBuilder':
        """Classic backbeat snare on 2 and 4."""
        return self.snare(beats=[1, 3], velocity=velocity)
    
    def eighth_hats(self, velocity: float = 0.7) -> 'DrumTrackBuilder':
        """Eighth note hi-hats."""
        return self.hihat(beats=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], velocity=velocity)
    
    def sixteenth_hats(self, velocity: float = 0.6) -> 'DrumTrackBuilder':
        """Sixteenth note hi-hats."""
        beats = [i * 0.25 for i in range(16)]
        return self.hihat(beats=beats, velocity=velocity)


class BassTrackBuilder(TrackBuilder):
    """
    Specialized builder for bass tracks.
    """

    def __init__(self, track: Track, song: Song, pattern_bars: int = 4,
                 library=None):
        super().__init__(track, song, library=library)
        self._pattern_bars = pattern_bars
    
    def note(self, note: str, beat: float, duration: float = 1.0,
             velocity: float = 1.0) -> 'BassTrackBuilder':
        """
        Add a bass note.
        
        Args:
            note: Note name (e.g., 'E2', 'G2', 'A1')
            beat: Beat position
            duration: Note duration in beats
            velocity: Note velocity
        """
        from .synth import BassSynth, note_to_freq
        
        freq = note_to_freq(note)
        duration_sec = self._song.beat_to_seconds(duration)
        sample = BassSynth.sub_bass(freq, duration_sec)
        
        self.add(sample, beat, velocity)
        return self
    
    def acid_note(self, note: str, beat: float, duration: float = 0.5,
                  velocity: float = 1.0) -> 'BassTrackBuilder':
        """Add an acid bass note."""
        from .synth import BassSynth, note_to_freq
        
        freq = note_to_freq(note)
        duration_sec = self._song.beat_to_seconds(duration)
        sample = BassSynth.acid_bass(freq, duration_sec)
        
        self.add(sample, beat, velocity)
        return self
    
    def line(self, notes: List[tuple]) -> 'BassTrackBuilder':
        """
        Add a bass line from a list of (note, beat, duration) tuples.
        
        Example:
            bass.line([
                ('E2', 0, 1),
                ('G2', 1, 0.5),
                ('A2', 1.5, 0.5),
                ('E2', 2, 2)
            ])
        """
        for item in notes:
            if len(item) == 2:
                note, beat = item
                duration = 1.0
            else:
                note, beat, duration = item
            self.note(note, beat, duration)
        
        return self
    
    def octave_pattern(self, root: str, beats: List[float],
                       duration: float = 0.5) -> 'BassTrackBuilder':
        """Play root note alternating with octave above."""
        from .synth import note_to_freq

        root_freq = note_to_freq(root)

        for i, beat in enumerate(beats):
            if i % 2 == 0:
                self.note(root, beat, duration)
            else:
                # Octave up - create note manually
                octave_note = root[:-1] + str(int(root[-1]) + 1)
                self.note(octave_note, beat, duration)

        return self

    def sample_note(self, key: str, beat: float, duration: float = 1.0,
                    velocity: float = 1.0,
                    transpose: float = 0.0) -> 'BassTrackBuilder':
        """
        Place a bass sample from the library, with optional pitch shift.

        Args:
            key:       Library key for the bass sample.
            beat:      Beat position.
            duration:  Duration in beats (used to trim the sample).
            velocity:  Volume multiplier.
            transpose: Semitones to pitch-shift (0 = original pitch).

        Example::

            .add_bass(lambda b: b
                .sample_note("bass/sub_C2", beat=0, duration=2)
                .sample_note("bass/sub_C2", beat=2, transpose=5)
            )
        """
        if self._library is None:
            raise RuntimeError(
                "No SampleLibrary attached. Use .samples(lib) on the "
                "SongBuilder before using .sample_note()."
            )
        s = self._library[key]
        if transpose != 0.0:
            s = s.pitched(transpose)
        self.add(s, beat, velocity)
        return self


class MelodyTrackBuilder(TrackBuilder):
    """
    Builder for melodic tracks using Phrase-based composition.

    Synthesizes notes on-the-fly from Phrase events and places them
    on the track timeline.
    """

    def __init__(self, track: Track, song: Song, pattern_bars: int = 4,
                 synth_type: str = 'saw', library=None):
        super().__init__(track, song, library=library)
        self._pattern_bars = pattern_bars
        self._synth_type = synth_type
        # Lazy import to avoid circular dependencies
        self._melody = None

    def _get_melody(self):
        if self._melody is None:
            from .melody import Melody
            self._melody = Melody(self._track.name)
        return self._melody

    def synth(self, synth_type: str) -> 'MelodyTrackBuilder':
        """
        Set the synthesizer type for rendering notes.

        Options: 'saw', 'square', 'sine', 'triangle', 'fm', 'pluck'
        """
        self._synth_type = synth_type
        return self

    def phrase(self, phrase, start_beat: Optional[float] = None) -> 'MelodyTrackBuilder':
        """Add a Phrase at a specific beat (or auto-append)."""
        self._get_melody().add(phrase, start_beat)
        return self

    def play(self, notation: str, start_beat: Optional[float] = None) -> 'MelodyTrackBuilder':
        """
        Add a phrase from inline string notation.

        Example: .play("C4:1 E4:0.5 G4:0.5 C5:2")
        """
        from .melody import Phrase
        p = Phrase.from_string(notation)
        return self.phrase(p, start_beat)

    def render_melody(self) -> None:
        """Render all melody events to track placements (called by SongBuilder.build)."""
        if self._melody is None:
            return

        events = self._melody.to_events()
        for beat, midi_note, velocity, duration_beats in events:
            from .synth import midi_to_freq, ADSREnvelope
            freq = midi_to_freq(midi_note)
            duration_sec = self._song.beat_to_seconds(duration_beats)
            sample = self._create_synth_sample(freq, duration_sec, velocity)
            time = self._song.beat_to_seconds(beat)
            self._track.add(sample, time, velocity)

    def _create_synth_sample(self, freq: float, duration: float,
                              velocity: float = 1.0) -> Sample:
        """Synthesize a note sample using the configured synth type."""
        from .synth import (sine_wave, sawtooth_wave, square_wave,
                           triangle_wave, ADSREnvelope, midi_to_freq)

        sr = self._song.sample_rate
        envelope = ADSREnvelope(0.01, 0.1, 0.7, 0.1)

        if self._synth_type == 'sine':
            audio = sine_wave(freq, duration, sr)
        elif self._synth_type == 'square':
            audio = square_wave(freq, duration, sr)
        elif self._synth_type == 'triangle':
            audio = triangle_wave(freq, duration, sr)
        elif self._synth_type == 'fm':
            try:
                from .synths import LeadSynth
                sample = LeadSynth.fm_lead(freq, duration, sample_rate=sr)
                return sample
            except Exception:
                audio = sawtooth_wave(freq, duration, sr)
        elif self._synth_type == 'pluck':
            try:
                from .synths import PluckSynth
                sample = PluckSynth.karplus_strong(freq, duration, sample_rate=sr)
                return sample
            except Exception:
                audio = sawtooth_wave(freq, duration, sr)
        else:  # 'saw' or default
            audio = sawtooth_wave(freq, duration, sr)

        audio = envelope.apply(audio)
        return Sample(f"note_{freq:.0f}hz", audio, tags=["melody"])

    def humanize(self, timing: float = 0.01, velocity: float = 0.1,
                 seed: Optional[int] = None) -> 'MelodyTrackBuilder':
        """Apply humanization to all placements after rendering."""
        from .expression import Humanizer
        Humanizer(timing_jitter=timing, velocity_variation=velocity,
                  seed=seed).apply_to_track(self._track)
        return self

    def groove(self, template) -> 'MelodyTrackBuilder':
        """Apply a groove template to all placements."""
        template.apply_to_track(self._track, self._song.bpm)
        return self

    def automate_volume(self, curve: AutomationCurve) -> 'MelodyTrackBuilder':
        """Attach a volume automation curve to this track."""
        self._track.volume_automation = curve
        return self

    def automate_pan(self, curve: AutomationCurve) -> 'MelodyTrackBuilder':
        """Attach a pan automation curve to this track."""
        self._track.pan_automation = curve
        return self


class HarmonyTrackBuilder(TrackBuilder):
    """
    Builder for harmony/chord tracks.

    Uses ChordProgression to place chord voicings on the track.
    """

    def __init__(self, track: Track, song: Song, pattern_bars: int = 4,
                 synth_type: str = 'saw', library=None):
        super().__init__(track, song, library=library)
        self._pattern_bars = pattern_bars
        self._synth_type = synth_type
        self._key = None
        self._progression = None
        self._voice_led = False
        self._num_voices = 4
        self._arpeggiate = False
        self._arp_rate = 0.25
        self._arp_direction = 'up'

    def key(self, root: str, scale_type: str = 'major') -> 'HarmonyTrackBuilder':
        """Set the musical key for chord construction."""
        from .harmony import Key
        from .arpeggiator import Scale
        scale_map = {
            'major': Scale.MAJOR, 'minor': Scale.MINOR,
            'dorian': Scale.DORIAN, 'mixolydian': Scale.MIXOLYDIAN,
            'harmonic_minor': Scale.HARMONIC_MINOR,
            'melodic_minor': Scale.MELODIC_MINOR,
        }
        scale = scale_map.get(scale_type, Scale.MAJOR)
        self._key = Key(root=root, scale=scale)
        return self

    def progression(self, numerals: str,
                    beats_per_chord: float = 4.0,
                    octave: int = 3) -> 'HarmonyTrackBuilder':
        """Set chord progression from Roman numeral notation."""
        from .harmony import ChordProgression
        if self._key is None:
            raise ValueError("Must set key before progression")
        self._progression = ChordProgression.from_roman(
            self._key, numerals, beats_per_chord, octave)
        return self

    def voice_lead(self, enable: bool = True,
                   num_voices: int = 4) -> 'HarmonyTrackBuilder':
        """Enable voice leading for smoother chord transitions."""
        self._voice_led = enable
        self._num_voices = num_voices
        return self

    def arpeggiate(self, rate: float = 0.25,
                   direction: str = 'up') -> 'HarmonyTrackBuilder':
        """Arpeggiate the chord progression instead of block chords."""
        self._arpeggiate = True
        self._arp_rate = rate
        self._arp_direction = direction
        return self

    def synth(self, synth_type: str) -> 'HarmonyTrackBuilder':
        """Set the synthesizer type."""
        self._synth_type = synth_type
        return self

    def render_harmony(self) -> None:
        """Render all chord events to track placements."""
        if self._progression is None:
            return

        if self._arpeggiate:
            self._render_arpeggiated()
        else:
            events = self._progression.to_events(
                start_beat=0.0,
                voice_led=self._voice_led,
                num_voices=self._num_voices)

            for beat, midi_note, velocity, duration_beats in events:
                from .synth import midi_to_freq, ADSREnvelope
                freq = midi_to_freq(midi_note)
                duration_sec = self._song.beat_to_seconds(duration_beats)
                sample = self._create_synth_sample(freq, duration_sec)
                time = self._song.beat_to_seconds(beat)
                self._track.add(sample, time, velocity)

    def _render_arpeggiated(self) -> None:
        """Render using the arpeggiator."""
        from .arpeggiator import Arpeggiator, ArpDirection

        dir_map = {
            'up': ArpDirection.UP, 'down': ArpDirection.DOWN,
            'up_down': ArpDirection.UP_DOWN, 'random': ArpDirection.RANDOM,
        }

        arp = Arpeggiator(
            bpm=self._song.bpm,
            direction=dir_map.get(self._arp_direction, ArpDirection.UP),
            rate=self._arp_rate,
        )

        arp_prog = self._progression.to_arp_progression()
        beats_per_chord = self._progression.chords[0].duration_beats if self._progression.chords else 4
        events = arp.generate_from_progression(arp_prog, int(beats_per_chord))

        for time, midi_note, velocity, duration in events:
            from .synth import midi_to_freq
            freq = midi_to_freq(midi_note)
            sample = self._create_synth_sample(freq, duration)
            self._track.add(sample, time, velocity)

    def _create_synth_sample(self, freq: float, duration: float) -> Sample:
        """Synthesize a chord note sample."""
        from .synth import (sine_wave, sawtooth_wave, square_wave,
                           triangle_wave, ADSREnvelope)

        sr = self._song.sample_rate
        envelope = ADSREnvelope(0.05, 0.2, 0.6, 0.3)

        if self._synth_type == 'sine':
            audio = sine_wave(freq, duration, sr)
        elif self._synth_type == 'square':
            audio = square_wave(freq, duration, sr)
        elif self._synth_type == 'triangle':
            audio = triangle_wave(freq, duration, sr)
        elif self._synth_type in ('warm_pad', 'pad'):
            try:
                from .synths import PadSynth
                sample = PadSynth.warm_pad(freq, duration, sample_rate=sr)
                return sample
            except Exception:
                audio = sawtooth_wave(freq, duration, sr)
        elif self._synth_type == 'string_pad':
            try:
                from .synths import PadSynth
                sample = PadSynth.string_pad(freq, duration, sample_rate=sr)
                return sample
            except Exception:
                audio = sawtooth_wave(freq, duration, sr)
        else:
            audio = sawtooth_wave(freq, duration, sr)

        audio = envelope.apply(audio)
        return Sample(f"chord_{freq:.0f}hz", audio, tags=["harmony"])

    def humanize(self, timing: float = 0.01, velocity: float = 0.1,
                 seed: Optional[int] = None) -> 'HarmonyTrackBuilder':
        from .expression import Humanizer
        Humanizer(timing_jitter=timing, velocity_variation=velocity,
                  seed=seed).apply_to_track(self._track)
        return self

    def groove(self, template) -> 'HarmonyTrackBuilder':
        template.apply_to_track(self._track, self._song.bpm)
        return self

    def automate_volume(self, curve: AutomationCurve) -> 'HarmonyTrackBuilder':
        self._track.volume_automation = curve
        return self

    def automate_pan(self, curve: AutomationCurve) -> 'HarmonyTrackBuilder':
        self._track.pan_automation = curve
        return self


class SectionBuilder:
    """
    Builder for creating reusable song sections.

    Provides the same track-building API as SongBuilder but produces
    Section objects that can be combined via an Arrangement.

    Example:
        verse = (song_builder.section("verse", bars=8)
            .add_drums(lambda d: d.four_on_floor().backbeat())
            .add_bass(lambda b: b.line([('E2', 0, 2)]))
            .build())
    """

    def __init__(self, name: str, bars: int, song_context: Song,
                 library=None):
        from .arrangement import Section
        self._section = Section(name=name, bars=bars)
        self._song = song_context
        self._bars = bars
        self._library = library

    def add_drums(self, builder: Callable[['DrumTrackBuilder'], 'DrumTrackBuilder']
                  ) -> 'SectionBuilder':
        """Add drums to this section."""
        track = Track(name="Drums", track_type=TrackType.DRUMS)
        drum_builder = DrumTrackBuilder(
            track, self._song, self._bars, library=self._library)
        builder(drum_builder)
        self._section.add_track(track)
        return self

    def add_bass(self, builder: Callable[['BassTrackBuilder'], 'BassTrackBuilder']
                 ) -> 'SectionBuilder':
        """Add bass to this section."""
        track = Track(name="Bass", track_type=TrackType.BASS)
        bass_builder = BassTrackBuilder(
            track, self._song, self._bars, library=self._library)
        builder(bass_builder)
        self._section.add_track(track)
        return self

    def add_melody(self, builder: Callable[['MelodyTrackBuilder'], 'MelodyTrackBuilder'],
                   name: str = "Melody",
                   synth_type: str = 'saw') -> 'SectionBuilder':
        """Add a melodic track to this section."""
        track = Track(name=name, track_type=TrackType.LEAD)
        melody_builder = MelodyTrackBuilder(
            track, self._song, self._bars, synth_type,
            library=self._library)
        builder(melody_builder)
        melody_builder.render_melody()
        self._section.add_track(track)
        return self

    def add_harmony(self, builder: Callable[['HarmonyTrackBuilder'], 'HarmonyTrackBuilder'],
                    name: str = "Harmony",
                    synth_type: str = 'saw') -> 'SectionBuilder':
        """Add a harmony/chord track to this section."""
        track = Track(name=name, track_type=TrackType.PAD)
        harmony_builder = HarmonyTrackBuilder(
            track, self._song, self._bars, synth_type,
            library=self._library)
        builder(harmony_builder)
        harmony_builder.render_harmony()
        self._section.add_track(track)
        return self

    def add_keygroup(
        self,
        name: str,
        program: 'KeygroupProgram',
        builder_fn: Callable[['KeygroupTrackBuilder'], 'KeygroupTrackBuilder'],
    ) -> 'SectionBuilder':
        """Add a keygroup-based track to this section.

        Parameters
        ----------
        name : str
            Track name.
        program : KeygroupProgram
            The keygroup instrument.
        builder_fn : callable
            Builder configuration function.

        Returns
        -------
        self
        """
        from beatmaker.keygroup import KeygroupTrackBuilder

        track = Track(name=name, track_type=TrackType.LEAD)
        builder = KeygroupTrackBuilder(track, self._song, program)
        builder_fn(builder)
        self._section.add_track(track)
        return self

    def add_track(self, name: str, track_type: TrackType = TrackType.FX,
                  builder: Optional[Callable[['TrackBuilder'], 'TrackBuilder']] = None
                  ) -> 'SectionBuilder':
        """Add a generic track to this section."""
        track = Track(name=name, track_type=track_type)
        if builder:
            track_builder = TrackBuilder(track, self._song, library=self._library)
            builder(track_builder)
        self._section.add_track(track)
        return self

    def build(self):
        """Build and return the Section."""
        return self._section


# Convenience function
def create_song(name: str = "Untitled") -> SongBuilder:
    """Create a new song builder."""
    return SongBuilder(name)
