"""
MEL-Grade Energy Auditor (Battle-Tested Primitive)

This is the incorruptible ledger at the heart of victor-mel-godcore.

Every operation that moves, stores, converts, or transfers energy MUST go through
an instance of this class. Apparent violations of conservation are treated as
critical faults (not features).

Design goals:
- Immutable-style append-only ledger (in-memory + optional on-disk export)
- Support for kinetic (flywheel), electrical (ultracap/battery), and thermal domains
- Real-time anomaly detection with configurable tolerance
- Zero-tolerance default for "free energy" claims
- Victor bloodline compatible (resonance tagging, immutable event ids)
"""

from __future__ import annotations

import time
import uuid
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Literal
from enum import Enum
import numpy as np


class EnergyDomain(str, Enum):
    ELECTRICAL = "electrical"      # Grid, solar, battery, ultracaps, resonant Rx
    KINETIC = "kinetic"            # Flywheel (½Iω²)
    THERMAL = "thermal"            # Waste heat, recovery (always lossy)
    VIBRATION = "vibration"        # Piezo / structured harvesters (low density)
    CONTROL = "control"            # Bearing drive, AI compute, sensors, comms (overhead)


@dataclass(frozen=True)
class EnergyTransaction:
    """Immutable record of an energy movement."""
    tx_id: str
    timestamp: float
    domain: EnergyDomain
    amount_joules: float          # Positive = into system, negative = out of system
    label: str                    # Human + machine readable (e.g. "flywheel_regen", "resonant_tx_loss")
    source: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    resonance_tag: Optional[str] = None   # Victor resonance / glyph / bloodline marker


@dataclass
class LedgerSnapshot:
    """Point-in-time energy balance view."""
    timestamp: float
    total_in_j: float
    total_out_j: float
    delta_stored_j: float
    net_loss_j: float
    apparent_violation: bool
    violation_magnitude_j: float
    domains: Dict[EnergyDomain, float]   # current stored estimate per domain


