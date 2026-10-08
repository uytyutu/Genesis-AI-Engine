"""Virtus Video AI product SSOT — catalog, modes, Visual DNA, credit costs.

Public brand: Virtus Video AI. Internal module id stays `viewora` for stable API paths.
Client never chooses AI model names. Orchestrator picks the pipeline via Provider Gateway.
"""

from __future__ import annotations

from typing import Any

PRODUCT_ID = "viewora"
BRAND_NAME = "Virtus Video AI"
TAGLINE = "Create something that gets watched."
POSITIONING = (
    "Professional AI Video Studio by Virtus Core — idea or source in, "
    "watchable content out. Modes, Visual DNA, Hook Lab, Watchability Score, "
    "Product Ads, AI Creator, Podcast→Shorts, Content Machine."
)

# Internal unit costs — change API economics here without changing plan prices.
UNIT_COSTS: dict[str, int] = {
    "script": 1,
    "image": 2,
    "voice": 3,
    "short_video": 10,
    "cinematic_video": 20,
    "ai_creator_video": 25,
    "podcast_20": 100,
}

CREATION_TYPES: list[dict[str, Any]] = [
    {"id": "viral_short", "label": "Viral Short", "emoji": "🔥", "credits": 10},
    {"id": "ad", "label": "Реклама", "emoji": "📢", "credits": 10},
    {"id": "ai_creator", "label": "AI Creator", "emoji": "👤", "credits": 25},
    {"id": "product_video", "label": "Product Video", "emoji": "🛍", "credits": 10},
    {"id": "podcast_shorts", "label": "Podcast → Shorts", "emoji": "🎙", "credits": 100},
    {"id": "link_video", "label": "Link → Video", "emoji": "🔗", "credits": 10},
    {"id": "photo_video", "label": "Photo → Video", "emoji": "📸", "credits": 10},
    {"id": "music_video", "label": "Music Video", "emoji": "🎵", "credits": 20},
    {"id": "story", "label": "Story / Storytelling", "emoji": "📖", "credits": 10},
    {"id": "cinematic", "label": "Cinematic", "emoji": "🎥", "credits": 20},
    {"id": "tiktok_reels", "label": "TikTok / Reels / Shorts", "emoji": "📱", "credits": 10},
]

MODES: list[dict[str, str]] = [
    {"id": "viral", "label": "Viral", "blurb": "Hook, pacing, captions, CTA"},
    {"id": "cinematic", "label": "Cinematic", "blurb": "Camera, light, slow motion"},
    {"id": "ugc", "label": "UGC", "blurb": "Native phone-shot feel"},
    {"id": "luxury", "label": "Luxury", "blurb": "Premium brand ad"},
    {"id": "dark", "label": "Dark", "blurb": "Dramatic atmosphere"},
    {"id": "fun", "label": "Fun", "blurb": "Bright dynamic energy"},
    {"id": "news", "label": "News", "blurb": "Headline → fact → close"},
    {"id": "story", "label": "Story", "blurb": "Narrative arc"},
    {"id": "documentary", "label": "Documentary", "blurb": "Calm voice + atmosphere"},
]

VISUAL_DNA: dict[str, list[str]] = {
    "camera": ["iPhone", "DSLR", "cinematic", "handheld", "drone", "POV", "selfie"],
    "light": ["daylight", "sunset", "neon", "studio", "dark", "golden hour"],
    "color": ["natural", "warm", "cold", "film", "vintage", "black & white"],
    "motion": ["static", "smooth", "dynamic", "handheld", "fast cuts", "slow motion"],
    "atmosphere": [
        "luxury",
        "emotional",
        "mysterious",
        "energetic",
        "futuristic",
        "romantic",
        "funny",
    ],
}

GENERATE_10_PRESETS: list[dict[str, str]] = [
    {"id": "01", "label": "Viral"},
    {"id": "02", "label": "Cinematic"},
    {"id": "03", "label": "UGC"},
    {"id": "04", "label": "Story"},
    {"id": "05", "label": "Luxury"},
    {"id": "06", "label": "Emotional"},
    {"id": "07", "label": "Fast"},
    {"id": "08", "label": "Documentary"},
    {"id": "09", "label": "Funny"},
    {"id": "10", "label": "Minimal"},
]

