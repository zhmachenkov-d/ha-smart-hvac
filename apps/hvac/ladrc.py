"""Discrete-time LADRC (first-order ESO + linear outer loop)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from hvac.models import LadrcConfig


@dataclass
class LadrcState:
    z1: float = 0.0
    z2: float = 0.0
    critical_zone: str | None = None
    _last_u_applied: float = field(default=0.0, repr=False)

    def reset(self, measured: float) -> None:
        self.z1 = measured
        self.z2 = 0.0
        self._last_u_applied = 0.0

    def compute_tracking(
        self,
        measured: float,
        reference: float,
        config: LadrcConfig,
        critical_zone: str,
    ) -> float:
        """Compute u_track (°C adjustment); does not advance the ESO."""
        if self.critical_zone != critical_zone:
            self.reset(measured)
            self.critical_zone = critical_zone

        u0 = config.kp * (reference - self.z1)
        u_track = (u0 - self.z2) / config.b0
        return u_track

    def advance(
        self,
        measured: float,
        u_applied: float,
        config: LadrcConfig,
    ) -> None:
        """Advance the ESO one step using the actually applied plant command."""
        dt = config.dt
        error = measured - self.z1
        omega_o = math.sqrt(config.beta2)
        alpha = 1.0 - math.exp(-omega_o * dt)
        g1 = 2.0 * alpha
        g2 = alpha * alpha

        self.z1 = self.z1 + dt * (self.z2 + config.b0 * u_applied) + g1 * error
        self.z2 = self.z2 + g2 * error
        self._last_u_applied = u_applied

    def clear(self) -> None:
        self.z1 = 0.0
        self.z2 = 0.0
        self.critical_zone = None
        self._last_u_applied = 0.0
