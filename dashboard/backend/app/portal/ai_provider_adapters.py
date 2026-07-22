"""AI Platform AP1.2 — Provider Adapters (vendor SDKs isolated here).

```text
Provider Adapters isolate vendor SDKs.
Provider Adapters return unified AIResponse.
Provider Adapters never modify ConversationContext.
Provider Adapters never manage conversations.
```

Implements AIProviderProtocol without changing Protocol / Registry / Manager.
Secrets come from environment (never portal configuration).
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.portal.ai_provider import AIProvider, STUB_UNAVAILABLE_REPLY
from app.portal.ai_provider_protocol import (
    AIGenerationResult,
    AIProviderHealth,
    AIProviderInfo,
)
from app.portal.ai_response import (
    AuthenticationFailed,
    GenerationFailed,
    InvalidConfiguration,
    ProviderPlatformError,
    ProviderUnavailable,
    RateLimited,
    ai_response_from_error,
    new_ai_response,
)
from app.portal.conversation import ConversationContext
from app.portal.prompt_package import PromptPackage

ENGINE_ID = "ai_provider_adapters_v1"

_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _model_name(record: AIProvider, default: str, package: PromptPackage | None = None) -> str:
    if package is not None:
        override = str(
            package.generation_parameters.get("model_name") or ""
        ).strip()
        if override:
            return override
    return (record.configuration.get("model_name") or default).strip() or default


class _BaseProviderAdapter:
    provider_type: str = "custom"
    default_model: str = "stub"

    def __init__(self, record: AIProvider) -> None:
        self._record = record

    def provider_info(self) -> AIProviderInfo:
        return AIProviderInfo(
            provider_id=self._record.provider_id,
            provider_type=self._record.provider_type,
            display_name=self._record.display_name,
            status=self._record.status,
        )

    def health(self) -> AIProviderHealth:
        if self._record.status == "enabled":
            try:
                self._ensure_ready()
                return AIProviderHealth(
                    ok=True,
                    status="enabled",
                    detail=f"{self.provider_type} adapter ready.",
                )
            except ProviderPlatformError as exc:
                return AIProviderHealth(
                    ok=False,
                    status="enabled",
                    detail=f"{exc.code}: {exc.message}",
                )
        if self._record.status == "configured":
            return AIProviderHealth(
                ok=True,
                status="configured",
                detail=f"{self.provider_type} adapter configured but not enabled.",
            )
        return AIProviderHealth(
            ok=False,
            status=self._record.status,
            detail=STUB_UNAVAILABLE_REPLY,
        )

    def prepare(self, context: ConversationContext) -> dict[str, Any]:
        # Never mutate ConversationContext — only read.
        return {
            "provider_type": self._record.provider_type,
            "conversation_id": context.conversation_id,
            "profile_id": context.profile_id,
            "message_count": len(context.messages),
            "knowledge_count": len(context.knowledge),
            "selected_categories": list(context.selected_categories),
            "ready": True,
            "adapter": ENGINE_ID,
        }

    def generate(self, prompt: PromptPackage) -> AIGenerationResult:
        prepared = {
            "provider_type": self._record.provider_type,
            "conversation_id": prompt.conversation_id,
            "profile_id": prompt.profile_id,
            "prompt_package_id": prompt.package_id,
            "ready": True,
            "adapter": ENGINE_ID,
        }
        model = _model_name(self._record, self.default_model, prompt)
        if self._record.status != "enabled":
            response = new_ai_response(
                provider=self.provider_type,
                model=model,
                content=STUB_UNAVAILABLE_REPLY,
                finish_reason="error",
                metadata={"error_code": "provider_unavailable"},
            )
            return self._to_generation_result(response, prepared)

        try:
            response = self._generate_ai_response(prompt, model=model)
        except ProviderPlatformError as exc:
            response = ai_response_from_error(
                provider=self.provider_type, model=model, error=exc
            )
        except Exception as exc:  # noqa: BLE001 — map unknown vendor failures
            response = ai_response_from_error(
                provider=self.provider_type,
                model=model,
                error=GenerationFailed(str(exc) or "generation_failed"),
            )
        return self._to_generation_result(response, prepared)

    def _to_generation_result(
        self, response: Any, prepared: dict[str, Any]
    ) -> AIGenerationResult:
        prepared_out = dict(prepared)
        prepared_out["ai_response"] = response.as_dict()
        return AIGenerationResult(
            text=response.content,
            provider_type=self.provider_type,
            prepared=prepared_out,
        )

    def _ensure_ready(self) -> None:
        raise NotImplementedError

    def _generate_ai_response(self, prompt: PromptPackage, *, model: str) -> Any:
        raise NotImplementedError


class OpenAIProviderAdapter(_BaseProviderAdapter):
    """OpenAI SDK isolated inside this adapter only."""

    provider_type = "openai"
    default_model = "gpt-4o-mini"

    def _api_key(self) -> str:
        key = os.environ.get(_ENV_KEYS["openai"], "").strip()
        if not key:
            raise InvalidConfiguration("OPENAI_API_KEY is not set")
        return key

    def _ensure_ready(self) -> None:
        self._api_key()
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            raise ProviderUnavailable("openai SDK is not installed") from exc

    def _generate_ai_response(self, prompt: PromptPackage, *, model: str) -> Any:
        self._ensure_ready()
        messages = prompt.provider_messages()
        temperature = float(prompt.generation_parameters.get("temperature", 0.4))
        max_tokens = int(prompt.generation_parameters.get("max_tokens", 800))
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key())
            completion = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = completion.choices[0]
            content = (choice.message.content or "").strip()
            usage = {}
            if completion.usage is not None:
                usage = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens,
                }
            return new_ai_response(
                provider="openai",
                model=model,
                content=content,
                usage=usage,
                finish_reason=str(choice.finish_reason or "stop"),
                metadata={"sdk": "openai", "prompt_package_id": prompt.package_id},
            )
        except ProviderPlatformError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise _map_openai_error(exc) from exc


class AnthropicProviderAdapter(_BaseProviderAdapter):
    """Anthropic SDK isolated inside this adapter only."""

    provider_type = "anthropic"
    default_model = "claude-3-5-haiku-latest"

    def _api_key(self) -> str:
        key = os.environ.get(_ENV_KEYS["anthropic"], "").strip()
        if not key:
            raise InvalidConfiguration("ANTHROPIC_API_KEY is not set")
        return key

    def _ensure_ready(self) -> None:
        self._api_key()
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise ProviderUnavailable("anthropic SDK is not installed") from exc

    def _generate_ai_response(self, prompt: PromptPackage, *, model: str) -> Any:
        self._ensure_ready()
        messages = prompt.provider_messages()
        system = ""
        chat: list[dict[str, str]] = []
        for item in messages:
            if item["role"] == "system":
                system = (
                    f"{system}\n{item['content']}".strip()
                    if system
                    else item["content"]
                )
            else:
                chat.append(item)
        if not chat:
            chat = [{"role": "user", "content": prompt.user_message or "Hello"}]
        max_tokens = int(prompt.generation_parameters.get("max_tokens", 800))
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key())
            result = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system or "You are a helpful business assistant.",
                messages=chat,  # type: ignore[arg-type]
            )
            parts = []
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            usage = {
                "input_tokens": getattr(result.usage, "input_tokens", 0),
                "output_tokens": getattr(result.usage, "output_tokens", 0),
            }
            return new_ai_response(
                provider="anthropic",
                model=model,
                content="\n".join(parts).strip(),
                usage=usage,
                finish_reason=str(result.stop_reason or "stop"),
                metadata={"sdk": "anthropic", "prompt_package_id": prompt.package_id},
            )
        except ProviderPlatformError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise _map_anthropic_error(exc) from exc


class OllamaProviderAdapter(_BaseProviderAdapter):
    """Ollama local HTTP API — isolated inside this adapter (no portal HTTP)."""

    provider_type = "ollama"
    default_model = "llama3.2"

    def _base_url(self) -> str:
        configured = (
            self._record.configuration.get("base_url_placeholder") or ""
        ).strip()
        env = os.environ.get("OLLAMA_HOST", "").strip()
        return (env or configured or "http://127.0.0.1:11434").rstrip("/")

    def _ensure_ready(self) -> None:
        url = f"{self._base_url()}/api/tags"
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(url)
            if response.status_code >= 400:
                raise ProviderUnavailable(
                    f"ollama health failed: HTTP {response.status_code}"
                )
        except ProviderPlatformError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailable(f"ollama unreachable: {exc}") from exc

    def _generate_ai_response(self, prompt: PromptPackage, *, model: str) -> Any:
        messages = prompt.provider_messages()
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(
                    prompt.generation_parameters.get("temperature", 0.4)
                ),
                "num_predict": int(prompt.generation_parameters.get("max_tokens", 800)),
            },
        }
        url = f"{self._base_url()}/api/chat"
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload)
            if response.status_code == 401:
                raise AuthenticationFailed("ollama authentication failed")
            if response.status_code == 429:
                raise RateLimited("ollama rate limited")
            if response.status_code >= 400:
                raise GenerationFailed(
                    f"ollama HTTP {response.status_code}: {response.text[:200]}"
                )
            data = response.json()
            message = data.get("message") or {}
            content = str(message.get("content") or "").strip()
            return new_ai_response(
                provider="ollama",
                model=model,
                content=content,
                usage={
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                },
                finish_reason="stop" if data.get("done") else "unknown",
                metadata={
                    "sdk": "ollama_http",
                    "base_url": self._base_url(),
                    "prompt_package_id": prompt.package_id,
                },
            )
        except ProviderPlatformError:
            raise
        except json.JSONDecodeError as exc:
            raise GenerationFailed("ollama returned invalid JSON") from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailable(str(exc) or "ollama_unavailable") from exc


class CustomProviderAdapter(_BaseProviderAdapter):
    """Placeholder custom adapter — no vendor SDK."""

    provider_type = "custom"
    default_model = "custom"

    def _ensure_ready(self) -> None:
        raise InvalidConfiguration("custom adapter has no backend configured")

    def _generate_ai_response(self, prompt: PromptPackage, *, model: str) -> Any:
        raise InvalidConfiguration("custom adapter has no backend configured")


def _map_openai_error(exc: Exception) -> ProviderPlatformError:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "auth" in name or "auth" in text or "api key" in text:
        return AuthenticationFailed(str(exc))
    if "rate" in name or "rate" in text or "429" in text:
        return RateLimited(str(exc))
    if "connect" in text or "timeout" in text:
        return ProviderUnavailable(str(exc))
    return GenerationFailed(str(exc) or "openai_generation_failed")


def _map_anthropic_error(exc: Exception) -> ProviderPlatformError:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "auth" in name or "auth" in text or "api key" in text:
        return AuthenticationFailed(str(exc))
    if "rate" in name or "rate" in text or "429" in text:
        return RateLimited(str(exc))
    if "connect" in text or "timeout" in text:
        return ProviderUnavailable(str(exc))
    return GenerationFailed(str(exc) or "anthropic_generation_failed")


def build_adapter_runtime(record: AIProvider) -> _BaseProviderAdapter:
    mapping: dict[str, type[_BaseProviderAdapter]] = {
        "openai": OpenAIProviderAdapter,
        "anthropic": AnthropicProviderAdapter,
        "ollama": OllamaProviderAdapter,
        "custom": CustomProviderAdapter,
    }
    cls = mapping.get(record.provider_type, CustomProviderAdapter)
    return cls(record)
