"""Continuous velocity decoding for fine motor control (e.g. wrist rotation,
proportional finger flexion) using a standard linear Kalman filter.

This complements the discrete grip classifier in `intent_decoder.py`:
the classifier picks *which* grip is intended, this model decodes
*how fast/how far* to move within that grip's degrees of freedom.
"""
from __future__ import annotations

import numpy as np


class VelocityKalmanDecoder:
    """Linear Kalman filter mapping neural features to joint velocities.

    State: [position, velocity] per degree of freedom.
    Observation: neural feature vector, linearly related to velocity
    via a tuning matrix `C` fit during calibration (see
    `neuroflex.calibration`).
    """

    def __init__(self, n_dof: int, n_features: int, dt: float = 0.02):
        self.n_dof = n_dof
        self.dt = dt
        state_dim = 2 * n_dof

        self.A = np.eye(state_dim)
        for i in range(n_dof):
            self.A[2 * i, 2 * i + 1] = dt  # position += velocity * dt

        self.Q = np.eye(state_dim) * 1e-3  # process noise
        self.R = np.eye(n_features) * 1.0  # observation noise, refined at calibration
        self.C = np.zeros((n_features, state_dim))  # tuning/encoding matrix, set by calibration
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)

    def set_tuning_matrix(self, C: np.ndarray, R: np.ndarray | None = None) -> None:
        """Install a freshly calibrated encoding matrix (see calibration/session.py)."""
        if C.shape != self.C.shape:
            raise ValueError(f"Expected tuning matrix shape {self.C.shape}, got {C.shape}")
        self.C = C
        if R is not None:
            self.R = R

    def step(self, feature_vector: np.ndarray) -> np.ndarray:
        """One Kalman predict/update step. Returns per-DOF velocity estimate."""
        # Predict
        x_pred = self.A @ self.x
        P_pred = self.A @ self.P @ self.A.T + self.Q

        # Update
        y = feature_vector - self.C @ x_pred
        S = self.C @ P_pred @ self.C.T + self.R
        K = P_pred @ self.C.T @ np.linalg.pinv(S)
        self.x = x_pred + K @ y
        self.P = (np.eye(len(self.x)) - K @ self.C) @ P_pred

        velocities = self.x[1::2]
        return velocities

    def reset(self) -> None:
        self.x[:] = 0.0
        self.P = np.eye(len(self.x))
