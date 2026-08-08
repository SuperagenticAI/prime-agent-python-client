# Architecture

```text
Python application
      |
      | PrimeSession
      v
PrimeRpcTransport
      |
      | stdin/stdout: strict LF-delimited JSON
      v
prime-agent --mode rpc
```

The client uses `asyncio.create_subprocess_exec`, never a shell. A write lock
keeps JSON records atomic, generated IDs correlate responses, and independent
queues allow multiple event consumers.

Prime Agent's response schema and event schema evolve at different speeds.
Known command results have convenience methods, while raw response and event
objects remain available. This lets an application consume additive upstream
fields without waiting for a client release.

Process stderr is drained concurrently into a bounded buffer. Request timeout
and process-exit exceptions include recent stderr, but the client never reads
or logs arbitrary environment variables.

The transport is deliberately dependency-free. Framework-specific adapters
belong in their consuming projects rather than the protocol package.

