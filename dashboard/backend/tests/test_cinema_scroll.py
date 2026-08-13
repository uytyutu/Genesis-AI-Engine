"""Cinema scroll helper — anti-jank contract."""

from __future__ import annotations

from app.factory.cinema_scroll import cinema_scroll_script


def test_cinema_scroll_script_uses_raf_and_transform():
    js = cinema_scroll_script(copies_js='["a","b"]')
    assert "requestAnimationFrame" in js
    assert "scaleX" in js
    assert "style.width" not in js
    assert "passive:true" in js
    assert "classList.remove('is-on')" in js
