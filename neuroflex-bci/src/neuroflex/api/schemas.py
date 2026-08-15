from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceStatus(BaseModel):
    patient_id: str
    connected: bool
    battery_pct: float = Field(ge=0, le=100)
    charging_active: bool
    last_calibration_at: Optional[datetime]
    calibration_valid: bool
    current_grip: str
    decoder_confidence: float = Field(ge=0, le=1)
    interlock_tripped: bool
    interlock_reason: str


class ModeSwitchRequest(BaseModel):
    patient_id: str
    mode: str  # e.g. "assisted", "manual_override", "locked"


class CalibrationStartRequest(BaseModel):
    patient_id: str
    cue_sequence: list[str]


class CalibrationResultResponse(BaseModel):
    accepted: bool
    r2_score: float
    per_grip_accuracy: dict[str, float]
    completed_at: datetime
    notes: str


class TelemetryEvent(BaseModel):
    patient_id: str
    timestamp: datetime
    event_type: str
    payload: dict


class LockoutRequest(BaseModel):
    patient_id: str
    locked: bool
    reason: Optional[str] = None
