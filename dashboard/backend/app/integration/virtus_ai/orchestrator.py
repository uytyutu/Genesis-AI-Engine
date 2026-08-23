"""Virtus AI orchestrator — intent → plan → model_hint (no vendor lock-in)."""

from __future__ import annotations

from typing import Any, Iterable, Literal

from app.integration.virtus_ai.character import redirect_to_project, welcome_message
from app.integration.virtus_ai.ownership import check_ownership
from app.integration.virtus_ai.session_memory import append_turn, load_session

ModelHint = Literal["claude", "gpt", "grok", "gemini", "local", "rules"]


def _pick_model(intent: str, *, confirm_required: bool) -> ModelHint:
    """Heuristic router — providers are swappable; client never sees the name."""
    t = intent.lower()
    if confirm_required or "дизайн" in t or "полностью" in t or "premium" in t:
        return "claude"
    if "seo" in t or "текст" in t or "копирайт" in t:
        return "gpt"
    if "код" in t or "компонент" in t or "фильтр" in t:
        return "grok"
    if "картин" in t or "фото" in t or "видео" in t or "media" in t:
        return "gemini"
    if len(t) < 24:
        return "rules"
    return "local"


def _plan_for(message: str) -> dict[str, Any]:
    t = (message or "").strip()
    low = t.lower()
    steps: list[str] = []
    confirm = False
    href = "/client/site"

    if "цен" in low and "страниц" in low:
        steps = ["Создать страницу «Цены»", "Добавить пункт в меню", "CTA на запись/заказ"]
        href = "/client/pages"
    elif "hero" in low or "первый экран" in low or "темнее" in low:
        steps = ["Скорректировать Hero (тон/контраст)", "Проверить читаемость заголовка", "Предпросмотр"]
        href = "/client/site"
    elif "отзыв" in low:
        steps = ["Добавить блок отзывов", "Подключить 3 карточки", "Разместить ниже услуг"]
        href = "/client/pages"
    elif "фото" in low or "изображ" in low or "галере" in low:
        steps = ["Открыть Медиа", "Заменить пластины галереи", "Проверить мобильную сетку"]
        href = "/client/media"
    elif "контакт" in low or "телефон" in low or "instagram" in low or "whatsapp" in low:
        steps = ["Обновить контакты", "Синхронизировать футер и Hero CTA"]
        href = "/client/contacts"
    elif "услуг" in low:
        steps = ["Добавить услугу в список", "Обновить иконку/описание", "SEO title"]
        href = "/client/texts"
    elif "товар" in low or "500 товар" in low:
        steps = ["Каталог и категории", "Поиск и фильтры", "Пагинация"]
        href = "/client/products"
        confirm = True
    elif "современн" in low or "красивее" in low or "дороже" in low or "полностью" in low:
        steps = ["Новый Hero", "Палитра и типографика", "Карточки и анимации"]
        href = "/client/site"
        confirm = True
    else:
        steps = ["Уточнить цель", "Подготовить план изменений", "Показать предпросмотр"]
        href = "/client"

    return {
        "summary": t[:200] or "Запрос по проекту",
        "steps": steps,
        "confirm_required": confirm,
        "deep_link": href,
    }


