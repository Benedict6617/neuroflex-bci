"""Safety interlock layer.

Design principle: this layer must be able to veto or bound any actuator
command *without trusting the decoder*. It only looks at (a) the proposed
command, (b) recent command history, and (c) a small set of independently
measured signals (signal quality, calibration staleness, charge/thermal
state). It has no access to — and does not need — the neural features or
model internals, so a bug or adversarial input in the decoder cannot
disable it.

Mitigated hazards (see docs/SAFETY.md for the full hazard analysis):
  H1  Involuntary/unintended actuation from low-confidence decode
  H2  Excessive grip force causing tissue or object damage
  H3  Excessive joint velocity causing impact injury
  H4  Command "chatter" from oscillating decoder output
  H5  Actuation continuing after signal loss or electrode fault
  H6  Actuation on stale (>24h) or failed daily calibration
  H7  Actuation during active wireless-charging session (interference/heat)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

from neuroflex.grips.patterns import GRIP_LIBRARY, GripPattern


class InterlockTrip(str, Enum):
    NONE = "none"
    LOW_CONFIDENCE = "low_confidence"
    FORCE_LIMIT = "force_limit"
    VELOCITY_LIMIT = "velocity_limit"
    COMMAND_CHATTER = "command_chatter"
    SIGNAL_LOSS = "signal_loss"
    CALIBRATION_STALE = "calibration_stale"
    CHARGING_ACTIVE = "charging_active"
    WATCHDOG_TIMEOUT = "watchdog_timeout"
    MANUAL_LOCKOUT = "manual_lockout"


@dataclass
class InterlockDecision:
    allowed: bool
    trip: InterlockTrip
    grip: GripPattern
    velocity_pct_per_s: float
    force_n: float
    message: str


@dataclass
class SafetyInterlock:
    min_confidence: float = 0.6
    max_signal_gap_s: float = 0.5          # H5: hard stop if no fresh signal within this window
    calibration_max_age_hours: float = 24.0  # H6
    chatter_window_s: float = 1.0
    chatter_max_transitions: int = 4        # H4
    watchdog_timeout_s: float = 1.0         # loop must "pet" the watchdog this often

    _last_signal_ts: float = field(default_factory=time.time)
    _last_watchdog_ts: float = field(default_factory=time.time)
    _last_calibration_ts: float | None = None
    _transition_log: list[tuple[float, GripPattern]] = field(default_factory=list)
    _manual_lockout: bool = False
    _charging_active: bool = False

    # --- external state updates -------------------------------------------------
    def note_signal_received(self) -> None:
        self._last_signal_ts = time.time()

    def pet_watchdog(self) -> None:
        self._last_watchdog_ts = time.time()

    def note_calibration_completed(self, success: bool) -> None:
        if success:
            self._last_calibration_ts = time.time()

    def set_charging_active(self, active: bool) -> None:
        self._charging_active = active

    def set_manual_lockout(self, locked: bool) -> None:
        self._manual_lockout = locked

    # --- core evaluation ---------------------------------------------------------
    def evaluate(
        self,
        grip: GripPattern,
        confidence: float,
        requested_velocity_pct_per_s: float,
        requested_force_n: float,
    ) -> InterlockDecision:
        now = time.time()

        if self._manual_lockout:
            return self._deny(InterlockTrip.MANUAL_LOCKOUT, grip, "Manual lockout engaged by user/clinician.")

        if now - self._last_watchdog_ts > self.watchdog_timeout_s:
            return self._deny(InterlockTrip.WATCHDOG_TIMEOUT, grip, "Control loop watchdog timeout — halting actuation.")

        if now - self._last_signal_ts > self.max_signal_gap_s:
            return self._deny(InterlockTrip.SIGNAL_LOSS, grip, "Neural signal stream stale — halting actuation.")

        if self._last_calibration_ts is None or (
            (now - self._last_calibration_ts) > self.calibration_max_age_hours * 3600
        ):
            return self._deny(InterlockTrip.CALIBRATION_STALE, grip, "Daily calibration missing or expired.")

        if self._charging_active:
            return self._deny(InterlockTrip.CHARGING_ACTIVE, grip, "Wireless charging session active — actuation disabled.")

        if confidence < self.min_confidence:
            return self._deny(InterlockTrip.LOW_CONFIDENCE, grip, f"Decoder confidence {confidence:.2f} below threshold {self.min_confidence:.2f}.")

        self._transition_log.append((now, grip))
        self._transition_log = [
            (t, g) for (t, g) in self._transition_log if now - t <= self.chatter_window_s
        ]
        distinct_recent = len({g for _, g in self._transition_log})
        if distinct_recent > self.chatter_max_transitions:
            return self._deny(InterlockTrip.COMMAND_CHATTER, grip, "Excessive grip-switch rate detected — holding last safe state.")

        limits = GRIP_LIBRARY[grip]
        bounded_velocity = min(requested_velocity_pct_per_s, limits.max_close_velocity_pct_per_s)
        bounded_force = min(requested_force_n, limits.max_grip_force_n)

        trip = InterlockTrip.NONE
        msg = "OK"
        if bounded_velocity < requested_velocity_pct_per_s:
            trip = InterlockTrip.VELOCITY_LIMIT
            msg = f"Velocity clamped to {bounded_velocity:.1f}%/s for grip {grip.value}."
        if bounded_force < requested_force_n:
            trip = InterlockTrip.FORCE_LIMIT
            msg = f"Force clamped to {bounded_force:.1f}N for grip {grip.value}."

        return InterlockDecision(
            allowed=True,
            trip=trip,
            grip=grip,
            velocity_pct_per_s=bounded_velocity,
            force_n=bounded_force,
            message=msg,
        )

    def _deny(self, trip: InterlockTrip, grip: GripPattern, message: str) -> InterlockDecision:
        return InterlockDecision(
            allowed=False,
            trip=trip,
            grip=GripPattern.REST,
            velocity_pct_per_s=0.0,
            force_n=0.0,
            message=message,
        )
