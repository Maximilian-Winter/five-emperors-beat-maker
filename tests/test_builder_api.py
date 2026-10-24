"""Public composition workflows and compatibility with callback builders."""

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from beatmaker import (
    Arrangement, AudioData, DrumSynth, Gain, KeygroupProgram, Sample,
    SampleLibrary, SongBuilder, TrackBuilder, TrackType, create_song,
)


@pytest.fixture
def builder():
    return create_song("API test", bpm=120, bars=2, sample_rate=8000)


def test_constructor_settings_and_named_direct_tracks(builder):
    builder.drums("Kit").kick(beats=[0, 2])
    builder.bass("Sub").note("C2", beat=4, duration=1)
    builder.melody("Lead", synth_type="sine").play("C4:1 R:1 E4:1")
    builder.harmony("Chords", synth_type="sine").key("C").progression("I")
    song = builder.build()
    assert song.bpm == 120
    assert song.sample_rate == 8000
    assert [t.name for t in song.tracks] == ["Kit", "Sub", "Lead", "Chords"]
    assert [p.time for p in song.get_track("Kit").placements] == [0, 1, 2, 3]
    assert [p.time for p in song.get_track("Sub").placements] == [2]
    assert [p.time for p in song.get_track("Lead").placements] == [0, 1]
    assert len(song.get_track("Chords").placements) == 3
    audio = song.render()
    assert audio.channels == 2
    assert np.isfinite(audio.samples).all()
    assert np.max(np.abs(audio.samples)) > 0


@pytest.mark.parametrize("kind", ["melody", "harmony"])
def test_build_is_idempotent_and_preserves_manual_samples(builder, kind):
    instrument = getattr(builder, kind)(synth_type="sine")
    manual = Sample("marker", AudioData.silence(0.1, 8000))
    instrument.add(manual, beat=6)
    if kind == "melody":
        instrument.play("C4:1 E4:1")
    else:
        instrument.key("C").progression("I")
    track = instrument.build()
    first = list(track.placements)
    builder.build()
    instrument.build()
    assert all(a is b for a, b in zip(first, track.placements))
    assert len(track.placements) == len(first)
    instrument.synth("triangle")
    builder.build()
    assert len(track.placements) == len(first)
    assert track.placements[0].sample is manual
    assert all(p.sample.audio.sample_rate == 8000 for p in track.placements)


def test_edit_after_build_replaces_generated_notes(builder):
    lead = builder.melody(synth_type="sine").play("C4:1")
    song = builder.build()
    lead.play("E4:1")
    assert builder.build() is song
    assert [p.time for p in song.tracks[0].placements] == [0, 0.5]


@pytest.mark.parametrize("kind", ["melody", "harmony"])
@pytest.mark.parametrize("callback", [False, True])
def test_humanize_runs_after_synthesis(builder, kind, callback):
    def configure(track):
        if kind == "melody":
            track.play("C4:1 E4:1")
        else:
            track.key("C").progression("I")
        return track.humanize(timing=0, velocity=0.2, seed=42)

    if callback:
        getattr(builder, "add_" + kind)(configure, synth_type="sine")
    else:
        configure(getattr(builder, kind)(synth_type="sine"))
    track = builder.build().tracks[0]
    first = [(p.time, p.velocity) for p in track.placements]
    assert any(p.velocity != 0.8 for p in track.placements)
    assert [(p.time, p.velocity) for p in builder.build().tracks[0].placements] == first


def test_groove_runs_after_synthesis(builder):
    class Shift:
        def apply_to_track(self, track, bpm):
            assert bpm == 120
            for placement in track.placements:
                placement.time += 0.125

    lead = builder.melody(synth_type="sine").groove(Shift()).play("C4:1")
    assert lead.build().placements[0].time == 0.125
    assert lead.build().placements[0].time == 0.125


def test_failed_synthesis_preserves_previous_notes_and_can_retry(builder, monkeypatch):
    lead = builder.melody(synth_type="sine").play("C4:1")
    track = lead.build()
    first = track.placements[0]
    lead.play("E4:1")
    synthesize = lead._create_synth_sample

    def fail(*args):
        raise RuntimeError("synthesis failed")

    monkeypatch.setattr(lead, "_create_synth_sample", fail)
    with pytest.raises(RuntimeError, match="synthesis failed"):
        builder.build()
    assert len(track.placements) == 1
    assert track.placements[0] is first
    monkeypatch.setattr(lead, "_create_synth_sample", synthesize)
    assert len(builder.build().tracks[0].placements) == 2


def test_callbacks_accept_functions_returning_none_and_custom_names(builder):
    def drums(track):
        track.kick(beats=[0])

    assert builder.add_drums(drums, name="Kick") is builder
    assert builder.add_bass(lambda t: t.note("C2", 0), name="Sub") is builder
    assert [t.name for t in builder.build().tracks] == ["Kick", "Sub"]


