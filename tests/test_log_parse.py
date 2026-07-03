"""Frontend log headline parsing."""

from launcher.log_parse import extract_frontend_error


def test_next_build_error_not_mislabeled_as_frontend_folder(monkeypatch, tmp_path):
    log_dir = tmp_path / "launcher" / "logs"
    log_dir.mkdir(parents=True)
    fe_log = log_dir / "frontend.log"
    fe_log.write_text(
        "⨯ [Error: Cannot find module "
        "'D:\\\\Games\\\\Genesis-AI-Engine\\\\dashboard\\\\frontend\\\\.next\\\\server\\\\pages\\\\_document.js'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("launcher.log_parse.log_dir", lambda root=None: log_dir)

    headline, _ = extract_frontend_error(None)
    assert "Модуль не найден" not in headline or ".next" in headline
    assert "сбор" in headline.lower() or "build" in headline.lower() or "поврежден" in headline.lower()
