# IEC 62304 Mapping (Template)

> Template only — see [`README.md`](README.md) disclaimer. This maps
> repository components to the IEC 62304 medical device software
> lifecycle *process areas*; it is not a completed lifecycle record.

## Suggested software safety classification

| Component | Suggested class | Rationale |
|---|---|---|
| `safety.interlocks` | C | Failure or malfunction could directly result in serious injury (unbounded/unintended actuation) |
| `decoder`, `grips` state machine | C (as input to safety layer) | Feeds the safety layer; even though safety re-validates independently, decode quality affects usability-related hazards |
| `calibration` | B–C | Directly gates whether actuation is permitted (`CALIBRATION_STALE`) |
| `sensory_feedback.encoder` | C | Directly bounds tissue-safe charge injection |
| `power.wireless_charging` | B | Contributes to thermal/interference hazard mitigation, not itself actuation-critical |
| `api` (companion app backend) | B | Mode switching and lockout affect safety state, but the safety layer is the final authority |
| `ml.train` (offline training) | A–B | Runs offline, does not directly control the device in real time |

Actual classification must be assigned by the manufacturer's design
controls process per IEC 62304 §4.3, considering the complete system,
not the software in isolation.

## Lifecycle process mapping

| IEC 62304 process | Where addressed in this repo (as a starting point) |
|---|---|
| 5.1 Software development planning | `CONTRIBUTING.md`, this document |
| 5.2 Software requirements analysis | `README.md` capability list; would need a formal SRS |
| 5.3 Software architectural design | `docs/ARCHITECTURE.md` |
| 5.4 Software detailed design | Module docstrings throughout `src/neuroflex/` |
| 5.5 Software unit implementation and verification | `tests/` (unit tests per module) |
| 5.6 Software integration and integration testing | `tests/test_api.py`, `scripts/run_session_demo.py` as an integration smoke test |
| 5.7 Software system testing | Not present — would require a full V&V test plan against a formal SRS |
| 5.8 Software release | `CHANGELOG.md`, semantic version in `neuroflex/__init__.py` |
| 6. Software maintenance | `CONTRIBUTING.md`, `SECURITY.md` |
| 7. Software risk management | `docs/SAFETY.md`, `docs/compliance/RISK_MANAGEMENT.md` |
| 8. Software configuration management | Git history; recommend branch protection + signed releases for a real program |
| 9. Software problem resolution | GitHub Issues + `SECURITY.md` disclosure process (to be established) |

## Gaps to close before any real submission

- Formal Software Requirements Specification with bidirectional
  traceability to test cases
- Independent verification (not just author-written unit tests) for Class
  C components
- Static analysis / MISRA-equivalent coding standard enforcement for any
  embedded-target code derived from this reference software
- Full system-level V&V on representative target hardware
