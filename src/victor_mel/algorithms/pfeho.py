"""
PFEHO — Piezo-Fractal Energy Harvesting Optimizer

This is the most directly MEL-relevant of the 10 algorithms.

It uses fractal decomposition of vibration spectra (from piezo skins or
structural harvesters) and reinforcement-style optimization to decide
real-time routing between ultracaps, flywheel, and loads to maximize
net usable energy while respecting system constraints.

All decisions are energy-audited.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..primitives.energy_auditor import EnergyAuditor, EnergyDomain


@dataclass
class HarvestingSnapshot:
    vibration_spectrum: List[float]   # simplified frequency bins
    predicted_harvest_w: float
    current_routing: Dict[str, float]  # e.g. {"ultracap": 0.6, "flywheel": 0.4}
    net_efficiency: float


class PiezoFractalEnergyHarvestingOptimizer:
    """
    Fractal + RL-inspired optimizer for piezo/metamaterial vibration harvesting
    in a MEL-style system.
    """

    def __init__(self, auditor: Optional[EnergyAuditor] = None):
        self.auditor = auditor or EnergyAuditor(name="pfeho")
        self.name = "PFEHO"

    def analyze_vibration(self, raw_vibration: List[float]) -> List[float]:
        """Very simplified fractal-style decomposition (placeholder for real wavelet/fractal)."""
        # In real version this would be proper fractal / wavelet decomposition
        return [v * 0.92 for v in raw_vibration]  # pretend we filtered noise

    def predict_harvest(self, decomposed: List[float]) -> float:
        """Extremely conservative real-world piezo harvesting model."""
        total = sum(decomposed)
        # Typical good piezo harvester on a machine: very low power density
        return min(12.0, total * 0.018)  # watts, capped realistically

    def optimize_routing(
        self,
        predicted_harvest_w: float,
        current_load_w: float,
        flywheel_soc: float,      # 0-1
        ultracap_soc: float,      # 0-1
    ) -> Dict[str, float]:
        """
        Returns recommended power routing percentages.
        Goal: maximize net usable energy + protect buffers.
        """
        routing = {"ultracap": 0.5, "flywheel": 0.3, "direct_load": 0.2}

        # Simple but effective heuristic (real version would use proper RL or MPC)
        if ultracap_soc < 0.35:
            routing["ultracap"] = min(0.75, routing["ultracap"] + 0.25)
            routing["flywheel"] = max(0.1, routing["flywheel"] - 0.15)

        if flywheel_soc > 0.75 and predicted_harvest_w > 3.0:
            routing["flywheel"] = min(0.55, routing["flywheel"] + 0.2)
            routing["ultracap"] = max(0.2, routing["ultracap"] - 0.15)

        # Normalize
        total = sum(routing.values())
        routing = {k: v / total for k, v in routing.items()}

        # Audit the decision
        self.auditor.record(
            EnergyDomain.VIBRATION,
            predicted_harvest_w,
            "pfeho_harvest_prediction",
            metadata={
                "routing": routing,
                "flywheel_soc": flywheel_soc,
                "ultracap_soc": ultracap_soc,
            },
        )

        return routing

    def step(
        self,
        raw_vibration: List[float],
        current_load_w: float,
        flywheel_soc: float,
        ultracap_soc: float,
    ) -> HarvestingSnapshot:
        """One control step — the main public interface."""
        decomposed = self.analyze_vibration(raw_vibration)
        predicted = self.predict_harvest(decomposed)
        routing = self.optimize_routing(predicted, current_load_w, flywheel_soc, ultracap_soc)

        # Simulate actual harvested power (with losses)
        actual_harvested = predicted * 0.87  # realistic conversion losses

        # Record actual energy entering the system
        self.auditor.record(
            EnergyDomain.VIBRATION,
            actual_harvested,
            "pfeho_actual_harvested",
            metadata={"routing": routing},
        )

        net_eff = actual_harvested / max(current_load_w, 0.1)

        return HarvestingSnapshot(
            vibration_spectrum=decomposed,
            predicted_harvest_w=predicted,
            current_routing=routing,
            net_efficiency=min(1.0, net_eff),
        )
