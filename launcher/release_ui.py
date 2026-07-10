"""Launcher UI — Stable Release activate, history, rollback."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from launcher.branding import (
    BRAND_NAME,
    GENESIS_ACCENT,
    GENESIS_ACCENT_HOVER,
    GENESIS_AMBER,
    GENESIS_BG,
    GENESIS_MUTED,
    GENESIS_PANEL,
    GENESIS_TEXT,
    apply_window_icon,
)
from launcher.stable_release import (
    activate_stable_release,
    compute_release_status,
    format_history_lines,
    format_release_info_lines,
    read_git_commit_short,
    rollback_to_previous_release,
)


class ActivateReleaseDialog(ctk.CTkToplevel):
    """CEO PASS → Release notes → Activate Stable Release."""

    def __init__(self, master, root, *, owner_name: str = "CEO") -> None:
        super().__init__(master)
        self._root = root
        self.result: tuple[bool, str] = (False, "")
        self.title(f"{BRAND_NAME} — Activate Stable Release")
        self.geometry("520x480")
        apply_window_icon(self)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Активировать стабильный релиз",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(16, 4))
        ctk.CTkLabel(
            self,
            text=f"Git: {read_git_commit_short(root) or '—'} · после CEO PASS",
            text_color=GENESIS_MUTED,
        ).pack(pady=(0, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24)

        ctk.CTkLabel(form, text="Дата релиза (label)", anchor="w").pack(fill="x")
        self.label_entry = ctk.CTkEntry(form, width=400)
        self.label_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Название / Product Block", anchor="w").pack(fill="x")
        self.title_entry = ctk.CTkEntry(form, width=400, placeholder_text="Project Platform v1")
        self.title_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Product Blocks (через запятую)", anchor="w").pack(fill="x")
        self.blocks_entry = ctk.CTkEntry(
            form,
            width=400,
            placeholder_text="Project Platform, Legal & Trust",
        )
        self.blocks_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Утвердил", anchor="w").pack(fill="x")
        self.approved_entry = ctk.CTkEntry(form, width=400)
        self.approved_entry.pack(fill="x", pady=(0, 8))
        self.approved_entry.insert(0, f"{owner_name} · CEO PASS")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(
            actions,
            text="Activate Stable Release",
            fg_color=GENESIS_ACCENT,
            hover_color=GENESIS_ACCENT_HOVER,
            command=self._confirm,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Отмена", command=self.destroy).pack(side="right")

    def _confirm(self) -> None:
        blocks_raw = self.blocks_entry.get().strip()
        blocks = [b.strip() for b in blocks_raw.split(",") if b.strip()]
        title = self.title_entry.get().strip()
        if not title and blocks:
            title = blocks[0]
        ok, msg = activate_stable_release(
            self._root,
            label=self.label_entry.get().strip() or None,
            title=title,
            product_blocks=blocks,
            approved_by=self.approved_entry.get().strip() or "CEO PASS",
        )
        self.result = (ok, msg)
        if ok:
            self.destroy()
        else:
            messagebox.showerror(BRAND_NAME, msg)

    @classmethod
    def run(cls, master, root, *, owner_name: str = "CEO") -> tuple[bool, str]:
        dialog = cls(master, root, owner_name=owner_name)
        master.wait_window(dialog)
        return dialog.result


class ReleaseHistoryDialog(ctk.CTkToplevel):
    def __init__(self, master, root) -> None:
        super().__init__(master)
        self.title(f"{BRAND_NAME} — Release History")
        self.geometry("480x360")
        apply_window_icon(self)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="История Stable Release",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(16, 8))

        box = ctk.CTkTextbox(self, width=440, height=240, font=ctk.CTkFont(size=12))
        box.pack(padx=16, pady=8)
        lines = format_history_lines(root, limit=12)
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")

        ctk.CTkButton(self, text="Закрыть", command=self.destroy).pack(pady=12)


def refresh_release_panel(panel: ctk.CTkTextbox, root) -> None:
    lines = format_release_info_lines(root)
    panel.configure(state="normal")
    panel.delete("1.0", "end")
    panel.insert("1.0", "\n".join(lines))
    panel.configure(state="disabled")
