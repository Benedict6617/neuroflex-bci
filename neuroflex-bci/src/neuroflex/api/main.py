"""Device API — the contract consumed by the companion mobile app.

This simulates the backend a phone app would talk to over a secure BLE
gateway/bridge in a real deployment. Endpoints intentionally mirror the
"mode switching", "calibration", and "telemetry" flows called out in the
product requirements.

Run with: uvicorn neuroflex.api.main:app --reload
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from neuroflex.api.schemas import (
    CalibrationResultResponse,
    CalibrationStartRequest,
    DeviceStatus,
    LockoutRequest,
    ModeSwitchRequest,
    TelemetryEvent,
)

app = FastAPI(
    title="NeuroFlex Device API",
    description="Backend contract for the NeuroFlex companion app (simulated device bridge).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the companion app's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory simulated device fleet state (replace with a real device bridge + DB).
_DEVICE_STATE: dict[str, dict] = {}


def _get_or_init(patient_id: str) -> dict:
    if patient_id not in _DEVICE_STATE:
        _DEVICE_STATE[patient_id] = {
            "connected": True,
            "battery_pct": 82.0,
            "charging_active": False,
            "last_calibration_at": None,
            "calibration_valid": False,
            "current_grip": "rest",
            "decoder_confidence": 0.0,
            "interlock_tripped": False,
            "interlock_reason": "calibration_stale",
            "mode": "assisted",
            "locked": False,
            "events": [],
        }
    return _DEVICE_STATE[patient_id]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/v1/devices/{patient_id}/status", response_model=DeviceStatus)
def get_status(patient_id: str) -> DeviceStatus:
    s = _get_or_init(patient_id)
    return DeviceStatus(
        patient_id=patient_id,
        connected=s["connected"],
        battery_pct=s["battery_pct"],
        charging_active=s["charging_active"],
        last_calibration_at=s["last_calibration_at"],
        calibration_valid=s["calibration_valid"],
        current_grip=s["current_grip"],
        decoder_confidence=s["decoder_confidence"],
        interlock_tripped=s["interlock_tripped"],
        interlock_reason=s["interlock_reason"],
    )


@app.post("/v1/devices/{patient_id}/mode")
def switch_mode(patient_id: str, req: ModeSwitchRequest) -> dict:
    if req.patient_id != patient_id:
        raise HTTPException(status_code=400, detail="patient_id mismatch")
    s = _get_or_init(patient_id)
    if req.mode not in {"assisted", "manual_override", "locked"}:
        raise HTTPException(status_code=422, detail="Unsupported mode")
    s["mode"] = req.mode
    s["locked"] = req.mode == "locked"
    s["events"].append({"type": "mode_switch", "mode": req.mode, "at": datetime.now(timezone.utc).isoformat()})
    return {"patient_id": patient_id, "mode": s["mode"]}


@app.post("/v1/devices/{patient_id}/lockout")
def set_lockout(patient_id: str, req: LockoutRequest) -> dict:
    s = _get_or_init(patient_id)
    s["locked"] = req.locked
    s["events"].append(
        {
            "type": "lockout",
            "locked": req.locked,
            "reason": req.reason,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {"patient_id": patient_id, "locked": s["locked"]}


@app.post("/v1/devices/{patient_id}/calibration/start", response_model=CalibrationResultResponse)
def start_calibration(patient_id: str, req: CalibrationStartRequest) -> CalibrationResultResponse:
    """Simulated calibration trigger — in a full deployment this kicks off
    the guided on-device routine (see neuroflex.calibration.session) and
    streams progress over the telemetry channel while the patient performs
    the cued movements.
    """
    if req.patient_id != patient_id:
        raise HTTPException(status_code=400, detail="patient_id mismatch")
    s = _get_or_init(patient_id)

    # Simulated outcome for API-contract demo purposes.
    accepted = True
    now = datetime.now(timezone.utc)
    s["last_calibration_at"] = now
    s["calibration_valid"] = accepted
    s["interlock_tripped"] = not accepted
    s["interlock_reason"] = "none" if accepted else "calibration_stale"

    return CalibrationResultResponse(
        accepted=accepted,
        r2_score=0.83,
        per_grip_accuracy={g: 0.9 for g in req.cue_sequence},
        completed_at=now,
        notes="Calibration accepted." if accepted else "Calibration below quality threshold.",
    )


@app.post("/v1/devices/{patient_id}/telemetry")
def post_telemetry(patient_id: str, event: TelemetryEvent) -> dict:
    if event.patient_id != patient_id:
        raise HTTPException(status_code=400, detail="patient_id mismatch")
    s = _get_or_init(patient_id)
    s["events"].append(event.model_dump(mode="json"))
    return {"accepted": True}


@app.get("/v1/devices/{patient_id}/events")
def get_events(patient_id: str, limit: int = 50) -> list[dict]:
    s = _get_or_init(patient_id)
    return s["events"][-limit:]
