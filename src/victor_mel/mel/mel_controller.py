"""
MEL Controller — The "Brain" of the MAGNETRON ENERGY LENS

Coordinates the flywheel, resonant wireless link, harvesting, and safety systems
while maintaining strict energy sovereignty through the EnergyAuditor.

This is what makes the system feel intelligent and self-optimizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..primitives.energy_auditor import EnergyAuditor
from ..primitives.resonance import ResonanceEngine
from .flywheel import MaglevFlywheel
from .resonant_coupler import ResonantCoupler


@dataclass
class MELStatus:
    rpm: float
    stored_kj: float
    wireless_efficiency: float
    resonance_score: float
    energy_violations: int
    elegant: bool   # "does it feel magical right now?"


class MELController:
    """
    High-level coordinator for a MEL system.

    Designed so that a human observer sees elegant, nearly invisible power delivery,
    while the internal ledger remains brutally honest.
    """

    def __init__(
        self,
        flywheel: Optional[MaglevFlywheel] = None,
        coupler: Optional[ResonantCoupler] = None,
        auditor: Optional[EnergyAuditor] = None,
        resonance: Optional[ResonanceEngine] = None,
    ):
        self.auditor = auditor or EnergyAuditor(name="mel_system")
        self.resonance = resonance or ResonanceEngine(name="mel_system")
        self.flywheel = flywheel or MaglevFlywheel(auditor=self.auditor)
        self.coupler = coupler or ResonantCoupler(auditor=self.auditor, resonance=self.resonance)

        self.target_rpm = 28_000

    @property
    def status(self) -> MELStatus:
        fw = self.flywheel.state
        coup = self.coupler.get_state(distance_m=0.28, power_request_w=180)

        resonance = self.resonance.mel_field_resonance(
            rpm=fw.rpm,
            target_rpm=self.target_rpm,
            coupling_k=coup.effective_k,
            load_power_w=180,
            available_power_w=fw.power_w,
            vibration_rms=0.08,
        )

        snap = self.auditor.get_snapshot()

        return MELStatus(
            rpm=fw.rpm,
            stored_kj=self.flywheel.stored_energy_j / 1000,
            wireless_efficiency=coup.efficiency,
            resonance_score=resonance,
            energy_violations=snap.violation_magnitude_j,
            elegant=(resonance > 0.82 and snap.violation_magnitude_j < 2.0),
        )

    def maintain_power(self, load_w: float, duration_s: float = 60.0) -> dict:
        """
        Main "magic" loop the user experiences.

        Tries to deliver `load_w` wirelessly for `duration_s` seconds
        while keeping the flywheel happy and the energy ledger clean.
        """
        delivered_total = 0.0

        # 1. Top up the flywheel if needed
        current_stored = self.flywheel.stored_energy_j
        desired = 180_000  # ~180 kJ target buffer
        if current_stored < desired * 0.6:
            needed = desired - current_stored
            self.flywheel.charge(420, needed / 380)

        # 2. Deliver wirelessly
        chunk = 5.0
        steps = int(duration_s / chunk)
        for _ in range(steps):
            delivered = self.coupler.transfer_power(load_w, distance_m=0.28, duration_s=chunk)
            delivered_total += delivered

            # Small standby loss on flywheel
            self.flywheel.standby_loss(chunk * 0.6)

        # 3. Final resonance check
        status = self.status

        return {
            "requested_w": load_w,
            "total_delivered_j": delivered_total,
            "average_efficiency": delivered_total / (load_w * duration_s) if load_w > 0 else 0,
            "final_status": status,
            "violations": self.auditor.get_snapshot().violation_magnitude_j,
        }

    def get_energy_report(self) -> dict:
        return self.auditor.get_health_report()
