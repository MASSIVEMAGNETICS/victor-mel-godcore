"""
Maglev Flywheel Simulator (MEL Core Component)

Models a high-performance carbon-composite rotor in vacuum with magnetic bearings.

Key physics:
- Stored energy: E = ½ I ω²  (joules)
- Power in/out via bidirectional motor/generator
- Extremely low drag due to maglev + vacuum
- Realistic efficiency and self-discharge (standby loss)

All energy deltas are reported through the EnergyAuditor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from ..primitives.energy_auditor import EnergyAuditor, EnergyDomain


@dataclass
class FlywheelState:
    rpm: float
    power_w: float          # Current mechanical power (positive = accelerating)
    efficiency: float       # Instantaneous round-trip efficiency estimate
    temperature_c: float
    vacuum_pa: float        # Pressure in pascals (lower = better)


class MaglevFlywheel:
    """
    High-fidelity (but still simplified) model of a MEL-style maglev flywheel.

    Designed to feel "magical" in operation while remaining 100% energy accountable.
    """

    def __init__(
        self,
        inertia_kg_m2: float = 0.85,           # Realistic for a desktop-to-small-lab rotor
        max_rpm: float = 45_000,
        vacuum_pa: float = 0.01,               # Good vacuum
        auditor: Optional[EnergyAuditor] = None,
        name: str = "mel_flywheel",
    ):
        self.inertia = inertia_kg_m2
        self.max_rpm = max_rpm
        self.vacuum_pa = vacuum_pa
        self.auditor = auditor or EnergyAuditor(name=name)
        self.name = name

        self.rpm: float = 0.0
        self.temperature_c: float = 22.0

        # Very low drag coefficients thanks to maglev + vacuum
        self._windage_coeff = 1.8e-10
        self._bearing_loss_w = 0.8          # Extremely low for active maglev

    @property
    def stored_energy_j(self) -> float:
        """Current kinetic energy in joules."""
        omega = self.rpm * 2 * math.pi / 60
        return 0.5 * self.inertia * omega * omega

    @property
    def state(self) -> FlywheelState:
        power = self._estimate_current_power()
        eff = self._estimate_efficiency()
        return FlywheelState(
            rpm=self.rpm,
            power_w=power,
            efficiency=eff,
            temperature_c=self.temperature_c,
            vacuum_pa=self.vacuum_pa,
        )

    def charge(self, power_w: float, duration_s: float) -> float:
        """
        Inject electrical power for `duration_s` seconds.
        Returns actual energy stored (after losses).
        """
        if power_w < 0:
            return self.discharge(-power_w, duration_s)

        omega = self.rpm * 2 * math.pi / 60
        torque = (power_w * 60) / (2 * math.pi * max(self.rpm, 100))

        # Very high motor efficiency in this regime (GaN/SiC assumed)
        motor_eff = 0.96
        energy_in_elec = power_w * duration_s
        energy_to_rotor = energy_in_elec * motor_eff

        # Apply to kinetic energy
        new_energy = self.stored_energy_j + energy_to_rotor
        new_omega = math.sqrt(max(0, 2 * new_energy / self.inertia))
        new_rpm = new_omega * 60 / (2 * math.pi)

        # Cap at max rpm
        if new_rpm > self.max_rpm:
            new_rpm = self.max_rpm
            new_energy = 0.5 * self.inertia * (new_rpm * 2 * math.pi / 60) ** 2

        delta_stored = new_energy - self.stored_energy_j

        self.rpm = new_rpm

        # Record through auditor
        self.auditor.record(
            EnergyDomain.ELECTRICAL,
            -energy_in_elec,
            "flywheel_charge_input",
            metadata={"power_w": power_w, "duration_s": duration_s},
        )
        self.auditor.record_flywheel_delta(delta_stored, self.rpm, "flywheel_accel")

        self._update_temperature(power_w * (1 - motor_eff) * duration_s)
        return delta_stored

    def discharge(self, power_w: float, duration_s: float) -> float:
        """Extract electrical power. Returns energy actually delivered."""
        if power_w <= 0:
            return 0.0

        omega = self.rpm * 2 * math.pi / 60
        if omega < 1:
            return 0.0

        available_mech_power = omega * (self.inertia * omega * 0.02)  # simplified torque limit
        actual_mech_power = min(power_w / 0.95, available_mech_power)

        energy_from_rotor = actual_mech_power * duration_s
        new_energy = max(0, self.stored_energy_j - energy_from_rotor)
        new_omega = math.sqrt(max(0, 2 * new_energy / self.inertia))
        self.rpm = new_omega * 60 / (2 * math.pi)

        delivered = energy_from_rotor * 0.95  # generator efficiency

        self.auditor.record_flywheel_delta(-energy_from_rotor, self.rpm, "flywheel_decel")
        self.auditor.record(
            EnergyDomain.ELECTRICAL,
            delivered,
            "flywheel_discharge_output",
            metadata={"requested_w": power_w, "actual_w": delivered / duration_s},
        )

        self._update_temperature(energy_from_rotor * 0.05)
        return delivered

    def standby_loss(self, duration_s: float) -> float:
        """Natural losses while spinning (very small thanks to maglev + vacuum)."""
        drag_power = (self._windage_coeff * (self.rpm ** 2.7)) + self._bearing_loss_w
        energy_lost = drag_power * duration_s

        if energy_lost > self.stored_energy_j:
            energy_lost = self.stored_energy_j

        new_energy = self.stored_energy_j - energy_lost
        new_omega = math.sqrt(max(0, 2 * new_energy / self.inertia))
        self.rpm = new_omega * 60 / (2 * math.pi)

        self.auditor.record(
            EnergyDomain.KINETIC,
            -energy_lost,
            "flywheel_standby_drag",
            metadata={"rpm": self.rpm, "vacuum_pa": self.vacuum_pa},
        )
        return energy_lost

    def _estimate_current_power(self) -> float:
        # Rough instantaneous power based on current speed and drag
        return (self._windage_coeff * (self.rpm ** 2.7)) + self._bearing_loss_w

    def _estimate_efficiency(self) -> float:
        # Round-trip efficiency estimate (very high for advanced maglev)
        base = 0.94
        speed_factor = max(0.7, 1.0 - (self.rpm / self.max_rpm) * 0.15)
        return min(0.97, base * speed_factor)

    def _update_temperature(self, heat_j: float) -> None:
        # Extremely simplified thermal model
        self.temperature_c += heat_j * 0.0008
        self.temperature_c = max(18, min(65, self.temperature_c * 0.995))  # passive cooling

    def emergency_stop(self) -> float:
        """Regenerative braking to safe speed. Returns energy recovered."""
        if self.rpm < 500:
            return 0.0
        recovered = self.discharge(self.rpm * 0.8, 8.0)  # aggressive but safe
        return recovered
