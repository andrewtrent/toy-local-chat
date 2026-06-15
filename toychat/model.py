from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResult:
    text: str
    ok: bool
    error: str | None = None


def call_ollama(prompt: str, model: str, *, timeout: int = 120) -> ModelResult:
    try:
        proc = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return ModelResult(
            "[dry fallback] Ollama executable not found. Context was built and saved, but no model was called.",
            ok=False,
            error="ollama not found",
        )
    except subprocess.TimeoutExpired:
        return ModelResult("[error] Ollama call timed out.", ok=False, error="timeout")

    if proc.returncode != 0:
        return ModelResult(
            f"[error] Ollama exited with {proc.returncode}:\n{proc.stderr.strip()}",
            ok=False,
            error=proc.stderr.strip(),
        )
    return ModelResult(proc.stdout.strip(), ok=True)
