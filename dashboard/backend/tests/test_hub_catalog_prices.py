"""Hub product cards must show Market Resolver currency — not hardcoded EUR."""

from __future__ import annotations

from app.integration.pricing_engine import resolve_hub_catalog_prices


# market → (currency, symbol, basic_amount)
_SMOKE: list[tuple[str, str, str, int]] = [
    ("AU", "AUD", "A$", 312),
    ("GB", "GBP", "£", 170),
    ("CZ", "CZK", "Kč", 8529),
    ("PL", "PLN", "zł", 682),
    ("US", "USD", "$", 227),
    ("DE", "EUR", "€", 199),
    ("FR", "EUR", "€", 188),
]


def _row_status(market: str, currency: str, symbol: str, basic: int) -> dict:
    hub = resolve_hub_catalog_prices(market)
    landing = hub["landing_website"]["range_label"]
    bot = hub["ai_business_bot"]["setup_label"]
    repair = hub["website_repair"]["from_label"]
    basic_fmt = f"{basic:,}".replace(",", " ")
    amount_ok = basic_fmt in landing or str(basic) in landing
    eur_ok = currency == "EUR" or (
        "€" not in landing and "€" not in bot and "€" not in repair
    )
    ok = (
        hub["currency"] == currency
        and hub["symbol"] == symbol
        and amount_ok
        and eur_ok
        and symbol in landing
        and symbol in bot
        and symbol in repair
    )
    return {
        "market": market,
        "expected": f"{basic_fmt}… {symbol} ({currency})",
        "actual_landing": landing,
        "actual_bot": bot,
        "actual_repair": repair,
        "status": "PASS" if ok else "FAIL",
    }


def test_hub_catalog_prices_match_market_resolver():
    for market, currency, symbol, basic in _SMOKE:
        row = _row_status(market, currency, symbol, basic)
        assert row["status"] == "PASS", row


def test_hub_smoke_table_print():
    """Print Expected → Actual for CEO smoke report."""
    lines = [
        "Market | Expected | Actual landing | Actual bot | Actual repair | Status",
        "-" * 110,
    ]
    for market, currency, symbol, basic in _SMOKE:
        row = _row_status(market, currency, symbol, basic)
        lines.append(
            f"{row['market']} | {row['expected']} | {row['actual_landing']} | "
            f"{row['actual_bot']} | {row['actual_repair']} | {row['status']}"
        )
        assert row["status"] == "PASS", row
    print("\n" + "\n".join(lines))
