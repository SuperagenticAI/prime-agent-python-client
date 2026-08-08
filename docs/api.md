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
| Lifecycle | `start`, `close`, `restart` |
| Escape hatch | `request` |

`prompt` acknowledges acceptance. Use `prompt_stream` or `prompt_and_wait` when
the application needs to wait for the terminal `agent_end` event.

`session.capabilities` contains the features declared for the detected Prime
Agent release. `session.supports("compact")` is a convenient feature check.
Compatibility metadata is advisory and does not hide the lower-level
`request()` escape hatch.

## `PrimeRpcTransport`

Use the lower-level transport when building a custom session abstraction:

```python
from prime_agent_client import PrimeRpcTransport


async with PrimeRpcTransport(cwd="/path/to/project") as transport:
    response = await transport.request("get_state")
    print(response.data)
```

Each call receives a generated correlation ID. Concurrent requests are safe,
pending calls fail immediately if the child process exits, and
`await transport.restart()` replaces a failed or stale child process.

Pass a standard-library `logging.Logger` through `PrimeSession(logger=...)` or
`PrimeRpcTransport(logger=...)` to integrate lifecycle and request logs. Log
records carry `prime_rpc_event`, `prime_rpc_command`, and
`prime_rpc_request_id` attributes where applicable. Prompts, response payloads,
and environment values are not logged.

## Events and responses

- `PrimeResponse.data` contains the command result.
- `PrimeResponse.raw` retains the full response object.
- `PrimeEvent.type` exposes the event discriminator.
- `PrimeEvent.raw` retains fields unknown to this client release.
- `PrimeEvent.get()` provides mapping-style access without closing the schema.
- `PrimeEvent.text_delta` extracts assistant text updates when present.
- `PrimeEvent.is_terminal` identifies the final `agent_end` event.

## Errors

All client exceptions inherit from `PrimeAgentError`:

- `PrimeNotStartedError`
- `PrimeProcessExited`
- `PrimeProtocolError`
- `PrimeRequestTimeout`
- `PrimeRpcError`
