# Daily Calibration Protocol

Electrode-tissue interfaces and cortical signal statistics drift day to
day. NeuroFlex re-anchors the decoder every day (and whenever
`neuroflex.calibration.drift.estimate_drift` recommends it mid-day) via a
short guided routine.

## Procedure

1. **Baseline rest block (30s).** Patient rests; used to update the
   resting-state feature baseline consumed by `estimate_drift`.
2. **Cued movement blocks (~15-25s per grip).** The companion app cues each
   grip pattern in turn (`POST /v1/devices/{id}/calibration/start` with the
   `cue_sequence`); the patient attempts the cued grip while features and
   (if available) ground-truth kinematics are recorded.
3. **Fit.** `CalibrationSession.run` fits an updated linear tuning matrix
   from the cued trials and computes:
   - `r2_score` — how well the fitted mapping explains the calibration data
   - `per_grip_accuracy` — a self-consistency score per grip block
4. **Accept or reject.**
   - Accepted (`r2_score >= min_r2` **and** every grip block above
     `min_per_grip_accuracy`): the new tuning matrix is installed
     (`VelocityKalmanDecoder.set_tuning_matrix`) and
     `SafetyInterlock.note_calibration_completed(True)` resets the
     24-hour calibration-freshness window.
   - Rejected: the previous day's calibration remains active. The patient
     is prompted to retry (e.g. after checking electrode contact); if no
     valid calibration is completed before the freshness window expires,
     the safety layer disables actuation (`CALIBRATION_STALE`).
5. **Log.** Every calibration attempt — accepted or not — is appended to
   the per-patient calibration log (see
   `data/sample/calibration_logs/*.json` for 30 days of realistic sample
   history, including days with elevated drift and rejected sessions) for
   clinician review.

## Mid-day drift checks

`neuroflex.calibration.drift.estimate_drift` compares a short resting-state
snapshot against the stored baseline and flags individual channels whose
feature distribution has shifted beyond a z-score threshold. A flagged
result surfaces a "recalibration recommended" prompt in the companion app
rather than forcing an immediate session — daily calibration is mandatory,
mid-day recalibration is advisory.

## Quality thresholds (reference defaults)

| Parameter | Default | Rationale |
|---|---|---|
| `min_r2` | 0.55 | Below this, the fitted mapping is not meaningfully explaining movement intent |
| `min_per_grip_accuracy` | 0.70 | Ensures no single grip pattern is silently unreliable |
| `calibration_max_age_hours` | 24 | Matches the daily-recalibration requirement |

These are reference defaults for the demo platform, not a clinical
prescription — real thresholds must be set per patient and electrode
configuration by the treating clinical team.
