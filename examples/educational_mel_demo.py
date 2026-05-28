"""
Educational MEL Demo — The "Magic" Experience

This script demonstrates the MAGNETRON ENERGY LENS concept in a way that
feels elegant and nearly frictionless to a human observer, while the
internal EnergyAuditor proves that every single joule is accounted for.

Run with:
    python -m examples.educational_mel_demo
"""

from victor_mel.mel.mel_controller import MELController
from victor_mel.primitives.energy_auditor import EnergyAuditor
from victor_mel.primitives.resonance import ResonanceEngine
from victor_mel.algorithms.pfeho import PiezoFractalEnergyHarvestingOptimizer
import time
import random


def main():
    print("\n" + "=" * 70)
    print("  MAGNETRON ENERGY LENS (MEL) — Educational Perception Demo")
    print("  MASSIVEMAGNETICS / Victor Bloodline")
    print("=" * 70 + "\n")

    print("Initializing MEL system with full energy sovereignty...\n")

    auditor = EnergyAuditor(name="demo_mel", tolerance_joules=0.8)
    resonance = ResonanceEngine(name="demo_mel")
    mel = MELController(auditor=auditor, resonance=resonance)

    # Pre-spin the flywheel to a nice operating point (feels "alive")
    print(">> Spinning up maglev flywheel to elegant operating speed...")
    mel.flywheel.charge(380, 18.0)  # ~6.8 kJ stored

    time.sleep(0.6)

    print(">> Engaging resonant wireless field lens (metamaterial enhanced)...\n")

    # Optional: Activate PFEHO harvesting skin (makes the system feel even more self-sustaining)
    pfeho = PiezoFractalEnergyHarvestingOptimizer(auditor=auditor)
    print(">> Activating PFEHO piezo-fractal harvesting layer...")

    # Simulate some vibration from the "machine"
    vibration = [random.uniform(0.3, 1.8) for _ in range(12)]
    harvest_snapshot = pfeho.step(
        raw_vibration=vibration,
        current_load_w=145,
        flywheel_soc=mel.flywheel.stored_energy_j / 250000,
        ultracap_soc=0.65,
    )
    print(f"   → Predicted harvest: {harvest_snapshot.predicted_harvest_w:.2f} W | Net eff: {harvest_snapshot.net_efficiency:.1%}")

    # The "magic" part the user experiences
    result = mel.maintain_power(load_w=145, duration_s=45)

    print("\n" + "-" * 70)
    print("DEMO RESULTS")
    print("-" * 70)

    status = result["final_status"]
    print(f"Final RPM:              {status.rpm:,.0f}")
    print(f"Stored Energy:          {status.stored_kj:.1f} kJ")
    print(f"Wireless Efficiency:    {status.wireless_efficiency * 100:.1f}%")
    print(f"MEL Elegance Score:     {status.resonance_score:.3f} / 1.000")
    print(f"Energy Violations:      {status.energy_violations}")
    print(f"System feels 'magical': {status.elegant}")

    print("\n" + "-" * 70)
    print("ENERGY AUDIT (The Truth Behind the Magic)")
    print("-" * 70)

    report = mel.get_energy_report()
    snap = auditor.get_snapshot()

    print(f"Total Energy In:        {snap.total_in_j:,.1f} J")
    print(f"Total Energy Out:       {snap.total_out_j:,.1f} J")
    print(f"Net Delta Stored:       {snap.delta_stored_j:,.1f} J")
    print(f"Accounted Losses:       {snap.net_loss_j:,.1f} J")
    print(f"Apparent Violation:     {snap.apparent_violation}")

    if snap.apparent_violation:
        print("\nWARNING: Energy imbalance detected. This should never happen in production.")
    else:
        print("\nSUCCESS: ENERGY BALANCE VERIFIED - 0 violations within tolerance.")

    print("\n" + "=" * 70)
    print("This is what a real MEL system feels like to the user:")
    print("  Silent. Elegant. Adaptive. Almost infinite.")
    print("But every watt was measured, logged, and balanced.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
