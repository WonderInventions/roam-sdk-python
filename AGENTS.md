# AGENTS.md

This is the generated Python SDK for the Roam API, published as `roamhq`.

## What you may edit

Hand-written files are listed in `.fernignore`:

- `src/roamhq/webhooks.py` — signature verification. Do not replace this with
  the generated helper.
- `tests/` — contract tests. See `tests/README.md` once present.
- `README.md`, `LICENSE`, `RELEASING.md`, `AGENTS.md`
- `.github/`, `.gitignore`, `.fernignore`

## What you must not edit

Everything else — `src/roamhq/` except `webhooks.py`, `pyproject.toml` (except
the version bump before a release) — is generated from
[WonderInventions/developer-ro-am](https://github.com/WonderInventions/developer-ro-am)
by Fern.

## Tests

```bash
python -m pip install -e .
python -m pytest tests/ -q
```
