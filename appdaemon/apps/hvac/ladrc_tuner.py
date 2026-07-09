"""Online adaptation of LADRC controller bandwidth (omega_c)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from hvac.models import LadrcConfig


class _SensorPublisher(Protocol):
    def set_state(
        self,
        entity_id: str,
        *,
        state: float,
        attributes: dict[str, Any] | None = None,
    ) -> None: ...


class LadrcTuner:
    def __init__(self, config: LadrcConfig, state_path: Path) -> None:
        self._config = config
        self._state_path = state_path
        self._omega_c = config.omega_c
        self._last_critical_zone: str | None = None
        self._steady_ticks = 0
        self._load()

    @property
    def omega_c(self) -> float:
        return self._omega_c

    def clear_steady(self) -> None:
        """Reset steady-tick counter; does not change adapted omega_c."""
        self._steady_ticks = 0

    def maybe_adapt(
        self,
        tracking_error: float,
        critical_zone: str,
        has_demand: bool,
        *,
        apply: bool = True,
    ) -> float | None:
        if not has_demand:
            self._steady_ticks = 0
            return None

        if critical_zone != self._last_critical_zone:
            zone_changed = self._last_critical_zone is not None
            self._last_critical_zone = critical_zone
            self._steady_ticks = 0
            if zone_changed:
                return None

        self._steady_ticks += 1
        tune = self._config.tune
        if self._steady_ticks < tune.min_steady_ticks:
            return None

        if abs(tracking_error) < tune.deadband:
            return None

        delta = tune.ki * tracking_error
        max_delta = tune.max_rate_fraction * self._omega_c
        delta = max(-max_delta, min(max_delta, delta))

        new_omega_c = max(
            self._config.omega_c_min,
            min(self._config.omega_c_max, self._omega_c + delta),
        )
        if new_omega_c == self._omega_c:
            return None

        if apply:
            self._omega_c = new_omega_c
            self._persist()
        return new_omega_c

    def commit_omega_c(self, omega_c: float) -> None:
        self._omega_c = omega_c
        self._persist()

    def publish_sensor(self, app: _SensorPublisher) -> None:
        app.set_state(
            "sensor.hvac_ladrc_omega_c",
            state=round(self._omega_c, 6),
            attributes={"unit_of_measurement": "1/s"},
        )

    def _load(self) -> None:
        if not self._state_path.is_file():
            return
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
            omega_c = float(raw["omega_c"])
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            return
        if not self._config.omega_c_min <= omega_c <= self._config.omega_c_max:
            return
        self._omega_c = omega_c

    def _persist(self) -> None:
        payload = {"omega_c": self._omega_c}
        self._state_path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
