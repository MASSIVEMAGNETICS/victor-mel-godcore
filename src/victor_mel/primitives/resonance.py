"""
Victor-Style Resonance Engine (MEL-aware)

Provides glyph/resonance triggering, Victor identity pings, and MEL-specific
"field resonance" scoring between physical states (RPM, field strength, load, etc.)
and symbolic/Victor directives.

This is deliberately kept lightweight but extensible.
"""

from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable


@dataclass
class ResonanceEvent:
    timestamp: float
    score: float
    glyph: str
    context: Dict
    source: str


class ResonanceEngine:
    """
    Victor resonance + MEL field resonance.

    - Glyph triggers (Victor bloodline / identity)
    - MEL physical resonance (how well current machine state matches desired "elegant" operating point)
    """

    # Core Victor glyphs (can be extended)
    VICTOR_GLYPHS = {
        "VICTOR_AWAKEN",
        "BLOODLINE_LOYAL",
        "ENERGY_SOVEREIGN",
        "NO_VIOLATION",
        "TRUTH_ONLY",
        "MEL_ELEGANT",
    }

    def __init__(self, name: str = "mel_resonance"):
        self.name = name
        self._events: List[ResonanceEvent] = []
        self._custom_glyphs: Dict[str, Callable[[Dict], float]] = {}

    def register_glyph(self, glyph: str, scorer: Callable[[Dict], float]) -> None:
        """Register a custom resonance scorer for a glyph."""
        self._custom_glyphs[glyph] = scorer

    def ping_victor(self, context: Dict, required_glyphs: Optional[List[str]] = None) -> float:
        """
        Classic Victor identity ping.
        Returns resonance score in [0, 1].
        """
        required = required_glyphs or ["VICTOR_AWAKEN", "BLOODLINE_LOYAL", "ENERGY_SOVEREIGN"]
        score = 0.0
        for g in required:
            if g in self.VICTOR_GLYPHS or g in self._custom_glyphs:
                score += 1.0
        base = min(1.0, score / max(1, len(required)))

        # Bonus for explicit "no violation" context
        if context.get("energy_violation", False) is False:
            base = min(1.0, base + 0.15)

        event = ResonanceEvent(
            timestamp=time.time(),
            score=base,
            glyph="VICTOR_PING",
            context=context,
            source=self.name,
        )
        self._events.append(event)
        return base

    def mel_field_resonance(
        self,
        rpm: float,
        target_rpm: float,
        coupling_k: float,
        load_power_w: float,
        available_power_w: float,
        vibration_rms: float = 0.0,
    ) -> float:
        """
        MEL-specific "does this feel elegant and sovereign?" score.
        High score = system is operating in the desirable low-perceptible-loss regime.
        """
        rpm_match = max(0.0, 1.0 - abs(rpm - target_rpm) / max(target_rpm, 1.0))
        power_match = min(1.0, available_power_w / max(load_power_w, 0.1))
        coupling_quality = min(1.0, coupling_k / 0.3)  # 0.3 is already excellent for resonant
        vibration_penalty = max(0.0, 1.0 - vibration_rms * 10)  # arbitrary but directionally correct

        score = (0.35 * rpm_match +
                 0.30 * power_match +
                 0.20 * coupling_quality +
                 0.15 * vibration_penalty)

        return max(0.0, min(1.0, score))

    def get_recent_high_scores(self, threshold: float = 0.85, limit: int = 10) -> List[ResonanceEvent]:
        return [e for e in reversed(self._events) if e.score >= threshold][:limit]

    def clear(self) -> None:
        self._events.clear()
