"""Digital filtering and artifact rejection for multi-channel neural recordings.

All functions operate on numpy arrays shaped ``(n_channels, n_samples)`` and
are written to be dependency-light (numpy + scipy only) so they can run in
constrained embedded-adjacent environments.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, iirnotch, sosfiltfilt, tf2sos


def bandpass_filter(
    signal: np.ndarray,
    fs: float,
    low_hz: float = 300.0,
    high_hz: float = 3000.0,
    order: int = 4,
) -> np.ndarray:
    """Zero-phase Butterworth bandpass, default tuned for spike-band (300-3000 Hz).

    Args:
        signal: array of shape (n_channels, n_samples)
        fs: sampling rate in Hz
        low_hz, high_hz: passband edges
        order: filter order

    Returns:
        Filtered array, same shape as input.
    """
    nyq = fs / 2.0
    if not (0 < low_hz < high_hz < nyq):
        raise ValueError(f"Invalid passband [{low_hz}, {high_hz}] for fs={fs}")
    sos = butter(order, [low_hz / nyq, high_hz / nyq], btype="band", output="sos")
    return sosfiltfilt(sos, signal, axis=-1)


def notch_filter(signal: np.ndarray, fs: float, freq_hz: float = 60.0, q: float = 30.0) -> np.ndarray:
    """Remove line noise (mains hum) at freq_hz (and harmonics not included)."""
    b, a = iirnotch(freq_hz, q, fs)
    sos = tf2sos(b, a)
    return sosfiltfilt(sos, signal, axis=-1)


def artifact_reject(
    signal: np.ndarray,
    threshold_uv: float = 500.0,
    window: int = 32,
) -> tuple[np.ndarray, np.ndarray]:
    """Flag and zero out saturating/movement-artifact segments per channel.

    A simple, explainable amplitude + short-window energy gate. Real systems
    would layer in template matching and cross-channel coherence checks;
    this keeps the reference implementation auditable.

    Returns:
        (cleaned_signal, artifact_mask) where artifact_mask is boolean,
        shape (n_channels, n_samples), True where samples were rejected.
    """
    mask = np.abs(signal) > threshold_uv
    n_channels, n_samples = signal.shape
    # Expand rejection to the surrounding window so we don't leave filter-ringing edges.
    expanded = mask.copy()
    for ch in range(n_channels):
        idx = np.where(mask[ch])[0]
        for i in idx:
            lo, hi = max(0, i - window), min(n_samples, i + window)
            expanded[ch, lo:hi] = True
    cleaned = signal.copy()
    cleaned[expanded] = 0.0
    return cleaned, expanded
