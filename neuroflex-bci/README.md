# NeuroFlex — Neural-Prosthetic Control Platform

A reference software platform for a real-time Brain-Computer Interface (BCI) that decodes motor-cortex signals, drives a multi-grip prosthetic hand, and closes the loop with peripheral-nerve sensory feedback.

> **Scope & disclaimer**
> This repository is a **software reference implementation and R&D/demo platform**. It ships with **synthetic sample data** and simulated hardware adapters so it can be run, tested, and demoed without any physical implant. It is **not** an FDA-cleared or CE-marked medical device, and none of the documentation in `docs/compliance/` constitutes regulatory clearance — those documents are **design-control templates** meant to show how such a system *would* be organized for an IEC 62304 / FDA QSR (21 CFR 820) submission. Before any use with human subjects or real implanted hardware, this software requires a full V&V program, clinical evaluation, and regulatory clearance from a qualified organization.

## Why NeuroFlex

Small clinical-device teams and prosthetics labs need a starting point that already has the boring-but-critical parts done well: signal hygiene, safety interlocks, daily recalibration, an auditable data model, and a companion-app contract — so engineering time goes into the decoder and the clinic workflow, not plumbing.

## System overview

```
Implant electrodes ──▶ Signal Acquisition ──▶ Feature Extraction ──▶ Intent Decoder (ML)
                                                                          │
                                                                          ▼
                         Safety Interlock Layer ◀──── Grip Pattern Selector
                                  │
                                  ▼
                         Prosthetic Actuator Driver ──▶ Limb Motion
                                  │
                                  ▼
                      Sensory Encoder ──▶ Peripheral Nerve Stimulation
                                  │
                     Companion App (BLE) ◀── Mode switching, calibration, logs
```

## Key capabilities

- **Signal processing pipeline** — bandpass/notch filtering, artifact rejection, spike-band and LFP feature extraction (`src/neuroflex/signal_processing`)
- **Adaptive intent decoder** — online-adaptive classifier + Kalman-filter-style velocity decoder with confidence scoring (`src/neuroflex/decoder`)
- **Daily drift calibration** — guided calibration session that re-anchors the decoder to account for electrode drift, with automatic rollback if calibration quality is poor (`src/neuroflex/calibration`)
- **Grip pattern library** — configurable multi-grip state machine (power, pinch, tripod, point, rest, etc.) (`src/neuroflex/grips`)
- **Safety interlock layer** — independent, decoder-agnostic layer that rate-limits, bounds, and vetoes actuator commands; hard-stops on low confidence, signal loss, or anomalous drive commands (`src/neuroflex/safety`)
- **Sensory feedback encoder** — maps grip force/contact sensors to peripheral-nerve stimulation waveforms within safe charge-density limits (`src/neuroflex/sensory_feedback`)
- **Wireless power monitor** — simulated inductive-charging session manager with thermal/SOC guardrails (`src/neuroflex/power`)
- **Device API + companion app contract** — FastAPI service exposing calibration, mode switching, telemetry, and event logs, consumed by a documented mobile app stub (`src/neuroflex/api`, `mobile/`)
- **ML training pipeline** — offline model training/adaptation on session data, with model registry and versioning (`src/neuroflex/ml`)
- **Realistic synthetic sample data** — multi-day, multi-patient synthetic neural sessions for demoing calibration drift, grip switching, and safety-interlock events (`data/sample`)

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the decoding + safety pipeline over a synthetic session
python scripts/run_session_demo.py --patient P-1002 --session data/sample/sessions/P-1002_2026-03-04.json

# Train the adaptive decoder on sample calibration data
python scripts/train_decoder.py --patient P-1002

# Start the device API (used by the companion app)
uvicorn neuroflex.api.main:app --reload
```

Run the test suite:

```bash
pytest -q
```

## Repository layout

```
src/neuroflex/
  signal_processing/   Filtering, artifact rejection, feature extraction
  decoder/              Intent decoder, confidence scoring, velocity model
  calibration/          Daily drift-calibration protocol & drift metrics
  grips/                Grip pattern definitions & state machine
  safety/               Interlocks: rate limiting, bounds, veto, watchdog
  sensory_feedback/     Force→stimulation waveform encoding
  power/                Wireless charging session simulation
  ml/                   Model training, evaluation, versioned registry
  api/                  FastAPI backend (device + companion app contract)
data/sample/             Synthetic patients, sessions, calibration logs
docs/                    Architecture, protocols, compliance templates
mobile/NeuroFlexApp/     Companion app contract + UI wireframe notes
scripts/                 CLI entry points for demos and training
tests/                   Unit + integration tests
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — component design and data flow
- [`docs/CALIBRATION_PROTOCOL.md`](docs/CALIBRATION_PROTOCOL.md) — daily calibration procedure
- [`docs/SAFETY.md`](docs/SAFETY.md) — safety interlock design and hazard mitigations
- [`docs/API.md`](docs/API.md) — device API reference
- [`docs/compliance/`](docs/compliance) — design-control document templates (IEC 62304, ISO 14971, FDA QSR mapping)
- [`CHANGELOG.md`](CHANGELOG.md), [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md)

## License

MIT — see [`LICENSE`](LICENSE). See disclaimer above regarding medical-device use.
