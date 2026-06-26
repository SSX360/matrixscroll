"""
LLM backend abstraction for Digital Rain.

Three backends, one interface:
  - "anthropic" (default): Claude via the Anthropic API. Best reasoning for the
    open-ended "what should I set up" recommendations. Needs ANTHROPIC_API_KEY.
  - "gemini": Google Gemini via the google-genai SDK. Needs GEMINI_API_KEY.
  - "ollama": a local model (e.g. gemma4:e4b). Fully offline, no API key.

Selection / fallback:
  LLM_BACKEND picks the preferred backend ("anthropic" by default). Resolution
  walks a chain — preferred first, then anthropic -> gemini -> ollama — and uses
  the first one that is actually usable (key present + SDK installed; ollama is
  always the last-resort offline fallback). At call time, if a backend errors we
  fall through to the next one in the chain. Callers don't care which ran.

Two call styles:
  - generate(...) -> str           : one complete answer (used by MCP tools)
  - stream(...)   -> Iterator[str] : token stream (used by the Flask web UI)

A "message" is {"role": "user"|"assistant", "content": str}. The system prompt is
passed separately and placed correctly per backend (Anthropic: top-level system=;
Gemini: config.system_instruction; Ollama: a leading {"role":"system"} message).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Iterator

import requests

# --- configuration ---------------------------------------------------------

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "").strip() or OLLAMA_MODEL
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "512"))
OLLAMA_BRAINSTORM_NUM_PREDICT = int(os.environ.get("OLLAMA_BRAINSTORM_NUM_PREDICT", "256"))

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
# claude-sonnet-4-6 is a cheaper alternative; set ANTHROPIC_MODEL to switch.

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# gemini-2.5-pro is the stronger (pricier) option; set GEMINI_MODEL to switch.

_PREFERRED = os.environ.get("LLM_BACKEND", "anthropic").strip().lower()

# Fall-through order once the preferred backend is moved to the front.
_PRIORITY = ["anthropic", "gemini", "ollama"]


def _log(msg: str) -> None:
    # stderr only: MCP stdio transport owns stdout.
    print(f"[llm] {msg}", file=sys.stderr)


def has_anthropic_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def has_gemini_key() -> bool:
    # Accept either GEMINI_API_KEY or Google's GOOGLE_API_KEY convention.
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _usable(backend: str) -> bool:
    """Can this backend actually run right now (key present + SDK installed)?"""
    if backend == "anthropic":
        return has_anthropic_key() and _has_module("anthropic")
    if backend == "gemini":
        return has_gemini_key() and _has_module("google.genai")
    if backend == "ollama":
        return True  # always the last-resort offline fallback
    return False


def _backend_chain() -> list[str]:
    """Preferred backend first, then the rest of the priority order."""
    ordered = [_PREFERRED] + [b for b in _PRIORITY if b != _PREFERRED]
    chain, seen = [], set()
    for b in ordered:
        if b in _PRIORITY and b not in seen:
            chain.append(b)
            seen.add(b)
    return chain


def active_backend() -> str:
    """The first usable backend in the chain (what a call will try first)."""
    for b in _backend_chain():
        if _usable(b):
            return b
    return "ollama"


def backend_status() -> dict:
    """Lightweight introspection for /api/health and diagnostics."""
    return {
        "preferred": _PREFERRED,
        "active": active_backend(),
        "chain": _backend_chain(),
        "anthropic_key": has_anthropic_key(),
        "anthropic_model": ANTHROPIC_MODEL,
        "gemini_key": has_gemini_key(),
        "gemini_model": GEMINI_MODEL,
        "ollama_model": OLLAMA_MODEL,
        "ollama_chat_model": OLLAMA_CHAT_MODEL,
        "ollama_url": OLLAMA_URL,
    }


# --- Anthropic -------------------------------------------------------------

def _anthropic_client():
    import anthropic
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def _anthropic_generate(system: str, messages: list[dict], max_tokens: int) -> str:
    client = _anthropic_client()
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _anthropic_stream(system: str, messages: list[dict], max_tokens: int) -> Iterator[str]:
    client = _anthropic_client()
    with client.messages.stream(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    ) as s:
        for text in s.text_stream:
            if text:
                yield text


# --- Gemini ----------------------------------------------------------------

def _gemini_client():
    from google import genai
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=key)


def _gemini_contents(messages: list[dict]) -> list[dict]:
    # Gemini uses role "model" for assistant turns; system is passed via config.
    return [{"role": "model" if m["role"] == "assistant" else "user",
             "parts": [{"text": m["content"]}]}
            for m in messages]


def _gemini_generate(system: str, messages: list[dict], max_tokens: int) -> str:
    client = _gemini_client()
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=_gemini_contents(messages),
        config={"system_instruction": system, "max_output_tokens": max_tokens},
    )
    return resp.text or ""


def _gemini_stream(system: str, messages: list[dict], max_tokens: int) -> Iterator[str]:
    client = _gemini_client()
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=_gemini_contents(messages),
        config={"system_instruction": system, "max_output_tokens": max_tokens},
    ):
        if chunk.text:
            yield chunk.text


# --- Ollama ----------------------------------------------------------------

def _ollama_messages(system: str, messages: list[dict]) -> list[dict]:
    out = [{"role": "system", "content": system}] if system else []
    out.extend(messages)
    return out


def _ollama_unreachable(e: Exception) -> "LLMError":
    return LLMError(
        f"Couldn't reach a local model at {OLLAMA_URL} ({e}). Start Ollama "
        f"('ollama serve' + 'ollama pull {OLLAMA_MODEL}'), or set ANTHROPIC_API_KEY "
        f"to use Claude.")


def _ollama_options(temperature: float, num_predict: int | None = None) -> dict:
    return {
        "temperature": temperature,
        "num_predict": num_predict if num_predict is not None else OLLAMA_NUM_PREDICT,
    }


def _ollama_generate(
    system: str,
    messages: list[dict],
    temperature: float,
    *,
    model: str | None = None,
    num_predict: int | None = None,
) -> str:
    use_model = model or OLLAMA_MODEL
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": use_model, "messages": _ollama_messages(system, messages),
                  "stream": False, "options": _ollama_options(temperature, num_predict)},
            timeout=300,
        )
    except requests.RequestException as e:
        raise _ollama_unreachable(e) from e
    if r.status_code == 404:
        raise LLMError(f"Model '{use_model}' isn't installed. Run: ollama pull {use_model}")
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")


def _ollama_chat_model() -> str:
    """Prefer OLLAMA_CHAT_MODEL when set; fall back to OLLAMA_MODEL if same or unset."""
    chat = OLLAMA_CHAT_MODEL.strip()
    return chat if chat else OLLAMA_MODEL


def _ollama_stream(
    system: str,
    messages: list[dict],
    temperature: float,
    *,
    model: str | None = None,
    num_predict: int | None = None,
) -> Iterator[str]:
    import json
    primary = model or _ollama_chat_model()
    fallback = OLLAMA_MODEL if primary != OLLAMA_MODEL else None
    for use_model in filter(None, [primary, fallback]):
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": use_model, "messages": _ollama_messages(system, messages),
                      "stream": True, "options": _ollama_options(temperature, num_predict)},
                stream=True, timeout=300,
            )
        except requests.RequestException as e:
            raise _ollama_unreachable(e) from e
        if r.status_code == 404 and fallback and use_model == primary:
            r.close()
            continue
        with r:
            if r.status_code == 404:
                raise LLMError(f"Model '{use_model}' isn't installed. Run: ollama pull {use_model}")
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                obj = json.loads(line.decode("utf-8"))
                token = obj.get("message", {}).get("content", "")
                if token:
                    yield token
                if obj.get("done"):
                    return
        return


# --- public interface ------------------------------------------------------

class LLMError(RuntimeError):
    """Raised when no backend can fulfil a request (with a user-facing message)."""


def _backend_error_message(errors: list[tuple[str, Exception]]) -> str:
    if not errors:
        return "No LLM backend could answer."
    details = "; ".join(f"{backend}: {error}" for backend, error in errors)
    return f"No LLM backend could answer. Backend errors: {details}"


def _generate_one(backend: str, system: str, messages: list[dict],
                  max_tokens: int, temperature: float, *,
                  ollama_num_predict: int | None = None) -> str:
    if backend == "anthropic":
        return _anthropic_generate(system, messages, max_tokens)
    if backend == "gemini":
        return _gemini_generate(system, messages, max_tokens)
    return _ollama_generate(system, messages, temperature, num_predict=ollama_num_predict)


def _stream_one(backend: str, system: str, messages: list[dict],
                max_tokens: int, temperature: float) -> Iterator[str]:
    if backend == "anthropic":
        return _anthropic_stream(system, messages, max_tokens)
    if backend == "gemini":
        return _gemini_stream(system, messages, max_tokens)
    return _ollama_stream(system, messages, temperature)


def generate(system: str, messages: list[dict], *,
             max_tokens: int = 4096, temperature: float = 0.2,
             ollama_num_predict: int | None = None) -> str:
    """Return one complete answer, trying each usable backend in chain order.
    `temperature` only applies to Ollama (Opus 4.8 rejects the parameter)."""
    chain = [b for b in _backend_chain() if _usable(b)]
    errors: list[tuple[str, Exception]] = []
    for backend in chain:
        try:
            return _generate_one(
                backend, system, messages, max_tokens, temperature,
                ollama_num_predict=ollama_num_predict,
            )
        except Exception as e:  # noqa: BLE001 - try the next backend in the chain
            errors.append((backend, e))
            _log(f"{backend} generate failed ({e}); trying next backend.")
    raise LLMError(_backend_error_message(errors))


def stream(system: str, messages: list[dict], *,
           max_tokens: int = 4096, temperature: float = 0.2) -> Iterator[str]:
    """Yield answer tokens, trying each usable backend in chain order. Falls
    through to the next backend only if the current one fails before emitting."""
    chain = [b for b in _backend_chain() if _usable(b)]
    errors: list[tuple[str, Exception]] = []
    for backend in chain:
        emitted = False
        try:
            for text in _stream_one(backend, system, messages, max_tokens, temperature):
                emitted = True
                yield text
            if not emitted:
                raise LLMError(f"{backend} stream returned empty output")
            return
        except Exception as e:  # noqa: BLE001
            if emitted:
                # Already streamed partial output; don't re-run on another backend.
                raise LLMError(f"{backend} stream interrupted: {e}") from e
            errors.append((backend, e))
            _log(f"{backend} stream failed before output ({e}); trying next backend.")
    raise LLMError(_backend_error_message(errors))
