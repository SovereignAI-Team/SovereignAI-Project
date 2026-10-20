"""Client for the local Ollama server (talks to 127.0.0.1 by default)."""
from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    """Ollama is not running, the model is missing, or the call failed."""


def llm_status() -> tuple[bool, str]:
    """Check that Ollama is reachable and the configured model is installed."""
    s = get_settings()
    try:
        r = httpx.get(f"{s.ollama_base_url}/api/tags", timeout=3.0)
        r.raise_for_status()
    except Exception:
        return False, "Ollama is not reachable. Install/start Ollama (https://ollama.com)."
    names = [m.get("name", "") for m in r.json().get("models", [])]
    wanted = s.ollama_model
    installed = any(n == wanted or n.split(":")[0] == wanted or (":" not in wanted and n == f"{wanted}:latest")
                    for n in names)
    if not installed:
        return False, f"Model '{wanted}' not installed. Run: ollama pull {wanted}"
    return True, f"{wanted} ready"


def generate(system_prompt: str, user_prompt: str) -> str:
    """Send one chat request to Ollama and return the answer text."""
    s = get_settings()
    ok, detail = llm_status()
    if not ok:
        raise LLMUnavailableError(detail)
    payload = {
        "model": s.ollama_model,
        "stream": False,
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        r = httpx.post(f"{s.ollama_base_url}/api/chat", json=payload, timeout=s.ollama_timeout_seconds)
        r.raise_for_status()
        content = r.json().get("message", {}).get("content", "").strip()
    except httpx.TimeoutException as exc:
        raise LLMUnavailableError(
            f"The local model timed out after {s.ollama_timeout_seconds}s. Try a smaller model or raise OLLAMA_TIMEOUT_SECONDS."
        ) from exc
    except Exception as exc:
        raise LLMUnavailableError(f"The local model call failed ({type(exc).__name__}).") from exc
    if not content:
        raise LLMUnavailableError("The local model returned an empty response.")
    return content
