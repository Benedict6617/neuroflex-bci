import time

from neuroflex.grips.patterns import GripPattern
from neuroflex.safety.interlocks import SafetyInterlock, InterlockTrip


def _ready_interlock(**overrides) -> SafetyInterlock:
    si = SafetyInterlock(**overrides)
    si.note_signal_received()
    si.pet_watchdog()
    si.note_calibration_completed(True)
    return si


def test_denies_without_calibration():
    si = SafetyInterlock()
    si.note_signal_received()
    si.pet_watchdog()
    decision = si.evaluate(GripPattern.POWER, 0.9, 100.0, 20.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.CALIBRATION_STALE


def test_denies_on_signal_loss():
    si = _ready_interlock(max_signal_gap_s=0.01)
    time.sleep(0.05)
    decision = si.evaluate(GripPattern.POWER, 0.9, 100.0, 20.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.SIGNAL_LOSS


def test_denies_low_confidence():
    si = _ready_interlock(min_confidence=0.8)
    decision = si.evaluate(GripPattern.POWER, 0.5, 50.0, 10.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.LOW_CONFIDENCE


def test_denies_during_charging():
    si = _ready_interlock()
    si.set_charging_active(True)
    decision = si.evaluate(GripPattern.PINCH, 0.9, 50.0, 10.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.CHARGING_ACTIVE


def test_denies_on_manual_lockout():
    si = _ready_interlock()
    si.set_manual_lockout(True)
    decision = si.evaluate(GripPattern.PINCH, 0.9, 50.0, 10.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.MANUAL_LOCKOUT


def test_clamps_force_and_velocity_to_grip_limits():
    si = _ready_interlock(min_confidence=0.1)
    # PINCH limits: velocity 80%/s, force 15N (see grips/patterns.py)
    decision = si.evaluate(GripPattern.PINCH, 0.9, requested_velocity_pct_per_s=500.0, requested_force_n=100.0)
    assert decision.allowed
    assert decision.velocity_pct_per_s <= 80.0
    assert decision.force_n <= 15.0


def test_watchdog_timeout_denies():
    si = SafetyInterlock(watchdog_timeout_s=0.01)
    si.note_signal_received()
    si.pet_watchdog()
    si.note_calibration_completed(True)
    time.sleep(0.05)
    decision = si.evaluate(GripPattern.POWER, 0.9, 50.0, 10.0)
    assert not decision.allowed
    assert decision.trip == InterlockTrip.WATCHDOG_TIMEOUT


def test_command_chatter_detected():
    si = _ready_interlock(chatter_window_s=5.0, chatter_max_transitions=2, min_confidence=0.1)
    grips = [GripPattern.POWER, GripPattern.PINCH, GripPattern.TRIPOD, GripPattern.POINT, GripPattern.LATERAL_KEY]
    decisions = [si.evaluate(g, 0.9, 10.0, 5.0) for g in grips]
    assert any(d.trip == InterlockTrip.COMMAND_CHATTER for d in decisions)
