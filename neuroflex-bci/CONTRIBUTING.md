# Contributing to NeuroFlex

Thanks for your interest in improving this reference platform.

## Ground rules

- This is a **software reference implementation**, not a certified medical
  device. Contributions should keep that boundary clear — don't add claims
  of regulatory clearance, and don't remove or weaken the disclaimers in
  `README.md` / `docs/compliance/`.
- Any change touching `src/neuroflex/safety/` requires accompanying test
  changes in `tests/test_safety.py` and a note in the PR description
  explaining which hazard(s) in `docs/SAFETY.md` are affected.
- Keep modules small and independently testable — see `docs/ARCHITECTURE.md`
  for the intended module boundaries.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

## Running checks locally

```bash
pytest -q                     # unit + API tests
python scripts/run_session_demo.py --patient P-1002 \
  --session data/sample/sessions/P-1002_2026-02-02.json   # integration smoke test
```

## Regenerating sample data

Sample data is synthetic and regenerated deterministically:

```bash
python scripts/generate_sample_data.py
```

If you change the generator, regenerate and commit the resulting files so
`data/sample/` stays in sync with the code that produced it.

## Commit / PR conventions

- Keep PRs focused on one module or concern where possible.
- Update `CHANGELOG.md` under "Unreleased" for any user-facing change.
- New public functions/classes should have a docstring explaining intent,
  not just parameters — this codebase favors "why" comments in
  safety-relevant modules.

## Reporting issues

Use GitHub Issues for bugs and feature requests. For anything you believe
is a security vulnerability, follow `SECURITY.md` instead of opening a
public issue.
