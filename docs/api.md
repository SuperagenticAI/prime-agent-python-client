# API guide

## `PrimeSession`

`PrimeSession` is the usual entry point. It detects the Prime Agent version,
starts RPC mode, probes readiness with `get_state`, handles extension UI
messages, and closes the subprocess when its async context exits.

| Area | Methods |
| --- | --- |
| Execution | `prompt`, `prompt_stream`, `prompt_and_wait`, `abort` |
| Queues | `steer`, `follow_up` |
| Inspection | `state`, `messages`, `stats`, `last_assistant_text` |
| Models | `set_model`, `available_models` |
| Context | `compact`, `refine` |
| Sessions | `new`, `switch_session`, `set_session_name`, `fork`, `clone` |
| Escape hatch | `request` |

`prompt` acknowledges acceptance. Use `prompt_stream` or `prompt_and_wait` when
the application needs to wait for the terminal `agent_end` event.

## `PrimeRpcTransport`

Use the lower-level transport when building a custom session abstraction:

```python
from prime_agent_client import PrimeRpcTransport


transport = PrimeRpcTransport(cwd="/path/to/project")
await transport.start()
try:
    response = await transport.request("get_state")
    print(response.data)
finally:
    await transport.close()
```

Each call receives a generated correlation ID. Concurrent requests are safe,
and pending calls fail immediately if the child process exits.

## Events and responses

- `PrimeResponse.data` contains the command result.
- `PrimeResponse.raw` retains the full response object.
- `PrimeEvent.type` exposes the event discriminator.
- `PrimeEvent.raw` retains fields unknown to this client release.
- `PrimeEvent.get()` provides mapping-style access without closing the schema.

## Errors

All client exceptions inherit from `PrimeAgentError`:

- `PrimeNotStartedError`
- `PrimeProcessExited`
- `PrimeProtocolError`
- `PrimeRequestTimeout`
- `PrimeRpcError`