VIRAL_LAB_VARIANTS: list[dict[str, str]] = [
    {"id": "A", "label": "Original", "mode": "viral"},
    {"id": "B", "label": "Aggressive Hook", "mode": "viral"},
    {"id": "C", "label": "Storytelling", "mode": "story"},
    {"id": "D", "label": "UGC", "mode": "ugc"},
    {"id": "E", "label": "Cinematic", "mode": "cinematic"},
    {"id": "F", "label": "Fast Cut", "mode": "fun"},
    {"id": "G", "label": "Emotional", "mode": "story"},
    {"id": "H", "label": "Product", "mode": "luxury"},
]

PRODUCT_AD_STYLES: list[str] = [
    "Amazon style",
    "TikTok style",
    "Luxury brand",
    "UGC",
    "Influencer",
    "Cinematic",
]

DUB_LANGUAGES: list[dict[str, str]] = [
    {"code": "de", "label": "German", "flag": "🇩🇪"},
    {"code": "en", "label": "English", "flag": "🇬🇧"},
    {"code": "fr", "label": "French", "flag": "🇫🇷"},
    {"code": "es", "label": "Spanish", "flag": "🇪🇸"},
    {"code": "it", "label": "Italian", "flag": "🇮🇹"},
    {"code": "uk", "label": "Ukrainian", "flag": "🇺🇦"},
    {"code": "ru", "label": "Russian", "flag": "🇷🇺"},
]

# Affordable client pricing (EUR). Credits hide model / unit cost.
PLANS: list[dict[str, Any]] = [
    {
        "id": "free",
        "name": "FREE",
        "monthly_eur": 0,
        "creations": 3,
        "credits": 0,
        "highlight": "Почувствовать продукт",
        "features": [
            "3 creations",
            "Viral / UGC / Cinematic modes",
            "Hook Lab (basic)",
            "Watchability Score preview",
            "No commercial watermark removal",
        ],
    },
    {
        "id": "creator",
        "name": "CREATOR",
        "monthly_eur": 12.99,
        "creations": None,
        "credits": 120,
        "highlight": "Для автора",
        "features": [
            "120 credits / month",
            "Generate 10 / Viral Lab",
            "Hook Lab + Test Hooks",
            "Make it Better",
            "Export captions + script",
            "Commercial use",
        ],
    },
    {
        "id": "pro",
        "name": "PRO",
        "monthly_eur": 29.99,
        "creations": None,
        "credits": 400,
        "popular": True,
        "highlight": "TikTok / Instagram",
        "features": [
            "400 credits / month",
            "Product Video mode",
            "AI Creator",
            "Dubbing (7 languages)",
            "Priority studio queue",
            "Watchability Optimize",
        ],
    },
    {
        "id": "business",
        "name": "BUSINESS",
        "monthly_eur": 59.99,
        "creations": None,
        "credits": 1000,
        "highlight": "Для бизнеса",
        "features": [
            "1000 credits / month",
            "Content Machine 30-day",
            "Podcast → 20 Shorts",
            "Brand kit + team seat (1)",
            "Analytics connect (Coming)",
            "Priority support",
        ],
    },
    {
        "id": "studio",
        "name": "STUDIO",
        "monthly_eur": 149.0,
        "creations": None,
        "credits": 3000,
        "highlight": "Агентства",
        "features": [
            "3000 credits / month",
            "Multi-brand workspaces",
            "Bulk Generate 10",
            "White-label export pack",
            "Dedicated queue",
            "Onboarding call",
        ],
    },
]

CREDIT_PACKS: list[dict[str, Any]] = [
    {"id": "pack_5", "eur": 5.0, "credits": 40},
    {"id": "pack_15", "eur": 15.0, "credits": 140},
    {"id": "pack_30", "eur": 30.0, "credits": 320},
    {"id": "pack_100", "eur": 100.0, "credits": 1200},
]

# Action spend — maps Studio buttons to unit economics (not 1 creation = 1 credit).
CREDIT_COSTS: dict[str, int] = {
    **UNIT_COSTS,
    "create": UNIT_COSTS["short_video"],
    "make_it_better": UNIT_COSTS["short_video"],
    "generate_10": UNIT_COSTS["short_video"] * 5,  # 10 versions, package lane
    "hook_lab": UNIT_COSTS["script"] * 3,
    "test_hooks": UNIT_COSTS["script"] * 5,
    "optimize_score": UNIT_COSTS["short_video"],
    "product_video": UNIT_COSTS["short_video"],
    "podcast_shorts": UNIT_COSTS["podcast_20"],
    "content_machine_30": UNIT_COSTS["script"] * 30,
    "dubbing_lang": UNIT_COSTS["voice"] * 7,
    "ai_creator_batch": UNIT_COSTS["ai_creator_video"] * 5,
    "viral_lab": UNIT_COSTS["short_video"] * 4,
    "cinematic_create": UNIT_COSTS["cinematic_video"],
}

