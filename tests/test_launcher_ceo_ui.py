"""CEO Launcher UI — build stamp and primary action."""


def test_start_button_at_top_with_play_glyph():
    src = open("launcher/app.py", encoding="utf-8").read()
    status_idx = src.index("self.status_label.pack")
    start_idx = src.index('text="▶ Запустить Genesis"')
    scroll_idx = src.index("self.scroll = ctk.CTkScrollableFrame")
    assert start_idx < scroll_idx, "▶ button must appear before metrics scroll"
    assert status_idx < start_idx, "▶ button must follow status label"


def test_build_info_module():
    from launcher import build_info

    assert "build" in build_info.BUILD_ID or "dev" in build_info.BUILD_ID
