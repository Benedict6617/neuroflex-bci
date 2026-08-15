"""Electrode/decoder drift estimation across sessions."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DriftReport:
    channel_drift: np.ndarray  # per-channel drift magnitude
    mean_drift: float
    flagged_channels: list[int]
    recommend_recalibration: bool


def estimate_drift(
    baseline_features: np.ndarray,
    today_features: np.ndarray,
    flag_threshold: float = 2.5,
) -> DriftReport:
    """Compare today's resting-state feature distribution to a stored baseline.

    Args:
        baseline_features: (n_samples_baseline, n_channels)
        today_features: (n_samples_today, n_channels)
        flag_threshold: z-score above which a channel is flagged as drifted

    Returns:
        DriftReport summarizing per-channel and aggregate drift.
    """
    baseline_mean = baseline_features.mean(axis=0)
    baseline_std = baseline_features.std(axis=0) + 1e-9
    today_mean = today_features.mean(axis=0)

    z = np.abs((today_mean - baseline_mean) / baseline_std)
    flagged = [int(i) for i in np.where(z > flag_threshold)[0]]

    return DriftReport(
        channel_drift=z,
        mean_drift=float(z.mean()),
        flagged_channels=flagged,
        recommend_recalibration=len(flagged) > 0 or float(z.mean()) > (flag_threshold * 0.6),
    )