PRODUCTION_GATE: dict[str, bool] = {
    "real_ai_credits": True,
    "provider_gateway": False,
    "first_real_video_generation": False,
    "mp4_storage": False,
    "download": False,
    "generation_history": True,
    "credit_deduction": True,
    "failed_generation_refund": False,
    "stripe_production": False,
    "free_quota": True,
    "subscription_status": True,
    "watchability_score": True,
    "generate_10": True,
    "end_to_end_mp4": False,
}

VIEWORA_PRODUCT: dict[str, Any] = {
    "product_id": PRODUCT_ID,
    "sku": "virtus_video_ai",
    "name": BRAND_NAME,
    "tagline": TAGLINE,
    "positioning": POSITIONING,
    "billing_modes": ["subscription", "credits", "free_trial"],
    "plans": PLANS,
    "credit_packs": CREDIT_PACKS,
    "unit_costs": UNIT_COSTS,
    "credit_costs": CREDIT_COSTS,
    "creation_types": CREATION_TYPES,
    "modes": MODES,
    "visual_dna": VISUAL_DNA,
    "generate_10": GENERATE_10_PRESETS,
    "viral_lab": VIRAL_LAB_VARIANTS,
    "product_ad_styles": PRODUCT_AD_STYLES,
    "dub_languages": DUB_LANGUAGES,
    "production_gate": PRODUCTION_GATE,
    "orchestrator": {
        "user_sees": "Create",
        "user_never_sees": ["model names", "provider pickers", "token costs"],
        "pipeline": [
            "AI Producer",
            "Storyboard",
            "Scene → Video → Voice → Music → Captions → Auto Edit",
            "Watchability Score",
            "MP4 (Provider Gateway — when live)",
        ],
        "provider_gateway": [
            "Video Provider A/B",
            "Image Provider",
            "Voice Provider",
            "Music Provider",
            "LLM",
        ],
    },
    "paths": {
        "home": "/viewora",
        "create": "/viewora/create",
        "pricing": "/viewora/pricing",
        "checkout": "/viewora/checkout",
    },
    "legal_paths": {
        "impressum": "/viewora/legal/impressum",
        "privacy": "/viewora/legal/datenschutz",
        "terms": "/viewora/legal/agb",
        "ai_notice": "/viewora/legal/ki-hinweis",
    },
    "stripe": {
        "status": "via_payment_checkout_service",
        "demo_allowed": True,
        "note": "Separate from Website/Store catalog SSOT",
    },
    "reality": {
        "package_generation": True,
        "storyboard_preview": True,
        "mp4_render": False,
        "social_publish": False,
        "analytics_connect": False,
        "note": (
            "Studio delivers creative packages, hooks, captions, scores, "
            "and storyboard previews. Full MP4 render wires through Provider "
            "Gateway when Production Gate clears — never expose model picker."
        ),
    },
}


def get_plan(plan_id: str) -> dict[str, Any] | None:
    for p in PLANS:
        if p["id"] == plan_id:
            return dict(p)
    return None


def get_credit_pack(pack_id: str) -> dict[str, Any] | None:
    for p in CREDIT_PACKS:
        if p["id"] == pack_id:
            return dict(p)
    return None


def public_catalog() -> dict[str, Any]:
    return {
        "product_id": PRODUCT_ID,
        "name": BRAND_NAME,
        "tagline": TAGLINE,
        "positioning": POSITIONING,
        "plans": PLANS,
        "credit_packs": CREDIT_PACKS,
        "unit_costs": UNIT_COSTS,
        "credit_costs": CREDIT_COSTS,
        "creation_types": CREATION_TYPES,
        "modes": MODES,
        "visual_dna": VISUAL_DNA,
        "generate_10": GENERATE_10_PRESETS,
        "viral_lab": VIRAL_LAB_VARIANTS,
        "product_ad_styles": PRODUCT_AD_STYLES,
        "dub_languages": DUB_LANGUAGES,
        "production_gate": PRODUCTION_GATE,
        "reality": VIEWORA_PRODUCT["reality"],
        "paths": VIEWORA_PRODUCT["paths"],
        "legal_paths": VIEWORA_PRODUCT["legal_paths"],
    }
