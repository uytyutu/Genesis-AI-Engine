"""Backend must import — release / Launcher gate."""

from __future__ import annotations


def test_backend_import_app() -> None:
    from app.main import app

    assert app is not None
    title = getattr(app, "title", "") or ""
    assert "Virtus" in title or title
