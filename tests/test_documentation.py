"""Execute the introductory examples as users would copy them from the docs."""

from pathlib import Path
import re
import runpy

import numpy as np
import pytest

from beatmaker import load_audio


ROOT = Path(__file__).resolve().parents[1]
GUIDES = [
    "README.md", "docs/song_building.md", "docs/migration.md",
    "docs/keygroup_integration_guide.md",
]
EXAMPLES = [
    pytest.param(name, index, code, id=f"{name}:example-{index + 1}")
    for name in GUIDES
    for index, code in enumerate(re.findall(
        r"```python\n(.*?)```", (ROOT / name).read_text(encoding="utf-8"), re.S
    ))
]


@pytest.mark.parametrize("name,index,code", EXAMPLES)
def test_introductory_example(name, index, code, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    namespace = {}
    exec(compile(code, f"{name}:example-{index + 1}", "exec"), namespace)
    if "song" in namespace:
        assert namespace["song"].tracks
    for path in tmp_path.glob("*.wav"):
        audio = load_audio(path)
        assert audio.channels == 2
        assert audio.num_samples > 0
        assert np.max(np.abs(audio.samples)) > 0


def test_direct_api_example_exports_audio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(ROOT / "examples/basics/02_direct_api.py"), run_name="__main__")
    audio = load_audio(tmp_path / "direct_api.wav")
    assert audio.channels == 2
    assert audio.duration > 8  # two two-bar sections at 120 BPM, plus render tail
    assert np.isfinite(audio.samples).all()
    assert np.max(np.abs(audio.samples)) > 0
