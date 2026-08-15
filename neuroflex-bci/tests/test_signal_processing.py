import numpy as np
import pytest

from neuroflex.signal_processing.filters import bandpass_filter, notch_filter, artifact_reject
from neuroflex.signal_processing.features import extract_band_power, extract_spike_rate, channel_quality_index


FS = 30000


def _synthetic_signal(n_channels=4, seconds=1.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(0, seconds, 1 / FS)
    noise = rng.normal(0, 15, size=(n_channels, len(t)))
    hum = 4 * np.sin(2 * np.pi * 60 * t)
    return noise + hum, t


def test_bandpass_filter_shape_preserved():
    sig, _ = _synthetic_signal()
    out = bandpass_filter(sig, FS)
    assert out.shape == sig.shape


def test_bandpass_filter_rejects_invalid_band():
    sig, _ = _synthetic_signal()
    with pytest.raises(ValueError):
        bandpass_filter(sig, FS, low_hz=5000, high_hz=1000)


def test_notch_filter_reduces_60hz_power():
    sig, t = _synthetic_signal()
    filtered = notch_filter(sig, FS, freq_hz=60.0)
    # crude power check around 60Hz via FFT magnitude at nearest bin
    def power_at_60hz(x):
        spec = np.abs(np.fft.rfft(x[0]))
        freqs = np.fft.rfftfreq(x.shape[-1], d=1 / FS)
        idx = np.argmin(np.abs(freqs - 60))
        return spec[idx]

    assert power_at_60hz(filtered) < power_at_60hz(sig)


def test_artifact_reject_flags_large_amplitude():
    sig, _ = _synthetic_signal()
    sig[0, 100] = 5000  # inject artifact
    cleaned, mask = artifact_reject(sig, threshold_uv=500.0, window=8)
    assert mask[0, 100]
    assert cleaned[0, 100] == 0.0


def test_extract_band_power_shape():
    sig, _ = _synthetic_signal(n_channels=6)
    bp = extract_band_power(sig, FS, band=(10, 40))
    assert bp.shape == (6,)
    assert np.all(bp >= 0)


def test_extract_spike_rate_nonnegative():
    sig, _ = _synthetic_signal(n_channels=3)
    rates = extract_spike_rate(sig, FS, threshold_uv=-40.0)
    assert rates.shape == (3,)
    assert np.all(rates >= 0)


def test_channel_quality_index_range():
    mask = np.zeros((4, 100), dtype=bool)
    mask[0, :50] = True
    quality = channel_quality_index(np.zeros((4, 100)), mask)
    assert quality[0] == pytest.approx(0.5)
    assert quality[1] == pytest.approx(1.0)
