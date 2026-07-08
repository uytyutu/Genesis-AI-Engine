"""OpenAI-compatible chat provider for Genesis AI."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

_ACTION_RE = re.compile(r"\nGENESIS_ACTION:\s*(\{.*\})\s*$", re.DOTALL)


class LlmChatProvider:
    """Swappable LLM backend — OpenAI API or compatible (Ollama, Azure, etc.)."""

    def __init__(self) -> None:
        self._api_key = (
            os.getenv("GENESIS_LLM_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )
        self._base_url = os.getenv(
            "GENESIS_LLM_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self._model = os.getenv("GENESIS_LLM_MODEL", "gpt-4o-mini").strip()
        self._timeout = float(os.getenv("GENESIS_LLM_TIMEOUT_SEC", "45"))

    def available(self) -> bool:
        return bool(self._api_key)

    def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        if not self._api_key:
            raise RuntimeError("LLM API key not configured")

        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0.75,
            "max_tokens": 1800,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"

        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        content = data["choices"][0]["message"]["content"].strip()
        return self._parse_action(content)

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
