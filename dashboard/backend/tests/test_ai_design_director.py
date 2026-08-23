"""AI Design Director scoring."""

from app.factory.visual_intelligence.ai_design_director import (
    FIRST_IMPRESSION_PREMIUM_THRESHOLD,
    PREMIUM_FEELING_THRESHOLD,
    PRODUCT_NAME,
    score_html,
    similarity_pct,
)


def test_product_name():
    assert "Experience" in PRODUCT_NAME


def test_score_experience_keys():
    html = """
    <html><head><meta name="viewport" content="width=device-width"></head>
    <body data-tier="business" data-hero-layout="C" data-layout-profile="L2"
      data-vie-engine="visual_intelligence_v1" data-motion="css">
    <header class="hero"><h1>SmileCare</h1><p class="lead">Praxis</p>
    <div class="hero-kpi">A</div><div class="trust-bar">B</div></header>
    <a class="btn" href="#contact">Termin</a>
    <section id="contact"><form></form></section>
    <style>@media (max-width: 768px){ .hero{}} body{font-family:system-ui}</style>
    </body></html>
    """
    out = score_html(html, package_id="business", niche="dental")
    for key in (
        "first_impression",
        "brand_emotion",
        "trust",
        "conversion_readiness",
        "mobile_experience",
        "creativity",
        "premium_feeling",
    ):
        assert key in out["scores"]
    assert out["acceptance_5s_ru"]


def test_premium_first_impression_gate():
    html = """
    <html><body data-tier="premium" data-hero-layout="B">
    <header class="hero"><h1>X</h1></header>
    </body></html>
    """
    out = score_html(html, package_id="premium", niche="dental", luxury_mode=True)
    # Weak hero-only premium should not clear First Impression 90
    assert (
        out["scores"]["first_impression"] < FIRST_IMPRESSION_PREMIUM_THRESHOLD
        or out["ok"] is False
    )


def test_similarity_identical():
    assert similarity_pct("abcdef", "abcdef") == 100
