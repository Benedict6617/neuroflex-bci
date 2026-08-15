"""Simulated inductive wireless-charging session manager for the implant battery.

Tracks state of charge and a simplified thermal model, and exposes the
`charging_active` flag consumed by the safety interlock layer (H7:
actuation is disabled while a charging session is active, per common
practice for active implantable devices with inductive charging).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class ChargingStatus(str, Enum):
    IDLE = "idle"
    CHARGING = "charging"
    COMPLETE = "complete"
    THERMAL_PAUSE = "thermal_pause"
    FAULT = "fault"


@dataclass
class WirelessChargingSession:
    capacity_mah: float = 220.0
    state_of_charge_pct: float = 100.0
    max_coil_temp_c: float = 41.0  # implant coil safety ceiling
    ambient_temp_c: float = 32.0

    status: ChargingStatus = ChargingStatus.IDLE
    coil_temp_c: float = 32.0
    _last_tick: float | None = None

    def start(self) -> None:
        if self.state_of_charge_pct >= 100.0:
            self.status = ChargingStatus.COMPLETE
            return
        self.status = ChargingStatus.CHARGING
        self._last_tick = time.time()

    def tick(self, elapsed_s: float, charge_rate_pct_per_min: float = 2.0, coupling_efficiency: float = 0.85) -> None:
        """Advance the simulated charging session by `elapsed_s` seconds."""
        if self.status not in (ChargingStatus.CHARGING, ChargingStatus.THERMAL_PAUSE):
            return

        # Simple thermal model: coil heats while charging, cools toward ambient otherwise.
        if self.status == ChargingStatus.CHARGING:
            self.coil_temp_c += 0.6 * coupling_efficiency * (elapsed_s / 60.0)
        else:
            self.coil_temp_c -= 0.4 * (elapsed_s / 60.0)
        self.coil_temp_c = max(self.ambient_temp_c, self.coil_temp_c)

        if self.coil_temp_c >= self.max_coil_temp_c:
            self.status = ChargingStatus.THERMAL_PAUSE
            return

        if self.status == ChargingStatus.CHARGING:
            self.state_of_charge_pct = min(
                100.0, self.state_of_charge_pct + charge_rate_pct_per_min * (elapsed_s / 60.0)
            )
            if self.coil_temp_c < self.max_coil_temp_c - 2.0:
                self.status = ChargingStatus.CHARGING  # resume from thermal pause once cooled

            if self.state_of_charge_pct >= 100.0:
                self.status = ChargingStatus.COMPLETE

    @property
    def charging_active(self) -> bool:
        return self.status in (ChargingStatus.CHARGING, ChargingStatus.THERMAL_PAUSE)

    def stop(self) -> None:
        self.status = ChargingStatus.IDLE
