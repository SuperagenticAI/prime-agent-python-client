# Development

The repository uses uv for environments, locking, commands, and builds.

```bash
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
uvx twine check dist/*
```

The test suite uses `tests/fixtures/fake_prime_rpc.py`; it needs neither Prime
credentials nor model calls. The fixture writes actual byte-level JSONL through
a subprocess, so framing, streaming, tools, cancellation, errors, restart, and
lifecycle tests exercise the same boundary as the real executable.

Before submitting a protocol change:

1. Add or update a deterministic fixture scenario.
2. Preserve unknown fields in `PrimeEvent.raw` or `PrimeResponse.raw`.
3. Run Ruff, strict mypy, and the complete test suite.
4. Build both distributions and smoke-test the resulting wheel.
5. If compatibility metadata changes, test the public Prime Agent executable.
