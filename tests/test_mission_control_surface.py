from __future__ import annotations

from launcher.mission_control_surface import (
    SURFACE_BROWSER,
    SURFACE_DESKTOP,
    open_mission_control,
    register_desktop_shell,
    resolve_surface_mode,
)


def test_open_mission_control_browser_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "launcher.mission_control_surface.webbrowser.open",
        lambda url, new=2: True,
    )
    ok, err = open_mission_control("http://localhost:3000", surface=SURFACE_BROWSER)
    assert ok is True
    assert err == ""


def test_desktop_without_host_falls_back_to_browser(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "launcher.mission_control_surface.webbrowser.open",
        lambda url, new=2: calls.append(url) or True,
    )
    ok, err = open_mission_control("http://localhost:3000", surface=SURFACE_DESKTOP)
    assert ok is True
    assert err == ""
    assert calls == ["http://localhost:3000"]


def test_desktop_with_registered_host(monkeypatch) -> None:
    monkeypatch.setattr(
        "launcher.mission_control_surface.webbrowser.open",
        lambda url, new=2: (_ for _ in ()).throw(AssertionError("browser should not run")),
    )

    register_desktop_shell(lambda url: url.endswith(":3000"))
    ok, err = open_mission_control("http://localhost:3000", surface=SURFACE_DESKTOP)
    assert ok is True
    assert err == ""


def test_resolve_surface_mode_env(monkeypatch) -> None:
    monkeypatch.setenv("GENESIS_MC_SURFACE", "desktop")
    assert resolve_surface_mode() == SURFACE_DESKTOP
