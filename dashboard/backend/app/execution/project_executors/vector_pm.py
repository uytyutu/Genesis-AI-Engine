"""Vector PM voice — service-agnostic; Vector does not name the product type."""

from __future__ import annotations

from app.integration.product_line import universal_first_version_scenario


def pm_company_step() -> str:
    return (
        "Проект создан.\n\n"
        "Прежде чем делать первую версию, хочу понять контекст.\n\n"
        "Как называется компания или подразделение, для которого ведём проект?"
    )


def pm_goal_step(company: str) -> str:
    return (
        f"Понял: речь о **{company}**.\n\n"
        "Какой результат вы хотите получить?\n"
        "Что должно измениться в работе после запуска?"
    )


def pm_structure_step(company: str) -> str:
    return (
        f"Хорошо. Для **{company}** предлагаю собрать первую концепцию "
        "на основе того, что уже обсудили.\n\n"
        "Если нужно уточнить процесс, этапы или интеграции — напишите сейчас. "
        "Иначе ответьте «хорошо, продолжаем» — и я подготовлю первую версию в проекте."
    )


def pm_first_concept_ready() -> str:
    return f"Первая версия в проекте.\n\n{universal_first_version_scenario()}"


def pm_preview_open_label() -> str:
    return "📄 Открыть версию"


def pm_workspace_title() -> str:
    return "Virtus Project"
