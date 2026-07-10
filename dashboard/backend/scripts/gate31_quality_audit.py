"""Commit 3.1 — quality self-check before CEO beta re-test. Run from repo root."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.execution.document_intelligence import (  # noqa: E402
    analyze_document,
    render_executive_summary_md,
    render_report_md,
)

CASES = [
    (
        "ru_business_plan (TechGenie-style)",
        "ru",
        """
        Бизнес-план TechGenie Haus Service — умный дом в Берлине
        Рынок: рост спроса на KNX и Smart Home в Германии 12% CAGR.
        Целевая аудитория: владельцы квартир и малый бизнес в Berlin-Mitte.
        Финансы: выручка год 1 — 180000 EUR, точка безубыточности — месяц 14.
        Сильные стороны:
        - Команда из 4 сертифицированных электриков KNX
        - Партнёрство с поставщиком Gira
        - Уникальная ниша: сервис + монтаж под ключ
        Слабые стороны:
        - Нет бренда на старте
        - Зависимость от 2 крупных клиентов B2B
        Риски: регуляторные требования VDE, дефицит монтажников.
        Стратегия: фокус на реферальный маркетинг и партнёрства с застройщиками.
        """,
        "Насколько бизнес готов к запуску?",
    ),
    (
        "de_geschaeftsplan",
        "de",
        """
        Geschäftsplan Kaffeehaus Berlin Mitte
        Markt: Specialty Coffee wächst in Berlin um 8% pro Jahr.
        Finanzen: Umsatz Jahr 1 — 120000 EUR, Break-even nach 9 Monaten.
        Stärken:
        - Einzigartige Lage an der Friedrichstraße
        - Erfahrenes Team mit 10 Jahren Gastronomie
        Schwächen:
        - Hohe Miete im ersten Jahr
        - Saisonale Schwankungen im Sommer
        Risiken: Neue Wettbewerber und steigende Energiekosten.
        """,
        "Prüfe meinen Geschäftsplan",
    ),
    (
        "en_startup_plan",
        "en",
        """
        Business Plan — SmileDent Dental Clinic London
        Market: UK private dentistry growing 6% annually.
        Revenue forecast year 1: GBP 450000. Break-even month 11.
        Strengths:
        - Digital X-ray and same-day implant workflow
        - Strong referral network with local GPs
        Weaknesses:
        - Limited marketing budget year one
        - Dependence on two lead dentists
        Risks: Regulatory CQC compliance and staffing shortages.
        """,
        "How ready is this business?",
    ),
    (
        "ru_small_2pages",
        "ru",
        """
        Краткий план автосервиса DriveFix
        Рынок: 5000 авто в радиусе 3 км. Выручка 90000 EUR.
        Сильные стороны: опыт 15 лет, своё оборудование.
        Риск: конкуренция с дилерами.
        """,
        "Проверь план",
    ),
    (
        "ru_large_synthetic",
        "ru",
        "\n".join(
            [
                f"Раздел {i}: Анализ рынка стоматологии в регионе {i}. "
                f"Выручка сегмента {i*50000} EUR. Сильные стороны команды {i}. "
                f"Риск конкуренции уровня {i}."
                for i in range(1, 41)
            ]
        ),
        "Проанализируй бизнес-план",
    ),
]


def _thirty_second_test(analysis) -> tuple[bool, str]:
    """CEO: can user decide in 30s if business is worth launching?"""
    checks = []
    if analysis.readiness_score >= 40:
        checks.append("score")
    if analysis.verdict and len(analysis.verdict) > 20:
        checks.append("verdict")
    if analysis.main_advantage and len(analysis.main_advantage) > 15:
        checks.append("advantage")
    if analysis.main_risk and len(analysis.main_risk) > 15:
        checks.append("risk")
    if len(analysis.priority_actions) >= 3:
        checks.append("steps")
    ok = len(checks) >= 4
    return ok, ",".join(checks) if checks else "none"


def main() -> int:
    print("=" * 72)
    print("GATE 3.1 QUALITY AUDIT")
    print("=" * 72)
    fails = 0
    for name, locale, text, goal in CASES:
        a = analyze_document(text, filename=f"{name}.pdf", goal=goal, locale=locale)
        exec_md = render_executive_summary_md(a, source_filename=f"{name}.pdf")
        report_md = render_report_md(a, source_filename=f"{name}.pdf")
        ok, signals = _thirty_second_test(a)
        mixed_en = "Strengths" in report_md and locale == "ru"
        placeholder_swot = "не выделены явно" in str(a.swot.get("strengths", []))

        print(f"\n--- {name} (locale={a.report_locale}) ---")
        print(f"Readiness: {a.readiness_score}/100 | Launch: {a.launch_probability_pct}%")
        print(f"SWOT strengths count: {len(a.strengths)} | priorities: {len(a.priority_actions)}")
        print(f"30-sec test: {'PASS' if ok else 'FAIL'} [{signals}]")
        print(f"Mixed EN in RU report: {mixed_en}")
        print(f"Placeholder SWOT: {placeholder_swot}")
        print("Executive Summary (excerpt):")
        for line in exec_md.splitlines()[:22]:
            print(f"  {line}")
        if not ok or mixed_en:
            fails += 1
    print("\n" + "=" * 72)
    print(f"Cases with issues: {fails}/{len(CASES)}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
