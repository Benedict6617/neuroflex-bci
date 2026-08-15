"""Generate realistic *synthetic* sample data for the NeuroFlex demo:

- Multi-day recording sessions per patient (feature-level, not raw voltage,
  to keep the repo small) with grip cues, decoder confidence, safety events.
- Daily calibration logs showing drift trends over ~30 days.
- A device event log (mode switches, charging sessions, interlock trips).

All data is generated from random distributions — it is not derived from
or a copy of any real dataset or third-party repository.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

RNG = np.random.default_rng(seed=7)

GRIPS = ["rest", "power", "pinch", "tripod", "point", "lateral_key", "open"]
ROOT = Path(__file__).resolve().parents[1] / "data" / "sample"


def gen_session(patient_id: str, day_offset: int, base_date: datetime, drift_level: float) -> dict:
    session_date = base_date + timedelta(days=day_offset)
    n_trials = int(RNG.integers(40, 70))
    trials = []
    t = 0.0
    for _ in range(n_trials):
        grip = RNG.choice(GRIPS, p=[0.30, 0.15, 0.15, 0.12, 0.10, 0.08, 0.10])
        # Confidence degrades slightly with drift_level and is noisier for rarer grips.
        base_conf = 0.92 - drift_level * 0.18 - (0.05 if grip != "rest" else 0.0)
        confidence = float(np.clip(RNG.normal(base_conf, 0.06), 0.15, 0.99))
        duration_s = float(RNG.uniform(1.2, 3.5))
        interlock_tripped = confidence < 0.6
        trial = {
            "trial_start_s": round(t, 2),
            "duration_s": round(duration_s, 2),
            "cued_grip": grip,
            "decoded_grip": grip if confidence > 0.6 else RNG.choice(GRIPS),
            "decoder_confidence": round(confidence, 3),
            "grip_force_n": round(float(RNG.uniform(2, 40)) if grip not in ("rest", "open") else 0.0, 1),
            "interlock_tripped": bool(interlock_tripped),
            "interlock_reason": "low_confidence" if interlock_tripped else "none",
        }
        trials.append(trial)
        t += duration_s + float(RNG.uniform(0.3, 1.0))

    return {
        "patient_id": patient_id,
        "session_id": f"{patient_id}_{session_date.date().isoformat()}",
        "session_date": session_date.date().isoformat(),
        "sampling_rate_hz": 30000,
        "n_channels": 96,
        "drift_index": round(drift_level, 3),
        "trials": trials,
    }


def gen_calibration_log(patient_id: str, base_date: datetime, n_days: int) -> list[dict]:
    log = []
    drift = 0.0
    for day in range(n_days):
        date = base_date + timedelta(days=day)
        drift = float(np.clip(drift + RNG.normal(0.02, 0.05), 0.0, 1.0))
        # Occasionally a bad calibration day (e.g. electrode/skin issue), forcing a retry.
        r2 = float(np.clip(RNG.normal(0.85 - drift * 0.35, 0.05), 0.2, 0.98))
        accepted = r2 >= 0.55
        log.append(
            {
                "patient_id": patient_id,
                "date": date.date().isoformat(),
                "drift_index": round(drift, 3),
                "r2_score": round(r2, 3),
                "accepted": accepted,
                "flagged_channels": sorted(
                    RNG.choice(96, size=int(RNG.integers(0, 4)), replace=False).tolist()
                ) if drift > 0.4 else [],
                "duration_s": int(RNG.integers(90, 240)),
            }
        )
        if accepted:
            drift *= 0.3  # successful calibration substantially resets drift
    return log


def gen_device_events(patient_id: str, base_date: datetime, n_days: int) -> list[dict]:
    events = []
    for day in range(n_days):
        date = base_date + timedelta(days=day)
        # Morning calibration event
        events.append(
            {
                "patient_id": patient_id,
                "timestamp": date.replace(hour=8, minute=0).isoformat(),
                "event_type": "calibration_started",
                "payload": {},
            }
        )
        # A charging session most evenings
        if RNG.random() < 0.85:
            charge_start = date.replace(hour=22, minute=int(RNG.integers(0, 59)))
            events.append(
                {
                    "patient_id": patient_id,
                    "timestamp": charge_start.isoformat(),
                    "event_type": "charging_started",
                    "payload": {"battery_pct_start": int(RNG.integers(15, 40))},
                }
            )
            events.append(
                {
                    "patient_id": patient_id,
                    "timestamp": (charge_start + timedelta(hours=2, minutes=int(RNG.integers(0, 40)))).isoformat(),
                    "event_type": "charging_complete",
                    "payload": {"battery_pct_end": 100},
                }
            )
        # Occasional interlock trip event during the day
        if RNG.random() < 0.2:
            events.append(
                {
                    "patient_id": patient_id,
                    "timestamp": date.replace(hour=int(RNG.integers(9, 20))).isoformat(),
                    "event_type": "interlock_tripped",
                    "payload": {
                        "reason": str(
                            RNG.choice(["low_confidence", "signal_loss", "command_chatter"])
                        )
                    },
                }
            )
        # Occasional mode switch via companion app
        if RNG.random() < 0.3:
            events.append(
                {
                    "patient_id": patient_id,
                    "timestamp": date.replace(hour=int(RNG.integers(9, 21))).isoformat(),
                    "event_type": "mode_switch",
                    "payload": {"mode": str(RNG.choice(["assisted", "manual_override"]))},
                }
            )
    return events


def main() -> None:
    sessions_dir = ROOT / "sessions"
    calib_dir = ROOT / "calibration_logs"
    events_dir = ROOT / "events"
    for d in (sessions_dir, calib_dir, events_dir):
        d.mkdir(parents=True, exist_ok=True)

    patients = json.loads((ROOT / "patients.json").read_text())["patients"]

    for p in patients:
        patient_id = p["patient_id"]
        base_date = datetime(2026, 2, 2, tzinfo=timezone.utc)
        n_days = 30

        calib_log = gen_calibration_log(patient_id, base_date, n_days)
        (calib_dir / f"{patient_id}_calibration_log.json").write_text(json.dumps(calib_log, indent=2))

        events = gen_device_events(patient_id, base_date, n_days)
        (events_dir / f"{patient_id}_events.json").write_text(json.dumps(events, indent=2))

        # Full session detail for a representative handful of days.
        for day_offset in (0, 7, 14, 21, 29):
            drift_level = next(
                (e["drift_index"] for e in calib_log if e["date"] == (base_date + timedelta(days=day_offset)).date().isoformat()),
                0.1,
            )
            session = gen_session(patient_id, day_offset, base_date, drift_level)
            out_path = sessions_dir / f"{session['session_id']}.json"
            out_path.write_text(json.dumps(session, indent=2))

        print(f"Generated sample data for {patient_id}")


if __name__ == "__main__":
    main()
