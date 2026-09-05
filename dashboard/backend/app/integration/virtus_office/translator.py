"""Text translation for Office Stage 3 — live LLM (chunked) for real documents.

offline_glossary remains only for short unit-test stubs. Long / commercial
documents refuse offline and require a live translator provider.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

import httpx

from app.integration.virtus_office.language_catalog import language_label_de

_ENTITY_RE = re.compile(
    r"("
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"  # email
    r"|\+?\d[\d\s\-/]{6,}\d"
    r"|\d{1,2}\.\d{1,2}\.\d{2,4}"
    r"|\d+[.,]\d{2}\s*€"
    r"|€\s*\d+[.,]\d{2}"
    r"|\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"  # IBAN-ish
    r"|\b\d{5,}\b"
    r")",
    re.I,
)

# Short stubs may use offline; Businessplan-scale text must use live LLM.
LIVE_REQUIRED_CHARS = 2_500
CHUNK_CHARS = 3_800
MAX_OUT_TOKENS = 3_500
CHUNK_PAUSE_SEC = float(os.getenv("OFFICE_TRANSLATE_CHUNK_PAUSE_SEC", "1.5"))
RATE_LIMIT_RETRIES = int(os.getenv("OFFICE_TRANSLATE_429_RETRIES", "6"))

# Small offline glossary DE → EN (tests only).
_DE_EN = {
    "arbeitsvertrag": "employment contract",
    "arbeitgeber": "employer",
    "arbeitnehmer": "employee",
    "probezeit": "probation period",
    "rechnung": "invoice",
    "gesamtbetrag": "total amount",
    "mwst": "VAT",
    "datum": "date",
    "vertrag": "contract",
    "betrag": "amount",
    "seite": "page",
    "lebenslauf": "curriculum vitae",
    "bewerbung": "application",
    "sehr geehrte": "dear",
    "mit freundlichen grüßen": "kind regards",
    "und": "and",
    "der": "the",
    "die": "the",
    "das": "the",
    "für": "for",
    "mit": "with",
    "nicht": "not",
}


def extract_entities(text: str) -> list[str]:
    return list(dict.fromkeys(m.group(0) for m in _ENTITY_RE.finditer(text or "")))


def llm_key_available() -> bool:
    return bool(
        os.getenv("GENESIS_GROQ_API_KEY", "").strip()
        or os.getenv("GENESIS_LLM_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("GROQ_API_KEY", "").strip()
    )


def translate_text(
    text: str,
    *,
    source_language: str,
    target_language: str,
    preserve_names: bool = True,
    preserve_numbers_dates: bool = True,
) -> dict[str, Any]:
    src = (source_language or "auto").lower().split("-")[0]
    tgt = (target_language or "en").lower().split("-")[0]
    entities = extract_entities(text)
    if not (text or "").strip():
        return {
            "ok": False,
            "provider": "none",
            "text": "",
            "entities": entities,
            "error": "empty_input",
        }

    needs_live = len(text) >= LIVE_REQUIRED_CHARS
    llm = _try_llm_translate(
        text,
        source=src,
        target=tgt,
        preserve_names=preserve_names,
        preserve_numbers_dates=preserve_numbers_dates,
    )
    if llm.get("ok"):
        out = str(llm["text"])
        missing = [e for e in entities if e and e not in out]
        if missing and preserve_numbers_dates:
            out = out.rstrip() + "\n\n[Preserved data]\n" + "\n".join(missing)
        return {
            "ok": True,
            "provider": llm.get("provider") or "llm",
            "text": out,
            "entities": entities,
            "error": None,
            "chunks": llm.get("chunks"),
            "chars_in": len(text),
            "chars_out": len(out),
        }

    # Commercial / soft-beta: never ship offline_glossary (???? / stub EN).
    # Unit tests may set OFFICE_ALLOW_OFFLINE_TRANSLATE=1 for short stubs only.
    if not _offline_translate_allowed():
        return {
            "ok": False,
            "provider": "none",
            "text": "",
            "entities": entities,
            "error": "translator_unavailable",
            "detail": (
                "Live translator required. offline_glossary is not a commercial translation. "
                f"{llm.get('error') or ''} {llm.get('detail') or ''}"
            ).strip(),
        }

    if needs_live:
        return {
            "ok": False,
            "provider": "none",
            "text": "",
            "entities": entities,
            "error": "translator_unavailable",
            "detail": (
                "Live translator required for this document. "
                "offline_glossary is not a commercial translation. "
                f"{llm.get('error') or ''} {llm.get('detail') or ''}"
            ).strip(),
        }

    offline = _offline_translate(text, source=src, target=tgt, entities=entities)
    return offline


def _offline_translate_allowed() -> bool:
    return os.getenv("OFFICE_ALLOW_OFFLINE_TRANSLATE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _chunk_paragraphs(text: str, *, max_chars: int = CHUNK_CHARS) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [text.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        candidate = f"{buf}\n\n{p}".strip() if buf else p
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(p) <= max_chars:
            buf = p
        else:
            # Hard-split oversized paragraph
            for i in range(0, len(p), max_chars):
                chunks.append(p[i : i + max_chars])
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks or [text]


def _provider_config() -> dict[str, str] | None:
    key = (
        os.getenv("GENESIS_GROQ_API_KEY", "").strip()
        or os.getenv("GENESIS_LLM_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("GROQ_API_KEY", "").strip()
    )
    if not key:
        return None
    if os.getenv("GENESIS_GROQ_API_KEY") or os.getenv("GROQ_API_KEY"):
        return {
            "key": key,
            "base": os.getenv("GENESIS_GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
            "model": os.getenv("GENESIS_GROQ_MODEL", "llama-3.3-70b-versatile"),
            "provider": "groq",
            "fallbacks": os.getenv(
                "GENESIS_GROQ_MODEL_FALLBACKS",
                "openai/gpt-oss-20b,llama-3.1-8b-instant,llama-3.3-70b-versatile",
            ),
        }
    return {
        "key": key,
        "base": os.getenv("GENESIS_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "model": os.getenv("GENESIS_LLM_MODEL", "gpt-4o-mini"),
        "provider": "openai",
        "fallbacks": os.getenv("GENESIS_LLM_MODEL", "gpt-4o-mini"),
    }


def _model_candidates(cfg: dict[str, str]) -> list[str]:
    primary = (cfg.get("model") or "").strip()
    raw = (cfg.get("fallbacks") or primary).split(",")
    out: list[str] = []
    for m in [primary, *[x.strip() for x in raw]]:
        if m and m not in out:
            out.append(m)
    return out or [primary]


def _try_llm_translate(
    text: str,
    *,
    source: str,
    target: str,
    preserve_names: bool,
    preserve_numbers_dates: bool,
) -> dict[str, Any]:
    cfg = _provider_config()
    if not cfg:
        return {"ok": False, "error": "no_api_key"}

    system = (
        "You are Virtus Office Document Translator for commercial document delivery. "
        "Translate the document text accurately into the target language. "
        "Preserve paragraph and section structure. "
        "Keep brand names, person names, company names exactly when asked. "
        "Keep numbers, currencies, dates, emails, IBANs and IDs exactly when asked. "
        "Do not summarize. Do not omit sections. Output only the translation."
    )
    rules = []
    if preserve_names:
        rules.append(
            "Preserve all person names, company names and brands exactly (e.g. Virtus Core, Vector)."
        )
    if preserve_numbers_dates:
        rules.append("Preserve all numbers, currencies, dates, emails and IDs exactly.")
    rule_block = "\n".join(f"- {r}" for r in rules) if rules else "- Translate fully."

    chunks = _chunk_paragraphs(text)
    timeout = float(os.getenv("GENESIS_LLM_TIMEOUT_SEC", "120"))
    models = _model_candidates(cfg)
    errors: list[str] = []

    for model in models:
        out_parts: list[str] = []
        try:
            with httpx.Client(timeout=timeout) as client:
                for idx, chunk in enumerate(chunks, start=1):
                    user = (
                        f"Source language: {source}\n"
                        f"Target language: {target}\n"
                        f"Chunk {idx}/{len(chunks)}\n"
                        f"Rules:\n{rule_block}\n\n"
                        f"---\n{chunk}"
                    )
                    # Rate-limit aware post
                    content = ""
                    for attempt in range(RATE_LIMIT_RETRIES):
                        res = client.post(
                            f"{cfg['base']}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {cfg['key']}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": system},
                                    {"role": "user", "content": user},
                                ],
                                "temperature": 0.15,
                                "max_tokens": MAX_OUT_TOKENS,
                            },
                        )
                        if res.status_code == 429:
                            wait = min(60.0, (2**attempt) * 1.5)
                            time.sleep(wait)
                            continue
                        if res.status_code == 404 and "model" in (res.text or "").lower():
                            errors.append(f"model_404:{model}")
                            raise RuntimeError("model_not_found")
                        if res.status_code >= 400:
                            errors.append(f"http_{res.status_code}:{model}")
                            raise RuntimeError("http_error")
                        data = res.json()
                        content = (data["choices"][0]["message"]["content"] or "").strip()
                        if not content:
                            time.sleep(min(20.0, (2**attempt) * 1.2))
                            continue
                        break
                    else:
                        errors.append(f"empty_or_rate:{model}:chunk_{idx}")
                        raise RuntimeError("empty_or_rate")
                    out_parts.append(content)
                    if idx < len(chunks) and CHUNK_PAUSE_SEC > 0:
                        time.sleep(CHUNK_PAUSE_SEC)
            return {
                "ok": True,
                "provider": cfg["provider"],
                "model": model,
                "text": "\n\n".join(out_parts),
                "chunks": len(chunks),
            }
        except RuntimeError:
            continue
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                return {
                    "ok": False,
                    "error": f"llm_http_{exc.response.status_code}",
                    "detail": (exc.response.text or "")[:240],
                }
            errors.append(f"http_{exc.response.status_code}:{model}")
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{type(exc).__name__}:{model}")
            continue

    return {
        "ok": False,
        "error": "llm_all_models_failed",
        "detail": "; ".join(errors[:8]) or "unknown",
    }



def _offline_translate(
    text: str,
    *,
    source: str,
    target: str,
    entities: list[str],
) -> dict[str, Any]:
    """Deterministic offline path for short tests / no-key stubs only."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    translated_paras: list[str] = []
    for para in paragraphs:
        protected = para
        holders: dict[str, str] = {}
        for i, ent in enumerate(extract_entities(para)):
            token = f"⟦E{i}⟧"
            holders[token] = ent
            protected = protected.replace(ent, token)
        out = protected
        for src_w, dst_w in sorted(_DE_EN.items(), key=lambda x: -len(x[0])):
            out = re.sub(rf"\b{re.escape(src_w)}\b", dst_w, out, flags=re.I)
        for token, ent in holders.items():
            out = out.replace(token, ent)
        if target in {"uk", "ru"} and not re.search(r"[\u0400-\u04FF]", out):
            label = "Українською" if target == "uk" else "На русском"
            out = f"{label}: {out}"
        elif target == "de" and source != "de":
            out = f"Deutsch: {out}"
        translated_paras.append(out)

    header = (
        f"Virtus Office Translation\n"
        f"Source: {language_label_de(source)} ({source})\n"
        f"Target: {language_label_de(target)} ({target})\n"
        f"Provider: offline_glossary"
    )
    body = "\n\n".join(translated_paras)
    missing = [e for e in entities if e and e not in body]
    if missing:
        body += "\n\n[Preserved data]\n" + "\n".join(missing)
    return {
        "ok": True,
        "provider": "offline_glossary",
        "text": f"{header}\n\n{body}",
        "entities": entities,
        "error": None,
    }
