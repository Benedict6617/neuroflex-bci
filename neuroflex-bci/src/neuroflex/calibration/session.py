"""Guided daily calibration session.

Electrode-tissue interfaces drift day to day (micro-motion, gliosis,
impedance changes), so the decoder is re-anchored each day via a short
guided routine: the patient attempts a sequence of cued grips/movements
while ground truth is known, and we refit the lightweight mapping layers
(decoder bias + Kalman tuning matrix) without retraining the full model.

If calibration quality is poor, `CalibrationResult.accepted` is False and
the previous day's calibration remains active — the safety interlock layer
(H6) will refuse actuation once that prior calibration expires, forcing a
retry rather than running on a bad fit.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from neuroflex.grips.patterns import GripPattern


@dataclass
class CalibrationResult:
    accepted: bool
    r2_score: float
    per_grip_accuracy: dict[GripPattern, float]
    tuning_matrix: np.ndarray | None
    completed_at: float
    notes: str = ""


@dataclass
class CalibrationSession:
    """Runs a cued-movement calibration block and fits updated decoder parameters."""

    cue_sequence: list[GripPattern]
    min_r2: float = 0.55
    min_per_grip_accuracy: float = 0.7

    def run(
        self,
        cued_features: dict[GripPattern, np.ndarray],
        cued_targets: dict[GripPattern, np.ndarray],
    ) -> CalibrationResult:
        """Fit a linear tuning matrix from features -> targets per grip block.

        Args:
            cued_features: {grip: array of shape (n_trials, n_features)}
            cued_targets: {grip: array of shape (n_trials, n_dof_velocity)}
        """
        all_features, all_targets = [], []
        per_grip_accuracy: dict[GripPattern, float] = {}

        for grip in self.cue_sequence:
            feats = cued_features.get(grip)
            targets = cued_targets.get(grip)
            if feats is None or targets is None or len(feats) == 0:
                per_grip_accuracy[grip] = 0.0
                continue
            all_features.append(feats)
            all_targets.append(targets)
            # Simple within-block self-consistency proxy for "accuracy":
            # how tightly clustered the feature vectors are for a repeated cue.
            spread = np.mean(np.std(feats, axis=0))
            per_grip_accuracy[grip] = float(max(0.0, 1.0 - spread))

        if not all_features:
            return CalibrationResult(
                accepted=False,
                r2_score=0.0,
                per_grip_accuracy=per_grip_accuracy,
                tuning_matrix=None,
                completed_at=time.time(),
                notes="No usable calibration trials collected.",
            )

        X = np.vstack(all_features)
        Y = np.vstack(all_targets)

        # Least-squares fit of the linear encoding matrix C such that X ~= state @ C^T
        # (state here approximated by targets augmented with a bias column).
        X_design = np.hstack([Y, np.ones((Y.shape[0], 1))])
        C, residuals, rank, _ = np.linalg.lstsq(X_design, X, rcond=None)

        y_pred = X_design @ C
        ss_res = np.sum((X - y_pred) ** 2)
        ss_tot = np.sum((X - X.mean(axis=0)) ** 2) + 1e-9
        r2 = float(1 - ss_res / ss_tot)

        accepted = r2 >= self.min_r2 and all(
            acc >= self.min_per_grip_accuracy for acc in per_grip_accuracy.values() if acc is not None
        )

        return CalibrationResult(
            accepted=accepted,
            r2_score=r2,
            per_grip_accuracy=per_grip_accuracy,
            tuning_matrix=C.T if accepted else None,
            completed_at=time.time(),
            notes="Calibration accepted." if accepted else "Calibration below quality threshold; previous session retained.",
        )
