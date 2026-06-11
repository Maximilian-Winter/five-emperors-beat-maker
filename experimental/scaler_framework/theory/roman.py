"""
Roman numeral / scale degree system for chord progressions.
"""

from scaler_framework.theory.constants import NOTE_NAMES

# Diatonic chords: degree symbol -> (semitone offset from root, quality)

MAJOR_DIATONIC = {
    "I":    (0, "maj"),
    "ii":   (2, "min"),
    "iii":  (4, "min"),
    "IV":   (5, "maj"),
    "V":    (7, "maj"),
    "vi":   (9, "min"),
    "viio": (11, "dim"),
}

MINOR_DIATONIC = {
    "i":    (0, "min"),
    "iio":  (2, "dim"),
    "III":  (3, "maj"),
    "iv":   (5, "min"),
    "v":    (7, "min"),
    "VI":   (8, "maj"),
    "VII":  (10, "maj"),
}

# Borrowed / secondary dominant chords available in major keys
MAJOR_EXTENDED = {
    "V7":       (7, "7"),
    "V/V":      (2, "maj"),
    "V/ii":     (9, "maj"),
    "V/vi":     (4, "maj"),
    "bVII":     (10, "maj"),
    "bVI":      (8, "maj"),
    "bIII":     (3, "maj"),
    "iv":       (5, "min"),
    "IVmaj7":   (5, "maj7"),
    "ii7":      (2, "min7"),
    "Imaj7":    (0, "maj7"),
    "iii7":     (4, "min7"),
    "vi7":      (9, "min7"),
}

# Functional harmony movement tables
# from_degree -> list of (to_degree, weight)

MAJOR_MOVEMENTS = {
    "I":    [("IV", 5), ("V", 5), ("vi", 4), ("ii", 3), ("iii", 2), ("I", 1)],
    "ii":   [("V", 6), ("viio", 2), ("IV", 2), ("ii", 1)],
    "iii":  [("vi", 5), ("IV", 4), ("ii", 2), ("iii", 1)],
    "IV":   [("V", 6), ("I", 4), ("ii", 3), ("vi", 2), ("IV", 1)],
    "V":    [("I", 7), ("vi", 4), ("IV", 2), ("V", 1)],
    "vi":   [("IV", 5), ("ii", 4), ("V", 3), ("I", 2), ("vi", 1)],
    "viio": [("I", 6), ("iii", 3), ("viio", 1)],
}

MINOR_MOVEMENTS = {
    "i":    [("iv", 5), ("v", 4), ("VI", 4), ("III", 3), ("VII", 2), ("i", 1)],
    "iio":  [("v", 5), ("VII", 3), ("i", 2)],
    "III":  [("VI", 5), ("iv", 3), ("VII", 3), ("III", 1)],
    "iv":   [("v", 5), ("i", 4), ("VII", 3), ("VI", 2)],
    "v":    [("i", 6), ("VI", 4), ("III", 2), ("v", 1)],
    "VI":   [("VII", 5), ("iv", 4), ("III", 3), ("iio", 2)],
    "VII":  [("III", 5), ("i", 4), ("VI", 2), ("VII", 1)],
}


def degree_to_note(degree: str, root: int, scale: str = "major") -> tuple[str, str]:
    """
    Convert a Roman numeral degree to (note_name, quality).

    Args:
        degree: Roman numeral like "I", "vi", "V7"
        root: Key root as pitch class (0=C)
        scale: "major" or "minor"

    Returns:
        (note_name, quality) e.g. ("G", "maj")
    """
    if scale in ("major", "lydian", "mixolydian"):
        lookup = {**MAJOR_DIATONIC, **MAJOR_EXTENDED}
    else:
        lookup = dict(MINOR_DIATONIC)

    if degree in lookup:
        interval, quality = lookup[degree]
        note = NOTE_NAMES[(root + interval) % 12]
        return note, quality
    return "?", "?"
