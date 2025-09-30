# Repository Guidelines

## Project Structure & Module Organization
The repository is intentionally lean right now; add substantive code under `src/idcard_ocr/` using package modules for readers, preprocessors, and inference pipelines. Store shared utilities in `src/idcard_ocr/utils/` and training notebooks under `notebooks/` when necessary. Put sample assets and anonymized fixtures in `assets/samples/`; keep secrets and raw ID scans out of git. Tests belong in `tests/` mirroring the module tree (e.g., `tests/pipelines/test_reader.py`). Configuration files (`configs/*.yaml`) should describe model weights, thresholds, and OCR engine choices.

## Build, Test, and Development Commands
Create a virtual environment with `python3 -m venv .venv && source .venv/bin/activate`. Install dependencies via `pip install -r requirements.txt` (add the file if your change introduces new packages). Run `make format` to apply `black` and `ruff` checks before committing; `make lint` surfaces style violations, while `make test` executes the pytest suite. Use `pytest -m "not slow"` before opening a PR.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and type annotations on public functions. Name modules after the artifact they expose (`ocr_reader.py`, `document_parser.py`), and prefer descriptive class names like `NationalIdExtractor`. Document non-obvious logic with concise docstrings. Linting uses `ruff` with the default ruleset and `black` with 88-character lines; add an inline comment if you must ignore a rule.

## Testing Guidelines
Write `pytest`-style tests that mirror the module structure (e.g., `tests/utils/test_image_ops.py`). Each new feature needs unit coverage plus property or integration tests for OCR pipelines. Target >=90% line coverage; justify any decreases inside the PR. Use factory helpers and redacted fixtures stored under `tests/fixtures/` rather than raw assets.

## Commit & Pull Request Guidelines
Git history currently uses short imperative subjects (`first commit`); continue that style with <=72 characters and an optional body explaining rationale. Reference issue IDs when available (`feat: add layout parser (#42)`). Pull requests must include a clear summary, validation notes (commands run, coverage stats), and screenshots or text dumps for OCR outputs if visuals change. Request review once CI is green and data files are redacted.

## Security & Data Handling
Treat ID documents as sensitive: never commit personal data or API keys. Store credentials via environment variables and document required keys in `.env.example`. When sharing assets, scrub names, numbers, and faces before uploading. Audit dependencies for OCR engines and ensure licenses allow redistribution.
