from fastapi.testclient import TestClient

from neuroflex.api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_status_initializes_device():
    resp = client.get("/v1/devices/P-TEST-1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["patient_id"] == "P-TEST-1"
    assert body["calibration_valid"] is False


def test_mode_switch():
    resp = client.post("/v1/devices/P-TEST-2/mode", json={"patient_id": "P-TEST-2", "mode": "manual_override"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "manual_override"


def test_mode_switch_rejects_mismatched_patient():
    resp = client.post("/v1/devices/P-TEST-2/mode", json={"patient_id": "OTHER", "mode": "assisted"})
    assert resp.status_code == 400


def test_mode_switch_rejects_unsupported_mode():
    resp = client.post("/v1/devices/P-TEST-3/mode", json={"patient_id": "P-TEST-3", "mode": "bogus"})
    assert resp.status_code == 422


def test_calibration_flow_updates_status():
    resp = client.post(
        "/v1/devices/P-TEST-4/calibration/start",
        json={"patient_id": "P-TEST-4", "cue_sequence": ["power", "pinch"]},
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True

    status = client.get("/v1/devices/P-TEST-4/status").json()
    assert status["calibration_valid"] is True


def test_lockout_endpoint():
    resp = client.post("/v1/devices/P-TEST-5/lockout", json={"patient_id": "P-TEST-5", "locked": True, "reason": "clinician request"})
    assert resp.status_code == 200
    assert resp.json()["locked"] is True


def test_telemetry_and_events_roundtrip():
    resp = client.post(
        "/v1/devices/P-TEST-6/telemetry",
        json={
            "patient_id": "P-TEST-6",
            "timestamp": "2026-03-01T12:00:00Z",
            "event_type": "grip_change",
            "payload": {"grip": "power"},
        },
    )
    assert resp.status_code == 200
    events = client.get("/v1/devices/P-TEST-6/events").json()
    assert len(events) == 1
    assert events[0]["event_type"] == "grip_change"
