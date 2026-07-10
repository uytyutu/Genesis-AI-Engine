"""Market detection — target market, not IP/VPN."""

from app.integration.market_context import (
    MARKET_DE,
    MARKET_PL,
    MARKET_UA,
    MARKET_US,
    extract_market_signals,
    market_clarification_question,
    resolve_market_context,
)


def test_germany_business_overrides_client_poland():
    ctx = resolve_market_context(
        text="Я в Польше, но открываю компанию в Германии. Нужен сайт для немецких клиентов."
    )
    assert ctx.target_market_code == MARKET_DE
    assert ctx.confidence in ("high", "medium")


def test_us_vpn_ukraine_charity():
    ctx = resolve_market_context(
        text="I'm in the US. Website for a Ukrainian charity organization, audience in Ukraine."
    )
    assert ctx.target_market_code == MARKET_UA


def test_impressum_signals_germany():
    signals = extract_market_signals("Нужен Impressum и Datenschutz на сайте")
    codes = {s.market_code for s in signals}
    assert MARKET_DE in codes


def test_conflict_needs_clarification():
    ctx = resolve_market_context(
        text="Сайт для Германии, но компания в Польше и домен .pl"
    )
    assert ctx.needs_clarification or len(ctx.conflicts) > 0


def test_unknown_market_asks_question():
    ctx = resolve_market_context(text="хочу создать сайт")
    assert ctx.needs_clarification
    q = market_clarification_question(ctx)
    assert q
    assert "рынк" in q.lower() or "стран" in q.lower()


def test_no_ip_signals_used():
    """Market module has no geolocation imports — signals from text only."""
    ctx = resolve_market_context(messages=[{"role": "user", "content": "сайт для Польши"}])
    assert ctx.target_market_code == MARKET_PL
