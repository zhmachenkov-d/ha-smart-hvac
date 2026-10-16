"""Continuous-form LADRC (first-order ESO + linear outer loop)."""

from __future__ import annotations

from dataclasses import dataclass, field

from hvac.models import LadrcConfig

# Forward Euler: thermal CAP-5 (ωo=0.03, dt=60) needs 2 substeps —
# one step: |1−2·dt·ωo|=2.6 > 1; two (h=30): |1−2·h·ωo|=0.8 < 1.
_ESO_EULER_SUBSTEPS = 2


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
        """Advance the ESO one sample via continuous-form integration.

        Continuous-form ESO (β1=2ωo, β2=ωo²):
            ż1 = z2 + β1(y − z1) + b0·u
            ż2 = β2(y − z1)
        Integrated with forward Euler over equal substeps of the sample.
        """
        h = config.dt / _ESO_EULER_SUBSTEPS
        beta1 = 2.0 * config.omega_o
        beta2 = config.beta2
        for _ in range(_ESO_EULER_SUBSTEPS):
            err = measured - self.z1
            self.z1 = self.z1 + h * (self.z2 + beta1 * err + config.b0 * u_applied)
            self.z2 = self.z2 + h * (beta2 * err)
        self._last_u_applied = u_applied

    def clear(self) -> None:
        self.z1 = 0.0
        self.z2 = 0.0
        self.critical_zone = None
        self._last_u_applied = 0.0
