"""OpenAI-compatible chat backends (OpenAI, DeepSeek, Ollama, etc.)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from typing import Any

import httpx

from app.integration.genesis_brain.types import ChatResult

_ACTION_RE = re.compile(r"\nGENESIS_ACTION:\s*(\{.*\})\s*$", re.DOTALL)


class OpenAICompatibleProvider:
    """Single OpenAI-compatible endpoint. API keys never logged."""

    def __init__(
        self,
        provider_id: str,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout: float = 45.0,
        require_key: bool = True,
    ) -> None:
        self.provider_id = provider_id
        self._api_key = (api_key or "").strip()
        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._timeout = timeout
        self._require_key = require_key

    @property
    def model_name(self) -> str:
        return self._model

    def available(self) -> bool:
        if self._require_key and not self._api_key:
            return False
        if self.provider_id == "ollama":
            return self._probe_ollama()
        return bool(self._base_url and self._model)

    def _probe_ollama(self) -> bool:
        try:
            root = self._base_url.replace("/v1", "")
            with httpx.Client(timeout=httpx.Timeout(3.0, connect=1.0)) as client:
                r = client.get(f"{root}/api/tags")
                return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    def chat(self, *, system: str, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        conv_cap = int(os.getenv("GENESIS_CONVERSATION_MAX_TOKENS", "320"))
        full_cap = int(os.getenv("GENESIS_MAX_TOKENS", "1200"))
        # Fast-lane prompts are compact; cap generation for snappier dialogue.
        max_tokens = conv_cap if len(system) < 10_000 else full_cap

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0.75,
            "max_tokens": max_tokens,
        }
        if self.provider_id == "ollama":
            payload["keep_alive"] = os.getenv("GENESIS_OLLAMA_KEEP_ALIVE", "10m")
        url = f"{self._base_url}/chat/completions"

        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        content = data["choices"][0]["message"]["content"].strip()
        parsed = self._parse_action(content)
        return ChatResult(
            answer=parsed["answer"],
            cta_href=parsed.get("cta_href"),
            cta_label=parsed.get("cta_label"),
            action=parsed.get("action"),
            provider_id=self.provider_id,
        )

    def chat_stream(
        self, *, system: str, messages: list[dict[str, str]], **kwargs: Any
    ) -> Iterator[str]:
        """Yield text deltas from a streaming chat/completions response (Ollama)."""
        if self.provider_id != "ollama":
            raise NotImplementedError(f"stream not supported for {self.provider_id}")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        conv_cap = int(os.getenv("GENESIS_CONVERSATION_MAX_TOKENS", "320"))
        full_cap = int(os.getenv("GENESIS_MAX_TOKENS", "1200"))
        max_tokens = conv_cap if len(system) < 10_000 else full_cap

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0.75,
            "max_tokens": max_tokens,
            "stream": True,
        }
        payload["keep_alive"] = os.getenv("GENESIS_OLLAMA_KEEP_ALIVE", "10m")
        url = f"{self._base_url}/chat/completions"

        with httpx.Client(timeout=self._timeout) as client:
            with client.stream("POST", url, headers=headers, json=payload) as res:
                res.raise_for_status()
                for raw in res.iter_lines():
                    if not raw:
                        continue
                    line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        yield content

    def _parse_action(self, content: str) -> dict[str, Any]:
        m = _ACTION_RE.search(content)
        if not m:
            return {"answer": content, "cta_href": None, "cta_label": None, "action": None}

        answer = content[: m.start()].rstrip()
        try:
            action = json.loads(m.group(1))
        except json.JSONDecodeError:
            return {"answer": content, "cta_href": None, "cta_label": None, "action": None}

        return {
            "answer": answer,
            "cta_href": action.get("cta_href"),
            "cta_label": action.get("cta_label"),
            "action": action,
        }


from app.integration.genesis_brain.local_mind import LocalMindProvider

Provider = OpenAICompatibleProvider | LocalMindProvider


def build_provider_chain(packages: list[dict[str, Any]] | None = None) -> list[Provider]:
    """
    All Genesis employees. Order is reshuffled per-turn by AI Workforce Manager.
    Free-first registry: Groq → Gemini → OpenRouter → Ollama → genesis-local.
    Premium (OpenAI/Claude) only when WorkforceManager allows complex tasks.
    """
    return list(build_provider_registry(packages).values())


def build_provider_registry(
    packages: list[dict[str, Any]] | None = None,
) -> dict[str, Provider]:
    if os.getenv("GENESIS_ACCEPTANCE_GATE") == "1":
        local = LocalMindProvider(packages=packages)
        return {local.provider_id: local}

    timeout = float(os.getenv("GENESIS_LLM_TIMEOUT_SEC", "45"))
    openrouter_key = os.getenv("GENESIS_OPENROUTER_API_KEY")
    gemini_key = os.getenv("GENESIS_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    defs: list[dict[str, Any]] = [
        {
            "id": "groq",
            "key": os.getenv("GENESIS_GROQ_API_KEY") or os.getenv("GENESIS_LLM_API_KEY"),
            "base": os.getenv("GENESIS_GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            "model": os.getenv("GENESIS_GROQ_MODEL", "llama-3.3-70b-versatile"),
        },
        {
            "id": "gemini",
            "key": gemini_key or openrouter_key,
            "base": (
                os.getenv("GENESIS_GEMINI_BASE_URL")
                or (
                    "https://generativelanguage.googleapis.com/v1beta/openai"
                    if gemini_key
                    else "https://openrouter.ai/api/v1"
                )
            ),
            "model": (
                os.getenv("GENESIS_GEMINI_MODEL")
                or ("gemini-2.0-flash" if gemini_key else "google/gemini-2.0-flash-001")
            ),
        },
        {
            "id": "openrouter",
            "key": openrouter_key,
            "base": os.getenv("GENESIS_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            "model": os.getenv("GENESIS_OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
        },
        {
            "id": "ollama",
            "key": os.getenv("GENESIS_OLLAMA_API_KEY", "ollama"),
            "base": os.getenv("GENESIS_OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
            "model": os.getenv("GENESIS_OLLAMA_MODEL", "llama3.2"),
            "require_key": False,
        },
        {
            "id": "openai",
            "key": os.getenv("GENESIS_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            "base": os.getenv("GENESIS_LLM_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("GENESIS_LLM_MODEL", "gpt-4o-mini"),
        },
        {
            "id": "anthropic",
            "key": os.getenv("GENESIS_ANTHROPIC_API_KEY") or openrouter_key,
            "base": os.getenv("GENESIS_ANTHROPIC_BASE_URL", "https://openrouter.ai/api/v1"),
            "model": os.getenv("GENESIS_ANTHROPIC_MODEL", "anthropic/claude-3.5-haiku"),
        },
        {
            "id": "deepseek",
            "key": os.getenv("GENESIS_DEEPSEEK_API_KEY"),
            "base": os.getenv("GENESIS_DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "model": os.getenv("GENESIS_DEEPSEEK_MODEL", "deepseek-chat"),
        },
    ]

    registry: dict[str, Provider] = {}
    ollama_timeout = float(os.getenv("GENESIS_OLLAMA_TIMEOUT_SEC", str(timeout)))
    for d in defs:
        provider_timeout = ollama_timeout if d["id"] == "ollama" else timeout
        registry[d["id"]] = OpenAICompatibleProvider(
            d["id"],
            api_key=d.get("key"),
            base_url=d["base"],
            model=d["model"],
            timeout=provider_timeout,
            require_key=d.get("require_key", True),
        )

    local = LocalMindProvider(packages=packages)
    registry[local.provider_id] = local
    return registry
