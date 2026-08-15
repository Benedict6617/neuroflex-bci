# Security Policy

## Scope

This repository is a software reference implementation (see `README.md`
disclaimer). It does not control a real implanted device. That said, we
treat the safety-interlock and API layers seriously as a matter of good
practice, since real deployments would be derived from patterns like these.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for suspected security
vulnerabilities. Instead:

1. Email the maintainers (add your contact address here before publishing)
   with a description of the issue and reproduction steps.
2. Allow a reasonable disclosure window before any public discussion.

We aim to acknowledge reports within 5 business days.

## Known limitations of this reference implementation

These are documented, not hidden — see `docs/compliance/CYBERSECURITY.md`
for detail:

- The device API (`src/neuroflex/api`) ships with **no authentication**.
  Do not expose it outside a trusted local/demo network.
- The model registry (`src/neuroflex/ml/train.py`) does not verify the
  integrity of loaded model artifacts.
- CORS is wide open (`allow_origins=["*"]`) for local development
  convenience — tighten before any shared deployment.
