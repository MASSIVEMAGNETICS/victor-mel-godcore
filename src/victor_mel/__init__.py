"""
victor-mel-godcore

Victor DNA + MAGNETRON ENERGY LENS (MEL)
Battle-tested, physics-honest, energy-audited framework.

Every joule is accounted for. No over-unity. Truth only.
"""

from .primitives import EnergyAuditor, ResonanceEngine
from .mel import MELController, MaglevFlywheel, ResonantCoupler

__version__ = "1.0.0"
__all__ = [
    "EnergyAuditor",
    "ResonanceEngine",
    "MELController",
    "MaglevFlywheel",
    "ResonantCoupler",
]
