"""Universal delivery messages — service-agnostic copy."""

from __future__ import annotations

from app.integration.product_line import (
    ASSISTANT_NAME,
    universal_concept_ready_message,
    universal_first_version_scenario,
    universal_service_intro,
)


def consultation_intro(service_id: str) -> str:
    """Consultation stage — same for every service."""
    return universal_service_intro(service_id)


def revision_prompt(service_id: str) -> str:
    from app.integration.product_line import artifact_label_ru

    artifact = artifact_label_ru(service_id)
    return (
        f"Версия **{artifact}** в проекте.\n\n"
        f"{universal_first_version_scenario()}\n\n"
        f"Когда всё устроит — скажите «согласовано» или «оформляем»."
    )


def progress_lines_for_capability(capability_id: str) -> tuple[str, ...]:
  profiles: dict[str, tuple[str, ...]] = {
      "generate_site": (
          "Изучаю задачу",
          "Готовлю структуру",
          "Создаю первый вариант",
          "Настраиваю мобильную версию",
          "Проверяю отображение",
          "Первая версия в проекте",
      ),
      "analyze_business_document": (
          "Принимаю документ",
          "Извлекаю текст",
          "Структурный анализ",
          "Формирую отчёты",
          "Первая версия в проекте",
      ),
      "filesystem_write": (
          "Принимаю задачу",
          "Готовлю документ",
          "Сохраняю в проект",
          "Первая версия в проекте",
      ),
  }
  return profiles.get(
      capability_id,
      ("Принимаю задачу", "Готовлю результат", "Первая версия в проекте"),
  )


def format_progress_answer(lines: tuple[str, ...]) -> str:
    out: list[str] = []
    for line in lines:
        if line == "Первая версия в проекте":
            out.append(f"✓ {line}.")
        else:
            out.append(f"✓ {line}...")
    return "\n".join(out)


def concept_completion_message(service_id: str, *, capability_id: str) -> str:
    body = universal_concept_ready_message(service_id)
    progress = format_progress_answer(progress_lines_for_capability(capability_id))
    return f"{progress}\n\n{body}"


def agreement_acknowledgement(service_id: str) -> str:
    from app.integration.product_line import service_label_ru

    label = service_label_ru(service_id).lower()
    return (
        f"Отлично — **{label} согласован**.\n\n"
        f"Сейчас подготовлю предварительную смету и варианты оформления."
    )


def delivery_started_message(service_id: str, purchase_type: str) -> str:
    from app.integration.delivery_engine.handoff import unified_handoff_message

    return unified_handoff_message(purchase_type, service_id)


def waiting_for_client_message() -> str:
    return (
        f"{ASSISTANT_NAME} ждёт вашего ответа, чтобы продолжить проект.\n"
        "Посмотрите версию в проекте или напишите, что изменить."
    )
