# Cybersecurity Considerations (Template)

> Template only — see [`README.md`](README.md) disclaimer.

## Attack surface (this repository's scope)

1. **Companion app ↔ device API link** (`neuroflex/api`) — in a real
   deployment this traverses BLE from phone to an external gateway, then
   to the implant's RF interface.
2. **Device API service** — currently unauthenticated in this reference
   implementation (development/demo only).
3. **Model/calibration artifacts** — the file-based model registry
   (`neuroflex/ml/train.py`) has no integrity checking in this reference
   version.

## Baseline considerations for a real premarket cybersecurity submission

- **Authentication & authorization**: mutual TLS or equivalent between app
  and gateway; per-patient/clinician scoped tokens; distinct clinician vs.
  patient privilege levels (e.g. only a clinician role should be able to
  change safety-relevant thresholds).
- **Confidentiality & integrity**: encrypt telemetry and calibration data
  in transit and at rest; sign model/calibration artifacts so a tampered
  `.joblib` file cannot silently be loaded (`ModelRegistry.load_latest`
  currently trusts the filesystem).
- **Availability**: the safety interlock's watchdog/fail-safe design
  (`docs/SAFETY.md`) is itself a resilience control — a denial-of-service
  against the API should degrade to "actuation disabled," never to
  "actuation unbounded."
- **Update mechanism**: any firmware/model OTA update path needs signed,
  versioned updates with rollback protection — not implemented in this
  reference repo.
- **SBOM**: maintain a software bill of materials for all third-party
  dependencies (`requirements.txt` here is a starting inventory, not a
  complete SBOM).
- **Vulnerability disclosure**: see [`../../SECURITY.md`](../../SECURITY.md).

## Explicitly out of scope for this reference implementation

- Real BLE stack implementation and pairing/bonding security
- Implant-side RF security
- Formal penetration testing / threat modeling deliverables (e.g. STRIDE
  analysis) — recommended before any real deployment
