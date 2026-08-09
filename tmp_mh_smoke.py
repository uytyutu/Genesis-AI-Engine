from pathlib import Path
from swarm.money_hunter import MoneyHunterService

s = MoneyHunterService(Path("/tmp/mh_test"))
r = s.import_opportunity(
    {
        "source": "manual",
        "title": "DE research",
        "description": "Public market research CSV",
        "budget_min": 100,
        "budget_max": 120,
        "currency": "EUR",
    }
)
print("ok", r["ok"], r["opportunity"]["status"], r["opportunity"]["economics"]["opportunity_score"])
print("reality", s.reality())
