"""
victor_mel.primitives

Hardened, energy-audited Victor DNA building blocks for MEL and the 10 algorithms.
"""

from .energy_auditor import (
    EnergyAuditor,
    EnergyConservationViolation,
    EnergyDomain,
    EnergyTransaction,
    LedgerSnapshot,
)
from .resonance import ResonanceEngine

__all__ = [
    "EnergyAuditor",
    "EnergyConservationViolation",
    "EnergyDomain",
    "EnergyTransaction",
    "LedgerSnapshot",
    "ResonanceEngine",
]
