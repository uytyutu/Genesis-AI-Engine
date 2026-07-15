"""Mission 2 KPI — full funnel, conversions, next action."""

from app.integration.mission2_kpi_service import build_mission2_kpi


def test_full_kpi_metrics():
    rows = [
        {"id": "1", "status": "new"},
        {
            "id": "2",
            "meta": {"qualification": {"passed": True}, "audit_report_md": "# audit"},
            "proposed_message": "Hi",
            "outreach_status": "sent",
            "status": "contacted",
        },
        {
            "id": "3",
            "meta": {"qualification": {"passed": True}, "audit_report_md": "# a"},
            "proposed_message": "Hello",
            "outreach_status": "sent",
            "status": "replied",
        },
    ]
    kpi = build_mission2_kpi(rows, received_eur=0, outbox_pending=2)
    by_id = {m["id"]: m for m in kpi["metrics"]}
    assert by_id["companies_found"]["value"] == 3
    assert by_id["after_qualification"]["value"] == 2
    assert by_id["audits_prepared"]["value"] == 2
    assert by_id["letters_ready"]["value"] == 2
    assert by_id["sent"]["value"] == 2
    assert by_id["replies"]["value"] == 1
    assert kpi["next_action"]["action_id"] == "approve_letters"
    assert kpi["conversions"][0]["percent"] == 67


def test_bottleneck_no_replies():
    rows = [{"id": str(i), "status": "contacted", "outreach_status": "sent", "proposed_message": "x",
             "meta": {"qualification": {"passed": True}}} for i in range(25)]
    kpi = build_mission2_kpi(rows, outbox_pending=0)
    assert "писем" in kpi["bottleneck_ru"].lower() or "ответ" in kpi["bottleneck_ru"].lower()


def test_next_action_prepare_leads_when_empty():
    kpi = build_mission2_kpi([], outbox_pending=0)
    assert kpi["next_action"]["action_id"] == "prepare_leads"
