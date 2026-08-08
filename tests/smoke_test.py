"""Installed-artifact smoke test used by package and release workflows."""

from importlib.metadata import version

from prime_agent_client import PrimeRpcTransport, __version__

assert version("prime-agent-python-client") == __version__
assert PrimeRpcTransport().argv == ("prime-agent", "--mode", "rpc")
