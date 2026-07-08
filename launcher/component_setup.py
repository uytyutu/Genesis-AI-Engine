"""Owner-facing dialogs for missing Python / Node.js."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

from launcher.component_install import install_component, open_component_site
from launcher.deps import check_dependencies, find_node, find_npm
from launcher.python_runtime import resolve_backend_python
from launcher.log_util import append_log
from launcher.paths import log_dir

_COMPONENTS = {
    "python": {
        "title": "Python 3.12",
        "reason": "Backend Virtus Core и Mission Control API работают на Python.",
    },
    "node": {
        "title": "Node.js LTS",
        "reason": "Mission Control использует современный веб-интерфейс (Next.js).",
    },
}


class MissingComponentDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        component: str,
        root: Path | None,
        on_done: Callable[[bool], None],
    ) -> None:
        super().__init__(master)
        meta = _COMPONENTS[component]
        self.component = component
        self._root = root
        self._on_done = on_done
        self._busy = False

        self.title("Необходим компонент")
        self.geometry("480x340")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Необходим компонент",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a78bfa",
        ).pack(pady=(22, 4))

        ctk.CTkLabel(self, text=meta["title"], font=ctk.CTkFont(size=22, weight="bold")).pack()

        ctk.CTkLabel(self, text="Причина:", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=28, pady=(18, 4)
        )
        ctk.CTkLabel(
            self,
            text=meta["reason"],
            wraplength=400,
            justify="left",
            text_color="#9ca3af",
        ).pack(anchor="w", padx=28)

        self.status = ctk.CTkLabel(self, text="", wraplength=400, text_color="#eab308")
        self.status.pack(pady=12)

        self.install_btn = ctk.CTkButton(
            self,
            text="Установить автоматически",
            height=42,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._install,
        )
        self.install_btn.pack(fill="x", padx=28, pady=(4, 6))

        ctk.CTkButton(
            self,
            text="Открыть официальный сайт",
            height=38,
            fg_color="#374151",
            hover_color="#4b5563",
            command=lambda: open_component_site(self.component),
        ).pack(fill="x", padx=28, pady=4)

        ctk.CTkButton(
            self,
            text="Продолжить после установки",
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color="#4b5563",
            command=self._recheck,
        ).pack(fill="x", padx=28, pady=(8, 16))

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _install(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.install_btn.configure(state="disabled")
        self._set_status("Установка… Это может занять несколько минут.")

        def work() -> None:
            ok, msg = install_component(self.component, log_dir=log_dir(self._root))
            append_log(f"Component install {self.component}: {msg}")

            def finish() -> None:
                self._busy = False
                self.install_btn.configure(state="normal")
                if ok:
                    self._set_status("Готово. Проверяем…")
                    self._recheck()
                else:
                    self._set_status(msg)

            self.after(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def _recheck(self) -> None:
        if self.component == "python" and resolve_backend_python():
            self.destroy()
            self._on_done(True)
            return
        if self.component == "node" and find_node() and find_npm():
            self.destroy()
            self._on_done(True)
            return
        self._set_status("Компонент ещё не найден. Завершите установку и нажмите «Продолжить».")


def ensure_launcher_components(master, root: Path | None, on_ready: Callable[[], None]) -> None:
    """Show install UI for missing Python/Node, then call on_ready."""

    def step_python() -> None:
        if resolve_backend_python():
            step_node()
            return

        def on_python(ok: bool) -> None:
            if ok:
                step_node()

        MissingComponentDialog(master, "python", root, on_python)

    def step_node() -> None:
        deps = check_dependencies(root)
        if deps.node_ok and deps.npm_ok:
            on_ready()
            return

        def on_node(ok: bool) -> None:
            if ok:
                on_ready()

        MissingComponentDialog(master, "node", root, on_node)

    step_python()