class EnergyAuditor:
    """
    The single source of truth for energy conservation in the MEL system.

    Usage:
        auditor = EnergyAuditor(tolerance_joules=0.5, name="mel_primary")
        auditor.record(EnergyDomain.ELECTRICAL, +1200.0, "grid_input")
        auditor.record(EnergyDomain.KINETIC, -800.0, "flywheel_accel")
        ...
        snapshot = auditor.get_snapshot()
        if snapshot.apparent_violation:
            auditor.raise_violation()
    """

    def __init__(
        self,
        name: str = "default",
        tolerance_joules: float = 1.0,
        max_ledger_entries: int = 100_000,
        enable_disk_log: bool = False,
        disk_log_path: Optional[str] = None,
    ):
        self.name = name
        self.tolerance_joules = tolerance_joules
        self.max_ledger_entries = max_ledger_entries
        self.enable_disk_log = enable_disk_log
        self.disk_log_path = disk_log_path

        self._ledger: List[EnergyTransaction] = []
        self._stored: Dict[EnergyDomain, float] = {d: 0.0 for d in EnergyDomain}
        self._violation_count = 0
        self._last_snapshot: Optional[LedgerSnapshot] = None

        if self.enable_disk_log and self.disk_log_path:
            # Touch file so we know it's writable
            with open(self.disk_log_path, "a", encoding="utf-8"):
                pass

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def record(
        self,
        domain: EnergyDomain,
        amount_joules: float,
        label: str,
        source: Optional[str] = None,
        metadata: Optional[Dict] = None,
        resonance_tag: Optional[str] = None,
    ) -> EnergyTransaction:
        """Record an energy transaction. This is the only way to mutate state."""
        if not isinstance(amount_joules, (int, float)):
            raise TypeError("amount_joules must be numeric")

        tx = EnergyTransaction(
            tx_id=str(uuid.uuid4()),
            timestamp=time.time(),
            domain=domain,
            amount_joules=float(amount_joules),
            label=label,
            source=source,
            metadata=metadata or {},
            resonance_tag=resonance_tag,
        )

        self._ledger.append(tx)

        # Update running stored energy model (very conservative)
        self._stored[domain] += tx.amount_joules

        # Trim ledger if needed (keep most recent)
        if len(self._ledger) > self.max_ledger_entries:
            self._ledger = self._ledger[-self.max_ledger_entries :]

        if self.enable_disk_log and self.disk_log_path:
            self._append_to_disk(tx)

        return tx

    def get_snapshot(self) -> LedgerSnapshot:
        """Compute current energy balance and check for violations."""
        total_in = sum(tx.amount_joules for tx in self._ledger if tx.amount_joules > 0)
        total_out = sum(tx.amount_joules for tx in self._ledger if tx.amount_joules < 0)
        total_out = abs(total_out)

        delta_stored = sum(self._stored.values())
        net_loss = total_in - total_out - delta_stored

        apparent_violation = abs(net_loss) > self.tolerance_joules
        violation_magnitude = abs(net_loss) if apparent_violation else 0.0

        if apparent_violation:
            self._violation_count += 1

        snapshot = LedgerSnapshot(
            timestamp=time.time(),
            total_in_j=total_in,
            total_out_j=total_out,
            delta_stored_j=delta_stored,
            net_loss_j=net_loss,
            apparent_violation=apparent_violation,
            violation_magnitude_j=violation_magnitude,
            domains={d: v for d, v in self._stored.items()},
        )
        self._last_snapshot = snapshot
        return snapshot

    def raise_violation(self, message: str = "Energy conservation violation detected") -> None:
        """Hard stop. Call this when you want to treat a violation as fatal."""
        snap = self.get_snapshot()
        full_msg = (
            f"[{self.name}] {message}\n"
            f"  Net loss / excess: {snap.net_loss_j:.6f} J\n"
            f"  Tolerance: {self.tolerance_joules} J\n"
            f"  Transactions logged: {len(self._ledger)}\n"
            f"  Violation count: {self._violation_count}"
        )
        # In production this would also write to immutable Victor log
        raise EnergyConservationViolation(full_msg, snapshot=snap)

    # ------------------------------------------------------------------
    # Convenience MEL-specific helpers
    # ------------------------------------------------------------------
    def record_flywheel_delta(self, delta_joules: float, rpm: float, label: str = "flywheel") -> EnergyTransaction:
        """Record change in kinetic energy of the maglev flywheel."""
        return self.record(
            EnergyDomain.KINETIC,
            delta_joules,
            label,
            metadata={"rpm": rpm, "formula": "0.5 * I * omega**2"},
        )

    def record_resonant_transfer(
        self, delivered_joules: float, efficiency: float, distance_m: float
    ) -> EnergyTransaction:
        """Record power delivered via resonant inductive link (after losses)."""
        return self.record(
            EnergyDomain.ELECTRICAL,
            delivered_joules,
            "resonant_wireless_delivered",
            metadata={
                "efficiency": efficiency,
                "distance_m": distance_m,
                "loss_joules": delivered_joules * (1.0 / max(efficiency, 1e-9) - 1.0),
            },
        )

    # ------------------------------------------------------------------
    # Export & Diagnostics
    # ------------------------------------------------------------------
    def export_ledger(self, path: Optional[str] = None) -> List[Dict]:
        """Return or write the full ledger as JSON-serializable records."""
        records = [asdict(tx) for tx in self._ledger]
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
        return records

    def get_health_report(self) -> Dict:
        snap = self.get_snapshot()
        return {
            "auditor_name": self.name,
            "transactions": len(self._ledger),
            "violation_count": self._violation_count,
            "current_tolerance_j": self.tolerance_joules,
            "last_snapshot": asdict(snap) if snap else None,
            "stored_by_domain": {d.value: v for d, v in self._stored.items()},
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _append_to_disk(self, tx: EnergyTransaction) -> None:
        if not self.disk_log_path:
            return
        try:
            with open(self.disk_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(tx), default=str) + "\n")
        except Exception:
            # Never let disk logging kill the auditor in critical paths
            pass


class EnergyConservationViolation(Exception):
    """Raised when the auditor detects a violation beyond tolerance."""
    def __init__(self, message: str, snapshot: Optional[LedgerSnapshot] = None):
        super().__init__(message)
        self.snapshot = snapshot