def handle_turn(
    message: str,
    *,
    client_id: str = "anon",
    products: Iterable[Any] | None = None,
    commerce_mode: str | None = None,
    package_id: str | None = None,
    context: dict[str, Any] | None = None,
    mode: str = "auto",  # auto | confirm
) -> dict[str, Any]:
    """One Virtus AI turn — character + ownership + plan + model_hint."""
    ctx = dict(context or {})
    text = (message or "").strip()

    if not text or text in ("__welcome__", "/start"):
        reply = welcome_message(ctx)
        append_turn(client_id, "assistant", reply, {"kind": "welcome"})
        return {
            "assistant": "Virtus AI",
            "reply": reply,
            "kind": "welcome",
            "model_hint": "rules",
            "quick_actions": _quick_actions(ctx),
        }

    redirect = redirect_to_project(text)
    if redirect == "__RESUME__":
        sess = load_session(client_id)
        last = sess.get("last_session") or {}
        done = list((sess.get("checklist") or {}).get("done") or [])[:5]
        todo = list((sess.get("checklist") or {}).get("todo") or [])[:5]
        reply = "Последний раз мы остановились на этом:\n\n"
        if done:
            for d in done:
                reply += f"✔ {d}\n"
        elif last.get("summary"):
            reply += f"✔ {last['summary']}\n"
        else:
            reply += "✔ Проект создан и доступен в Workspace\n"
        reply += "\nОсталось:\n"
        if todo:
            for t in todo:
                reply += f"• {t}\n"
        else:
            reply += "• проверить мобильную версию\n• добавить отзывы\n• опубликовать изменения\n"
        reply += "\nПродолжим с этого места?"
        append_turn(client_id, "user", text)
        append_turn(client_id, "assistant", reply, {"kind": "resume"})
        return {
            "assistant": "Virtus AI",
            "reply": reply,
            "kind": "resume",
            "model_hint": "rules",
            "quick_actions": _quick_actions(ctx),
        }
    if redirect:
        append_turn(client_id, "user", text)
        append_turn(client_id, "assistant", redirect, {"kind": "redirect"})
        return {
            "assistant": "Virtus AI",
            "reply": redirect,
            "kind": "redirect",
            "model_hint": "rules",
            "quick_actions": _quick_actions(ctx),
        }

    own = check_ownership(
        text, products=products, commerce_mode=commerce_mode, package_id=package_id
    )
    if not own.get("allowed"):
        up = own.get("upsell") or {}
        reply = (
            f"{up.get('message') or 'Эта возможность относится к отдельному продукту.'}\n\n"
            f"Модуль: {up.get('label', 'Connected')} · {up.get('price_hint', '')}\n"
            "После подключения я автоматически интегрирую его в ваш текущий проект."
        )
        append_turn(client_id, "user", text)
        append_turn(client_id, "assistant", reply, {"kind": "upsell", "upsell": up})
        return {
            "assistant": "Virtus AI",
            "reply": reply,
            "kind": "upsell",
            "upsell": up,
            "model_hint": "rules",
            "quick_actions": [
                {
                    "id": "buy",
                    "label": (up.get("cta") or {}).get("label") or "Marketplace",
                    "href": (up.get("cta") or {}).get("href") or "/client/shop",
                }
            ],
        }

    plan = _plan_for(text)
    confirm = bool(plan.get("confirm_required")) or mode == "confirm"
    model = _pick_model(text, confirm_required=confirm)

    if confirm:
        reply = (
            "Я проанализировал запрос. Вот что изменится:\n\n"
            + "\n".join(f"• {s}" for s in plan["steps"])
            + "\n\nКнопки: Применить · Доработать · Отменить.\n"
            "Показать предпросмотр перед публикацией?"
        )
        kind = "plan_confirm"
    else:
        reply = (
            "Подготовлю изменения:\n\n"
            + "\n".join(f"• {s}" for s in plan["steps"])
            + "\n\nОткрою нужный раздел Workspace и покажу предпросмотр."
        )
        kind = "plan_auto"

    append_turn(client_id, "user", text)
    append_turn(
        client_id,
        "assistant",
        reply,
        {"kind": kind, "plan": plan, "model_hint": model},
    )

    return {
        "assistant": "Virtus AI",
        "reply": reply,
        "kind": kind,
        "plan": plan,
        "model_hint": model,
        "deep_link": plan.get("deep_link"),
        "quick_actions": [
            {"id": "preview", "label": "Показать изменения", "href": plan.get("deep_link") or "/client/site"},
            {"id": "checklist", "label": "Готовность бизнеса", "href": "/client"},
            *(_quick_actions(ctx)[:3]),
        ],
        "note": "model_hint is internal — never show vendor name to the client",
    }


def _quick_actions(ctx: dict[str, Any]) -> list[dict[str, str]]:
    has_store = bool(ctx.get("has_store"))
    actions = [
        {"id": "hero", "label": "Изменить главную", "message": "Сделай главную страницу современнее."},
        {"id": "photos", "label": "Заменить фотографии", "message": "Замени фотографии на более подходящие нише."},
        {"id": "contacts", "label": "Обновить контакты", "message": "Обнови контакты и часы работы."},
        {"id": "service", "label": "Добавить услугу", "message": "Добавь новую услугу на сайт."},
        {"id": "page", "label": "Создать страницу", "message": "Добавь страницу О компании."},
        {"id": "ready", "label": "Готовность бизнеса", "message": "Проверь готовность бизнеса и чек-лист запуска."},
    ]
    if has_store:
        actions.insert(
            4,
            {"id": "products", "label": "Добавить товары", "message": "Добавь первые товары в магазин."},
        )
    return actions
