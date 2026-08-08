"""High-level async Prime Agent session API."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .compatibility import PrimeCompatibility, compatibility_for, parse_version
from .errors import PrimeProcessExited, PrimeRequestTimeout
from .transport import PrimeEventStream, PrimeRpcTransport
from .types import ImageContent, PrimeEvent, PrimeResponse, PrimeVersion

UIResult = Mapping[str, Any] | bool | str | None
UIHandler = Callable[[PrimeEvent], Awaitable[UIResult] | UIResult]


class PrimeSession:
    """Own a Prime Agent RPC subprocess and expose typed Python operations."""

    def __init__(
        self,
        *,
        cwd: str | Path | None = None,
        provider: str | None = None,
        model: str | None = None,
        resume: str | Path | None = None,
        continue_session: bool = False,
        session_dir: str | Path | None = None,
        persist_session: bool = True,
        command: Sequence[str] = ("prime-agent",),
        args: Sequence[str] = (),
        env: Mapping[str, str] | None = None,
        request_timeout: float = 30.0,
        startup_timeout: float = 30.0,
        prompt_timeout: float = 600.0,
        refine_timeout: float = 600.0,
        check_version: bool = True,
        ui_handler: UIHandler | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        launch_args: list[str] = []
        if provider:
            launch_args.extend(("--provider", provider))
        if model:
            launch_args.extend(("--model", model))
        if resume is not None:
            launch_args.extend(("--resume", str(resume)))
        elif continue_session:
            launch_args.append("--continue")
        if session_dir is not None:
            launch_args.extend(("--session-dir", str(session_dir)))
        if not persist_session:
            launch_args.append("--no-session")
        launch_args.extend(str(arg) for arg in args)
        self.cwd = Path(cwd).resolve() if cwd is not None else Path.cwd().resolve()
        self.command = tuple(str(part) for part in command)
        self.startup_timeout = float(startup_timeout)
        self.prompt_timeout = float(prompt_timeout)
        self.refine_timeout = float(refine_timeout)
        self.check_version = check_version
        self.ui_handler = ui_handler
        self.version: PrimeVersion | None = None
        self.compatibility: PrimeCompatibility | None = None
        self.transport = PrimeRpcTransport(
            command=self.command,
            args=launch_args,
            cwd=self.cwd,
            env=env,
            request_timeout=request_timeout,
            logger=logger,
        )
        self._unsubscribe_ui: Callable[[], None] | None = None

    @property
    def running(self) -> bool:
        return self.transport.running

    @property
    def capabilities(self) -> frozenset[str]:
        """Capabilities declared for the detected Prime Agent version."""
        return self.compatibility.features if self.compatibility is not None else frozenset()

    def supports(self, feature: str) -> bool:
        """Return whether compatibility metadata declares a feature."""
        return self.compatibility is not None and self.compatibility.supports(feature)

    async def __aenter__(self) -> PrimeSession:
        await self.start()
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def start(self) -> None:
        if self.running:
            return
        if self.check_version:
            self.version = await self.detect_version()
            self.compatibility = compatibility_for(self.version)
        await self.transport.start()
        if self.ui_handler is not None:
            self._unsubscribe_ui = self.transport.add_event_callback(self._handle_ui_event)
        try:
            await self.state(timeout=self.startup_timeout)
        except Exception:
            await self.transport.close()
            raise

    async def close(self) -> None:
        if self._unsubscribe_ui is not None:
            self._unsubscribe_ui()
            self._unsubscribe_ui = None
        await self.transport.close()

    async def restart(self) -> None:
        """Replace the subprocess and repeat version and readiness checks."""
        await self.close()
        await self.start()

    async def detect_version(self) -> PrimeVersion:
        process = await asyncio.create_subprocess_exec(
            *self.command,
            "--version",
            cwd=str(self.cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise PrimeProcessExited(process.returncode, detail)
        return parse_version(stdout.decode("utf-8", errors="replace"))

    def events(self) -> PrimeEventStream:
        return self.transport.events()

    async def request(
        self, command: str, *, timeout: float | None = None, **params: Any
    ) -> PrimeResponse:
        return await self.transport.request(command, timeout=timeout, **params)

    async def prompt(
        self,
        message: str,
        *,
        images: Sequence[ImageContent] | None = None,
        streaming_behavior: str | None = None,
    ) -> None:
        params: dict[str, Any] = {"message": message}
        if images:
            params["images"] = list(images)
        if streaming_behavior:
            params["streamingBehavior"] = streaming_behavior
        await self.request("prompt", **params)

    async def prompt_stream(
        self,
        message: str,
        *,
        images: Sequence[ImageContent] | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[PrimeEvent]:
        stream = self.events()
        timeout_seconds = self.prompt_timeout if timeout is None else float(timeout)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        try:
            await self.prompt(message, images=images)
            while True:
                try:
                    remaining = deadline - asyncio.get_running_loop().time()
                    if remaining <= 0:
                        raise asyncio.TimeoutError
                    event = await asyncio.wait_for(stream.__anext__(), timeout=remaining)
                except asyncio.TimeoutError as exc:
                    with contextlib.suppress(Exception):
                        await self.abort()
                    raise PrimeRequestTimeout(
                        "prompt_events", timeout_seconds, self.transport.stderr
                    ) from exc
                except StopAsyncIteration:
                    return
                yield event
                if event.is_terminal:
                    return
        except asyncio.CancelledError:
            with contextlib.suppress(Exception):
                await asyncio.shield(self.abort())
            raise
        finally:
            await stream.aclose()

    async def prompt_and_wait(
        self,
        message: str,
        *,
        images: Sequence[ImageContent] | None = None,
        timeout: float | None = None,
    ) -> list[PrimeEvent]:
        return [
            event async for event in self.prompt_stream(message, images=images, timeout=timeout)
        ]

    async def steer(self, message: str, *, images: Sequence[ImageContent] | None = None) -> None:
        params: dict[str, Any] = {"message": message}
        if images:
            params["images"] = list(images)
        await self.request("steer", **params)

    async def follow_up(
        self, message: str, *, images: Sequence[ImageContent] | None = None
    ) -> None:
        params: dict[str, Any] = {"message": message}
        if images:
            params["images"] = list(images)
        await self.request("follow_up", **params)

    async def abort(self) -> None:
        await self.request("abort")

    async def new(self, *, parent_session: str | None = None) -> Mapping[str, Any]:
        params: dict[str, Any] = {"parentSession": parent_session} if parent_session else {}
        response = await self.request("new_session", **params)
        return _mapping(response.data)

    async def state(self, *, timeout: float | None = None) -> Mapping[str, Any]:
        return _mapping((await self.request("get_state", timeout=timeout)).data)

    async def messages(self) -> list[Mapping[str, Any]]:
        data = _mapping((await self.request("get_messages")).data)
        messages = data.get("messages")
        return list(messages) if isinstance(messages, list) else []

    async def stats(self) -> Mapping[str, Any]:
        return _mapping((await self.request("get_session_stats")).data)

    async def last_assistant_text(self) -> str | None:
        data = _mapping((await self.request("get_last_assistant_text")).data)
        text = data.get("text")
        return str(text) if text is not None else None

    async def set_model(self, provider: str, model_id: str) -> Mapping[str, Any]:
        return _mapping((await self.request("set_model", provider=provider, modelId=model_id)).data)

    async def available_models(self) -> list[Mapping[str, Any]]:
        data = _mapping((await self.request("get_available_models")).data)
        models = data.get("models")
        return list(models) if isinstance(models, list) else []

    async def switch_session(self, session_path: str | Path) -> Mapping[str, Any]:
        return _mapping((await self.request("switch_session", sessionPath=str(session_path))).data)

    async def set_session_name(self, name: str) -> None:
        await self.request("set_session_name", name=name)

    async def fork(self, entry_id: str) -> Mapping[str, Any]:
        return _mapping((await self.request("fork", entryId=entry_id)).data)

    async def clone(self) -> Mapping[str, Any]:
        return _mapping((await self.request("clone")).data)

    async def compact(self, instructions: str | None = None) -> Mapping[str, Any]:
        params: dict[str, Any] = {"customInstructions": instructions} if instructions else {}
        return _mapping((await self.request("compact", **params)).data)

    async def refine(
        self,
        *,
        instructions: str | None = None,
        rollback_id: str | None = None,
        global_: bool = False,
    ) -> Mapping[str, Any]:
        params: dict[str, Any] = {"global": bool(global_)}
        if instructions:
            params["instructions"] = instructions
        if rollback_id:
            params["rollbackId"] = rollback_id
        return _mapping((await self.request("refine", timeout=self.refine_timeout, **params)).data)

    async def _handle_ui_event(self, event: PrimeEvent) -> None:
        if event.type != "extension_ui_request" or self.ui_handler is None:
            return
        request_id = event.get("id")
        if not isinstance(request_id, str):
            return
        result = self.ui_handler(event)
        if inspect.isawaitable(result):
            result = await result
        if event.get("method") not in {"select", "confirm", "input", "editor"}:
            return
        response: dict[str, Any] = {"type": "extension_ui_response", "id": request_id}
        if isinstance(result, Mapping):
            response.update(result)
        elif isinstance(result, bool):
            response["confirmed"] = result
        elif isinstance(result, str):
            response["value"] = result
        else:
            response["cancelled"] = True
        await self.transport.send(response)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
