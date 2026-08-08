# Prime Agent Python Client

[![CI](https://github.com/SuperagenticAI/prime-agent-python-client/actions/workflows/ci.yml/badge.svg)](https://github.com/SuperagenticAI/prime-agent-python-client/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/prime-agent-python-client.svg)](https://pypi.org/project/prime-agent-python-client/)
[![Python](https://img.shields.io/pypi/pyversions/prime-agent-python-client.svg)](https://pypi.org/project/prime-agent-python-client/)

An async, typed Python host client for the public JSONL RPC mode of
[Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent).

This package owns the application-side boundary: subprocess lifecycle,
correlated commands, streamed events, timeouts, cancellation, diagnostics, and
extension UI responses. Prime Agent remains the coding runtime and must be
installed separately.

> **Community project:** this package is maintained by Superagentic AI. It is
> not an official Prime Intellect product and is not endorsed by Prime
> Intellect. Prime Agent and Prime Intellect are names of their respective
> owners.

## Why this package exists

Prime Agent documents a capable RPC protocol, but its bundled host client is
TypeScript. Python applications otherwise need to reimplement framing,
correlation, lifecycle, and evolving event handling. This package provides one
small, dependency-free implementation that can be shared by CLIs, IDEs,
services, notebooks, and agent harnesses.

## Install

Install Prime Agent first and complete its normal login or provider setup:

```bash
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh
prime-agent
```

Then install the Python client:

```bash
uv add prime-agent-python-client
```

For a one-off script without a project, use
`uv run --with prime-agent-python-client your_script.py`. See the
[installation guide](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/installation.md)
for source checkouts and upgrades.

For a complete standalone and SuperQode walkthrough, use the
[recordable demo](examples/README.md).

## Quick start

```python
import asyncio

from prime_agent_client import PrimeSession


async def main() -> None:
    async with PrimeSession(
        cwd="/path/to/repository",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    ) as session:
        async for event in session.prompt_stream("Fix the failing tests"):
            if event.text_delta:
                print(event.text_delta, end="", flush=True)


asyncio.run(main())
```

No shell is used. `PrimeSession` launches the public executable as
`prime-agent --mode rpc` with an argv sequence.

## High-level API

```python
async with PrimeSession(cwd=".") as session:
    await session.prompt("Implement the feature")
    await session.steer("Keep the public API backward compatible")
    await session.follow_up("Run the focused tests when finished")

    state = await session.state()
    messages = await session.messages()
    stats = await session.stats()
    models = await session.available_models()

    await session.set_model("anthropic", "claude-sonnet-4-20250514")
    await session.compact("Keep decisions and unresolved failures")
    await session.refine(instructions="Remove redundant context")
```

Session operations include `new`, `switch_session`, `set_session_name`,
`fork`, and `clone`. The lower-level `PrimeRpcTransport.request()` method makes
new protocol commands usable before a convenience method is added.

Both levels support explicit restart. `PrimeSession.restart()` repeats version
detection and the readiness probe; `PrimeRpcTransport.restart()` replaces only
the subprocess. Cancelling `prompt_stream()` asks Prime Agent to abort the
active run before releasing the stream.

## Event compatibility

Events are intentionally open rather than modelled as a closed enum:

```python
async for event in session.prompt_stream("Inspect the repository"):
    print(event.type, event.raw)
```

`PrimeEvent.raw` preserves the complete RPC object, including event types and
fields introduced by later Prime Agent versions. Malformed records become
observable `protocol_error` events instead of disappearing.

The transport follows Prime Agent's strict framing requirements:

- LF is the only record delimiter
- CRLF input is accepted
- U+2028 and U+2029 inside JSON strings do not split records
- requests are correlated by generated IDs
- pending requests fail immediately if the process exits
- stderr is retained in a bounded diagnostic buffer

## Extension UI

Interactive extensions can ask the host to select, confirm, or collect input:

```python
async def ui(event):
    if event.get("method") == "confirm":
        return True
    return {"cancelled": True}


async with PrimeSession(cwd=".", ui_handler=ui) as session:
    await session.prompt_and_wait("Run the extension workflow")
```

Notification and status events are delivered to the handler but do not receive
a protocol response, matching Prime Agent's fire-and-forget semantics.

## Compatibility

The 0.2 line is tested against Prime Agent 0.7.0 and 0.7.1. Unknown versions
are allowed because the RPC protocol is additive, but they are marked as
untested:

```python
assert session.compatibility is not None
print(session.compatibility.tested)
print(session.supports("compact"))
```

The library supports Python 3.10 through 3.13 and has no runtime Python
dependencies.

## Security

Prime Agent executes model-generated Python and project commands with the
permissions of its process. This client is a transport, not a sandbox. Run it
only in repositories and execution environments whose trust model you
understand.

## Contributing

See the
[contribution guide](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/CONTRIBUTING.md).
Protocol changes should include a fake RPC fixture test and, where possible,
validation against the public Prime Agent executable.

## Documentation

- [Installation](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/installation.md)
- [API guide](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/api.md)
- [Architecture](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/architecture.md)
- [Compatibility policy](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/compatibility.md)
- [Development](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/development.md)
- [Releasing](https://github.com/SuperagenticAI/prime-agent-python-client/blob/main/docs/releasing.md)

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
