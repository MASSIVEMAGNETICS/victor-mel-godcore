"""
Base classes and interfaces for Victor-DNA algorithms.

All algorithms in this package should inherit from or follow the patterns here
to guarantee consistent energy auditing and MEL integration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..primitives.energy_auditor import EnergyAuditor


@dataclass
class AlgorithmResult:
    output: Any
    energy_cost_j: float
    metadata: Dict[str, Any]


class VictorAlgorithm(ABC):
    """
    Abstract base for all Victor-DNA algorithms.

    Guarantees:
    - Every forward pass goes through an EnergyAuditor
    - Consistent result shape
    - MEL context awareness (optional)
    """

    def __init__(self, name: str, auditor: Optional[EnergyAuditor] = None):
        self.name = name
        self.auditor = auditor or EnergyAuditor(name=name)

    @abstractmethod
    def forward(self, *args, **kwargs) -> AlgorithmResult:
        """Main computation. Must record energy usage via self.auditor."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}>"
