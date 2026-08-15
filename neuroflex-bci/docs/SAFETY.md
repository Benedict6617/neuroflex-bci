# Safety Design

> This document describes the safety architecture of the reference
> implementation. It is written in the style of a hazard analysis to show
> how such a system should be organized, but it is **not** a substitute for
> a formal ISO 14971 risk management file, which would be required before
> any real clinical or investigational use.

## Design principle

The `neuroflex.safety.SafetyInterlock` layer is the single authority that
approves or denies any command sent to the prosthetic actuator. It is
**decoder-agnostic**: it never inspects neural features or model internals,
only the proposed command plus a small set of independently tracked
signals. This means the safety layer keeps working even if the decoder is
wrong, stale, or compromised.

## Hazard analysis (representative, non-exhaustive)

| ID | Hazard | Mitigation | Where implemented |
|---|---|---|---|
| H1 | Involuntary/unintended actuation from a low-confidence decode | Hard confidence floor; command denied below threshold | `SafetyInterlock.evaluate` (`LOW_CONFIDENCE`) |
| H2 | Excessive grip force causing tissue or object damage | Per-grip force ceiling, independent of decoder output | `GRIP_LIBRARY` limits, enforced in `evaluate` (`FORCE_LIMIT`) |
| H3 | Excessive joint velocity causing impact injury | Per-grip velocity ceiling | `GRIP_LIBRARY` limits, enforced in `evaluate` (`VELOCITY_LIMIT`) |
| H4 | Disorienting/hazardous rapid grip switching ("chatter") while holding an object | Debounced grip commitment + chatter-rate interlock | `GripStateMachine`, `SafetyInterlock` (`COMMAND_CHATTER`) |
| H5 | Actuation continuing after signal loss or electrode fault | Command denied if no fresh signal within `max_signal_gap_s` | `SafetyInterlock` (`SIGNAL_LOSS`) |
| H6 | Actuation on stale or failed daily calibration | Calibration age tracked independently; expires after `calibration_max_age_hours` | `SafetyInterlock` (`CALIBRATION_STALE`), `calibration/session.py` |
| H7 | Actuation during active wireless charging (EMI/thermal risk) | Actuation disabled whenever a charging session is active | `SafetyInterlock` (`CHARGING_ACTIVE`), `power/wireless_charging.py` |
| H8 | Control loop hang/deadlock silently stops safety checks | Watchdog heartbeat required every `watchdog_timeout_s`; timeout denies actuation | `SafetyInterlock` (`WATCHDOG_TIMEOUT`) |
| H9 | Excess charge injection during sensory stimulation causing tissue damage | Hard per-pulse charge-density ceiling, validated before any pulse is returned | `sensory_feedback/encoder.py` (`StimulationSafetyError`) |
| H10 | Patient or clinician unable to stop actuation in an emergency | Manual lockout flag, checked first in `evaluate`, settable via API/app | `SafetyInterlock` (`MANUAL_LOCKOUT`), `api/main.py` `/lockout` |
| H11 | Coil overheating during wireless charging | Thermal ceiling pauses charging and is exposed to the interlock layer | `power/wireless_charging.py` (`THERMAL_PAUSE`) |

## Fail-safe defaults

- Every denial path in `SafetyInterlock._deny` returns `grip=REST`,
  `velocity=0`, `force=0` — there is no partial/ambiguous command state.
- Calibration failure keeps the *previous* validated calibration active
  rather than falling back to an unvalidated one; only expiry disables
  actuation.
- The watchdog is checked **before** any other evaluation, so a hung
  control loop cannot produce stale "allowed" decisions.

## What this reference implementation does not include

- Redundant/voting multi-channel signal acquisition hardware
- Independent hardware-level e-stop circuitry (software interlocks alone
  are not sufficient for a real Class III device)
- Formal verification of the interlock logic (recommended: property-based
  testing and, for a real submission, static analysis / formal methods
  appropriate to IEC 62304 Class C software)
- Cybersecurity threat modeling for the wireless (BLE) link (see
  `docs/compliance/` for where this would be documented)

## Testing

`tests/test_safety.py` exercises each interlock trip condition
independently and in combination (see `test_command_chatter_detected`,
`test_clamps_force_and_velocity_to_grip_limits`, etc.). Any change to
`SafetyInterlock` should keep 100% branch coverage on `evaluate()`.
