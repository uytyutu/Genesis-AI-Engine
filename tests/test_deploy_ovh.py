"""deploy_ovh.sh must target the live OVH git checkout path."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "deploy_ovh.sh"
OVH_DEFAULT_REMOTE = "/home/ubuntu/Genesis-AI-Engine"


def test_deploy_ovh_default_remote_path() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert f'GENESIS_OVH_REMOTE_PATH:-{OVH_DEFAULT_REMOTE}' in text
    assert "/srv/genesis" not in text


def test_deploy_ovh_runs_compose_from_deploy_subdir() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'cd "$REMOTE"' in text
    assert "cd deploy" in text
    assert "docker compose up -d --build" in text
