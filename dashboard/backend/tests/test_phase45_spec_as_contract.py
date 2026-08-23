"""Phase 4/5 — Design Spec as sole production contract.

Proves:
- invalid Spec -> REJECT (no improvisation)
- Director may patch only allowed fields
- same Spec -> same builder contract (determinism)
- V1 remains immutable when V2 is created
- Automotive != Restaurant DNA preserved
- Premium QA stays independent of LLM claims
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from app.factory.business_interview import interview_from_payload, interview_to_contacts
from app.factory.factory_service import FactoryService
from app.factory.premium_site_qa import run_premium_site_qa
from app.factory.website_design_spec import (
    SCHEMA,
    apply_director_config_patch,
    builder_contract_from_spec,
    build_website_design_spec,
    freeze_website_design_spec,
    read_website_design_spec,
    read_website_design_spec_version,
    spec_contract_fingerprint,
    validate_website_design_spec,
    write_website_design_spec,
)


def _brief(
    niche: str, name: str, free: str, services: list[str], style: str
) -> tuple[dict, dict]:
    iv = interview_from_payload(
        {
            "company_name": name,
            "city": "Berlin",
            "free_text": free,
            "top_services": services,
            "style": style,
            "niche": niche,
        }
    )
    contacts = interview_to_contacts(
        iv,
        {
            "phone": "+49 30 1000000",
            "email": "owner@example.de",
            "domain_status": "need_help",
            "opening_hours": "Mo–Fr 9–18",
            "package_id": "business",
            "market_code": "DE",
            "client_delivery": True,
            "diversity_salt": "phase45-deterministic",
        },
    )
    return iv.as_dict(), contacts


def _auto() -> tuple[dict, dict]:
    return _brief(
        "auto",
        "Kfz Meisterbetrieb Schmidt",
        "Werkstatt für Inspektion, Bremsen, Ölwechsel und HU/AU.",
        ["Inspektion", "Bremsenservice", "Ölwechsel"],
        "technological",
    )


def _restaurant() -> tuple[dict, dict]:
    return _brief(
        "restaurant",
        "Restaurant Alt Berlin",
        "Regionale Küche, saisonale Speisekarte und Reservierung.",
        ["Mittagstisch", "Abendkarte", "Weinbar"],
        "warm",
    )


def test_valid_spec_passes_contract_gate():
    iv, contacts = _auto()
    spec = build_website_design_spec(
        contacts=contacts,
        client_legal={"city": "Berlin"},
        niche_id="auto",
        package_id="business",
        market_code="DE",
        interview=iv,
    )
    gate = validate_website_design_spec(spec)
    assert gate["ok"] is True
    assert gate["status"] == "OK"
    assert spec["schema"] == SCHEMA
    contract = builder_contract_from_spec(spec)
    assert contract["ok"] is True
    assert contract["renderer_strategy"] == "craftsman"
    assert "werkstatt" in contract["section_plan"]


def test_invalid_spec_is_reject_not_improvised():
    bad = {
        "schema": SCHEMA,
        "version_id": "V1",
        "niche_id": "auto",
        "industry_family": "automotive",
        "package_id": "business",
        "market_code": "DE",
        "html": "<html>forbidden</html>",
    }
    gate = validate_website_design_spec(bad)
    assert gate["ok"] is False
    assert gate["status"] == "REJECT"
    assert any(e.startswith("required:") for e in gate["errors"])
    assert "forbidden:html" in gate["errors"]

    qa = run_premium_site_qa(
        html="<html><body>" + ("x" * 500) + "</body></html>",
        meta={},
        niche_id="auto",
        design_spec=bad,
    )
    assert qa["verdict"] == "REJECT"
    assert any(str(x).startswith("design_spec:") for x in qa["hard_failures"])


def test_director_patch_only_allowed_fields_and_bumps_version():
    iv, contacts = _auto()
    v1 = freeze_website_design_spec(
        build_website_design_spec(
            contacts=contacts,
            niche_id="auto",
            package_id="business",
            market_code="DE",
            interview=iv,
        )
    )
    v1_fp = spec_contract_fingerprint(v1)

    rejected = apply_director_config_patch(
        v1,
        {
            "niche_id": "restaurant",
            "html": "<script>alert(1)</script>",
            "section_plan": ["hero", "services", "contact"],
        },
    )
    assert rejected["ok"] is False
    assert rejected["status"] == "REJECT"
    assert any(
        e.startswith("immutable:") or e.startswith("forbidden:")
        for e in rejected["errors"]
    )

    ok = apply_director_config_patch(
        v1,
        {
            "style_hint": "editorial",
            "cta_primary": "Jetzt anrufen",
            "section_plan": [
                "hero",
                "services",
                "werkstatt",
                "trust",
                "faq",
                "contact",
            ],
            "hero_profile": {"hero_mode": "cinematic", "hero_focus": "service"},
        },
    )
    assert ok["ok"] is True
    v2 = ok["spec"]
    assert v2 is not None
    assert v2["version_id"] == "V2"
    assert v2["parent_version_id"] == "V1"
    assert v2["cta_primary"] == "Jetzt anrufen"
    assert "faq" in v2["section_plan"]
    assert v2["design_dna_directive"]["style_hint"] == "editorial"
    assert v1["version_id"] == "V1"
    assert v1["immutable"] is True
    assert spec_contract_fingerprint(v1) == v1_fp
    assert v2["contract_fingerprint"] != v1_fp


def test_determinism_same_spec_same_builder_contract():
    iv, contacts = _auto()
    a = build_website_design_spec(
        contacts=contacts,
        niche_id="auto",
        package_id="business",
        market_code="DE",
        interview=iv,
    )
    b = build_website_design_spec(
        contacts=copy.deepcopy(contacts),
        niche_id="auto",
        package_id="business",
        market_code="DE",
        interview=copy.deepcopy(iv),
    )
    assert spec_contract_fingerprint(a) == spec_contract_fingerprint(b)
    ca = builder_contract_from_spec(a)
    cb = builder_contract_from_spec(b)
    for key in (
        "niche_id",
        "industry_family",
        "renderer_strategy",
        "cta_primary",
        "section_plan",
        "hero_profile",
        "style_hint",
        "business_name",
        "city",
        "services",
        "contract_fingerprint",
    ):
        assert ca[key] == cb[key], key


def test_automotive_restaurant_dna_remain_distinct():
    auto_iv, auto_c = _auto()
    rest_iv, rest_c = _restaurant()
    auto = build_website_design_spec(
        contacts=auto_c,
        niche_id="auto",
        package_id="business",
        market_code="DE",
        interview=auto_iv,
    )
    rest = build_website_design_spec(
        contacts=rest_c,
        niche_id="restaurant",
        package_id="business",
        market_code="DE",
        interview=rest_iv,
    )
    assert auto["industry_family"] != rest["industry_family"]
    assert auto["renderer_strategy"] != rest["renderer_strategy"]
    assert auto["section_plan"] != rest["section_plan"]
    assert auto["cta_primary"] != rest["cta_primary"]
    assert "werkstatt" in auto["section_plan"]
    assert "speisekarte" in rest["section_plan"]
    assert validate_website_design_spec(auto)["ok"]
    assert validate_website_design_spec(rest)["ok"]


def test_version_snapshot_files_are_immutable(tmp_path: Path):
    iv, contacts = _auto()
    v1 = freeze_website_design_spec(
        build_website_design_spec(
            contacts=contacts,
            niche_id="auto",
            package_id="business",
            market_code="DE",
            interview=iv,
        )
    )
    write_website_design_spec(tmp_path, v1)
    patched = apply_director_config_patch(v1, {"cta_primary": "Termin sichern"})
    assert patched["ok"]
    v2 = freeze_website_design_spec(patched["spec"])
    write_website_design_spec(tmp_path, v2)

    disk_v1 = read_website_design_spec_version(tmp_path, "V1")
    disk_v2 = read_website_design_spec_version(tmp_path, "V2")
    current = read_website_design_spec(tmp_path)
    assert disk_v1 is not None and disk_v1["version_id"] == "V1"
    assert disk_v1["cta_primary"] == v1["cta_primary"]
    assert disk_v2 is not None and disk_v2["version_id"] == "V2"
    assert disk_v2["cta_primary"] == "Termin sichern"
    assert current is not None and current["version_id"] == "V2"


def test_live_build_preserves_version_id_through_pipeline(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    iv, contacts = _auto()
    product = factory.build_landing(
        "Kfz Meisterbetrieb Berlin Werkstatt Inspektion Bremsen Service.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Schmidt",
            "street": "Werkstattstr. 1",
            "zip": "10115",
            "city": "Berlin",
            "email": "service@kfz-schmidt.de",
            "phone": "+49 30 9876543",
        },
        contacts=contacts,
    )
    product_dir = tmp_path / "sandbox" / product["product_id"]
    spec = read_website_design_spec(product_dir)
    assert spec is not None
    assert spec["version_id"] == "V1"
    assert (product_dir / "website_design_spec.V1.json").is_file()
    meta_path = product_dir / "meta.json"
    assert meta_path.is_file()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("owner_version_id") == "V1"
    assert meta.get("website_design_spec", {}).get("version_id") == "V1"
    assert meta.get("premium_qa_verdict") in (
        "REJECT",
        "IMPROVE",
        "READY_FOR_REVIEW",
    )
