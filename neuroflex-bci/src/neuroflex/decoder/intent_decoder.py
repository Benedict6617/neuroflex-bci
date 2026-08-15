"""Intent decoder: maps neural feature vectors to a grip intent + confidence.

The decoder is intentionally split from the safety layer (see
`neuroflex.safety`): this module is allowed to be wrong or uncertain, and it
reports a calibrated confidence so the safety layer can veto low-confidence
or ambiguous commands before they reach the actuator.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from neuroflex.grips.patterns import GripPattern
from neuroflex.signal_processing.features import FeatureVector


@dataclass
class DecodedIntent:
    grip: GripPattern
    confidence: float  # 0..1, calibrated probability of the top class
    class_probabilities: dict[GripPattern, float]
    timestamp: float


class IntentDecoder:
    """Thin, swappable wrapper around a trained classifier.

    In production this wraps a model trained by `neuroflex.ml.train`
    (e.g. a regularized linear discriminant or small MLP appropriate for
    low-latency embedded inference). The wrapper's job is to keep the
    inference-time contract (feature vector in, calibrated intent out)
    stable regardless of which model backend is used.
    """

    def __init__(self, model, grip_labels: list[GripPattern], min_confidence: float = 0.6):
        self.model = model
        self.grip_labels = grip_labels
        self.min_confidence = min_confidence

    def decode(self, features: FeatureVector) -> DecodedIntent:
        x = features.as_array().reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        top_idx = int(np.argmax(proba))
        class_probabilities = {label: float(p) for label, p in zip(self.grip_labels, proba)}
        return DecodedIntent(
            grip=self.grip_labels[top_idx],
            confidence=float(proba[top_idx]),
            class_probabilities=class_probabilities,
            timestamp=features.timestamp,
        )

    def is_actionable(self, intent: DecodedIntent) -> bool:
        """Gate used upstream of the safety layer; safety layer re-checks independently."""
        return intent.confidence >= self.min_confidence
