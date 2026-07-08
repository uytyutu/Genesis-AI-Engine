"""First-run onboarding — owner company setup."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

import customtkinter as ctk

from launcher.config import LauncherConfig
from launcher.deps import check_dependencies, ensure_frontend_ready, install_backend_deps
from launcher.processes import launch_genesis, wait_until_ready


class OnboardingWizard(ctk.CTkToplevel):
    def __init__(self, master, config: LauncherConfig) -> None:
        super().__init__(master)
        self.master_app = master
        self.config = config
        self.title("Добро пожаловать в Virtus Core")
        self.geometry("520x520")
        self.resizable(False, False)
        self.grab_set()

        self.step = 0
        self._goal_vars: dict[str, ctk.BooleanVar] = {}
        self._product_vars: dict[str, ctk.BooleanVar] = {}

        self.heading = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.heading.pack(pady=(20, 8))

        self.body = ctk.CTkTextbox(self, width=460, height=160)
        self.body.pack(padx=24, pady=4)

        self.form = ctk.CTkFrame(self, fg_color="transparent")
        self.form.pack(padx=24, pady=4, fill="x")

        self.name_entry = ctk.CTkEntry(self.form, width=280, placeholder_text="Ваше имя")
        self.name_entry.insert(0, config.owner_name)

        self.action_btn = ctk.CTkButton(self, text="Начать", command=self._next)
        self.action_btn.pack(pady=12)

        self._render_step()

    def _clear_form(self) -> None:
        for child in self.form.winfo_children():
            child.destroy()

    def _render_step(self) -> None:
        self.heading.configure(text="")
        self.body.delete("1.0", "end")
        self._clear_form()
        self.name_entry.pack_forget()
        self.action_btn.configure(state="normal", command=self._next, text="Далее")

        if self.step == 0:
            self.heading.configure(text="Добро пожаловать")
            self.body.insert(
                "1.0",
                "Я Vector.\n\nДавайте создадим вашу первую цифровую компанию.\n"
                "Всё настроим за пару минут — без терминала.",
            )
            self.action_btn.configure(text="Начать")
        elif self.step == 1:
            self.heading.configure(text="Как вас зовут?")
            self.name_entry.pack(pady=8)
        elif self.step == 2:
            self.heading.configure(text="Какая цель?")
            for key, label in (
                ("earnings", "Заработок"),
                ("learning", "Обучение"),
                ("development", "Разработка"),
            ):
                var = ctk.BooleanVar(value=key in self.config.goals)
                self._goal_vars[key] = var
                ctk.CTkCheckBox(self.form, text=label, variable=var).pack(anchor="w", pady=4)
        elif self.step == 3:
            self.heading.configure(text="Какие продукты создавать?")
            for key, label in (
                ("landing", "Landing"),
                ("shop", "Интернет-магазины"),
                ("telegram", "Telegram-боты"),
                ("saas", "SaaS"),
            ):
                var = ctk.BooleanVar(value=key in self.config.product_interests)
                self._product_vars[key] = var
                ctk.CTkCheckBox(self.form, text=label, variable=var).pack(anchor="w", pady=4)
        elif self.step == 4:
            self.heading.configure(text="Проверяем компьютер")
            deps = check_dependencies()
            self.body.insert(
                "1.0",
                f"Python: {'✔' if deps.python_ok else '✘'}\n"
                f"Node.js: {'✔' if deps.node_ok else '✘'}\n"
                f"Virtus Core подготовит всё автоматически.",
            )
        elif self.step == 5:
            self.heading.configure(text="Установка")
            self.body.insert("1.0", "Устанавливаем зависимости…")
            self.action_btn.configure(state="disabled")
            threading.Thread(target=self._install_deps, daemon=True).start()
        elif self.step == 6:
            self.heading.configure(text="Запуск Virtus Core")
            self.body.insert("1.0", "Запускаем систему…")
            self.action_btn.configure(state="disabled")
            threading.Thread(target=self._start_genesis, daemon=True).start()
        elif self.step == 7:
            self._save_profile()
            self.heading.configure(text="Готово!")
            self.body.insert(
                "1.0",
                f"Добро пожаловать, {self.config.owner_name}!\n\n"
                "Vector знает, кто вы — и готов к работе.\n"
                "Нажмите «Запустить Virtus Core» в главном окне.",
            )
            self.action_btn.configure(text="Закрыть", command=self.destroy)

    def _save_profile(self) -> None:
        self.config.owner_name = self.name_entry.get().strip() or "Владелец"
        self.config.goals = [k for k, v in self._goal_vars.items() if v.get()]
        self.config.product_interests = [k for k, v in self._product_vars.items() if v.get()]
        if not self.config.goals:
            self.config.goals = ["earnings"]
        if not self.config.product_interests:
            self.config.product_interests = ["landing"]
        if not self.config.company_founded_at:
            self.config.company_founded_at = datetime.now(timezone.utc).isoformat()
        self.config.first_run_complete = True
        self.config.save()

    def _next(self) -> None:
        if self.step == 1:
            self.config.owner_name = self.name_entry.get().strip() or "Владелец"
        if self.step < 7:
            if self.step == 4:
                self.step = 5
            elif self.step == 5 or self.step == 6:
                return
            else:
                self.step += 1
            self._render_step()

    def _install_deps(self) -> None:
        ok, msg = install_backend_deps()
        deps = check_dependencies()
        if deps.node_ok:
            ok2, _ = ensure_frontend_ready()
            ok = ok and ok2

        def finish() -> None:
            self.body.delete("1.0", "end")
            self.body.insert("1.0", "Зависимости готовы." if ok else "Частичная установка — продолжаем.")
            self.step = 6
            self._render_step()

        self.after(0, finish)

    def _start_genesis(self) -> None:
        ok, msg = launch_genesis(self.master_app.managed, install_deps=False)
        ready = wait_until_ready() if ok else False

        def finish() -> None:
            self.body.delete("1.0", "end")
            self.body.insert("1.0", "Система запущена." if ready else msg)
            self.step = 7
            self._render_step()
            self.master_app.refresh_status()

        self.after(0, finish)
