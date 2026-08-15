# Risk Management Summary (Template, ISO 14971-style)

> Template only — see [`README.md`](README.md) disclaimer. This is a
> software-scoped excerpt of what a full risk management file would
> contain; it does not cover hardware, biocompatibility, or manufacturing
> risks.

## Scope

Software risks associated with the signal-decoding-to-actuation control
loop, daily calibration, sensory stimulation, and wireless charging
subsystems implemented in this repository. See `docs/SAFETY.md` for the
detailed hazard table (H1–H11) with implemented mitigations.

## Risk control approach

1. **Inherent safety by design** — e.g. the safety layer's independence
   from the decoder (see `docs/ARCHITECTURE.md`), fixed per-grip force/
   velocity ceilings that cannot be overridden by a software command,
   fail-safe defaults (deny → REST/zero-force/zero-velocity).
2. **Protective measures** — watchdog timeout, calibration freshness
   window, chatter-rate limiting, manual lockout.
3. **Information for safety** — companion app status/telemetry surfaces
   (`docs/API.md`) so patients/clinicians can see interlock trips and
   calibration state rather than the system failing silently.

## Residual risk (illustrative — not exhaustive)

| Residual risk | Why it remains | Suggested further mitigation |
|---|---|---|
| Decoder misclassifies a grip *above* the confidence threshold | Statistical classifiers have an inherent error rate even when "confident" | Track per-patient confusion matrices over time; consider requiring confirmatory cue for high-force grips |
| Watchdog/interlock logic itself has a defect | Software is not provably correct without formal verification | Independent code review, property-based testing, consider a hardware watchdog as a second layer |
| Companion app / API link is spoofed or intercepted | No authentication implemented in this reference version | See `CYBERSECURITY.md`; add mutual authentication before any real deployment |
| Patient over-relies on sensory feedback and doesn't visually confirm grip | Human factors risk, not purely software | Usability engineering file (IEC 62366-1), patient training program |

## Verification of risk controls

Each hazard in `docs/SAFETY.md` has at least one corresponding automated
test in `tests/test_safety.py`. A real risk management file would require
traceability records linking each risk control to its verification
evidence and sign-off, not just an automated test suite.

## Review cadence

For an actual program: risk management file is a living document, reviewed
at minimum at each design change, each post-market surveillance cycle, and
per adverse event/complaint investigation.
