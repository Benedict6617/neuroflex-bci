# NeuroFlex Companion App — Contract & Wireframe Notes

This folder documents the contract between the NeuroFlex companion mobile
app and the device API (`src/neuroflex/api`). It is a specification +
wireframe reference for the app, not a full app implementation — a real
app would be a separate iOS/Android (e.g. React Native or native) project
consuming this same API contract.

## Screens

### 1. Home / Status
- Current grip (from `GET /status` → `current_grip`)
- Decoder confidence meter (`decoder_confidence`)
- Battery + charging indicator (`battery_pct`, `charging_active`)
- Calibration status badge: "Calibrated today" / "Calibration needed" (`calibration_valid`, `last_calibration_at`)
- Prominent **interlock banner** whenever `interlock_tripped` is true, showing `interlock_reason` in plain language (see mapping table below)

### 2. Mode Switching
- Segmented control: **Assisted** / **Manual Override** / **Locked**
- Calls `POST /mode`
- "Locked" requires a confirmation step (irreversible-feeling action for the patient)

### 3. Daily Calibration
- Guided, cued sequence (progress bar over `cue_sequence`)
- Calls `POST /calibration/start`
- On reject, show plain-language retry guidance (e.g. "check electrode site contact") rather than raw `r2_score`

### 4. Emergency Lockout
- Single, always-reachable button (bottom tab, not buried in settings)
- Calls `POST /lockout` with `locked: true`
- Confirmation-free — an emergency stop should never require a confirm dialog

### 5. Activity Log
- Reads `GET /events`
- Human-readable event feed: calibration attempts, charging sessions, interlock trips, mode switches

## Interlock reason → patient-facing copy

| `interlock_reason` | Suggested app copy |
|---|---|
| `low_confidence` | "Signal wasn't clear enough to move safely — try repositioning or resting a moment." |
| `signal_loss` | "Lost connection to the sensor array — check the implant link." |
| `calibration_stale` | "Today's calibration hasn't been completed yet." |
| `charging_active` | "Hand control is paused while charging." |
| `command_chatter` | "Detected rapid switching — holding current grip for safety." |
| `watchdog_timeout` | "Control system restarted — please wait a moment." |
| `manual_lockout` | "Hand control is locked." |

## Design notes

- Never let the app itself compute or override safety limits — it only
  displays what the device API reports and sends *requests* (mode, lockout,
  calibration) that the device-side safety layer independently validates.
- All safety-relevant actions (lockout on/off, mode change) should be
  logged via `POST /telemetry` for the clinician-facing activity log.
