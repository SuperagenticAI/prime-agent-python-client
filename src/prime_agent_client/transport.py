"""Async subprocess transport for Prime Agent's strict JSONL RPC protocol."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .errors import (
    PrimeNotStartedError,
    PrimeProcessExited,
    PrimeProtocolError,
    PrimeRequestTimeout,
    PrimeRpcError,
)
from .types import PrimeEvent, PrimeResponse

_STREAM_CLOSED = object()
EventCallback = Callable[[PrimeEvent], Awaitable[None] | None]


class PrimeEventStream(AsyncIterator[PrimeEvent]):
    """Independent async stream of events emitted by a transport."""

    def __init__(self, transport: PrimeRpcTransport) -> None:
        self._transport = transport
        self._queue: asyncio.Queue[PrimeEvent | object] = asyncio.Queue()
        self._closed = False
        transport._event_queues.add(self._queue)

    def __aiter__(self) -> PrimeEventStream:
        return self

    async def __anext__(self) -> PrimeEvent:
        item = await self._queue.get()
        if item is _STREAM_CLOSED:
            self._closed = True
            raise StopAsyncIteration
        return item  # type: ignore[return-value]

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._transport._event_queues.discard(self._queue)
        self._queue.put_nowait(_STREAM_CLOSED)

    async def __aenter__(self) -> PrimeEventStream:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()


class PrimeRpcTransport:
    """Correlated request/response transport over a Prime Agent subprocess."""

    def __init__(
        self,
        *,
        command: Sequence[str] = ("prime-agent",),
        args: Sequence[str] = (),
        cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        request_timeout: float = 30.0,
        shutdown_timeout: float = 5.0,
        max_line_bytes: int = 16 * 1024 * 1024,
        stderr_limit: int = 64 * 1024,
        logger: logging.Logger | None = None,
    ) -> None:
        if not command:
            raise ValueError("Prime Agent command cannot be empty")
        self.command = tuple(str(part) for part in command)
        self.args = tuple(str(part) for part in args)
        self.cwd = Path(cwd).resolve() if cwd is not None else None
        self.env = dict(env or {})
        self.request_timeout = float(request_timeout)
        self.shutdown_timeout = float(shutdown_timeout)
        self.max_line_bytes = int(max_line_bytes)
        self.stderr_limit = int(stderr_limit)
        self.logger = logger or logging.getLogger("prime_agent_client.transport")

        self._process: asyncio.subprocess.Process | None = None
        self._stdout_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._wait_task: asyncio.Task[None] | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._write_lock = asyncio.Lock()
        self._request_id = 0
        self._stderr_chunks: deque[bytes] = deque()
        self._stderr_size = 0
        self._event_queues: set[asyncio.Queue[PrimeEvent | object]] = set()
        self._callbacks: list[EventCallback] = []
        self._closing = False

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def argv(self) -> tuple[str, ...]:
        return (*self.command, "--mode", "rpc", *self.args)

    @property
    def stderr(self) -> str:
        return b"".join(self._stderr_chunks).decode("utf-8", errors="replace")

    async def __aenter__(self) -> PrimeRpcTransport:
        await self.start()
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def start(self) -> None:
        if self.running:
            raise RuntimeError("Prime Agent RPC transport is already started")
        if self._process is not None:
            await self.close()
        process_env = os.environ.copy()
        process_env.update(self.env)
        self._closing = False
        self._stderr_chunks.clear()
        self._stderr_size = 0
        self.logger.debug(
            "Starting Prime Agent RPC process",
            extra={
                "prime_rpc_event": "process_start",
                "prime_rpc_executable": self.command[0],
            },
        )
        self._process = await asyncio.create_subprocess_exec(
            *self.argv,
            cwd=str(self.cwd) if self.cwd is not None else None,
            env=process_env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=self.max_line_bytes + 1,
        )
        self._stdout_task = asyncio.create_task(self._read_stdout(), name="prime-rpc-stdout")
        self._stderr_task = asyncio.create_task(self._read_stderr(), name="prime-rpc-stderr")
        self._wait_task = asyncio.create_task(self._watch_process(), name="prime-rpc-process")

    async def restart(self) -> None:
        """Close any current process and start a fresh RPC subprocess."""
        await self.close()
        await self.start()

    async def close(self) -> None:
        process = self._process
        if process is None:
            return
        self._closing = True
        if process.stdin is not None and not process.stdin.is_closing():
            process.stdin.close()
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                await process.stdin.wait_closed()
        try:
            await asyncio.wait_for(process.wait(), timeout=self.shutdown_timeout)
        except asyncio.TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        await self._finish_tasks()
        self._reject_pending(PrimeProcessExited(process.returncode, self.stderr))
        self._close_event_streams()
        self._process = None
        self.logger.debug(
            "Closed Prime Agent RPC process",
            extra={"prime_rpc_event": "process_close", "prime_rpc_returncode": process.returncode},
        )

    async def request(
        self,
        command: str,
        *,
        timeout: float | None = None,
        **params: Any,
    ) -> PrimeResponse:
        process = self._process
        if process is None or process.returncode is not None or process.stdin is None:
            raise PrimeNotStartedError("Prime Agent RPC transport is not running")

        self._request_id += 1
        request_id = f"py_{self._request_id}"
        payload = {"id": request_id, "type": command, **params}
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[request_id] = future
        log_context = {"prime_rpc_command": command, "prime_rpc_request_id": request_id}
        self.logger.debug("Sending Prime Agent RPC request", extra=log_context)

        wire = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        )
        try:
            async with self._write_lock:
                process.stdin.write(wire)
                await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as exc:
            self._pending.pop(request_id, None)
            raise PrimeProcessExited(process.returncode, self.stderr) from exc

        deadline = self.request_timeout if timeout is None else float(timeout)
        try:
            response = await asyncio.wait_for(asyncio.shield(future), timeout=deadline)
        except asyncio.TimeoutError as exc:
            self._pending.pop(request_id, None)
            future.cancel()
            self.logger.warning(
                "Prime Agent RPC request timed out",
                extra={**log_context, "prime_rpc_timeout": deadline},
            )
            raise PrimeRequestTimeout(command, deadline, self.stderr) from exc
        except asyncio.CancelledError:
            self._pending.pop(request_id, None)
            future.cancel()
            raise

        if response.get("success") is not True:
            self.logger.warning("Prime Agent RPC request failed", extra=log_context)
            raise PrimeRpcError(command, str(response.get("error") or "Unknown error"), response)
        self.logger.debug("Received Prime Agent RPC response", extra=log_context)
        return PrimeResponse(
            id=request_id,
            command=str(response.get("command") or command),
            data=response.get("data"),
            raw=response,
        )

    async def send(self, payload: Mapping[str, Any]) -> None:
        """Send an uncorrelated protocol message, such as a UI response."""
        process = self._process
        if process is None or process.returncode is not None or process.stdin is None:
            raise PrimeNotStartedError("Prime Agent RPC transport is not running")
        wire = (
            json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        async with self._write_lock:
            process.stdin.write(wire)
            await process.stdin.drain()

    def events(self) -> PrimeEventStream:
        return PrimeEventStream(self)

    def add_event_callback(self, callback: EventCallback) -> Callable[[], None]:
        self._callbacks.append(callback)

        def unsubscribe() -> None:
            with contextlib.suppress(ValueError):
                self._callbacks.remove(callback)

        return unsubscribe

    async def _read_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        while True:
            try:
                raw = await process.stdout.readline()
            except (ValueError, asyncio.LimitOverrunError) as exc:
                self._publish_protocol_error(f"RPC line exceeded {self.max_line_bytes} bytes", exc)
                return
            if not raw:
                return
            if len(raw) > self.max_line_bytes:
                self._publish_protocol_error(f"RPC line exceeded {self.max_line_bytes} bytes")
                continue
            if raw.endswith(b"\n"):
                raw = raw[:-1]
            if raw.endswith(b"\r"):
                raw = raw[:-1]
            if not raw:
                continue
            try:
                decoded = raw.decode("utf-8")
                payload = json.loads(decoded)
                if not isinstance(payload, dict):
                    raise PrimeProtocolError("RPC record must be a JSON object")
            except (UnicodeDecodeError, json.JSONDecodeError, PrimeProtocolError) as exc:
                self._publish_protocol_error("Invalid RPC JSON record", exc, raw=raw)
                continue
            self._handle_payload(payload)

    async def _read_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        while chunk := await process.stderr.read(4096):
            self._stderr_chunks.append(chunk)
            self._stderr_size += len(chunk)
            while self._stderr_size > self.stderr_limit and self._stderr_chunks:
                removed = self._stderr_chunks.popleft()
                self._stderr_size -= len(removed)

    async def _watch_process(self) -> None:
        process = self._process
        if process is None:
            return
        returncode = await process.wait()
        if not self._closing:
            self.logger.warning(
                "Prime Agent RPC process exited",
                extra={
                    "prime_rpc_event": "process_exit",
                    "prime_rpc_returncode": returncode,
                },
            )
            self._reject_pending(PrimeProcessExited(returncode, self.stderr))
            self._close_event_streams()

    def _handle_payload(self, payload: dict[str, Any]) -> None:
        request_id = payload.get("id")
        if payload.get("type") == "response" and isinstance(request_id, str):
            pending = self._pending.pop(request_id, None)
            if pending is not None and not pending.done():
                pending.set_result(payload)
                return
        event = PrimeEvent.from_dict(payload)
        for queue in tuple(self._event_queues):
            queue.put_nowait(event)
        for callback in tuple(self._callbacks):
            try:
                result = callback(event)
                if result is not None:
                    task = asyncio.ensure_future(result)
                    task.add_done_callback(_consume_task_exception)
            except Exception:
                # One observer must not prevent protocol processing or delivery
                # to other observers.
                continue

    def _publish_protocol_error(
        self,
        message: str,
        error: BaseException | None = None,
        *,
        raw: bytes | None = None,
    ) -> None:
        payload: dict[str, Any] = {"type": "protocol_error", "message": message}
        if error is not None:
            payload["error"] = str(error)
        if raw is not None:
            payload["raw"] = raw.decode("utf-8", errors="replace")[:2000]
        self._handle_payload(payload)

    def _reject_pending(self, error: BaseException) -> None:
        pending = list(self._pending.values())
        self._pending.clear()
        for future in pending:
            if not future.done():
                future.set_exception(error)

    def _close_event_streams(self) -> None:
        for queue in tuple(self._event_queues):
            queue.put_nowait(_STREAM_CLOSED)
        self._event_queues.clear()

    async def _finish_tasks(self) -> None:
        current = asyncio.current_task()
        tasks = [
            task
            for task in (self._stdout_task, self._stderr_task, self._wait_task)
            if task is not None and task is not current
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._stdout_task = None
        self._stderr_task = None
        self._wait_task = None


def _consume_task_exception(task: asyncio.Future[None]) -> None:
    """Retrieve observer failures so they do not become loop-level warnings."""
    if not task.cancelled():
        task.exception()
