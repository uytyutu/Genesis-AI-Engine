"""Record owner product creation intents and run Factory v0.1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import FactoryIntentRequest

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


def compose_factory_brief(request: FactoryIntentRequest) -> str:
    """Merge wizard fields into one brief for the landing analyzer."""
    parts = [request.description.strip()]
    if request.audience and request.audience.strip():
        parts.append(f"Целевая аудитория: {request.audience.strip()}")
    if request.goal and request.goal.strip():
        parts.append(f"Цель продукта: {request.goal.strip()}")
    if request.price_eur is not None:
        parts.append(f"Планируемая цена: {request.price_eur:g} €")
    if request.deadline and request.deadline.strip():
        parts.append(f"Дедлайн: {request.deadline.strip()}")
    return "\n".join(parts)


class FactoryIntentService:
    def __init__(self, memory_dir: Path | None = None, factory: object | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._factory = factory
        self._memory.mkdir(parents=True, exist_ok=True)

    def submit(self, request: FactoryIntentRequest) -> dict:
        intent_id = str(uuid.uuid4())
        brief = compose_factory_brief(request)
        record = {
            "intent_id": intent_id,
            "product_type": request.product_type,
            "description": request.description,
            "audience": request.audience,
            "goal": request.goal,
            "price_eur": request.price_eur,
            "deadline": request.deadline,
            "brief": brief,
            "at": datetime.now(timezone.utc).isoformat(),
            "status": "building",
        }
        path = self._memory / "factory_intents.jsonl"
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        if self._factory is None:
            return {
                "ok": True,
                "intent_id": intent_id,
                "message": "Заявка принята. Отдел создания продуктов готовится к сборке.",
            }

        product = self._factory.build_landing(
            brief,
            intent_id=intent_id,
            client_legal=request.client_legal if isinstance(request.client_legal, dict) else None,
        )
        record["status"] = "completed"
        record["product_id"] = product["product_id"]
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {**record, "at": datetime.now(timezone.utc).isoformat()},
                    ensure_ascii=False,
                )
                + "\n"
            )

        return {
            "ok": True,
            "intent_id": intent_id,
            "product_id": product["product_id"],
            "quality_percent": product["quality_percent"],
            "message": (
                f"Отдел создания продуктов завершил работу. "
                "Откройте превью и нажмите «Готов отправить клиенту», когда результат устроит."
            ),
            "product": product,
        }

    def list_intents(self, limit: int = 50) -> list[dict]:
        path = self._memory / "factory_intents.jsonl"
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return list(reversed(rows[-limit:]))
