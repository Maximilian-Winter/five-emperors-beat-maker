"""A small composition using direct track builders.

Install from the repository root with: python -m pip install -e .
Run with: python examples/basics/02_direct_api.py
"""

from pathlib import Path

from beatmaker import Arrangement, Song, create_song


def make_song() -> Song:
    project = create_song("Direct API demo", bpm=120, bars=2)
    verse = project.section("Verse", bars=2)
    verse.drums().four_on_floor().backbeat().eighth_hats().volume(0.6)
    verse.bass().line([
        ("C2", 0, 2), ("G2", 2, 2),
        ("A2", 4, 2), ("F2", 6, 2),
    ]).volume(0.5)
    verse.melody("Hook", synth_type="sine").play(
        "C4:1 E4:1 G4:2 A4:1 G4:1 E4:2"
    ).humanize(timing=0.005, velocity=0.05, seed=7).volume(0.3)
    section = verse.build()
    project.arrange(Arrangement().add(section, repeat=2))
    return project.master_limiter().build()


if __name__ == "__main__":
    output = make_song().export(Path("direct_api.wav"))
    print(f"Wrote {output.resolve()}")
