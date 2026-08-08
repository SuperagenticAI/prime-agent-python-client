# Installation

## Add the client to a project

Use uv to add the published package and record it in your project metadata:

```bash
uv add prime-agent-python-client
```

Upgrade within the version range declared by your project:

```bash
uv lock --upgrade-package prime-agent-python-client
uv sync
```

For a one-off script that does not have a uv project, provide the dependency to
the run without modifying the current environment:

```bash
uv run --with prime-agent-python-client your_script.py
```

The distribution name is `prime-agent-python-client`; the import name is
`prime_agent_client`.

## Install Prime Agent

This package hosts the RPC process but does not redistribute the Prime Agent
executable. Install Prime Agent using its official instructions, complete its
login or provider configuration, and verify it is available:

```bash
prime-agent --version
```

The client launches `prime-agent --mode rpc`. A different executable or wrapper
can be supplied through `PrimeSession(command=(...))`.

## Install from source

```bash
git clone https://github.com/SuperagenticAI/prime-agent-python-client.git
cd prime-agent-python-client
uv sync --locked --extra dev
uv run pytest
```
