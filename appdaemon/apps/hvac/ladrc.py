"""Discrete-time LADRC (first-order ESO + linear outer loop)."""

from __future__ import annotations

from dataclasses import dataclass, field

from hvac.models import LadrcConfig


@dataclass
class LadrcState:
    z1: float = 0.0
    z2: float = 0.0
    critical_zone: str | None = None
    _last_u_track: float = field(default=0.0, repr=False)

    def reset(self, measured: float) -> None:
        self.z1 = measured
        self.z2 = 0.0
        self._last_u_track = 0.0

    def step(
        self,
        measured: float,
        reference: float,
        config: LadrcConfig,
        critical_zone: str,
    ) -> float:
        """Advance one control tick; return u_track (°C adjustment)."""
        if self.critical_zone != critical_zone:
            self.reset(measured)
            self.critical_zone = critical_zone

        dt = config.dt
        error = measured - self.z1

        self.z1 = self.z1 + dt * (
            self.z2 + config.beta1 * error + config.b0 * self._last_u_track
        )
        self.z2 = self.z2 + dt * config.beta2 * error

        u0 = config.kp * (reference - self.z1)
        u_track = (u0 - self.z2) / config.b0
        self._last_u_track = u_track
        return u_track

    def clear(self) -> None:
        self.z1 = 0.0
        self.z2 = 0.0
        self.critical_zone = None
        self._last_u_track = 0.0
