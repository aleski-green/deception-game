from __future__ import annotations

import asyncio
import shutil


_claude_path: str | None = shutil.which("claude")


async def chat(system: str, messages: list[dict], max_tokens: int = 1024) -> str:
    """Call Claude via the claude CLI tool (uses Max plan, no API key needed)."""
    if not _claude_path:
        raise RuntimeError("claude CLI not found in PATH")

    # Build the prompt: system context + user message
    user_content = messages[-1]["content"] if messages else ""
    full_prompt = f"{system}\n\n---\n\n{user_content}"

    proc = await asyncio.create_subprocess_exec(
        _claude_path, "-p", "--output-format", "text",
        "--max-turns", "1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate(input=full_prompt.encode())

    if proc.returncode != 0:
        err = stderr.decode().strip()
        raise RuntimeError(f"claude CLI error (exit {proc.returncode}): {err}")

    return stdout.decode().strip()


def set_api_key(key: str):
    """No-op — claude CLI uses Max plan credentials."""
    pass
