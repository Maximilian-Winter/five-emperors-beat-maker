"""
Single source of truth for all music theory constants.
"""

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

NOTE_ALIASES = {
    "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#", "Ab": "G#",
    "Bb": "A#", "Cb": "B", "E#": "F", "B#": "C",
}

# ---------------------------------------------------------------------------
# Chord interval templates (semitones from root)
# ---------------------------------------------------------------------------

CHORD_TEMPLATES = {
    # Triads
    "maj":        (0, 4, 7),
    "min":        (0, 3, 7),
    "dim":        (0, 3, 6),
    "aug":        (0, 4, 8),
    "sus2":       (0, 2, 7),
    "sus4":       (0, 5, 7),

    # Sevenths
    "maj7":       (0, 4, 7, 11),
    "min7":       (0, 3, 7, 10),
    "7":          (0, 4, 7, 10),     # dominant 7
    "dim7":       (0, 3, 6, 9),
    "m7b5":       (0, 3, 6, 10),     # half-diminished
    "minmaj7":    (0, 3, 7, 11),
    "aug7":       (0, 4, 8, 10),

    # Extended
    "9":          (0, 4, 7, 10, 14),
    "maj9":       (0, 4, 7, 11, 14),
    "min9":       (0, 3, 7, 10, 14),
    "add9":       (0, 4, 7, 14),
    "6":          (0, 4, 7, 9),
    "min6":       (0, 3, 7, 9),

    # Eleventh / thirteenth
    "11":         (0, 4, 7, 10, 14, 17),
    "min11":      (0, 3, 7, 10, 14, 17),
    "maj11":      (0, 4, 7, 11, 14, 17),
    "13":         (0, 4, 7, 10, 14, 21),
    "min13":      (0, 3, 7, 10, 14, 21),
}

# ---------------------------------------------------------------------------
# Scale interval templates (semitones from root)
# ---------------------------------------------------------------------------

SCALE_TEMPLATES = {
    "major":              (0, 2, 4, 5, 7, 9, 11),
    "natural_minor":      (0, 2, 3, 5, 7, 8, 10),
    "harmonic_minor":     (0, 2, 3, 5, 7, 8, 11),
    "melodic_minor":      (0, 2, 3, 5, 7, 9, 11),
    "dorian":             (0, 2, 3, 5, 7, 9, 10),
    "phrygian":           (0, 1, 3, 5, 7, 8, 10),
    "lydian":             (0, 2, 4, 6, 7, 9, 11),
    "mixolydian":         (0, 2, 4, 5, 7, 9, 10),
    "locrian":            (0, 1, 3, 5, 6, 8, 10),
    "pentatonic_major":   (0, 2, 4, 7, 9),
    "pentatonic_minor":   (0, 3, 5, 7, 10),
    "blues":              (0, 3, 5, 6, 7, 10),
    "whole_tone":         (0, 2, 4, 6, 8, 10),
    "diminished_hw":      (0, 1, 3, 4, 6, 7, 9, 10),
    "diminished_wh":      (0, 2, 3, 5, 6, 8, 9, 11),
    "chromatic":          tuple(range(12)),
}

# ---------------------------------------------------------------------------
# Chord symbol parsing map (suffix -> quality key)
# ---------------------------------------------------------------------------

CHORD_SYMBOL_MAP = {
    "":         "maj",
    "m":        "min",
    "min":      "min",
    "maj":      "maj",
    "dim":      "dim",
    "aug":      "aug",
    "sus2":     "sus2",
    "sus4":     "sus4",
    "7":        "7",
    "dom7":     "7",
    "maj7":     "maj7",
    "M7":       "maj7",
    "m7":       "min7",
    "min7":     "min7",
    "dim7":     "dim7",
    "m7b5":     "m7b5",
    "aug7":     "aug7",
    "mM7":      "minmaj7",
    "minmaj7":  "minmaj7",
    "add9":     "add9",
    "9":        "9",
    "maj9":     "maj9",
    "M9":       "maj9",
    "m9":       "min9",
    "min9":     "min9",
    "6":        "6",
    "m6":       "min6",
    "min6":     "min6",
    "11":       "11",
    "m11":      "min11",
    "min11":    "min11",
    "maj11":    "maj11",
    "13":       "13",
    "m13":      "min13",
    "min13":    "min13",
}


def note_name_to_pc(name: str) -> int:
    """Convert note name to pitch class (0-11). C=0."""
    name = name.strip()
    if name in NOTE_ALIASES:
        name = NOTE_ALIASES[name]
    if name in NOTE_NAMES:
        return NOTE_NAMES.index(name)
    raise ValueError(f"Unknown note: {name}")


def pc_to_name(pc: int) -> str:
    """Convert pitch class (0-11) to note name."""
    return NOTE_NAMES[pc % 12]
