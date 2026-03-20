"""
靈寶五帝策使編碼之法
The Numinous Treasure Five Emperors Beat Maker

A Python library for creating beats and songs with a fluent builder pattern.

Example:
    from beatmaker import create_song, DrumSynth

    song = (create_song("My Beat")
        .tempo(128)
        .bars(4)
        .add_drums(lambda d: d
            .four_on_floor()
            .backbeat()
            .eighth_hats()
        )
        .build())

    song.export("my_beat.wav")

The Five Emperors govern:
    🐉 Azure Emperor (East)    - Architecture & Structure
    🔥 Vermilion Emperor (South) - Performance & Optimization
    🌍 Yellow Emperor (Center)   - Integration & Balance
    🐅 White Emperor (West)      - Debugging & Protection
    🐢 Black Emperor (North)     - Data & Flow
"""

__version__ = "0.4.0-dev"
__author__ = "Five Emperors Coding Council"

# ── Core types ────────────────────────────────────────────────────────────────

from .core import (
    AudioData,
    Sample,
    Track,
    TrackType,
    TimeSignature,
    SamplePlacement,
    NoteValue,
    AudioEffect,
)

# ── Music theory (shared utilities) ──────────────────────────────────────────

from .music import (
    note_name_to_midi,
    midi_to_note_name,
    midi_to_freq,
    freq_to_midi,
    note_to_freq,
    Scale,
    ChordShape,
)

# ── Song building ────────────────────────────────────────────────────────────

from .builder import (
    Song,
    SongBuilder,
    TrackBuilder,
    DrumTrackBuilder,
    BassTrackBuilder,
    MelodyTrackBuilder,
    HarmonyTrackBuilder,
    SectionBuilder,
    create_song,
)

# ── Synthesis (beatmaker.synthesis subpackage) ───────────────────────────────

from .synthesis import (
    Waveform,
    Oscillator,
    ADSREnvelope,
    sine_wave,
    square_wave,
    sawtooth_wave,
    triangle_wave,
    white_noise,
    pink_noise,
    DrumSynth,
    BassSynth,
    LFO,
    Filter,
    PadSynth,
    LeadSynth,
    PluckSynth,
    FXSynth,
    create_pad,
    create_lead,
    create_pluck,
)

# ── Effects (beatmaker.effects subpackage) ───────────────────────────────────

from .effects import (
    Gain,
    Limiter,
    SoftClipper,
    Delay,
    Reverb,
    LowPassFilter,
    HighPassFilter,
    Compressor,
    BitCrusher,
    Chorus,
    EffectChain,
    SidechainCompressor,
    SidechainEnvelope,
    PumpingBass,
    SidechainBuilder,
    SidechainPresets,
    create_sidechain,
)

# ── Sequencer ─────────────────────────────────────────────────────────────────

from .sequencer import (
    Step,
    Pattern,
    StepSequencer,
    ClassicPatterns,
    EuclideanPattern,
    PolyrhythmGenerator,
    StepValue,
)

# ── Arpeggiator ──────────────────────────────────────────────────────────────

from .arpeggiator import (
    Arpeggiator,
    ArpeggiatorBuilder,
    ArpDirection,
    ArpMode,
    ArpSynthesizer,
    create_arpeggiator,
    arp_chord,
    arp_scale,
)

# ── Melody & Phrase ──────────────────────────────────────────────────────────

from .melody import (
    Note,
    Phrase,
    Melody,
)

# ── Harmony & Key ────────────────────────────────────────────────────────────

from .harmony import (
    Key,
    ChordProgression,
    ChordEntry,
)

# ── Automation ───────────────────────────────────────────────────────────────

from .automation import (
    AutomationCurve,
    AutomationPoint,
    CurveType,
    AutomatableEffect,
    AutomatedGain,
    AutomatedFilter,
)

# ── Arrangement ──────────────────────────────────────────────────────────────

from .arrangement import (
    Section,
    Arrangement,
    ArrangementEntry,
    Transition,
)

# ── Expression ───────────────────────────────────────────────────────────────

from .expression import (
    Vibrato,
    PitchBend,
    Portamento,
    NoteExpression,
    Humanizer,
    GrooveTemplate,
    VelocityCurve,
)

# ── MIDI ─────────────────────────────────────────────────────────────────────

from .midi import (
    MIDIFile,
    MIDITrack,
    MIDINote,
    MIDIReader,
    MIDIWriter,
    load_midi,
    save_midi,
    create_midi,
    midi_to_beatmaker_events,
    beatmaker_events_to_midi,
    song_to_midi,
)

# ── I/O ──────────────────────────────────────────────────────────────────────

from .io import (
    load_audio,
    save_audio,
    load_samples_from_directory,
    SampleLibrary,
    SampleLibraryConfig,
)

# ── SPC700 DSP Integration (optional — install beatmaker-spc700) ─────────────

