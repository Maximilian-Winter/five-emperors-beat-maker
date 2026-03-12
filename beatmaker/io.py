"""
靈寶五帝策使編碼之法 - Audio I/O Module
The gateway through which sound enters and exits our realm.

By the Dark Turtle's authority,
Let data flow like eternal waters,
Deep as ocean, persistent as tide,
急急如律令敕
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, List, Dict
import numpy as np
import wave
import struct

from .core import AudioData, Sample


# ─── Configuration ─────────────────────────────────────────────────────────

@dataclass
class SampleLibraryConfig:
    """
    Configuration for how a SampleLibrary loads and processes samples.

    Example::

        config = SampleLibraryConfig(
            lazy=True,
            normalize=True,
            target_sample_rate=44100,
        )
        lib = SampleLibrary.from_directory("./samples", config=config)
    """
    extensions: tuple[str, ...] = ('.wav', '.mp3', '.ogg', '.flac', '.aiff')
    auto_tag: bool = True
    lazy: bool = False
    normalize: bool = False
    normalize_peak: float = 0.95
    target_sample_rate: Optional[int] = None
    trim_silence: bool = False
    trim_threshold: float = 0.001
    default_tags: list[str] = field(default_factory=list)


def load_audio(path: Union[str, Path]) -> AudioData:
    """
    Load audio from a file.
    
    Supports: WAV (native), MP3/OGG/FLAC (via pydub if available)
    """
    path = Path(path)
    suffix = path.suffix.lower()
    
    if suffix == '.wav':
        return _load_wav(path)
    else:
        # Try pydub for other formats
        try:
            return _load_with_pydub(path)
        except ImportError:
            raise ValueError(
                f"Format {suffix} requires pydub. Install with: pip install pydub"
            )


def _load_wav(path: Path) -> AudioData:
    """Load a WAV file natively."""
    with wave.open(str(path), 'rb') as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        
        raw_data = wav.readframes(n_frames)
    
    # Determine format string based on sample width
    if sample_width == 1:
        fmt = f'{n_frames * channels}B'  # unsigned 8-bit
        max_val = 128.0
        offset = 128
    elif sample_width == 2:
        fmt = f'{n_frames * channels}h'  # signed 16-bit
        max_val = 32768.0
        offset = 0
    elif sample_width == 4:
        fmt = f'{n_frames * channels}i'  # signed 32-bit
        max_val = 2147483648.0
        offset = 0
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    # Unpack and normalize to float
    int_data = struct.unpack(fmt, raw_data)
    float_data = np.array(int_data, dtype=np.float64)
    float_data = (float_data - offset) / max_val
    
    # Reshape for multi-channel
    if channels > 1:
        float_data = float_data.reshape(-1, channels)
    
    return AudioData(float_data, sample_rate, channels)


def _load_with_pydub(path: Path) -> AudioData:
    """Load audio using pydub."""
    from pydub import AudioSegment
    
    audio = AudioSegment.from_file(str(path))
    
    # Convert to numpy array
    samples = np.array(audio.get_array_of_samples(), dtype=np.float64)
    samples = samples / (2 ** (audio.sample_width * 8 - 1))
    
    channels = audio.channels
    if channels > 1:
        samples = samples.reshape(-1, channels)
    
    return AudioData(samples, audio.frame_rate, channels)


def save_audio(audio: AudioData, path: Union[str, Path], 
               format: Optional[str] = None) -> None:
    """
    Save audio to a file.
    
    Supports: WAV (native), MP3/OGG/FLAC (via pydub if available)
    """
    path = Path(path)
    suffix = format or path.suffix.lower().lstrip('.')
    
    if suffix == 'wav':
        _save_wav(audio, path)
    else:
        try:
            _save_with_pydub(audio, path, suffix)
        except ImportError:
            raise ValueError(
                f"Format {suffix} requires pydub. Install with: pip install pydub"
            )


def _save_wav(audio: AudioData, path: Path, sample_width: int = 2) -> None:
    """Save audio as WAV file."""
    # Ensure path has .wav extension
    if path.suffix.lower() != '.wav':
        path = path.with_suffix('.wav')
    
    # Normalize and convert to integers
    samples = np.clip(audio.samples, -1.0, 1.0)
    
    if sample_width == 2:
        max_val = 32767
        int_samples = (samples * max_val).astype(np.int16)
    elif sample_width == 1:
        max_val = 127
        int_samples = ((samples * max_val) + 128).astype(np.uint8)
    else:
        max_val = 2147483647
        int_samples = (samples * max_val).astype(np.int32)
    
    # Flatten for multi-channel (interleaved)
    if audio.channels > 1:
        int_samples = int_samples.flatten()
    
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(audio.channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(audio.sample_rate)
        wav.writeframes(int_samples.tobytes())


def _save_with_pydub(audio: AudioData, path: Path, format: str) -> None:
    """Save audio using pydub."""
    from pydub import AudioSegment
    
    # Convert to 16-bit integers
    samples = np.clip(audio.samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    
    if audio.channels > 1:
        int_samples = int_samples.flatten()
    
    # Create AudioSegment
    segment = AudioSegment(
        data=int_samples.tobytes(),
        sample_width=2,
        frame_rate=audio.sample_rate,
        channels=audio.channels
    )
    
    segment.export(str(path), format=format)


def load_samples_from_directory(directory: Union[str, Path], 
                                 recursive: bool = False,
                                 extensions: tuple = ('.wav', '.mp3', '.ogg', '.flac')
                                 ) -> dict[str, Sample]:
    """
    Load all audio files from a directory as samples.
    
    Returns a dictionary mapping sample names to Sample objects.
    """
    directory = Path(directory)
    samples = {}
    
    if recursive:
        files = directory.rglob('*')
    else:
        files = directory.iterdir()
    
    for path in files:
        if path.suffix.lower() in extensions:
            try:
                audio = load_audio(path)
                name = path.stem
                samples[name] = Sample(name=name, audio=audio)
            except Exception as e:
                print(f"Warning: Could not load {path}: {e}")
    
    return samples


class SampleLibrary:
    """
    A managed collection of samples organized by tags, categories,
    directory-relative paths, and configurable aliases.

    Samples can be retrieved by their relative path without extension::

        lib = SampleLibrary.from_directory("./samples")
        kick = lib["drums/kick"]          # loads drums/kick.wav
        snare = lib["drums/snare_01"]     # loads drums/snare_01.wav
        pad = lib["synths/pads/warm"]     # loads synths/pads/warm.wav

    Aliases provide shorthand access::

        lib.alias("kick", "drums/808/kick_hard")
        lib.aliases(snare="drums/acoustic/snare_02", pad="synths/pads/warm")
        kick = lib["kick"]  # resolves to "drums/808/kick_hard"

    Configuration controls loading behaviour::

        config = SampleLibraryConfig(lazy=True, normalize=True)
        lib = SampleLibrary.from_directory("./samples", config=config)

    Directory structure is preserved as a natural namespace.
    Forward slashes are used regardless of OS.
    """

    def __init__(self, config: Optional[SampleLibraryConfig] = None):
        self._samples: dict[str, Sample] = {}
        self._by_tag: dict[str, list[str]] = {}
        self._aliases: dict[str, str] = {}
        self._root: Optional[Path] = None
        self._config: SampleLibraryConfig = config or SampleLibraryConfig()

    # ── Factory ───────────────────────────────────────────────────────

    @classmethod
    def from_directory(cls, directory: Union[str, Path],
                       config: Optional[SampleLibraryConfig] = None,
                       *,
                       extensions: Optional[tuple[str, ...]] = None,
                       auto_tag: Optional[bool] = None,
                       lazy: Optional[bool] = None) -> 'SampleLibrary':
        """
        Create a SampleLibrary from a folder, indexing by relative path.

        Args:
            directory:  Root folder containing audio files.
            config:     A ``SampleLibraryConfig`` controlling all load options.
                        Individual kwargs override config fields when both
                        are supplied.
            extensions: Override config extensions.
            auto_tag:   Override config auto_tag.
            lazy:       Override config lazy.

        Returns:
            A populated SampleLibrary instance.

        Example::

            lib = SampleLibrary.from_directory("./my_samples")
            kick = lib["drums/kick"]
            lib.list("drums")  # all samples under drums/
        """
        directory = Path(directory).resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"Sample directory not found: {directory}")

        cfg = config or SampleLibraryConfig()
        # Allow individual kwargs to override config
        exts = extensions if extensions is not None else cfg.extensions
        do_auto_tag = auto_tag if auto_tag is not None else cfg.auto_tag
        do_lazy = lazy if lazy is not None else cfg.lazy

        lib = cls(config=cfg)
        lib._root = directory

        for path in sorted(directory.rglob('*')):
            if path.suffix.lower() not in exts:
                continue
            if not path.is_file():
                continue

            # Key = relative path without extension, forward slashes
            rel = path.relative_to(directory).with_suffix('')
            key = rel.as_posix()  # always forward slashes

            if do_lazy:
                lib._samples[key] = _DeferredSample(path, key, cfg)
            else:
                try:
                    audio = _load_and_process(path, cfg)
                    tags = list(cfg.default_tags)
                    if do_auto_tag:
                        tags += [p for p in rel.parent.parts if p != '.']
                    sample = Sample(name=key, audio=audio, tags=tags)
                    lib._add_internal(key, sample)
                except Exception as e:
                    print(f"Warning: Could not load {path}: {e}")

        return lib

    # ── Adding samples ────────────────────────────────────────────────

    def add(self, sample: Sample, key: Optional[str] = None) -> 'SampleLibrary':
        """
        Add a sample to the library.

        Args:
            sample: The Sample to add.
            key:    Optional explicit key.  If omitted, ``sample.name``
                    is used.
        """
        k = key or sample.name
        self._add_internal(k, sample)
        return self

    def _add_internal(self, key: str, sample: Sample) -> None:
        """Internal: register sample under key and index its tags."""
        self._samples[key] = sample
        for tag in sample.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            if key not in self._by_tag[tag]:
                self._by_tag[tag].append(key)

    # ── Aliases ────────────────────────────────────────────────────────

    def alias(self, short_name: str, target_key: str) -> 'SampleLibrary':
        """
        Register an alias for a sample key.

        Example::

            lib.alias("kick", "drums/808/kick_hard")
            kick = lib["kick"]  # resolves to "drums/808/kick_hard"
        """
        self._aliases[short_name] = target_key.replace('\\', '/')
        return self

    def aliases(self, **mapping: str) -> 'SampleLibrary':
        """
        Register multiple aliases at once.

        Example::

            lib.aliases(
                kick="drums/808/kick_hard",
                snare="drums/acoustic/snare_02",
                pad="synths/pads/warm_analog",
            )
        """
        for short_name, target_key in mapping.items():
            self._aliases[short_name] = target_key.replace('\\', '/')
        return self

    def resolve(self, name: str) -> str:
        """
        Resolve a name through aliases.

        If ``name`` is a registered alias, returns the target key.
        Otherwise returns ``name`` unchanged.
        """
        name = name.replace('\\', '/')
        return self._aliases.get(name, name)

    # ── Retrieval ─────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[Sample]:
        """
        Get a sample by key, alias, or stem (relative path without extension).

        Resolution order:
        1. Exact key match
        2. Alias resolution -> key match
        3. Returns None

        Returns None if not found.
        """
        name = name.replace('\\', '/')
        # Try direct key
        sample = self._samples.get(name)
        if sample is None:
            # Try alias resolution
            resolved = self._aliases.get(name)
            if resolved is not None:
                sample = self._samples.get(resolved)
        if sample is not None and isinstance(sample, _DeferredSample):
            actual_key = self._aliases.get(name, name)
            sample = sample.load()
            self._samples[actual_key] = sample
        return sample

    def __getitem__(self, name: str) -> Sample:
        """
        Get a sample by key or alias (raises KeyError if not found).

        Resolution order:
        1. Exact key match
        2. Alias resolution
        3. Stem-only fallback (last path component)

        Example::

            kick = lib["drums/kick"]
            kick = lib["kick"]  # alias or stem fallback
        """
        sample = self.get(name)
        if sample is None:
            # Try a stem-only match as fallback
            name_clean = name.replace('\\', '/')
            for key, s in self._samples.items():
                if key.rsplit('/', 1)[-1] == name_clean:
                    if isinstance(s, _DeferredSample):
                        s = s.load()
                        self._samples[key] = s
                    return s
            raise KeyError(
                f"Sample '{name}' not found. "
                f"Available: {', '.join(sorted(self._samples.keys())[:10])}..."
            )
        return sample

    def __contains__(self, name: str) -> bool:
        name = name.replace('\\', '/')
        return name in self._samples or name in self._aliases

    # ── Browsing & search ─────────────────────────────────────────────

    def list(self, prefix: str = '') -> list[str]:
        """
        List sample keys, optionally filtered by path prefix.

        Example::

            lib.list("drums")        # ['drums/kick', 'drums/snare', ...]
            lib.list("synths/pads")  # ['synths/pads/warm', ...]
        """
        prefix = prefix.replace('\\', '/')
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        return sorted(k for k in self._samples if k.startswith(prefix) or not prefix)

    def search(self, pattern: str) -> list[str]:
        """
        Search sample keys by substring (case-insensitive).

        Example::

            lib.search("kick")  # ['drums/kick', 'drums/kick_hard', ...]
        """
        pat = pattern.lower()
        return sorted(k for k in self._samples if pat in k.lower())

    def by_tag(self, tag: str) -> list[Sample]:
        """Get all samples with a specific tag."""
        names = self._by_tag.get(tag, [])
        results = []
        for n in names:
            s = self._samples.get(n)
            if s is not None:
                if isinstance(s, _DeferredSample):
                    s = s.load()
                    self._samples[n] = s
                results.append(s)
        return results

    def load_directory(self, directory: Union[str, Path],
                       tags: Optional[list[str]] = None,
                       recursive: bool = False) -> 'SampleLibrary':
        """Load all samples from a directory (flat stem-based keys)."""
        loaded = load_samples_from_directory(directory, recursive)
        for name, sample in loaded.items():
            if tags:
                sample = sample.with_tags(*tags)
            self.add(sample)
        return self

    # ── Properties ────────────────────────────────────────────────────

    @property
    def names(self) -> list[str]:
        """List all sample keys."""
        return sorted(self._samples.keys())

    @property
    def tags(self) -> list[str]:
        """List all tags in the library."""
        return sorted(self._by_tag.keys())

    @property
    def root(self) -> Optional[Path]:
        """The root directory, if created via from_directory."""
        return self._root

    def __len__(self) -> int:
        return len(self._samples)

    def __repr__(self) -> str:
        root_str = f", root='{self._root}'" if self._root else ""
        return f"SampleLibrary({len(self)} samples{root_str})"

    # ── Iteration ─────────────────────────────────────────────────────

    def __iter__(self):
        """Iterate over (key, sample) pairs."""
        for key in sorted(self._samples):
            sample = self._samples[key]
            if isinstance(sample, _DeferredSample):
                sample = sample.load()
                self._samples[key] = sample
            yield key, sample

    def keys(self) -> list[str]:
        """All sample keys."""
        return sorted(self._samples.keys())

    def values(self) -> list[Sample]:
        """All samples (triggers lazy loading)."""
        return [s for _, s in self]

    def items(self) -> list[tuple[str, Sample]]:
        """All (key, sample) pairs."""
        return list(self)


def _load_and_process(path: Path, config: SampleLibraryConfig) -> AudioData:
    """Load audio from a file and apply config-based processing."""
    audio = load_audio(path)

    if config.trim_silence:
        # Trim leading and trailing silence
        samples = audio.samples
        if audio.channels > 1:
            amplitude = np.max(np.abs(samples), axis=1)
        else:
            amplitude = np.abs(samples)
        above = np.where(amplitude > config.trim_threshold)[0]
        if len(above) > 0:
            start, end = above[0], above[-1] + 1
            audio = AudioData(
                samples[start:end].copy(),
                audio.sample_rate,
                audio.channels,
            )

    if config.target_sample_rate is not None:
        audio = audio.resample(config.target_sample_rate)

    if config.normalize:
        audio = audio.normalize(config.normalize_peak)

    return audio


class _DeferredSample:
    """
    Sentinel for lazy-loaded samples.

    Stores only the path until the sample is first accessed,
    then loads and replaces itself in the library.
    """
    __slots__ = ('path', 'key', '_config')

    def __init__(self, path: Path, key: str,
                 config: Optional[SampleLibraryConfig] = None):
        self.path = path
        self.key = key
        self._config = config or SampleLibraryConfig()

    def load(self) -> Sample:
        audio = _load_and_process(self.path, self._config)
        tags = list(self._config.default_tags)
        if self._config.auto_tag:
            tags += [p for p in Path(self.key).parent.parts if p != '.']
        return Sample(name=self.key, audio=audio, tags=tags)
