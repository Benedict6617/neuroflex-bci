"""Feature extraction from cleaned neural signals for the intent decoder."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.signal import welch


@dataclass
class FeatureVector:
    """A single decoder input, extracted over one sliding window."""

    timestamp: float
    band_power: np.ndarray  # shape (n_channels,)
    spike_rate: np.ndarray  # shape (n_channels,)
    channel_quality: np.ndarray  # shape (n_channels,), 0..1 confidence per channel
    meta: dict = field(default_factory=dict)

    def as_array(self) -> np.ndarray:
        """Flatten into the vector consumed by the decoder model."""
        return np.concatenate([self.band_power, self.spike_rate, self.channel_quality])


def extract_band_power(signal: np.ndarray, fs: float, band: tuple[float, float] = (10, 40)) -> np.ndarray:
    """Mean power spectral density in `band` per channel, via Welch's method."""
    # nperseg chosen for enough frequency resolution to resolve narrow low-frequency
    # bands (e.g. mu/beta) even when the input is a high sample-rate spike-band signal.
    nperseg = min(4096, signal.shape[-1])
    freqs, psd = welch(signal, fs=fs, nperseg=nperseg, axis=-1)
    band_mask = (freqs >= band[0]) & (freqs <= band[1])
    if not band_mask.any():
        raise ValueError(f"Band {band} outside available frequency range for fs={fs}")
    return psd[..., band_mask].mean(axis=-1)


def extract_spike_rate(signal: np.ndarray, fs: float, threshold_uv: float = -50.0) -> np.ndarray:
    """Threshold-crossing spike rate (Hz) per channel — a standard BCI feature.

    Negative-going threshold crossing is used as a simple, fast proxy for
    single/multi-unit activity, consistent with common intracortical BCI
    front-ends.
    """
    n_channels, n_samples = signal.shape
    duration_s = n_samples / fs
    rates = np.zeros(n_channels)
    for ch in range(n_channels):
        below = signal[ch] < threshold_uv
        crossings = np.diff(below.astype(int)) == 1  # rising into "below threshold"
        rates[ch] = crossings.sum() / duration_s
    return rates


def channel_quality_index(signal: np.ndarray, artifact_mask: np.ndarray) -> np.ndarray:
    """Fraction of clean (non-artifact) samples per channel, used as a soft confidence weight."""
    return 1.0 - artifact_mask.mean(axis=-1)
