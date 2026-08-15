# Architecture

## Overview

NeuroFlex is organized as a linear signal-to-actuation pipeline with an
independent safety layer that can veto any stage's output. Every stage is a
plain Python module with a narrow, typed interface so it can be tested in
isolation and swapped out (e.g. replacing the reference linear decoder with
a different model backend) without touching the rest of the system.

```
┌────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ Signal          │──▶│ Feature            │──▶│ Intent Decoder     │
│ Acquisition     │   │ Extraction         │   │ (classification +  │
│ (filters,       │   │ (band power,       │   │  velocity model)   │
│ artifact reject)│   │  spike rate)       │   │                    │
└────────────────┘   └───────────────────┘   └─────────┬─────────┘
                                                          │ candidate grip,
                                                          │ confidence
                                                          ▼
                                              ┌───────────────────┐
                                              │ Grip State Machine │  debounce
                                              └─────────┬─────────┘
                                                          │ committed grip
                                                          ▼
                       independent inputs   ┌───────────────────┐
        signal freshness ───────────────────▶│ Safety Interlock   │──▶ actuator
        calibration age  ───────────────────▶│ Layer               │   command
        charging state   ───────────────────▶│ (veto / bound /     │
        watchdog / lockout──────────────────▶│  rate-limit)        │
                                              └───────────────────┘
```

In parallel, prosthetic sensor data (contact, force) flows through the
**sensory encoder** to peripheral-nerve stimulation, and the **calibration**
and **power** subsystems run on their own schedules (daily, and whenever
charging is initiated) and publish state that the safety layer reads.

## Modules

| Module | Responsibility |
|---|---|
| `signal_processing` | Bandpass/notch filtering, artifact rejection, band-power and spike-rate feature extraction |
| `decoder` | Discrete grip classifier (`IntentDecoder`) + continuous `VelocityKalmanDecoder` for proportional control |
| `grips` | Grip pattern definitions, per-grip force/velocity limits, debounced state machine |
| `safety` | `SafetyInterlock` — the single authority allowed to approve an actuator command |
| `calibration` | Daily guided calibration session + cross-session drift estimation |
| `sensory_feedback` | Force → charge-balanced stimulation pulse encoding with hard safety ceilings |
| `power` | Wireless (inductive) charging session simulation with thermal guardrails |
| `ml` | Offline training pipeline and a file-based per-patient model registry |
| `api` | FastAPI backend implementing the companion-app contract (status, mode switching, calibration, telemetry) |

## Design decisions worth calling out

**Safety is architecturally separate from the decoder.** `SafetyInterlock`
never imports or calls into `decoder` or `ml`. It receives only a proposed
command and a small set of independently-tracked state variables (signal
freshness, calibration age, charging state, watchdog heartbeat, manual
lockout). This means a bug, adversarial input, or model regression in the
decoder cannot, by construction, disable the safety layer — see
[`docs/SAFETY.md`](SAFETY.md) for the full hazard analysis.

**Grip switching is debounced.** `GripStateMachine` requires a sustained
majority vote before committing to a new grip, which absorbs decoder
jitter near the confidence threshold and avoids disorienting rapid
switching while the hand may be holding an object.

**Linear/explainable models are the default ML backend.** See the module
docstring in `ml/train.py` — a deliberate choice favoring auditability and
low-latency embedded inference over marginal accuracy gains from opaque
models.

**Calibration failure is fail-safe, not fail-open.** If a daily calibration
session doesn't meet quality thresholds, the previous calibration remains
in effect until it expires (`SafetyInterlock.calibration_max_age_hours`),
at which point actuation is disabled rather than running on an unvalidated
mapping.

## Data flow at the API boundary

The companion mobile app never talks to the decoder or safety layer
directly — it talks to the FastAPI `api` service, which exposes a stable,
versioned contract (`/v1/devices/{patient_id}/...`). See
[`docs/API.md`](API.md).
