from pathlib import Path

import pytest

from app.integration.lead_intake_service import (
    LeadIntakeService,
    extract_lead_facts,
    is_hot_lead,
    lead_gaps,
    merge_lead_known,
    score_lead,
)
from app.integration.opportunity_service import OpportunityService


@pytest.fixture()
def intake_svc(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    return LeadIntakeService(opp, notifications=None)


def test_extract_lead_facts_from_ru_message():
    msg = (
        "Привет, меня зовут Алекс. В Пирне сломались тормоза, срочно нужен автосервис. "
        "Телефон +49 170 1234567"
    )
    facts = extract_lead_facts(msg)
    assert facts.get("customer_name")
    assert facts.get("problem")
    assert facts.get("location")
    assert facts.get("phone")
    assert facts.get("urgency")


def test_hot_lead_requires_problem_location_contact():
    known = merge_lead_known(
        {},
        {
            "problem": "Не включается ноутбук",
            "location": "Dresden",
            "phone": "+49 170 999",
        },
    )
    assert is_hot_lead(known)
    assert score_lead(known) >= 70
    assert lead_gaps(known) == ["urgency"]


def test_intake_creates_qualified_opportunity(intake_svc: LeadIntakeService):
    known = {
        "customer_name": "Алекс",
        "problem": "Сломались тормоза",
        "location": "Pirna",
        "phone": "+49 170 111222",
        "urgency": "Сегодня",
    }
    result = intake_svc.intake(
        niche="autoservice",
        known=known,
        visitor_id="vis-test-1",
        transcript="Нужен автосервис срочно",
    )
    assert result["hot"] is True
    assert result["lead_id"]
    inbox = intake_svc.inbox(today_only=False)
    assert len(inbox) == 1
    assert inbox[0]["status"] == "qualified"
    assert inbox[0]["source_id"] == "inbound_chat"
    assert inbox[0]["potential_value_eur"] == 20.0


def test_intake_not_hot_returns_gaps(intake_svc: LeadIntakeService):
    result = intake_svc.intake(
        niche="plumber",
        known={"problem": "Протечка крана"},
        visitor_id="vis-2",
        transcript="",
    )
    assert result["hot"] is False
    assert "location" in result["gaps"]
    assert result["follow_up"]