def test_failed_callback_removes_only_its_track(builder):
    existing = builder.melody("Lead", synth_type="sine").play("C4:1")

    def fail(track):
        track.play("E4:1")
        raise ValueError("bad configuration")

    with pytest.raises(ValueError, match="bad configuration"):
        builder.add_melody(fail, name="Lead")
    assert builder.build().tracks == [existing.build()]


@pytest.mark.parametrize("callback", [False, True])
def test_sections_share_track_factories_and_finish_before_arranging(builder, callback):
    verse = builder.section("Verse", bars=1)
    if callback:
        verse.add_drums(lambda d: d.kick(beats=[0]), name="Kit")
        verse.add_melody(lambda m: m.play("C4:1"), synth_type="sine")
        verse.add_harmony(lambda h: h.key("C").progression("I"), synth_type="sine")
    else:
        verse.drums("Kit").kick(beats=[0])
        verse.melody(synth_type="sine").play("C4:1")
        verse.harmony(synth_type="sine").key("C").progression("I")
    section = verse.build()
    assert [len(t.placements) for t in section.tracks] == [1, 1, 3]
    assert verse.build() is section
    builder.arrange(Arrangement().add(section, repeat=2))
    song = builder.build()
    assert [p.time for p in song.get_track("Melody").placements] == [0, 2]


def test_library_propagates_to_direct_and_section_tracks(builder):
    kick = DrumSynth.kick(sample_rate=8000)
    library = SampleLibrary().add(kick, key="kick")
    builder.samples(library)
    builder.track("FX").sample("kick", beat=3)
    builder.drums().use_sample("kick", "kick").kick(beats=[0])
    section = builder.section("Verse", 1)
    section.track("FX").sample("kick", beat=0)
    assert section.build().tracks[0].placements[0].sample is kick
    assert builder.build().tracks[0].placements[0].sample is kick


def test_keygroup_uses_common_track_api(builder):
    program = KeygroupProgram.from_sample(DrumSynth.kick(sample_rate=8000), root_note="C4")
    keys = builder.keygroup("Keys", program)
    assert isinstance(keys, TrackBuilder)
    keys.note("C4", beat=0, duration=1).volume(0.5).pan(0.2).effect(Gain(0.8))
    keys.mute().solo()
    track = keys.build()
    assert track.muted and track.solo
    assert track.volume == 0.5
    assert track.pan == 0.2
    assert len(track.placements) == len(track.effects) == 1
    section = builder.section("Verse", 1)
    assert section.add_keygroup("Keys", program, lambda k: k.note("E4", 0)) is section
    assert len(section.build().tracks[0].placements) == 1


def test_legacy_generic_track_defaults_remain_compatible(builder):
    builder.add_track("Legacy")
    builder.track("Direct")
    assert builder.build().tracks[0].track_type == TrackType.DRUMS
    assert builder.build().tracks[1].track_type == TrackType.FX
    section = builder.section("Verse", 1).add_track("FX").build()
    assert section.tracks[0].track_type == TrackType.FX


@pytest.mark.parametrize("kwargs", [
    {"bpm": 0}, {"bpm": -1}, {"bpm": float("nan")}, {"bpm": float("inf")},
    {"bars": 0}, {"bars": 1.5}, {"bars": True},
    {"sample_rate": 0}, {"sample_rate": 8000.5},
])
def test_invalid_constructor_settings_fail_early(kwargs):
    with pytest.raises(ValueError):
        create_song(**kwargs)
    with pytest.raises(ValueError):
        SongBuilder(**kwargs)


@pytest.mark.parametrize("method,args", [
    ("tempo", (0,)), ("bars", (0,)), ("sample_rate", (0,)),
    ("time_signature", (0, 4)), ("time_signature", (4, 0)),
    ("section", ("Verse", 0)),
])
def test_invalid_fluent_settings_fail_early(builder, method, args):
    with pytest.raises(ValueError):
        getattr(builder, method)(*args)


def test_spc700_helpers_import_optional_package(builder, monkeypatch):
    calls = []

    class SPCBuilder:
        def __init__(self, engine, bpm):
            calls.append((engine, bpm))

        def render(self, sample_rate, tail):
            return AudioData.silence(0.1, sample_rate)

    def echo(*args):
        calls.append(args)
        return Gain(1)

    monkeypatch.setitem(sys.modules, "beatmaker_spc700", SimpleNamespace(
        SPC700SongBuilder=SPCBuilder, SPC700Echo=echo))
    builder.add_spc700("engine", lambda s: None).master_spc700_echo()
    assert calls[0] == ("engine", 120)
    assert len(builder.build().tracks) == 1
    assert len(builder.build().master_effects) == 1
