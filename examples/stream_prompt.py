"""Stream a Prime Agent response from a standalone Python application."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from prime_agent_client import PrimeSession


async def run(repository: Path, prompt: str, provider: str | None, model: str | None) -> None:
    async with PrimeSession(
        cwd=repository,
        provider=provider,
        model=model,
    ) as session:
        async for event in session.prompt_stream(prompt):
            if event.text_delta:
                print(event.text_delta, end="", flush=True)
        print()
        print(json.dumps(await session.stats(), indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--provider")
    parser.add_argument("--model")
    args = parser.parse_args()
    asyncio.run(run(args.repository.resolve(), args.prompt, args.provider, args.model))


if __name__ == "__main__":
    main()
