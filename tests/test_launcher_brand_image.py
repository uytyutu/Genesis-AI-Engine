"""Regression: launcher brand image must be PIL.Image for CTkImage."""

from __future__ import annotations

from launcher.branding import load_mark_pil_image


def test_load_mark_pil_image_returns_pil_not_path():
    from PIL import Image

    img = load_mark_pil_image()
    assert img is not None, "genesis-icon.png missing"
    assert isinstance(img, Image.Image)


def test_ctkimage_constructor_accepts_pil_image():
    """CTkImage rejects str paths — regression for 2026-07-04 launch crash."""
    import customtkinter as ctk

    img = load_mark_pil_image()
    assert img is not None
    ctk.CTkImage(light_image=img, dark_image=img, size=(52, 52))
