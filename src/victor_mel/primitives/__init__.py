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

__all__ = [
    "EnergyAuditor",
    "EnergyConservationViolation",
    "EnergyDomain",
    "EnergyTransaction",
    "LedgerSnapshot",
]
