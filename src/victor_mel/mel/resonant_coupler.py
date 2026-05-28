"""
Resonant Inductive Coupler with Metamaterial Field Enhancement (MEL Layer)

Models near-field wireless power transfer enhanced by engineered magnetic metamaterials.

Core equations used:
- Figure of merit: U = k * sqrt(Q1 * Q2)
- Optimal efficiency: η ≈ U² / (1 + sqrt(1 + U²))²

Metamaterial "lens" can increase effective coupling k or reduce losses in the near field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..primitives.energy_auditor import EnergyAuditor, EnergyDomain
from ..primitives.resonance import ResonanceEngine


@dataclass
class CouplerState:
    distance_m: float
    effective_k: float
    efficiency: float
    power_delivered_w: float
    metamaterial_boost: float


class ResonantCoupler:
    """
    Tuned resonant inductive wireless power link with metamaterial enhancement.

    This is the component that lets the system feel like "power appears from nowhere"
    while remaining fully physics-accountable.
    """

    def __init__(
        self,
        base_coupling_k: float = 0.22,
        q_tx: float = 280,
        q_rx: float = 240,
        metamaterial_enhancement: float = 1.35,   # realistic boost from good metamaterial slab
        auditor: Optional[EnergyAuditor] = None,
        resonance: Optional[ResonanceEngine] = None,
    ):
        self.base_k = base_coupling_k
        self.q_tx = q_tx
        self.q_rx = q_rx
        self.metamaterial_enhancement = metamaterial_enhancement
        self.auditor = auditor or EnergyAuditor(name="mel_resonant_coupler")
        self.resonance = resonance or ResonanceEngine(name="mel_wireless_resonance")

    def get_state(self, distance_m: float, power_request_w: float) -> CouplerState:
        effective_k = min(0.65, self.base_k * self.metamaterial_enhancement)
        u = effective_k * (self.q_tx * self.q_rx) ** 0.5
        eta = (u ** 2) / (1 + (1 + u ** 2) ** 0.5) ** 2 if u > 0 else 0.0

        # Distance penalty (near-field only)
        distance_factor = max(0.15, 1.0 / (1 + (distance_m / 0.35) ** 1.8))
        eta *= distance_factor

        delivered = power_request_w * eta
        return CouplerState(
            distance_m=distance_m,
            effective_k=effective_k,
            efficiency=eta,
            power_delivered_w=delivered,
            metamaterial_boost=self.metamaterial_enhancement,
        )

    def transfer_power(
        self,
        power_requested_w: float,
        distance_m: float = 0.28,
        duration_s: float = 1.0,
    ) -> float:
        """
        Attempt to deliver power wirelessly for `duration_s` seconds.
        Returns actual energy delivered to the load (after all losses).
        """
        state = self.get_state(distance_m, power_requested_w)

        energy_requested = power_requested_w * duration_s
        energy_delivered = state.power_delivered_w * duration_s
        loss = energy_requested - energy_delivered

        # Record input side (what was drawn from the source)
        self.auditor.record(
            EnergyDomain.ELECTRICAL,
            -energy_requested,
            "resonant_tx_input",
            metadata={
                "distance_m": distance_m,
                "requested_w": power_requested_w,
                "effective_k": state.effective_k,
                "metamaterial_boost": state.metamaterial_boost,
            },
        )

        # Record what actually arrived at the receiver
        self.auditor.record(
            EnergyDomain.ELECTRICAL,
            energy_delivered,
            "resonant_rx_delivered",
            metadata={"efficiency": state.efficiency, "distance_m": distance_m},
        )

        # Record the loss explicitly
        if loss > 0:
            self.auditor.record(
                EnergyDomain.ELECTRICAL,
                -loss,
                "resonant_coupling_loss",
                metadata={"reason": "imperfect_k_and_distance"},
            )

        # Update resonance engine for MEL elegance scoring
        self.resonance.mel_field_resonance(
            rpm=0,  # not applicable here
            target_rpm=0,
            coupling_k=state.effective_k,
            load_power_w=power_requested_w,
            available_power_w=energy_requested / duration_s,
        )

        return energy_delivered
