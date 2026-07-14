"""Modal dialogs — always visible on top (CEO must never see a frozen launcher)."""

from __future__ import annotations


def arm_modal(dialog, master) -> None:
    """Center on parent, raise above main window, grab focus."""
    try:
        dialog.transient(master)
    except Exception:
        pass
    dialog.update_idletasks()
    try:
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = max(master.winfo_width(), 420)
        mh = max(master.winfo_height(), 320)
        dw = max(dialog.winfo_width(), 480)
        dh = max(dialog.winfo_height(), 280)
        x = mx + max(0, (mw - dw) // 2)
        y = my + max(0, (mh - dh) // 2)
        dialog.geometry(f"+{x}+{y}")
    except Exception:
        pass
    try:
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after(120, lambda: dialog.attributes("-topmost", False))
        dialog.focus_force()
    except Exception:
        pass
