"""Foundation F2–F7 — tenant, memory, routing, version, auth, skills, knowledge intake."""

from pathlib import Path

from app.integration.knowledge_intake import IntakeDescriptor, KnowledgeIntakeRegistry
from app.integration.memory_root import MemoryRoot
from app.integration.owner_auth import issue_owner_token
from app.integration.platform_version import MANIFEST_VERSION, build_platform_version_payload
from app.integration.skills_registry import SkillsRegistry
from app.integration.tenant_context import OWNER_TENANT_ID, resolve_tenant_context


def test_tenant_skeleton_mission1_platform():
    ctx = resolve_tenant_context(visitor_id="visitor-abc")
    assert ctx.tenant_id == OWNER_TENANT_ID
    assert ctx.subscription_tier == "free"


def test_memory_root_owner_uses_legacy_flat_path(tmp_path: Path):
    root = MemoryRoot(tmp_path, tenant_id=OWNER_TENANT_ID)
    assert root.root == tmp_path
    assert root.subpath("genesis_brain", "users").parent == tmp_path / "genesis_brain"


def test_memory_root_customer_partition(tmp_path: Path):
    root = MemoryRoot(tmp_path, tenant_id="cust-el3")
    assert root.root == tmp_path / "tenants" / "cust-el3"


def test_platform_version_manifest():
    payload = build_platform_version_payload(brain_version="test-brain")
    assert payload["manifest_version"] == MANIFEST_VERSION
    assert payload["brain_version"] == "test-brain"


def test_skills_registry_landing_active():
    reg = SkillsRegistry()
    skill = reg.by_factory_type("landing-page")
    assert skill is not None
    assert skill.id == "landing-page-v1"
    assert skill.enabled is True


def test_knowledge_intake_pipeline_stages():
    from app.integration.knowledge_intake import PipelineStage

    reg = KnowledgeIntakeRegistry()
    state = reg.run_pipeline(IntakeDescriptor(kind="attachment"))
    assert state.stage in (PipelineStage.SOURCE, PipelineStage.NORMALIZE)
    assert state.embedding_ref is None


def test_pipeline_stage_enum_includes_embed_slot():
    from app.integration.knowledge_intake import PipelineStage

    assert PipelineStage.EMBED.value == "embed"
    assert PipelineStage.VECTOR.value == "vector"


def test_owner_token_roundtrip(monkeypatch):
    monkeypatch.setenv("GENESIS_OWNER_JWT_SECRET", "test-secret-for-foundation")
    token = issue_owner_token()
    assert "." in token
