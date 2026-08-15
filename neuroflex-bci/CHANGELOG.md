# Changelog

All notable changes to this project are documented in this file.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [1.0.0] - 2026-08-14

### Added
- Signal processing pipeline: bandpass/notch filtering, artifact rejection, band-power and spike-rate feature extraction
- Grip-intent decoder (classifier wrapper) and continuous velocity Kalman decoder
- Grip pattern library with per-grip force/velocity limits and a debounced grip state machine
- Independent safety interlock layer with 10 tracked hazard mitigations (see `docs/SAFETY.md`)
- Daily drift-calibration session logic and cross-session drift estimation
- Sensory feedback encoder mapping force to charge-balanced, safety-bounded stimulation pulses
- Simulated wireless charging session manager with thermal guardrails
- Offline ML training pipeline with a file-based per-patient model registry
- FastAPI device API implementing the companion-app contract (status, mode switching, lockout, calibration, telemetry)
- Realistic synthetic sample data: patient profiles, 30-day calibration logs, device event logs, detailed session trials for representative days
- Full documentation set: architecture, safety hazard analysis, calibration protocol, API reference, and compliance-template mapping (IEC 62304, ISO 14971, cybersecurity)
- Unit and integration test suite covering all modules
- CLI demo scripts for running a sample session and training the decoder
