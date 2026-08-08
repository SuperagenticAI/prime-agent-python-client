# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-08-08

### Added

- Context-manager and explicit restart support for the low-level RPC transport.
- Session restart, compatibility capability checks, event text helpers, and
  structured standard-library lifecycle and request logging.
- Contract tests for tool events, request and prompt cancellation, clean
  restart, context shutdown, and logging metadata.

### Changed

- Cancelling a prompt stream now asks Prime Agent to abort the active run before
  releasing the event stream.
- Async deadline handling uses `asyncio.TimeoutError` so Python 3.10 raises the
  same public `PrimeRequestTimeout` exceptions as Python 3.11 through 3.13.

## [0.1.0] - 2026-08-08

### Added

- Dependency-free asyncio subprocess transport for Prime Agent RPC mode.
- Strict LF JSONL framing with CRLF tolerance and Unicode separator safety.
- Correlated requests, bounded stderr diagnostics, request deadlines, process
  failure propagation, and graceful shutdown.
- Open `PrimeEvent` values that preserve unknown event fields.
- High-level prompt, steering, follow-up, model, compaction, refinement,
  statistics, and session operations.
- Independent async event streams, observer callbacks, and extension UI
  request handling.
- Explicit compatibility metadata for Prime Agent 0.7.0 and 0.7.1.

[Unreleased]: https://github.com/SuperagenticAI/prime-agent-python-client/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/SuperagenticAI/prime-agent-python-client/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/SuperagenticAI/prime-agent-python-client/releases/tag/v0.1.0
