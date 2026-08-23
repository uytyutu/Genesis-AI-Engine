"""Horizon Media Engine — Internal-only product shell (Phase D Proof).

Not a video generator. Positioning: commercial-ready ads studio / Creative Director.
No live video engines until Virtus Core proves Horizon on its own marketing.
"""

from __future__ import annotations

from typing import Any


HORIZON_STAGE = "internal_only"

PLATFORMS = [
    {"id": "tiktok", "label": "TikTok", "aspect": "9:16", "durations_sec": [15, 20, 30, 45, 60]},
    {
        "id": "instagram_reels",
        "label": "Instagram Reels",
        "aspect": "9:16",
        "durations_sec": [15, 30, 60, 90],
    },
    {
        "id": "facebook_reels",
        "label": "Facebook Reels",
        "aspect": "9:16",
        "durations_sec": [15, 30, 60],
    },
    {
        "id": "youtube_shorts",
        "label": "YouTube Shorts",
        "aspect": "9:16",
        "durations_sec": [30, 45, 60],
    },
    {
        "id": "youtube",
        "label": "YouTube",
        "aspect": "16:9",
        "durations_sec": [120, 180, 300, 480],
    },
    {"id": "linkedin", "label": "LinkedIn", "aspect": "1:1", "durations_sec": [30, 60, 90]},
    {"id": "x", "label": "X", "aspect": "16:9", "durations_sec": [15, 30, 60]},
    {"id": "pinterest", "label": "Pinterest", "aspect": "2:3", "durations_sec": [15, 30]},
]

GOALS = [
    "sell",
    "lead",
    "brand",
    "company_story",
    "product",
    "education",
    "case_study",
    "promo",
]

GENRES = [
    "cinematic",
    "realistic",
    "documentary",
    "commercial",
    "corporate",
    "minimal",
    "luxury",
    "tech",
    "cartoon",
    "anime",
    "3d",
    "futurism",
]

QUALITY_TARGETS = [
    {"id": "economy", "label": "Economy", "retries": 1},
    {"id": "business", "label": "Business", "retries": 2},
    {"id": "premium", "label": "Premium", "retries": 3},
    {"id": "cinema", "label": "Cinema", "retries": 5},
]

PRODUCT_TIERS = [
    {
        "id": "horizon_ads",
        "label": "Horizon Ads",
        "detail_ru": "Короткие ролики 15–60 сек · TikTok / Reels / Shorts",
    },
    {
        "id": "horizon_promo",
        "label": "Horizon Promo",
        "detail_ru": "Полноценная реклама 30–120 сек · сайт / YouTube / Facebook",
    },
    {
        "id": "horizon_studio",
        "label": "Horizon Studio",
        "detail_ru": "Большие проекты · бренд-фильм · запуск продукта",
    },
]

# Creative Bible — professional production rules (SSOT for future Director).
CREATIVE_BIBLE: dict[str, Any] = {
    "positioning_ru": (
        "Horizon генерирует не «AI-видео», а готовую рекламу коммерческого уровня. "
        "Зритель не должен подумать: «это сделал ИИ»."
    ),
    "principles": [
        "Prompt Director — последний шаг, не первый",
        "Пользователь принимает творческие решения; Horizon исполняет",
        "Media Orchestrator — не привязка к одному видеодвижку",
        "Quality Gate обязателен до Export MP4",
        "Сначала Internal Only (реклама Virtus Core), потом клиентам",
        "Универсальный Media Engine — адаптация одного сценария под площадки",
    ],
    "hook_seconds": 3,
    "pipeline": [
        "structure",
        "script",
        "storyboard",
        "voice",
        "visuals",
        "music",
        "subtitles",
        "edit",
        "quality_gate",
        "export",
    ],
    "quality_gate": [
        "character_consistency",
        "motion_consistency",
        "story_consistency",
        "transition_engine",
        "audio_sync",
        "subtitle_quality",
        "brand_safety",
        "ai_artifact_detector",
    ],
    "commercial_ready_checks": [
        "story",
        "motion",
        "audio",
        "brand",
        "subtitle",
        "artifact_check",
        "export",
    ],
    "knowledge_domains": [
        "рекламный монтаж",
        "драматургия коротких видео",
        "психология рекламы",
        "удержание внимания",
        "особенности TikTok / Reels / Shorts",
        "композиция",
        "теория цвета",
        "типографика",
        "субтитры",
        "safe zones платформ",
    ],
    "orchestrator_engines_planned": [
        "openai",
        "google_veo",
        "runway",
        "pika",
        "luma",
        "kling",
        "minimax",
    ],
}


def build_horizon_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Horizon Media Engine",
        "brand_line_ru": "AI Creative Director · автоматическая студия рекламных кампаний",
        "stage": HORIZON_STAGE,
        "stage_ru": "Internal Only — только реклама Virtus Core и своих продуктов",
        "client_sales": False,
        "video_generation_enabled": False,
        "blocked_until_ru": (
            "Horizon ждёт Digital Experience Factory: 5s Starter<Business<Premium, "
            "Store Login/Register, Premium First Impression ≥ 90. Иначе реклама слабых демо."
        ),
        "note_ru": (
            "Phase D Proof: оболочка и Creative Bible. "
            "Живые движки и Export MP4 — после месяцев внутренней проверки качества."
        ),
        "platforms": PLATFORMS,
        "goals": GOALS,
        "genres": GENRES,
        "quality_targets": QUALITY_TARGETS,
        "product_tiers": PRODUCT_TIERS,
        "studio_steps": [
            {"id": "platform", "label_ru": "Площадка"},
            {"id": "goal", "label_ru": "Цель"},
            {"id": "audience", "label_ru": "Аудитория"},
            {"id": "duration", "label_ru": "Длительность"},
            {"id": "genre", "label_ru": "Жанр"},
            {"id": "edit_style", "label_ru": "Стиль монтажа"},
            {"id": "voice", "label_ru": "Озвучка"},
            {"id": "music", "label_ru": "Музыка"},
            {"id": "assets", "label_ru": "Материалы"},
            {"id": "branding", "label_ru": "Брендинг"},
            {"id": "prompt_director", "label_ru": "Prompt Director"},
        ],
        "creative_bible": CREATIVE_BIBLE,
        "creative_control": {
            "enabled_planned": True,
            "variants": ["A_premium_calm", "B_tiktok_dynamic", "C_cinematic", "D_commercial"],
            "note_ru": "Несколько вариантов → выбор → точечная замена голоса/музыки/субтитров без полной перегенерации.",
        },
        "factory_hook_planned": {
            "enabled": False,
            "flow": ["website", "generate_promo", "tiktok", "instagram", "shorts", "facebook"],
        },
        "related": {"tiktok_horizon": "/tiktok-horizon", "horizon_studio": "/horizon"},
    }
