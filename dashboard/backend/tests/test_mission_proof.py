"""Mission Proof checklist."""

from app.integration.mission_proof_service import build_mission_proof


def test_mission_proof_progress():
    rows = [
        {"id": "1", "status": "new"},
        {"status": "contacted", "outreach_status": "sent", "proposed_message": "hi"},
        {"status": "replied", "outreach_status": "sent", "proposed_message": "x", "meta": {"call_done": True}},
    ]
    proof = build_mission_proof(rows)
    assert proof["progress_label_ru"].startswith("4/")
    done = [s for s in proof["steps"] if s["done"]]
    assert len(done) == 4
