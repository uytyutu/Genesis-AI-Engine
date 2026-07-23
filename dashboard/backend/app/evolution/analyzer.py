"""G3.1 analyzer — recommend only (never apply)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from app.evolution.models import KnowledgeLedgerEntry


@dataclass(frozen=True)
class AnalysisResult:
    category: str
    fingerprint: str
    problem: str
    analysis: str
    suggested_fix: str
    diff_preview: str
    diff_summary: str
    risk: Literal["low", "medium", "high"]
    confidence_percent: int
    confidence_basis: list[str]
    business_impact: dict[str, Any]
    rollback_available: bool
    tests_planned: list[str]
    similar_case_ids: list[str]


# pattern, category, analysis, suggested, diff, diff_summary, risk, impact, tests
_RULES: tuple[
    tuple[
        re.Pattern[str],
        str,
        str,
        str,
        str,
        str,
        Literal["low", "medium", "high"],
        dict[str, Any],
        tuple[str, ...],
    ],
    ...,
] = (
    (
        re.compile(r"форм|form|submit|отправ", re.I),
        "form",
        "Contact/order form may fail validation or miss endpoint wiring.",
        "Check form action URL, required fields, CSRF/SameSite cookie, and API 4xx responses.",
        "--- a/form\n+++ b/form\n@@\n- action missing / wrong endpoint\n+ wire to existing /api or /order path\n+ preserve validation errors for the user",
        "Исправляется обработчик формы обратной связи / заказа. Изменения касаются только пути формы. Остальные страницы не затрагиваются.",
        "medium",
        {
            "clients_affected_estimate": 34,
            "error_reduction_percent_estimate": 82,
            "risk": "low",
            "sales_impact": "none",
            "sales_impact_label": "Нет",
        },
        ("tests/test_portal_security_s1_3_negative.py", "scripts/s1_security_regression_suite.py"),
    ),
    (
        re.compile(r"оплат|payment|stripe|checkout|pay", re.I),
        "payments",
        "Payment or checkout confirmation may not complete or not show in client cabinet.",
        "Verify Landing Path A: create order → checkout/webhook/sandbox → public status paid → client orders view.",
        "--- a/payments\n+++ b/payments\n@@\n- status stuck awaiting_payment\n+ confirm webhook/sandbox applied\n+ surface order in /client/orders",
        "Исправляется подтверждение оплаты Landing Path A. Затрагивается только цикл заказа → оплата → кабинет. Цены и каталог не меняются.",
        "high",
        {
            "clients_affected_estimate": 12,
            "error_reduction_percent_estimate": 70,
            "risk": "medium",
            "sales_impact": "positive_if_fixed",
            "sales_impact_label": "Восстановление checkout",
        },
        ("tests/test_commercial_g23.py", "scripts/s1_security_regression_suite.py"),
    ),
    (
        re.compile(r"вход|login|session|cookie|авториз", re.I),
        "auth",
        "Login/session may expire or cookie not HttpOnly/Secure as expected.",
        "Check virtus_session cookie, SameSite=Lax, expired session handling, portal 401 on protected routes.",
        "--- a/session\n+++ b/session\n@@\n- anonymous principal on valid cookie\n+ validate active session + account lookup",
        "Исправляется проверка сессии входа. Изменения только в session/cookie path. Коммерческий каталог не затрагивается.",
        "high",
        {
            "clients_affected_estimate": 20,
            "error_reduction_percent_estimate": 75,
            "risk": "medium",
            "sales_impact": "none",
            "sales_impact_label": "Нет",
        },
        ("tests/test_portal_security_s1_2_infra.py", "tests/test_session_r42.py"),
    ),
    (
        re.compile(r"медлен|slow|timeout|зависа", re.I),
        "performance",
        "Page or API feels slow / times out.",
        "Measure endpoint latency; check rate limits and heavy middleware; avoid expanding scope into redesign.",
        "--- a/perf\n+++ b/perf\n@@\n- unbounded work on request path\n+ cache or defer non-critical work",
        "Предлагается сузить тяжёлую работу на горячем пути запроса. UI-редизайн не входит в предложение.",
        "medium",
        {
            "clients_affected_estimate": 40,
            "error_reduction_percent_estimate": 50,
            "risk": "low",
            "sales_impact": "indirect",
            "sales_impact_label": "Косвенно (UX)",
        },
        ("scripts/s1_security_regression_suite.py",),
    ),
    (
        re.compile(r"безопас|security|xss|csrf|hack|уязв", re.I),
        "security",
        "Security concern reported by client or operator.",
        "Reproduce with Security Regression Suite; never weaken headers/auth to 'fix' UX.",
        "--- a/security\n+++ b/security\n@@\n- missing regression for reported vector\n+ add permanent automated test",
        "Добавляется постоянный security-регрессионный тест по заявленному вектору. Поведение продукта для честных пользователей не расширяется.",
        "high",
        {
            "clients_affected_estimate": 100,
            "error_reduction_percent_estimate": 90,
            "risk": "low",
            "sales_impact": "none",
            "sales_impact_label": "Нет",
        },
        ("scripts/s1_security_regression_suite.py", "tests/test_portal_security_s1_4_ai.py"),
    ),
)


def _confidence(
    *,
    category: str,
    similar_count: int,
    successful_fixes: int,
) -> tuple[int, list[str]]:
    base = 42 if category == "general" else 68
    bump = min(25, similar_count * 4) + min(20, successful_fixes * 5)
    # Matched category + suite planned implies higher floor
    if category != "general":
        base += 12
    percent = min(97, base + bump)
    basis = [
        f"{similar_count} похожих случаях в Knowledge Ledger",
        f"{successful_fixes} успешных исправлениях (promoted rules)",
        "Security Regression Suite в плане проверки",
    ]
    if category != "general":
        basis.insert(0, f"Распознан паттерн категории «{category}»")
    return percent, basis


def analyze_support_message(
    message: str,
    *,
    ledger: list[KnowledgeLedgerEntry] | None = None,
) -> AnalysisResult:
    text = (message or "").strip()
    ledger = ledger or []
    matched = None
    for rule in _RULES:
        if rule[0].search(text):
            matched = rule
            break

    if matched is None:
        category = "general"
        fingerprint = "general:unclassified"
        problem = text[:280] or "Unspecified support issue"
        analysis = (
            "No strong pattern matched. Collect reproduction steps, URL, and screenshots. "
            "Do not change platform code without a concrete root cause."
        )
        suggested = (
            "Ask the client for steps to reproduce; map to existing product path "
            "(Landing /client /portal). Owner decides next action."
        )
        diff = "--- a/support\n+++ b/support\n@@\n+ triage only — no code change proposed yet\n"
        diff_summary = (
            "Пока нет конкретного кода для изменения — только triage. "
            "Платформа не модифицируется до ясной причины и Approve владельца."
        )
        risk: Literal["low", "medium", "high"] = "low"
        impact = {
            "clients_affected_estimate": 1,
            "error_reduction_percent_estimate": 0,
            "risk": "low",
            "sales_impact": "none",
            "sales_impact_label": "Нет",
        }
        tests = ["scripts/s1_security_regression_suite.py"]
    else:
        (
            _cre,
            category,
            analysis,
            suggested,
            diff,
            diff_summary,
            risk,
            impact,
            tests,
        ) = matched
        fingerprint = f"{category}:{_cre.pattern[:40]}"
        problem = text[:280]

    similar: list[str] = []
    successful = 0
    for entry in ledger:
        blob = f"{entry.problem} {entry.solution}".lower()
        if category != "general" and category in blob:
            similar.append(entry.knowledge_id)
            successful += 1
        elif fingerprint.split(":")[0] in blob:
            similar.append(entry.knowledge_id)
            successful += 1
    similar = similar[:5]
    confidence_percent, confidence_basis = _confidence(
        category=category,
        similar_count=len(similar),
        successful_fixes=successful,
    )

    return AnalysisResult(
        category=category,
        fingerprint=fingerprint,
        problem=problem,
        analysis=analysis,
        suggested_fix=suggested,
        diff_preview=diff,
        diff_summary=diff_summary,
        risk=risk,
        confidence_percent=confidence_percent,
        confidence_basis=confidence_basis,
        business_impact=dict(impact),
        rollback_available=True,
        tests_planned=list(tests),
        similar_case_ids=similar,
    )
