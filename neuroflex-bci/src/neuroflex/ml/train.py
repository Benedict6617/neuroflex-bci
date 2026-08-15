"""Offline training pipeline for the grip-intent classifier, plus a small
file-based model registry for versioning per-patient decoders.

Model choice: regularized logistic regression / LDA is used as the default
backend rather than a deep model. For intracortical BCI decoding, linear
models with good feature engineering are a well-established, low-latency,
low-power choice suitable for embedded inference and are much easier to
validate and explain during a regulatory review than an opaque deep net —
an intentional design decision for this platform, not a limitation.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


@dataclass
class TrainingReport:
    patient_id: str
    n_samples: int
    n_classes: int
    accuracy: float
    macro_f1: float
    trained_at: float
    model_version: str


def train_grip_classifier(
    X: np.ndarray,
    y: np.ndarray,
    patient_id: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[Pipeline, TrainingReport]:
    """Train a calibrated logistic-regression grip classifier.

    Args:
        X: (n_samples, n_features) feature matrix
        y: (n_samples,) grip labels (strings or ints)
        patient_id: patient identifier, used for versioning

    Returns:
        (fitted_pipeline, training_report)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=1.0,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))

    report = TrainingReport(
        patient_id=patient_id,
        n_samples=int(len(X)),
        n_classes=int(len(np.unique(y))),
        accuracy=accuracy,
        macro_f1=macro_f1,
        trained_at=time.time(),
        model_version=f"{patient_id}-{int(time.time())}",
    )
    return pipeline, report


class ModelRegistry:
    """Minimal file-based model registry: one directory per patient, one
    versioned artifact + metadata JSON per training run.
    """

    def __init__(self, root: str | Path = "data/models"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, pipeline: Pipeline, report: TrainingReport) -> Path:
        patient_dir = self.root / report.patient_id
        patient_dir.mkdir(parents=True, exist_ok=True)
        model_path = patient_dir / f"{report.model_version}.joblib"
        meta_path = patient_dir / f"{report.model_version}.json"

        joblib.dump(pipeline, model_path)
        meta_path.write_text(json.dumps(asdict(report), indent=2))
        return model_path

    def load_latest(self, patient_id: str) -> tuple[Pipeline, TrainingReport]:
        patient_dir = self.root / patient_id
        versions = sorted(patient_dir.glob("*.json"))
        if not versions:
            raise FileNotFoundError(f"No trained model found for patient {patient_id}")
        latest_meta = versions[-1]
        report_dict = json.loads(latest_meta.read_text())
        model_path = latest_meta.with_suffix(".joblib")
        pipeline = joblib.load(model_path)
        return pipeline, TrainingReport(**report_dict)
