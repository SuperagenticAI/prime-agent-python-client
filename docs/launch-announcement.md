# Launch announcement

## Native Python hosting for Prime Agent

Prime Agent can now be hosted from an async Python application with
`prime-agent-python-client`, a small open-source RPC client maintained by
Superagentic AI.

The package manages the application side of Prime Agent's public JSONL RPC
mode: subprocess lifecycle, correlated requests, streamed events, cancellation,
timeouts, bounded diagnostics, extension UI responses, and forward-compatible
event handling. Prime Agent remains the coding runtime and is installed and
authenticated separately.

Add it to a Python project with uv:

```bash
uv add "prime-agent-python-client>=0.2.0"
```

Then stream a response without a JavaScript host:

```python
import asyncio

from prime_agent_client import PrimeSession


async def main() -> None:
    async with PrimeSession(cwd=".", provider="github-copilot", model="gpt-4.1") as session:
        async for event in session.prompt_stream("Explain this repository"):
            if event.text_delta:
                print(event.text_delta, end="", flush=True)


asyncio.run(main())
```

The same package powers SuperQode's `prime-agent` harness backend. Install the
released CLI, then save this as `prime-agent.yaml` in the target repository:

```bash
uv tool install superqode
```

```yaml
name: prime-agent-coder
inherits: coding
runtime:
  backend: prime-agent
  config:
    prime_agent:
      prompt_timeout: 900
model_policy:
  primary: github-copilot/gpt-4.1
workflow:
  mode: single
```

Run it with streaming output:

```bash
superqode harness run \
  --spec prime-agent.yaml \
  --prompt "Explain this repository" \
  --provider github-copilot \
  --model gpt-4.1 \
  --stream
```

The integration has been exercised against the real Prime Agent RPC process and
GitHub Copilot, while its CI contract suite uses a deterministic subprocess and
requires no provider credentials.

Links:

- Client repository: <https://github.com/SuperagenticAI/prime-agent-python-client>
- Python package: <https://pypi.org/project/prime-agent-python-client/>
- SuperQode repository: <https://github.com/SuperagenticAI/superqode>
- SuperQode documentation: <https://superagenticai.github.io/superqode/prime-agent-python-client/>

`prime-agent-python-client` is a community-maintained project and is not an
official Prime Intellect product.

## Short version

Prime Agent now has a reusable async Python host client. Install
`prime-agent-python-client` 0.2.0 with uv to manage RPC lifecycle, correlated
commands, streaming, cancellation, and diagnostics from Python, or use it
through the Prime Agent harness backend in SuperQode 0.2.80 and later.
