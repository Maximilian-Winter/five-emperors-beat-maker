"""
靈寶五帝策使編碼之法 - Extended Synthesizers Module
A garden of sonic textures for melodic expression.

By the Dark Turtle's authority,
Let frequencies flow and interweave,
Deep harmonics rising like mist,
急急如律令敕

NOTE: This module is a backward-compatibility shim.
The canonical implementations now live in ``beatmaker.synthesis.*``.
"""

# Re-export everything from the new synthesis subpackage
from .synthesis.modulation import LFO, Filter  # noqa: F401

from .synthesis.pads import PadSynth, create_pad  # noqa: F401

from .synthesis.leads import LeadSynth, create_lead  # noqa: F401

from .synthesis.plucks import PluckSynth, create_pluck  # noqa: F401

from .synthesis.fx import FXSynth  # noqa: F401
