"""Website Analysis v1 — public owner report (Solve Digital Problems).

Uses real read-only fetch + heuristics. Never invents pass/fail for
checks that were not run.

Commercial MVP funnel (not two equal storefront cards):
  free Analysis → recommend Repair *or* New Website → orderable CTAs.
Repair delivery = operator-led after payment (no auto CMS surgery in MVP).
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from app.integration.site_analysis_service import SiteAnalysisService

ENGINE_ID = "website_analysis_v1"

# Locked Path A website prices
PRICE_BASIC = 350
PRICE_BUSINESS = 650
PRICE_PREMIUM = 1200
# Repair MVP packages (operator delivery after Stripe)
PRICE_REPAIR_LITE = 199
PRICE_REPAIR_STANDARD = 349
PRICE_REPAIR_COMPLETE = 499
PRICE_REPAIR_FROM = PRICE_REPAIR_LITE
PRICE_SEO = 249
PRICE_SPEED = 199

CheckStatus = Literal["pass", "fail", "unavailable"]
_REPAIR_VS_NEW_RATIO = 0.8  # if repair quote ≥ 80% of Business → prefer New


def compute_repair_quote(
    *, health_score: int, fail_n: int, fetch_ok: bool
) -> dict[str, Any]:
    """Estimate repair package from failed checks — honest, not a fake Lighthouse bill."""
    if not fetch_ok:
        return {
            "package_id": None,
            "price_eur": None,
            "label": None,
            "prefer_new": True,
            "reason": "site_unreachable",
        }
    if fail_n <= 0:
        return {
            "package_id": "repair_lite",
            "price_eur": PRICE_REPAIR_LITE,
            "label": f"{PRICE_REPAIR_LITE} €",
            "prefer_new": False,
            "reason": "tune_up",
        }
    if health_score >= 70 and fail_n <= 2:
        pkg, price = "repair_lite", PRICE_REPAIR_LITE
    elif health_score >= 50 and fail_n <= 4:
        pkg, price = "repair_standard", PRICE_REPAIR_STANDARD
    else:
        pkg, price = "repair_complete", PRICE_REPAIR_COMPLETE
    prefer_new = price >= int(PRICE_BUSINESS * _REPAIR_VS_NEW_RATIO) or health_score < 45 or fail_n >= 5
    return {
        "package_id": pkg,
        "price_eur": price,
        "label": f"{price} €",
        "prefer_new": prefer_new,
        "reason": "new_cheaper" if prefer_new else "repair_viable",
    }


def _normalize_email(raw: str) -> str:
    return str(raw or "").strip().lower()[:200]


def _domain_key(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        return host
    except Exception:
        return ""


def _check(
    id_: str,
    label: str,
    status: CheckStatus,
    detail: str,
) -> dict[str, Any]:
    return {"id": id_, "label": label, "status": status, "detail": detail}


def build_owner_report(
    raw: dict[str, Any],
    *,
    locale: str = "ru",
) -> dict[str, Any]:
    """Map stealth/heuristic analysis → owner-facing report."""
    error = raw.get("error")
    checks: list[dict[str, Any]] = []

    if error and error not in (None, ""):
        checks.append(
            _check(
                "reachability",
                "Доступность сайта",
                "fail",
                "Сайт недоступен или URL некорректен. Анализ страницы не выполнен.",
            )
        )
        for cid, label in (
            ("https", "HTTPS"),
            ("mobile", "Mobile Friendly"),
            ("speed", "Скорость ответа"),
            ("contacts", "Контакты"),
            ("cta", "Призыв к действию (CTA)"),
            ("forms", "Форма обратной связи"),
            ("seo_title", "SEO Title"),
            ("maps", "Google Maps"),
            ("structure", "Объём и структура контента"),
        ):
            checks.append(
                _check(
                    cid,
                    label,
                    "unavailable",
                    "Эта проверка пока недоступна — страница не была загружена.",
                )
            )
        return _finalize(
            raw,
            checks=checks,
            health_score=0,
            strengths=[],
            problems=["Сайт не удалось проверить"],
            locale=locale,
            fetch_ok=False,
        )

    # --- Real checks from fetch ---
    has_https = bool(raw.get("has_https"))
    checks.append(
        _check(
            "https",
            "HTTPS",
            "pass" if has_https else "fail",
            "Соединение защищено." if has_https else "Нет HTTPS — риск для посетителей и доверия.",
        )
    )

    has_viewport = bool(raw.get("has_viewport"))
    checks.append(
        _check(
            "mobile",
            "Mobile Friendly",
            "pass" if has_viewport else "fail",
            "Есть viewport для телефонов."
            if has_viewport
            else "Нет viewport — сайт часто плохо выглядит на телефоне.",
        )
    )

    load_ms = int(raw.get("load_ms") or 0)
    if load_ms <= 0:
        checks.append(
            _check(
                "speed",
                "Скорость ответа",
                "unavailable",
                "Время ответа не измерено в этом прогоне.",
            )
        )
    elif load_ms > 3000:
        checks.append(
            _check(
                "speed",
                "Скорость ответа",
                "fail",
                f"Медленный ответ сервера (~{load_ms} мс).",
            )
        )
    else:
        checks.append(
            _check(
                "speed",
                "Скорость ответа",
                "pass",
                f"Ответ за ~{load_ms} мс (простая проверка, не полный Lighthouse).",
            )
        )

    flags = raw.get("flags") if isinstance(raw.get("flags"), dict) else {}
    has_flags = bool(flags)

    if has_flags:
        has_contact = bool(flags.get("has_contact"))
        has_cta = bool(flags.get("has_cta"))
        has_form = bool(flags.get("has_form"))
        has_maps = bool(flags.get("has_maps"))
        content_thin = bool(flags.get("content_thin"))
        title_ok = bool((raw.get("title") or "").strip())
        checks.append(
            _check(
                "contacts",
                "Контакты",
                "pass" if has_contact else "fail",
                "Есть телефон, WhatsApp или e-mail."
                if has_contact
                else "Не видно прямого телефона / WhatsApp / e-mail.",
            )
        )
        checks.append(
            _check(
                "forms",
                "Форма обратной связи",
                "pass" if has_form else "fail",
                "Найдена форма или поле e-mail."
                if has_form
                else "Форма заявки / поле e-mail не обнаружены.",
            )
        )
        checks.append(
            _check(
                "cta",
                "Призыв к действию (CTA)",
                "pass" if has_cta else "fail",
                "Есть заметный призыв (заказ, звонок, запись)."
                if has_cta
                else "Явный CTA на главной не найден.",
            )
        )
        checks.append(
            _check(
                "maps",
                "Google Maps",
                "pass" if has_maps else "fail",
                "Карта или ссылка на Maps найдена."
                if has_maps
                else "Google Maps на странице не обнаружен.",
            )
        )
    else:
        content_thin = False
        title_ok = bool((raw.get("title") or "").strip())
        for cid, label in (
            ("contacts", "Контакты"),
            ("forms", "Форма обратной связи"),
            ("cta", "Призыв к действию (CTA)"),
            ("maps", "Google Maps"),
        ):
            checks.append(
                _check(
                    cid,
                    label,
                    "unavailable",
                    "Эта проверка пока недоступна в кэше — нажмите анализ ещё раз.",
                )
            )

    checks.append(
        _check(
            "seo_title",
            "SEO Title",
            "pass" if title_ok else "fail",
            f"Title: «{(raw.get('title') or '')[:80]}»"
            if title_ok
            else "Нет или пустой <title> — слабо для поиска.",
        )
    )

    checks.append(
        _check(
            "structure",
            "Объём и структура контента",
            "fail" if content_thin else "pass",
            "Очень мало контента — возможна заглушка."
            if content_thin
            else "Базовый объём HTML достаточен для лендинга (эвристика).",
        )
    )

    # Health score: only from pass/fail (unavailable excluded)
    scored = [c for c in checks if c["status"] in ("pass", "fail")]
    if not scored:
        health = 0
    else:
        health = int(round(100 * sum(1 for c in scored if c["status"] == "pass") / len(scored)))

    strengths = [c["label"] for c in checks if c["status"] == "pass"]
    problems = [
        f"{c['label']}: {c['detail']}" for c in checks if c["status"] == "fail"
    ]

    return _finalize(
        raw,
        checks=checks,
        health_score=health,
        strengths=strengths,
        problems=problems,
        locale=locale,
        fetch_ok=True,
    )


def _finalize(
    raw: dict[str, Any],
    *,
    checks: list[dict[str, Any]],
    health_score: int,
    strengths: list[str],
    problems: list[str],
    locale: str,
    fetch_ok: bool,
) -> dict[str, Any]:
    fail_n = sum(1 for c in checks if c["status"] == "fail")
    quote = compute_repair_quote(
        health_score=health_score, fail_n=fail_n, fetch_ok=fetch_ok
    )
    recommendations = _recommendations(
        health_score=health_score, fail_n=fail_n, fetch_ok=fetch_ok, quote=quote
    )
    justification = _justification(
        health_score=health_score,
        fail_n=fail_n,
        recommendations=recommendations,
        fetch_ok=fetch_ok,
        quote=quote,
    )
    vector_plain = _vector_plain(
        health_score=health_score,
        fail_n=fail_n,
        problems=problems,
        recommendations=recommendations,
        fetch_ok=fetch_ok,
        quote=quote,
        locale=locale,
    )
    return {
        "engine": ENGINE_ID,
        "principle": "Solve Digital Problems",
        "url": raw.get("url") or "",
        "final_url": raw.get("final_url") or raw.get("url") or "",
        "title": raw.get("title") or "",
        "health_score": health_score,
        "checks": checks,
        "strengths": strengths,
        "problems": problems,
        "repair_quote": quote,
        "recommendations": recommendations,
        "justification": justification,
        "vector_plain": vector_plain,
        "analyzed_at": raw.get("analyzed_at"),
        "from_cache": bool(raw.get("from_cache")),
        "error": raw.get("error"),
        "stealth": raw.get("stealth"),
        "locale": locale,
    }


def _recommendations(
    *,
    health_score: int,
    fail_n: int,
    fetch_ok: bool,
    quote: dict[str, Any],
) -> list[dict[str, Any]]:
    """Funnel CTAs: Repair (priced) + New Website packages. No separate Repair hero."""
    repair_pkg = quote.get("package_id") or "repair_standard"
    repair_label = quote.get("label") or f"от {PRICE_REPAIR_FROM} €"
    repair_available = bool(quote.get("package_id")) and fetch_ok
    rows: list[dict[str, Any]] = [
        {
            "id": "repair",
            "title": "Website Repair",
            "price_label": repair_label if repair_available else f"от {PRICE_REPAIR_FROM} €",
            "summary": (
                "Точечный ремонт текущего сайта. После оплаты работу ведёт оператор "
                "Virtus Core по вашему отчёту — без обещания «AI сам починит любой CMS»."
            ),
            "availability": "available" if repair_available else "unavailable",
            "cta": "order_now" if repair_available else "coming_soon",
            "cta_href": f"/order?package={repair_pkg}" if repair_available else None,
            "cta_label": "Заказать ремонт" if repair_available else "Сначала нужен доступный сайт",
            "package_id": repair_pkg if repair_available else None,
            "price_eur": quote.get("price_eur"),
        },
        {
            "id": "new_business",
            "title": "New Website",
            "price_label": f"{PRICE_BASIC}–{PRICE_PREMIUM} €",
            "summary": (
                f"Новый сайт: Basic {PRICE_BASIC} € · Business {PRICE_BUSINESS} € · "
                f"Premium {PRICE_PREMIUM} €."
            ),
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order?package=business",
            "cta_label": f"Заказать Business (€{PRICE_BUSINESS})",
            "alt_ctas": [
                {"href": "/order?package=basic", "label": f"Basic (€{PRICE_BASIC})"},
                {"href": "/order?package=premium", "label": f"Premium (€{PRICE_PREMIUM})"},
            ],
        },
    ]
    prefer_new = bool(quote.get("prefer_new")) or not fetch_ok
    if prefer_new:
        rows[1]["recommended"] = True
        rows[1]["why"] = (
            "По объёму проблем или цене ремонта выгоднее новый сайт "
            f"(Business €{PRICE_BUSINESS}), чем долгий ремонт."
        )
        if repair_available:
            rows[0]["why"] = (
                f"Ремонт ≈ {repair_label} возможен, но новый сайт обычно надёжнее "
                "при таком состоянии."
            )
    else:
        rows[0]["recommended"] = True
        rows[0]["why"] = (
            f"Сайт в целом живой (оценка {health_score}/100, проблем: {fail_n}). "
            f"Точечный ремонт ≈ {repair_label} обычно выгоднее полной замены."
        )
    return rows


def _justification(
    *,
    health_score: int,
    fail_n: int,
    recommendations: list[dict[str, Any]],
    fetch_ok: bool,
    quote: dict[str, Any],
) -> str:
    rec = next((r for r in recommendations if r.get("recommended")), recommendations[-1])
    if not fetch_ok:
        return (
            "Сначала нужно восстановить доступность сайта. "
            "Пока страница не открывается, ремонт «вслепую» ненадёжен — "
            f"разумный следующий шаг: {rec['title']} ({rec['price_label']})."
        )
    if rec["id"] == "new_business":
        return (
            f"Оценка ≈ {health_score}/100, заметных проблем: {fail_n}. "
            f"Смета ремонта ≈ {quote.get('label') or '—'}. "
            f"Я рекомендую новый сайт Business (€{PRICE_BUSINESS}) — "
            "современная база и понятный путь заявок."
        )
    return (
        f"Оценка ≈ {health_score}/100, проблем: {fail_n}. "
        f"Рекомендую ремонт (~{quote.get('label')}) на текущем сайте. "
        "После оплаты оператор Virtus Core выполнит работы по отчёту; "
        "автоматический «ремонт любого WordPress/Wix» мы не обещаем."
    )


def _vector_plain(
    *,
    health_score: int,
    fail_n: int,
    problems: list[str],
    recommendations: list[dict[str, Any]],
    fetch_ok: bool,
    quote: dict[str, Any],
    locale: str,
) -> str:
    """Short client-facing explanation for Vector / cabinet (plain language)."""
    rec = next((r for r in recommendations if r.get("recommended")), recommendations[-1])
    top = problems[:3]
    probs = "; ".join(top) if top else ("сайт недоступен" if not fetch_ok else "критичных дыр мало")
    if (locale or "").startswith("de"):
        return (
            f"Kurz: Gesundheit {health_score}/100, {fail_n} Probleme. "
            f"Wichtig: {probs}. Empfehlung: {rec['title']} ({rec['price_label']}). "
            "Kein Versprechen, dass KI jedes CMS automatisch repariert."
        )
    return (
        f"Коротко: оценка {health_score}/100, проблем: {fail_n}. "
        f"Главное: {probs}. Рекомендация: {rec['title']} ({rec['price_label']}). "
        "Мы не обещаем, что ИИ сам починит любой CMS — после оплаты работу ведёт команда."
    )


class AnalysisCaseStore:
    """Persist analysis reports for client cabinet (by email + case id)."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "analysis_cases"
        self._root.mkdir(parents=True, exist_ok=True)
        self._index = self._root / "index.jsonl"

    def save(
        self,
        report: dict[str, Any],
        *,
        email: str = "",
        problem_note: str = "",
    ) -> dict[str, Any]:
        case_id = f"an-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        email_n = _normalize_email(email)
        row = {
            "case_id": case_id,
            "created_at": now,
            "email": email_n,
            "domain": _domain_key(str(report.get("final_url") or report.get("url") or "")),
            "url": report.get("url"),
            "final_url": report.get("final_url"),
            "health_score": report.get("health_score"),
            "repair_quote": report.get("repair_quote"),
            "recommended_id": next(
                (r["id"] for r in (report.get("recommendations") or []) if r.get("recommended")),
                None,
            ),
            "problem_note": str(problem_note or "").strip()[:2000],
            "vector_plain": report.get("vector_plain"),
            "justification": report.get("justification"),
            "report": report,
        }
        path = self._root / f"{case_id}.json"
        path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        with self._index.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "case_id": case_id,
                        "created_at": now,
                        "email": email_n,
                        "domain": row["domain"],
                        "health_score": row["health_score"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        return {"case_id": case_id, "email": email_n, "created_at": now}

    def get(self, case_id: str) -> dict[str, Any] | None:
        cid = re.sub(r"[^a-zA-Z0-9_-]", "", str(case_id or ""))[:40]
        path = self._root / f"{cid}.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def list_for_email(self, email: str, *, limit: int = 40) -> list[dict[str, Any]]:
        want = _normalize_email(email)
        if not want or not self._index.is_file():
            return []
        rows: list[dict[str, Any]] = []
        try:
            lines = self._index.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                meta = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(meta.get("email") or "") != want:
                continue
            full = self.get(str(meta.get("case_id") or ""))
            if full:
                rows.append(
                    {
                        "case_id": full["case_id"],
                        "created_at": full.get("created_at"),
                        "url": full.get("final_url") or full.get("url"),
                        "health_score": full.get("health_score"),
                        "repair_quote": full.get("repair_quote"),
                        "recommended_id": full.get("recommended_id"),
                        "vector_plain": full.get("vector_plain"),
                    }
                )
            if len(rows) >= limit:
                break
        return rows


class WebsiteAnalysisV1:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._site = SiteAnalysisService(memory_dir)
        self._cases = AnalysisCaseStore(memory_dir)

    def analyze(
        self,
        url: str,
        *,
        locale: str = "ru",
        use_cache: bool = True,
        email: str = "",
        problem_note: str = "",
        save_case: bool = True,
    ) -> dict[str, Any]:
        raw = self._site.analyze(url, use_cache=use_cache)
        report = build_owner_report(raw, locale=locale)
        if save_case:
            meta = self._cases.save(report, email=email, problem_note=problem_note)
            report = {**report, **meta}
        return report

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        return self._cases.get(case_id)

    def list_cases_for_email(self, email: str) -> list[dict[str, Any]]:
        return self._cases.list_for_email(email)


# --- Commercial MVP Vector speech (narrow gate fix — no architecture) ---

_REPAIR_SPEECH = re.compile(
    r"(?:"
    r"repair\s*(?:lite|standard|complete)|"
    r"website\s*repair|"
    r"смета\s+ремонт|"
    r"ремонт(?:а|у)?\s+(?:сайт|wordpress|wix|shopify)|"
    r"почините?\s+ли\s+вы|"
    r"автоматически\s+(?:любой\s+)?(?:wordpress|wix|shopify)|"
    r"(?:199|349|499)\s*€?\s*.{0,30}repair|"
    r"repair.{0,40}(?:199|349|499)"
    r")",
    re.I,
)

_WEBSITE_PACKAGES_SPEECH = re.compile(
    r"(?:"
    r"(?:basic|business|premium).{0,60}(?:пакет|package|выбрать)|"
    r"пакет(?:ы|ах)?.{0,60}(?:basic|business|premium)|"
    r"объясни\s+пакет|"
    r"350\s*/\s*650\s*/\s*1200|"
    r"(?:basic|business|premium).{0,40}(?:350|650|1200)"
    r")",
    re.I,
)


def is_commercial_website_repair_query(text: str) -> bool:
    """True when the user asks about Virtus Core Website Repair — not Bau/Handwerk."""
    return bool(_REPAIR_SPEECH.search(text or ""))


def try_commercial_mvp_speech(question: str) -> dict[str, Any] | None:
    """Honest commercial answers for Repair / Path A packages. Early route only."""
    q = (question or "").strip()
    if len(q) < 12:
        return None

    if is_commercial_website_repair_query(q):
        answer = (
            "Понял — речь про **Website Repair** по отчёту анализа, не про стройку.\n\n"
            "После анализа мы показываем найденные проблемы (HTTPS, скорость, мобильная "
            "версия, CTA, title/SEO, контакты, формы, карта и т.п.) и честную смету:\n\n"
            f"• **Repair Lite — {PRICE_REPAIR_LITE} €** — точечные правки по отчёту "
            "(тексты, CTA, контакты, простые SEO-правки).\n"
            f"• **Repair Standard — {PRICE_REPAIR_STANDARD} €** — расширенный объём по "
            "отчёту + краткий before/after.\n"
            f"• **Repair Complete — {PRICE_REPAIR_COMPLETE} €** — максимальный согласованный "
            "объём; если выгоднее — честно рекомендуем **новый сайт** "
            f"({PRICE_BASIC} / {PRICE_BUSINESS} / {PRICE_PREMIUM} €).\n\n"
            "**Важно (MVP):** ремонт выполняет **оператор** Virtus Core по вашему отчёту "
            "после оплаты и доступа. Мы **не** обещаем автоматический ремонт WordPress, "
            "Wix, Shopify или любого CMS без участия человека.\n\n"
            "Старт: бесплатный анализ на `/site#analysis` → смета → оплата → кабинет."
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "commercial_mvp_speech",
            "cta_href": "/site#analysis",
            "cta_label": "Сначала анализ",
            "cta_actions": [
                {"href": "/site#analysis", "label": "Website Analysis"},
                {
                    "href": f"/order?package=repair_standard",
                    "label": f"Repair Standard {PRICE_REPAIR_STANDARD} €",
                },
                {"href": "/order?package=business", "label": f"New Website {PRICE_BUSINESS} €"},
            ],
        }

    if _WEBSITE_PACKAGES_SPEECH.search(q) and re.search(
        r"сайт|лендинг|website|webseite|клининг|cleaning|компани", q, re.I
    ):
        answer = (
            "Понял — нужен **новый сайт** (Path A). Пакеты онлайн:\n\n"
            f"• **Basic — {PRICE_BASIC} €** — готовый лендинг под нишу, контакты, форма, "
            "базовая мобильная версия.\n"
            f"• **Business — {PRICE_BUSINESS} €** — рекомендую большинству: сильнее дизайн, "
            "галерея/доверие, карта, больше секций под заявки.\n"
            f"• **Premium — {PRICE_PREMIUM} €** — максимум визуала и сопровождения "
            "(калькулятор/showcase, приоритетная поддержка).\n\n"
            "Оформление: `/order` → оплата → Factory → ZIP в кабинете "
            "(`/client/downloads`). Срок обычно около 15 минут после оплаты.\n\n"
            "CTA на готовом сайте зависят от ниши (не «запись ко всем подряд»)."
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "commercial_mvp_speech",
            "cta_href": "/order?package=business",
            "cta_label": f"Business {PRICE_BUSINESS} €",
            "cta_actions": [
                {"href": "/order?package=basic", "label": f"Basic {PRICE_BASIC} €"},
                {"href": "/order?package=business", "label": f"Business {PRICE_BUSINESS} €"},
                {"href": "/order?package=premium", "label": f"Premium {PRICE_PREMIUM} €"},
            ],
        }

    return None
