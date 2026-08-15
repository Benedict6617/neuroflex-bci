"""Run the decode -> safety -> (simulated) actuation pipeline over a sample session file.

Usage:
    python scripts/run_session_demo.py --patient P-1002 --session data/sample/sessions/P-1002_2026-02-02.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neuroflex.grips.patterns import GripPattern
from neuroflex.grips.state_machine import GripStateMachine
from neuroflex.safety.interlocks import SafetyInterlock


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a synthetic session through the safety-gated grip pipeline.")
    parser.add_argument("--patient", required=True)
    parser.add_argument("--session", required=True, type=Path)
    args = parser.parse_args()

    session = json.loads(args.session.read_text())
    if session["patient_id"] != args.patient:
        print(f"Warning: session patient_id={session['patient_id']} does not match --patient={args.patient}")

    sm = GripStateMachine()
    safety = SafetyInterlock(min_confidence=0.6)
    safety.note_calibration_completed(True)

    print(f"Session {session['session_id']}  ({len(session['trials'])} trials, drift_index={session['drift_index']})")
    print("-" * 78)

    allowed, denied = 0, 0
    for trial in session["trials"]:
        safety.note_signal_received()
        safety.pet_watchdog()

        candidate = GripPattern(trial["decoded_grip"])
        committed = sm.observe(candidate)

        decision = safety.evaluate(
            grip=committed,
            confidence=trial["decoder_confidence"],
            requested_velocity_pct_per_s=100.0,
            requested_force_n=trial["grip_force_n"],
        )

        status = "ALLOW" if decision.allowed else "DENY "
        if decision.allowed:
            allowed += 1
        else:
            denied += 1

        print(
            f"t={trial['trial_start_s']:>6.2f}s  cue={trial['cued_grip']:<12} "
            f"decoded={candidate.value:<12} conf={trial['decoder_confidence']:.2f}  "
            f"{status}  [{decision.trip.value}]  {decision.message}"
        )

    print("-" * 78)
    print(f"Total trials: {len(session['trials'])}  allowed={allowed}  denied={denied}")


if __name__ == "__main__":
    main()
