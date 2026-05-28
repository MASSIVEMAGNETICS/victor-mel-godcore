"""
Critical energy balance tests.

These tests must never be allowed to pass if the system appears to create energy.
"""

import pytest
from victor_mel.primitives.energy_auditor import EnergyAuditor, EnergyDomain
from victor_mel.mel.mel_controller import MELController


def test_energy_auditor_basic_conservation():
    auditor = EnergyAuditor(tolerance_joules=0.1)

    auditor.record(EnergyDomain.ELECTRICAL, 1000.0, "input")
    auditor.record(EnergyDomain.KINETIC, -850.0, "stored")
    auditor.record(EnergyDomain.ELECTRICAL, -120.0, "loss")

    snap = auditor.get_snapshot()

    assert not snap.apparent_violation
    assert abs(snap.net_loss_j) < 50  # reasonable losses


def test_mel_demo_run_produces_no_violation():
    """The educational demo must run cleanly with zero violations."""
    auditor = EnergyAuditor(name="test_mel", tolerance_joules=2.0)
    mel = MELController(auditor=auditor)

    # Pre-charge
    mel.flywheel.charge(300, 12)

    # Run a short cycle
    mel.maintain_power(load_w=80, duration_s=12)

    snap = auditor.get_snapshot()
    assert not snap.apparent_violation, f"Energy violation detected: {snap.net_loss_j} J"


def test_flywheel_round_trip_reasonable_efficiency():
    auditor = EnergyAuditor(tolerance_joules=1.0)
    from victor_mel.mel.flywheel import MaglevFlywheel

    fw = MaglevFlywheel(auditor=auditor)
    fw.charge(500, 10)  # charge
    delivered = fw.discharge(400, 8)  # discharge

    # We expect > 80% round trip in this model
    assert delivered > 3200, "Flywheel efficiency unrealistically low"
