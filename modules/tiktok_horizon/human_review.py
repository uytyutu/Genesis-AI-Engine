"""Human Review Engine — mandatory edit gate before queue."""

from __future__ import annotations

from typing import Any

EDITABLE_FIELDS = (
    "title",
    "hook_seconds",
    "narrator_text",
    "caption",
    "hashtags",
    "voice_preference",
    "style_variant",
    "scene_order",
    "subtitles_enabled",
)


class HumanReviewEngine:
    """Checklist + apply patches. Approve is explicit — never auto-publish."""

    def checklist(self, draft: dict[str, Any]) -> dict[str, Any]:
        script = draft.get("script") or {}
        return {
            "draft_id": draft.get("id"),
            "status": draft.get("status"),
            "items": [
                {"id": "title", "label_ru": "Изменить заголовок", "value": draft.get("title")},
                {
                    "id": "hook_seconds",
                    "label_ru": "Заменить первые 3 секунды (hook)",
                    "value": script.get("hook_seconds"),
                },
                {
                    "id": "narrator_text",
                    "label_ru": "Изменить сценарий / текст диктора",
                    "value": script.get("narrator_text"),
                },
                {
                    "id": "caption",
                    "label_ru": "Переписать описание",
                    "value": script.get("caption"),
                },
                {
                    "id": "hashtags",
                    "label_ru": "Изменить хештеги",
                    "value": script.get("hashtags"),
                },
                {
                    "id": "voice_preference",
                    "label_ru": "Выбрать другой голос (preference only in Stage 1)",
                    "value": draft.get("voice_preference") or "default",
                },
                {
                    "id": "style_variant",
                    "label_ru": "Сменить стиль подачи",
                    "value": script.get("style_variant") or draft.get("style_variant"),
                },
                {
                    "id": "scene_order",
                    "label_ru": "Поменять порядок сцен",
                    "value": draft.get("scene_order") or script.get("structure"),
                },
                {
                    "id": "subtitles_enabled",
                    "label_ru": "Субтитры вкл/выкл",
                    "value": draft.get("subtitles_enabled", True),
                },
                {
                    "id": "publish_window",
                    "label_ru": "Выбрать другое время публикации",
                    "value": (draft.get("publish_window") or {}).get("window_start_local"),
                },
            ],
            "rule_ru": "Публикация только после Approve. На Stage 1 публикация отключена — только очередь.",
        }

    def apply_edits(self, draft: dict[str, Any], edits: dict[str, Any]) -> dict[str, Any]:
        out = dict(draft)
        script = dict(out.get("script") or {})
        if "title" in edits and edits["title"] is not None:
            out["title"] = str(edits["title"])[:200]
        if "hook_seconds" in edits and edits["hook_seconds"] is not None:
            script["hook_seconds"] = str(edits["hook_seconds"])[:200]
        if "narrator_text" in edits and edits["narrator_text"] is not None:
            script["narrator_text"] = str(edits["narrator_text"])[:4000]
        if "caption" in edits and edits["caption"] is not None:
            script["caption"] = str(edits["caption"])[:500]
        if "hashtags" in edits and edits["hashtags"] is not None:
            tags = edits["hashtags"]
            if isinstance(tags, str):
                tags = [t.strip().lstrip("#") for t in tags.replace(",", " ").split() if t.strip()]
            script["hashtags"] = [str(t)[:40] for t in tags][:12]
        if "style_variant" in edits and edits["style_variant"] is not None:
            script["style_variant"] = str(edits["style_variant"])[:40]
            out["style_variant"] = script["style_variant"]
        if "scene_order" in edits and edits["scene_order"] is not None:
            order = edits["scene_order"]
            if isinstance(order, str):
                order = [x.strip() for x in order.split(",") if x.strip()]
            out["scene_order"] = [str(x)[:40] for x in order][:20]
            if out["scene_order"]:
                script["structure"] = list(out["scene_order"])
        if "voice_preference" in edits and edits["voice_preference"] is not None:
            out["voice_preference"] = str(edits["voice_preference"])[:60]
        if "subtitles_enabled" in edits and edits["subtitles_enabled"] is not None:
            out["subtitles_enabled"] = bool(edits["subtitles_enabled"])
        if "publish_window" in edits and isinstance(edits["publish_window"], dict):
            out["publish_window"] = edits["publish_window"]
        out["script"] = script
        out["status"] = "review"
        out["human_edited"] = True
        return out
