import numpy as np
import pytest

from neuroflex.calibration.session import CalibrationSession
from neuroflex.calibration.drift import estimate_drift
from neuroflex.grips.patterns import GripPattern
from neuroflex.sensory_feedback.encoder import SensoryEncoder, StimulationSafetyError
from neuroflex.power.wireless_charging import WirelessChargingSession, ChargingStatus


def test_calibration_session_accepts_clean_data():
    rng = np.random.default_rng(3)
    cs = CalibrationSession(cue_sequence=[GripPattern.POWER, GripPattern.PINCH], min_r2=0.0, min_per_grip_accuracy=0.0)
    cued_features = {
        GripPattern.POWER: rng.normal(0, 0.01, size=(30, 5)),
        GripPattern.PINCH: rng.normal(1, 0.01, size=(30, 5)),
    }
    cued_targets = {
        GripPattern.POWER: rng.normal(0, 0.01, size=(30, 2)),
        GripPattern.PINCH: rng.normal(1, 0.01, size=(30, 2)),
    }
    result = cs.run(cued_features, cued_targets)
    assert result.accepted
    assert result.tuning_matrix is not None


def test_calibration_session_rejects_empty_data():
    cs = CalibrationSession(cue_sequence=[GripPattern.POWER])
    result = cs.run({}, {})
    assert not result.accepted
    assert result.tuning_matrix is None


def test_estimate_drift_flags_shifted_channels():
    rng = np.random.default_rng(4)
    baseline = rng.normal(0, 1, size=(200, 10))
    today = baseline.copy()[:100]
    today[:, 3] += 10  # inject a large drift on channel 3
    report = estimate_drift(baseline, today, flag_threshold=2.0)
    assert 3 in report.flagged_channels
    assert report.recommend_recalibration


def test_sensory_encoder_within_limits():
    se = SensoryEncoder()
    pulse = se.encode_force(channel=2, normalized_force=0.5)
    assert 0 <= pulse.amplitude_ma <= se.max_amplitude_ma
    assert pulse.charge_per_phase_nc <= se.max_charge_per_phase_nc


def test_sensory_encoder_rejects_overlimit_charge():
    se = SensoryEncoder(max_charge_per_phase_nc=10.0)  # artificially tiny ceiling
    with pytest.raises(StimulationSafetyError):
        se.encode_force(channel=0, normalized_force=1.0)


def test_wireless_charging_progresses_and_completes():
    session = WirelessChargingSession(state_of_charge_pct=95.0)
    session.start()
    for _ in range(20):
        session.tick(60)
    assert session.state_of_charge_pct == 100.0
    assert session.status == ChargingStatus.COMPLETE


def test_wireless_charging_thermal_pause():
    session = WirelessChargingSession(state_of_charge_pct=10.0, max_coil_temp_c=33.0, ambient_temp_c=32.0)
    session.start()
    session.tick(600)
    assert session.status in (ChargingStatus.THERMAL_PAUSE, ChargingStatus.CHARGING)


def test_charging_active_flag_blocks_when_charging():
    session = WirelessChargingSession(state_of_charge_pct=10.0)
    session.start()
    assert session.charging_active
    session.stop()
    assert not session.charging_active
