# Compatibility policy

The client currently marks Prime Agent 0.7.0 and 0.7.1 as tested. Version
detection is advisory: an unknown release can still start because the RPC
protocol is designed to grow additively.

```python
async with PrimeSession(cwd=".") as session:
    assert session.version is not None
    assert session.compatibility is not None
    print(session.version.normalized)
    print(session.compatibility.tested)
```

A Prime Agent release is added to the tested set only after the fake-process
suite and a real `get_state` lifecycle smoke test pass. Breaking protocol
changes require a new client minor release and a compatibility note in the
changelog.

The 0.1 client supports Python 3.10 through 3.13. The CI matrix exercises every
supported minor version.

