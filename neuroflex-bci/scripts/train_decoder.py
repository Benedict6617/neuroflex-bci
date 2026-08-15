"""Train the grip-intent classifier from synthetic per-trial session data
and save it to the local model registry.

Usage:
    python scripts/train_decoder.py --patient P-1002
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neuroflex.ml.train import train_grip_classifier, ModelRegistry

ROOT = Path(__file__).resolve().parents[1]


def load_training_data(patient_id: str) -> tuple[np.ndarray, np.ndarray]:
    """Builds a toy feature matrix from the sample session trial metadata.

    In production, X would be the real extracted FeatureVector.as_array()
    values recorded per trial; here we synthesize plausible features from
    the (confidence, force, grip) trial summaries stored in the sample data
    so the training pipeline can be exercised end-to-end without shipping
    raw multi-gigabyte voltage traces in the repo.
    """
    sessions_dir = ROOT / "data" / "sample" / "sessions"
    rng = np.random.default_rng(hash(patient_id) % (2**32))

    X_rows, y_rows = [], []
    for path in sorted(sessions_dir.glob(f"{patient_id}_*.json")):
        session = json.loads(path.read_text())
        for trial in session["trials"]:
            grip = trial["cued_grip"]
            base = {"rest": 0, "power": 1, "pinch": 2, "tripod": 3, "point": 4, "lateral_key": 5, "open": 6}[grip]
            feat = rng.normal(loc=base, scale=0.6, size=12)
            X_rows.append(feat)
            y_rows.append(grip)

    if not X_rows:
        raise FileNotFoundError(f"No sample sessions found for patient {patient_id} in {sessions_dir}")

    return np.vstack(X_rows), np.array(y_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the grip-intent classifier on sample session data.")
    parser.add_argument("--patient", required=True)
    args = parser.parse_args()

    X, y = load_training_data(args.patient)
    print(f"Loaded {len(X)} trials across {len(set(y))} grip classes for {args.patient}")

    pipeline, report = train_grip_classifier(X, y, patient_id=args.patient)
    print(f"Accuracy: {report.accuracy:.3f}   Macro F1: {report.macro_f1:.3f}")

    registry = ModelRegistry(root=ROOT / "data" / "models")
    path = registry.save(pipeline, report)
    print(f"Saved model -> {path}")


if __name__ == "__main__":
    main()
