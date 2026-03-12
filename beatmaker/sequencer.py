"""
靈寶五帝策使編碼之法 - Sequencer Module
Step sequencing in the style of the ancient drum machines.

By the Azure Dragon's authority,
Let patterns emerge like constellations,
Each step a star in the rhythmic sky,
急急如律令敕
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Callable
from enum import Enum, auto
import numpy as np

from .core import AudioData, Sample, Track, TrackType, TimeSignature


class StepValue(Enum):
    """Step sequencer note values."""
    OFF = 0
    ON = 1
    ACCENT = 2
    GHOST = 3  # Soft hit


@dataclass
class Step:
    """A single step in a sequence."""
    active: bool = False
    velocity: float = 1.0
    pitch_offset: int = 0  # Semitones
    probability: float = 1.0  # 0-1, chance of triggering
    flam: bool = False  # Double hit
    num_hits: int = 1  # Number of hits (1=normal, 2=roll, 4=fast roll)

    @classmethod
    def on(cls, velocity: float = 1.0) -> 'Step':
        return cls(active=True, velocity=velocity)

    @classmethod
    def off(cls) -> 'Step':
        return cls(active=False)

    @classmethod
    def accent(cls) -> 'Step':
        return cls(active=True, velocity=1.2)

    @classmethod
    def ghost(cls) -> 'Step':
        return cls(active=True, velocity=0.4)

    @classmethod
    def roll(cls, divisions: int = 2, velocity: float = 0.8) -> 'Step':
        return cls(active=True, velocity=velocity, num_hits=divisions)

    @classmethod
    def prob(cls, probability: float, velocity: float = 1.0) -> 'Step':
        return cls(active=True, velocity=velocity, probability=probability)


@dataclass
class Pattern:
    """
    A rhythmic pattern for step sequencing.

    Supports variable length patterns with per-step control.
    """
    name: str = "Pattern"
    steps: List[Step] = field(default_factory=lambda: [Step() for _ in range(16)])
    length: int = 16  # Pattern length in steps
    swing: float = 0.0  # Swing amount 0-1

    def __post_init__(self):
        # Ensure steps list matches length
        while len(self.steps) < self.length:
            self.steps.append(Step())
        self.steps = self.steps[:self.length]

    @classmethod
    def from_string(cls, pattern_str: str, name: str = "Pattern") -> 'Pattern':
        """
        Create pattern from string notation.

        Characters:
            x or X = hit (X = accent)
            . or - = rest
            o = ghost note
            r = roll

        Example: "x...x...x...x..." = four on the floor
        """
        steps = []
        for char in pattern_str:
            if char in 'xX':
                velocity = 1.2 if char == 'X' else 1.0
                steps.append(Step.on(velocity))
            elif char == 'o':
                steps.append(Step.ghost())
            elif char == 'r':
                steps.append(Step.roll(2))
            else:
                steps.append(Step.off())

        return cls(name=name, steps=steps, length=len(steps))

    @classmethod
    def from_list(cls, hits: List[bool], name: str = "Pattern") -> 'Pattern':
        """Create pattern from boolean list."""
        steps = [Step.on() if hit else Step.off() for hit in hits]
        return cls(name=name, steps=steps, length=len(steps))

    @classmethod
    def from_positions(cls, positions: List[int], length: int = 16,
                       name: str = "Pattern") -> 'Pattern':
        """Create pattern from step positions (0-indexed)."""
        steps = [Step() for _ in range(length)]
        for pos in positions:
            if 0 <= pos < length:
                steps[pos] = Step.on()
        return cls(name=name, steps=steps, length=length)

    def rotate(self, amount: int) -> 'Pattern':
        """Rotate pattern by amount of steps."""
        rotated = self.steps[-amount:] + self.steps[:-amount]
        return Pattern(name=f"{self.name}_rot{amount}", steps=rotated,
                       length=self.length, swing=self.swing)

    def reverse(self) -> 'Pattern':
        """Reverse the pattern."""
        return Pattern(name=f"{self.name}_rev", steps=list(reversed(self.steps)),
                       length=self.length, swing=self.swing)

    def stretch(self, factor: int) -> 'Pattern':
        """Stretch pattern by repeating each step."""
        stretched = []
        for step in self.steps:
            stretched.extend([step] * factor)
        return Pattern(name=f"{self.name}_x{factor}", steps=stretched,
                       length=self.length * factor, swing=self.swing)

    def compress(self, factor: int) -> 'Pattern':
        """Compress pattern by taking every nth step."""
        compressed = self.steps[::factor]
        return Pattern(name=f"{self.name}_/{factor}", steps=compressed,
                       length=len(compressed), swing=self.swing)

    def combine(self, other: 'Pattern', mode: str = 'or') -> 'Pattern':
        """
        Combine two patterns.

        Modes: 'or' (any hit), 'and' (both hit), 'xor' (exclusive)
        """
        max_len = max(self.length, other.length)
        combined = []

        for i in range(max_len):
            s1 = self.steps[i % self.length]
            s2 = other.steps[i % other.length]

            if mode == 'or':
                active = s1.active or s2.active
            elif mode == 'and':
                active = s1.active and s2.active
            elif mode == 'xor':
                active = s1.active != s2.active
            else:
                active = s1.active or s2.active

            velocity = max(s1.velocity if s1.active else 0,
                          s2.velocity if s2.active else 0)
            combined.append(Step(active=active, velocity=velocity))

        return Pattern(name=f"{self.name}+{other.name}", steps=combined,
                       length=max_len, swing=self.swing)

    def __str__(self) -> str:
        chars = []
        for step in self.steps:
            if not step.active:
                chars.append('.')
            elif step.velocity > 1.1:
                chars.append('X')
            elif step.velocity < 0.5:
                chars.append('o')
            elif step.num_hits > 1:
                chars.append('r')
            else:
                chars.append('x')
        return ''.join(chars)


# Classic drum machine patterns
class ClassicPatterns:
    """Pre-built classic drum patterns."""

    # Kick patterns
    FOUR_ON_FLOOR = Pattern.from_string("x...x...x...x...", "four_on_floor")
    KICK_2_AND_4 = Pattern.from_string("....x.......x...", "kick_2_4")
    BOOM_BAP_KICK = Pattern.from_string("x.....x.x.......", "boom_bap_kick")
    TRAP_KICK = Pattern.from_string("x.......x.x.....", "trap_kick")
    DNB_KICK = Pattern.from_string("x.....x.....x...", "dnb_kick")
    BREAKBEAT_KICK = Pattern.from_string("x.....x...x.....", "breakbeat_kick")

    # Snare patterns
    BACKBEAT = Pattern.from_string("....x.......x...", "backbeat")
    TRAP_SNARE = Pattern.from_string("....X.......X...", "trap_snare")
    BREAKBEAT_SNARE = Pattern.from_string("....x.....x.x...", "breakbeat_snare")
    DNB_SNARE = Pattern.from_string("....x.......x...", "dnb_snare")

    # Hi-hat patterns
    EIGHTH_HATS = Pattern.from_string("x.x.x.x.x.x.x.x.", "eighth_hats")
    SIXTEENTH_HATS = Pattern.from_string("xxxxxxxxxxxxxxxx", "sixteenth_hats")
    OFFBEAT_HATS = Pattern.from_string(".x.x.x.x.x.x.x.x", "offbeat_hats")
    TRAP_HATS = Pattern.from_string("x.xxrxx.x.xxrxxx", "trap_hats")

    # Full kit patterns (dict of instrument -> pattern)
    @classmethod
    def house_kit(cls) -> Dict[str, Pattern]:
        return {
            'kick': cls.FOUR_ON_FLOOR,
            'snare': cls.BACKBEAT,
            'hihat': cls.OFFBEAT_HATS,
        }

    @classmethod
    def trap_kit(cls) -> Dict[str, Pattern]:
        return {
            'kick': cls.TRAP_KICK,
            'snare': cls.TRAP_SNARE,
            'hihat': cls.TRAP_HATS,
        }

    @classmethod
    def dnb_kit(cls) -> Dict[str, Pattern]:
        return {
            'kick': cls.DNB_KICK,
            'snare': cls.DNB_SNARE,
            'hihat': cls.EIGHTH_HATS,
        }

    @classmethod
    def boom_bap_kit(cls) -> Dict[str, Pattern]:
        return {
            'kick': cls.BOOM_BAP_KICK,
            'snare': cls.BACKBEAT,
            'hihat': cls.EIGHTH_HATS,
        }


@dataclass
class StepSequencer:
    """
    TR-style step sequencer.

    Manages multiple patterns for different instruments and renders
    them to a Track.
    """
    bpm: float = 120.0
    steps_per_beat: int = 4  # 4 = 16th notes, 2 = 8th notes
    swing: float = 0.0  # Global swing 0-1
    patterns: Dict[str, Pattern] = field(default_factory=dict)
    samples: Dict[str, Sample] = field(default_factory=dict)

    def add_pattern(self, name: str, pattern: Pattern,
                    sample: Optional[Sample] = None) -> 'StepSequencer':
        """Add a pattern for an instrument."""
        self.patterns[name] = pattern
        if sample:
            self.samples[name] = sample
        return self

    def set_sample(self, name: str, sample: Sample) -> 'StepSequencer':
        """Set the sample for an instrument."""
        self.samples[name] = sample
        return self

    def load_kit(self, kit: Dict[str, Pattern],
                 samples: Optional[Dict[str, Sample]] = None) -> 'StepSequencer':
        """Load a full kit of patterns."""
        for name, pattern in kit.items():
            self.patterns[name] = pattern
            if samples and name in samples:
                self.samples[name] = samples[name]
        return self

    def load_samples_from(self, library, mapping: Dict[str, str]) -> 'StepSequencer':
        """
        Load samples from a SampleLibrary using a name-to-key mapping.

        Args:
            library: A ``SampleLibrary`` instance.
            mapping: Dict mapping pattern/instrument names to library keys.

        Example::

            seq.load_samples_from(lib, {
                "kick":  "drums/kick",
                "snare": "drums/snare",
                "hat":   "drums/hat_closed",
            })
        """
        for instrument_name, library_key in mapping.items():
            self.samples[instrument_name] = library[library_key]
        return self

    def _get_step_time(self, step: int, pattern: Pattern) -> float:
        """Get the time in seconds for a step, including swing."""
        step_duration = 60.0 / self.bpm / self.steps_per_beat
        base_time = step * step_duration

        # Apply swing to off-beats
        swing_amount = pattern.swing if pattern.swing else self.swing
        if swing_amount > 0 and step % 2 == 1:
            base_time += step_duration * swing_amount * 0.5

        return base_time

    def render_pattern(self, name: str, bars: int = 1,
                       sample: Optional[Sample] = None) -> List[tuple]:
        """
        Render a pattern to a list of (time, velocity, sample) tuples.
        """
        if name not in self.patterns:
            return []

        pattern = self.patterns[name]
        sample = sample or self.samples.get(name)

        if not sample:
            return []

        events = []
        steps_per_bar = self.steps_per_beat * 4  # Assuming 4/4
        total_steps = bars * steps_per_bar

        for bar in range(bars):
            for step in range(pattern.length):
                global_step = bar * steps_per_bar + step
                if global_step >= total_steps:
                    break

                s = pattern.steps[step]
                if not s.active:
                    continue

                # Check probability
                if s.probability < 1.0 and np.random.random() > s.probability:
                    continue

                base_time = self._get_step_time(global_step, pattern)

                # Handle rolls
                if s.num_hits > 1:
                    roll_duration = 60.0 / self.bpm / self.steps_per_beat / s.num_hits
                    for r in range(s.num_hits):
                        roll_vel = s.velocity * (1.0 - r * 0.1)  # Decreasing velocity
                        events.append((base_time + r * roll_duration, roll_vel, sample))
                else:
                    events.append((base_time, s.velocity, sample))
                
                # Handle flam
                if s.flam:
                    flam_time = base_time + 0.02  # 20ms after
                    events.append((flam_time, s.velocity * 0.6, sample))
        
        return events
    
    def render_to_track(self, bars: int = 4, name: str = "Sequencer",
                        track_type: TrackType = TrackType.DRUMS) -> Track:
        """Render all patterns to a single track."""
        track = Track(name=name, track_type=track_type)
        
        for pattern_name in self.patterns:
            events = self.render_pattern(pattern_name, bars)
            for time, velocity, sample in events:
                track.add(sample, time, velocity)
        
        return track
    
    def apply_groove(self, groove_template) -> 'StepSequencer':
        """
        Apply a GrooveTemplate to this sequencer's swing and velocity.

        The groove template's timing offsets and velocity scales
        are baked into each pattern's steps.

        Args:
            groove_template: a GrooveTemplate instance from the expression module.

        Returns:
            self for chaining.
        """
        for name, pattern in self.patterns.items():
            template_len = groove_template.length
            for i, step in enumerate(pattern.steps):
                if step.active:
                    groove_idx = i % template_len
                    step.velocity *= groove_template.velocity_scales[groove_idx]
        return self

    def create_variation(self, variation_type: str = 'fill') -> 'StepSequencer':
        """Create a variation of current patterns."""
        new_seq = StepSequencer(
            bpm=self.bpm,
            steps_per_beat=self.steps_per_beat,
            swing=self.swing,
            samples=self.samples.copy()
        )
        
        for name, pattern in self.patterns.items():
            if variation_type == 'fill':
                # Add more hits for fills
                if 'snare' in name.lower():
                    new_pattern = Pattern.from_string(
                        "....x...x.xxx.xx", f"{pattern.name}_fill"
                    )
                elif 'kick' in name.lower():
                    new_pattern = pattern
                else:
                    new_pattern = pattern
            elif variation_type == 'sparse':
                # Remove some hits
                new_steps = []
                for i, step in enumerate(pattern.steps):
                    if step.active and np.random.random() > 0.3:
                        new_steps.append(step)
                    else:
                        new_steps.append(Step.off())
                new_pattern = Pattern(f"{pattern.name}_sparse", new_steps, pattern.length)
            elif variation_type == 'double':
                # Double the density
                new_pattern = pattern.stretch(1)  # Actually we just add more hits
                for i in range(len(new_pattern.steps)):
                    if i % 2 == 1 and not new_pattern.steps[i].active:
                        if np.random.random() > 0.5:
                            new_pattern.steps[i] = Step.ghost()
            else:
                new_pattern = pattern
            
            new_seq.patterns[name] = new_pattern
        
        return new_seq


class EuclideanPattern:
    """
    Generate Euclidean rhythms.
    
    Euclidean rhythms distribute n hits as evenly as possible
    across k steps, creating interesting polyrhythmic patterns.
    """
    
    @staticmethod
    def generate(hits: int, steps: int, rotation: int = 0) -> Pattern:
        """
        Generate a Euclidean rhythm pattern.
        
        Args:
            hits: Number of hits to distribute
            steps: Total number of steps
            rotation: Rotate pattern by this many steps
        
        Examples:
            E(3,8) = "x..x..x." - Cuban tresillo
            E(5,8) = "x.xx.xx." - Cuban cinquillo
            E(7,12) = "x.xx.x.xx.x." - West African bell pattern
        """
        if hits > steps:
            hits = steps
        if hits <= 0:
            return Pattern.from_string('.' * steps, f"E(0,{steps})")
        
        # Bjorklund's algorithm
        pattern = []
        counts = []
        remainders = []
        
        divisor = steps - hits
        remainders.append(hits)
        level = 0
        
        while remainders[level] > 1:
            counts.append(divisor // remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level += 1
        
        counts.append(divisor)
        
        def build(level):
            if level == -1:
                pattern.append(False)
            elif level == -2:
                pattern.append(True)
            else:
                for _ in range(counts[level]):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)
        
        build(level)
        
        # Convert to Steps
        steps_list = [Step.on() if hit else Step.off() for hit in pattern]
        
        # Apply rotation
        if rotation != 0:
            steps_list = steps_list[-rotation:] + steps_list[:-rotation]
        
        return Pattern(
            name=f"E({hits},{steps})",
            steps=steps_list,
            length=len(steps_list)
        )
    
    @staticmethod
    def common_patterns() -> Dict[str, Pattern]:
        """Common Euclidean rhythm patterns."""
        return {
            'tresillo': EuclideanPattern.generate(3, 8),      # Cuban
            'cinquillo': EuclideanPattern.generate(5, 8),     # Cuban
            'bembé': EuclideanPattern.generate(7, 12),        # West African
            'aksak': EuclideanPattern.generate(4, 9),         # Turkish
            'rumba': EuclideanPattern.generate(5, 12),        # Afro-Cuban
            'soukous': EuclideanPattern.generate(5, 16),      # Central African
        }


@dataclass
class PolyrhythmGenerator:
    """Generate polyrhythmic patterns."""
    
    @staticmethod
    def create(rhythm_a: int, rhythm_b: int, steps: int = 16) -> tuple:
        """
        Create two patterns that form a polyrhythm.
        
        Args:
            rhythm_a: First rhythm (e.g., 3 for 3 beats)
            rhythm_b: Second rhythm (e.g., 4 for 4 beats)
            steps: Pattern length
        
        Returns:
            Tuple of two patterns
        """
        pattern_a = [False] * steps
        pattern_b = [False] * steps
        
        # Distribute rhythm_a hits
        for i in range(rhythm_a):
            pos = int(i * steps / rhythm_a)
            pattern_a[pos] = True
        
        # Distribute rhythm_b hits
        for i in range(rhythm_b):
            pos = int(i * steps / rhythm_b)
            pattern_b[pos] = True
        
        return (
            Pattern.from_list(pattern_a, f"poly_{rhythm_a}"),
            Pattern.from_list(pattern_b, f"poly_{rhythm_b}")
        )
