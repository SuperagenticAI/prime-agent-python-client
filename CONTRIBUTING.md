# Contributing

Contributions are welcome, especially protocol conformance tests and support
for additive Prime Agent RPC commands.

## Development

```bash
git clone https://github.com/SuperagenticAI/prime-agent-python-client.git
cd prime-agent-python-client
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

Tests use a deterministic fake RPC process and do not require credentials or a
model call. Before changing framing or lifecycle behaviour, also inspect Prime
Agent's current `packages/coding-agent/docs/rpc.md` contract.

## Pull requests

- Keep the runtime dependency-free unless a dependency is essential.
- Preserve unknown response and event fields.
- Add a regression test for protocol and lifecycle changes.
- Do not expose credentials, environment values, or unbounded stderr.
- Update the compatibility matrix only after testing that Prime Agent release.