try:
    from beatmaker_spc700 import (
        SPC700Sound,
        SPC700Engine,
        SPC700SongBuilder,
        SPC700Echo,
    )
    from beatmaker_spc700 import (
        ADSR as SPC_ADSR,
        Gain as SPC_Gain,
        EchoConfig as SPC_EchoConfig,
        Instrument as SPC_Instrument,
        Sample as SPC_Sample,
    )
except ImportError:
    pass  # SPC700 support not installed

# ── Signal Graph (beatmaker.graph subpackage) ────────────────────────────────

from .graph import (
    SignalGraph,
    SignalNode,
    Port,
    PortDirection,
    AudioInput,
    TrackInput,
    OscillatorNode,
    NoiseNode,
    EffectNode,
    GainNode,
    FilterNode,
    CompressorNode,
    MixNode,
    MultiplyNode,
    CrossfadeNode,
    EnvelopeFollower,
    FilterBankNode,
    ChannelSplitNode,
    StereoMergeNode,
    GraphEffect,
)

# ── Utilities ────────────────────────────────────────────────────────────────

from .utils import (
    detect_bpm,
    detect_onsets,
    slice_at_onsets,
    extract_samples_from_file,
    split_stereo,
    merge_to_stereo,
    time_stretch,
    pitch_shift,
    reverse,
    loop,
    crossfade,
    concatenate,
    mix,
    export_samples,
)

# ── Public API ───────────────────────────────────────────────────────────────

__all__ = [
    # Version
    "__version__",

    # Core
    "AudioData", "Sample", "Track", "TrackType", "TimeSignature",
    "SamplePlacement", "NoteValue", "AudioEffect",

    # Music theory
    "note_name_to_midi", "midi_to_note_name", "midi_to_freq",
    "freq_to_midi", "note_to_freq", "Scale", "ChordShape",

    # Building
    "Song", "SongBuilder", "TrackBuilder", "DrumTrackBuilder",
    "BassTrackBuilder", "MelodyTrackBuilder", "HarmonyTrackBuilder",
    "SectionBuilder", "create_song",

    # Synthesis
    "Waveform", "Oscillator", "ADSREnvelope",
    "sine_wave", "square_wave", "sawtooth_wave", "triangle_wave",
    "white_noise", "pink_noise",
    "DrumSynth", "BassSynth",
    "LFO", "Filter", "PadSynth", "LeadSynth", "PluckSynth", "FXSynth",
    "create_pad", "create_lead", "create_pluck",

    # Effects
    "Gain", "Limiter", "SoftClipper", "Delay", "Reverb",
    "LowPassFilter", "HighPassFilter", "Compressor", "BitCrusher",
    "Chorus", "EffectChain",
    "SidechainCompressor", "SidechainEnvelope", "PumpingBass",
    "SidechainBuilder", "SidechainPresets", "create_sidechain",

    # Sequencer
    "Step", "Pattern", "StepSequencer", "ClassicPatterns",
    "EuclideanPattern", "PolyrhythmGenerator", "StepValue",

    # Arpeggiator
    "Arpeggiator", "ArpeggiatorBuilder", "ArpDirection", "ArpMode",
    "ArpSynthesizer", "create_arpeggiator", "arp_chord", "arp_scale",

    # Melody
    "Note", "Phrase", "Melody",

    # Harmony
    "Key", "ChordProgression", "ChordEntry",

    # Automation
    "AutomationCurve", "AutomationPoint", "CurveType",
    "AutomatableEffect", "AutomatedGain", "AutomatedFilter",

    # Arrangement
    "Section", "Arrangement", "ArrangementEntry", "Transition",

    # Expression
    "Vibrato", "PitchBend", "Portamento", "NoteExpression",
    "Humanizer", "GrooveTemplate", "VelocityCurve",

    # MIDI
    "MIDIFile", "MIDITrack", "MIDINote", "MIDIReader", "MIDIWriter",
    "load_midi", "save_midi", "create_midi",
    "midi_to_beatmaker_events", "beatmaker_events_to_midi", "song_to_midi",

    # I/O
    "load_audio", "save_audio", "load_samples_from_directory",
    "SampleLibrary", "SampleLibraryConfig",

    # Signal Graph
    "SignalGraph", "SignalNode", "Port", "PortDirection",
    "AudioInput", "TrackInput", "OscillatorNode", "NoiseNode",
    "EffectNode", "GainNode", "FilterNode", "CompressorNode",
    "MixNode", "MultiplyNode", "CrossfadeNode",
    "EnvelopeFollower", "FilterBankNode",
    "ChannelSplitNode", "StereoMergeNode", "GraphEffect",

    # Utilities
    "detect_bpm", "detect_onsets", "slice_at_onsets",
    "extract_samples_from_file", "split_stereo", "merge_to_stereo",
    "time_stretch", "pitch_shift", "reverse", "loop",
    "crossfade", "concatenate", "mix", "export_samples",
]
