# Releasing

Releases are built in GitHub Actions and published through PyPI Trusted
Publishing. No long-lived PyPI token should be stored in repository secrets.

## One-time repository configuration

1. Create a GitHub environment named `pypi`.
2. In the PyPI project settings, add a Trusted Publisher for:
   - owner: `SuperagenticAI`
   - repository: `prime-agent-python-client`
   - workflow: `release.yml`
   - environment: `pypi`
3. Protect the GitHub environment if release approval is desired.

## Release checklist

1. Update the version in `pyproject.toml` and
   `src/prime_agent_client/_version.py`.
2. Move the release notes from `Unreleased` into a dated changelog section.
3. Run:

   ```bash
   uv sync --locked --extra dev
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy
   uv run pytest
   uv build
   uvx twine check dist/*
   ```

4. Merge the release commit to `main`.
5. Create and push the matching annotated tag:

   ```bash
   git tag -a v0.1.1 -m "v0.1.1"
   git push origin v0.1.1
   ```

The tag workflow rebuilds and smoke-tests both artifacts before publishing.
The PyPA publish action uploads provenance attestations automatically.
