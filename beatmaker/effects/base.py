"""
Effect chain for composing multiple effects in sequence.
"""

from ..core import AudioEffect, AudioData


class EffectChain:
    """Chain multiple effects together."""

    def __init__(self, *effects: AudioEffect):
        self.effects = list(effects)

    def add(self, effect: AudioEffect) -> 'EffectChain':
        """Add an effect to the chain."""
        self.effects.append(effect)
        return self

    def process(self, audio: AudioData) -> AudioData:
        """Process audio through all effects in order."""
        result = audio
        for effect in self.effects:
            result = effect.process(result)
        return result

    def __iter__(self):
        return iter(self.effects)
