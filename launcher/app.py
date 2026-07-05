"""Genesis Launcher — CEO mode for business owners."""

from __future__ import annotations

import os
import threading
import time
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

from launcher import build_info
from launcher.branding import (
  GENESIS_ACCENT,
  GENESIS_ACCENT_HOVER,
  GENESIS_AMBER,
  GENESIS_BG,
  GENESIS_ELEVATED,
  GENESIS_GREEN,
  GENESIS_GREEN_HOVER,
  GENESIS_MUTED,
  GENESIS_PANEL,
  GENESIS_ROSE,
  GENESIS_TEXT,
  apply_window_icon,
  load_mark_pil_image,
)
from launcher.desktop_identity import ensure_desktop_identity_async

from launcher.config import LauncherConfig
from launcher.deps import ensure_frontend_ready
from launcher.startup_stages import repair_staged
from launcher.frontend_repair import failure_headline, repair_frontend
from launcher.health import (
  COMMAND_CENTER_URL,
  overall_label,
  owner_ready_live,
)
from launcher.log_parse import frontend_log_path
from launcher.log_util import append_log, read_log
from launcher.dogfooding import (
  begin_launch_session,
  format_dogfooding_report,
  record_browser_open,
  record_launch_failure,
  record_launch_success,
  record_launcher_open,
)
from launcher.mission_control_surface import open_mission_control, resolve_surface_mode
from launcher.component_setup import ensure_launcher_components
from launcher import paths
from launcher.status_worker import StatusSnapshot, gather_status
from launcher.processes import (
  ManagedProcesses,
  reconnect_managed,
  stop_all,
)
from launcher.runtime_boot import (
  BootResult,
  format_boot_failure_message,
  run_runtime_boot,
  write_boot_report,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PYTHON_URL = "https://www.python.org/downloads/"
NODE_URL = "https://nodejs.org/"
BASE_URL = COMMAND_CENTER_URL.rstrip("/")
CREATE_URL = f"{BASE_URL}/create"


class SettingsDialog(ctk.CTkToplevel):
  def __init__(self, master: "GenesisLauncher", config: LauncherConfig) -> None:
    super().__init__(master)
    self.config = config
    self.title("Настройки")
    self.geometry("400x280")
    apply_window_icon(self)
    self.grab_set()

    ctk.CTkLabel(self, text="Ваше имя").pack(pady=(20, 4))
    self.name = ctk.CTkEntry(self, width=280)
    self.name.pack()
    self.name.insert(0, config.owner_name)

    self.auto_browser = ctk.CTkCheckBox(self, text="Открывать браузер при запуске")
    self.auto_browser.pack(pady=16)
    if config.auto_open_browser:
      self.auto_browser.select()

    ctk.CTkButton(self, text="Сохранить", command=self._save).pack(pady=8)

  def _save(self) -> None:
    self.config.owner_name = self.name.get().strip() or "Владелец"
    self.config.auto_open_browser = bool(self.auto_browser.get())
    self.config.save()
    self.destroy()


class LogDialog(ctk.CTkToplevel):
  def __init__(self, master: "GenesisLauncher") -> None:
    super().__init__(master)
    self.title("Журнал Genesis")
    self.geometry("640x420")
    text = ctk.CTkTextbox(self, width=600, height=360)
    text.pack(padx=16, pady=16)
    content = read_log()
    backend_log = paths.log_dir() / "backend.log"
    if backend_log.exists():
      content += "\n\n--- Backend ---\n"
      content += backend_log.read_text(encoding="utf-8", errors="replace")[-4000:]
    frontend_log = paths.log_dir() / "frontend.log"
    if frontend_log.exists():
      content += "\n\n--- Frontend ---\n"
      content += frontend_log.read_text(encoding="utf-8", errors="replace")[-8000:]
    text.insert("1.0", content)
    text.configure(state="disabled")


class FrontendErrorDialog(ctk.CTkToplevel):
  def __init__(self, master: "GenesisLauncher", message: str, project_root) -> None:
    super().__init__(master)
    self.title("Genesis — ошибка Frontend")
    self.geometry("560x480")
    self.grab_set()

    ctk.CTkLabel(
      self,
      text="Genesis не запустился",
      font=ctk.CTkFont(size=16, weight="bold"),
      text_color="#f87171",
    ).pack(pady=(16, 8))

    box = ctk.CTkTextbox(self, width=520, height=320, font=ctk.CTkFont(size=12))
    box.pack(padx=16, pady=8)
    box.insert("1.0", message)
    box.configure(state="disabled")

    actions = ctk.CTkFrame(self, fg_color="transparent")
    actions.pack(fill="x", padx=16, pady=(0, 16))

    def open_log() -> None:
      log_path = frontend_log_path(project_root)
      if log_path.exists():
        os.startfile(str(log_path))  # type: ignore[attr-defined]
      else:
        messagebox.showinfo("Genesis", f"Файл не найден:\n{log_path}")

    ctk.CTkButton(
      actions,
      text="Открыть frontend.log",
      fg_color="#374151",
      hover_color="#4b5563",
      command=open_log,
    ).pack(side="left", padx=(0, 8))
    ctk.CTkButton(actions, text="Закрыть", command=self.destroy).pack(side="right")


class BootFailureDialog(ctk.CTkToplevel):
  def __init__(self, master: "GenesisLauncher", result: BootResult) -> None:
    super().__init__(master)
    self.result = result
    self.title("Genesis — не удалось запуститься")
    self.geometry("560x520")
    self.grab_set()

    ctk.CTkLabel(
      self,
      text="Genesis не смог открыть рабочее пространство",
      font=ctk.CTkFont(size=16, weight="bold"),
      text_color="#f87171",
    ).pack(pady=(16, 8))

    box = ctk.CTkTextbox(self, width=520, height=340, font=ctk.CTkFont(size=12))
    box.pack(padx=16, pady=8)
    box.insert("1.0", format_boot_failure_message(result))
    box.configure(state="disabled")

    actions = ctk.CTkFrame(self, fg_color="transparent")
    actions.pack(fill="x", padx=16, pady=(0, 16))

    ctk.CTkButton(
      actions,
      text="Сообщить о проблеме",
      fg_color=GENESIS_ACCENT,
      hover_color=GENESIS_ACCENT_HOVER,
      command=self._report,
    ).pack(side="left", padx=(0, 8))
    ctk.CTkButton(actions, text="Закрыть", command=self.destroy).pack(side="right")

  def _report(self) -> None:
    write_boot_report(self.result, self.master._project_root)
    LogDialog(self.master)


def _show_boot_failure(master: "GenesisLauncher", result: BootResult) -> None:
  BootFailureDialog(master, result)


def _show_error(master: "GenesisLauncher", message: str) -> None:
  FrontendErrorDialog(master, message, master._project_root)


class GenesisLauncher(ctk.CTk):
  def __init__(self) -> None:
    super().__init__()
    self.title("Genesis")
    self.geometry("460x780")
    self.minsize(420, 720)
    self.configure(fg_color=GENESIS_BG)
    apply_window_icon(self)
    self._brand_image: ctk.CTkImage | None = None
    self.managed = ManagedProcesses()
    self.config = LauncherConfig.load()
    self._busy = False
    self._dev_open = False
    self._status_busy = False
    self._launch_session_id = ""
    self._launch_started_at = 0.0
    self._last_snapshot: StatusSnapshot | None = None
    self._last_error = ""
    self._launch_attempted = False
    # NEVER use self._root — shadows tkinter.Misc._root() and breaks focus/widgets.
    self._project_root = paths.find_project_root()
    ok_layout, layout_msg = paths.validate_layout(self._project_root)
    if not ok_layout:
      self._last_error = layout_msg
    elif not self.config.project_root:
      self.config.project_root = str(self._project_root.resolve())
      self.config.save()

    ensure_desktop_identity_async(self._project_root)

    self._build_ui()
    self.after(500, self.refresh_status)
    self.after(900, self._ensure_components_and_bootstrap)
    self.protocol("WM_DELETE_WINDOW", self._on_exit)

    if not self.config.first_run_complete:
      self.after(300, lambda: OnboardingWizard(self, self.config))

    append_log("Genesis OS opened")
    record_launcher_open(root=self._project_root)

  def _build_ui(self) -> None:
    pad = {"padx": 20, "pady": 6}

    header = ctk.CTkFrame(self, fg_color="transparent")
    header.pack(fill="x", padx=20, pady=(16, 0))

    mark_img = load_mark_pil_image()
    if mark_img is not None:
      self._brand_image = ctk.CTkImage(
        light_image=mark_img,
        dark_image=mark_img,
        size=(52, 52),
      )
      ctk.CTkLabel(header, image=self._brand_image, text="").pack(side="left")

    brand_text = ctk.CTkFrame(header, fg_color="transparent")
    brand_text.pack(side="left", padx=(12, 0))
    ctk.CTkLabel(
      brand_text,
      text="Genesis",
      font=ctk.CTkFont(size=26, weight="bold"),
      text_color=GENESIS_TEXT,
    ).pack(anchor="w")
    ctk.CTkLabel(
      brand_text,
      text="Company OS",
      font=ctk.CTkFont(size=11),
      text_color=GENESIS_MUTED,
    ).pack(anchor="w")

    self.greeting_label = ctk.CTkLabel(
      self,
      text=f"Доброе утро, {self.config.owner_name}",
      text_color=GENESIS_MUTED,
      font=ctk.CTkFont(size=14),
    )
    self.greeting_label.pack(pady=(8, 4))

    self.status_label = ctk.CTkLabel(
      self,
      text="⚪ Genesis остановлен",
      font=ctk.CTkFont(size=18, weight="bold"),
      text_color=GENESIS_MUTED,
    )
    self.status_label.pack(pady=(4, 8))

    actions = ctk.CTkFrame(self, fg_color="transparent")
    actions.pack(fill="x", **pad)

    self.start_btn = ctk.CTkButton(
      actions,
      text="▶ Открыть Mission Control",
      height=48,
      font=ctk.CTkFont(size=15, weight="bold"),
      fg_color=GENESIS_GREEN,
      hover_color=GENESIS_GREEN_HOVER,
      command=self._on_start,
    )
    self.start_btn.pack(fill="x", pady=(0, 6))

    self.install_btn = ctk.CTkButton(
      actions,
      text="Установить Mission Control",
      height=40,
      fg_color=GENESIS_ACCENT,
      hover_color=GENESIS_ACCENT_HOVER,
      command=self._on_install_frontend,
    )
    self.install_btn.pack(fill="x", pady=3)
    self.install_btn.pack_forget()

    self.fix_btn = ctk.CTkButton(
      actions,
      text="Исправить автоматически",
      height=40,
      fg_color=GENESIS_AMBER,
      hover_color="#d97706",
      command=self._on_auto_fix,
    )
    self.fix_btn.pack(fill="x", pady=3)
    self.fix_btn.pack_forget()

    self.scroll = ctk.CTkScrollableFrame(
      self, fg_color=GENESIS_PANEL, corner_radius=12, height=300, border_width=1, border_color=GENESIS_ELEVATED
    )
    self.scroll.pack(fill="both", expand=True, padx=20, pady=4)

    self.metric_labels: list[ctk.CTkLabel] = []
    for _ in range(7):
      lbl = ctk.CTkLabel(self.scroll, text="—", anchor="w", font=ctk.CTkFont(size=13))
      lbl.pack(fill="x", padx=12, pady=2)
      self.metric_labels.append(lbl)

    ctk.CTkLabel(
      self.scroll,
      text="Что произошло за ночь",
      font=ctk.CTkFont(size=13, weight="bold"),
      anchor="w",
    ).pack(fill="x", padx=12, pady=(12, 4))

    self.overnight_box = ctk.CTkTextbox(self.scroll, height=88, font=ctk.CTkFont(size=12))
    self.overnight_box.pack(fill="x", padx=12, pady=(0, 8))
    self.overnight_box.configure(state="disabled")

    ctk.CTkLabel(
      self.scroll,
      text="Требует вашего решения",
      font=ctk.CTkFont(size=13, weight="bold"),
      anchor="w",
    ).pack(fill="x", padx=12, pady=(4, 4))

    self.decisions_box = ctk.CTkTextbox(self.scroll, height=64, font=ctk.CTkFont(size=12))
    self.decisions_box.pack(fill="x", padx=12, pady=(0, 10))
    self.decisions_box.configure(state="disabled")

    nav = ctk.CTkFrame(self, fg_color="transparent")
    nav.pack(fill="x", **pad)
    nav_buttons = (
      ("🏢 Компания", "/company"),
      ("💰 Финансы", "/finance"),
      ("📦 Продукты", "/projects"),
      ("🤖 AI-команда", "/ai"),
      ("📈 Аналитика", "/growth"),
      ("⚙️ Разработчик", None),
    )
    for i, (label, href) in enumerate(nav_buttons):
      row, col = divmod(i, 2)
      if href:
        cmd = lambda h=href: webbrowser.open(f"{BASE_URL}{h}")
      else:
        cmd = self._toggle_dev
      btn = ctk.CTkButton(nav, text=label, height=36, command=cmd)
      btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
    nav.grid_columnconfigure(0, weight=1)
    nav.grid_columnconfigure(1, weight=1)

    secondary = ctk.CTkFrame(self, fg_color="transparent")
    secondary.pack(fill="x", **pad)

    ctk.CTkButton(
      secondary,
      text="Создать продукт",
      height=40,
      fg_color=GENESIS_ACCENT,
      hover_color=GENESIS_ACCENT_HOVER,
      command=self._open_create,
    ).pack(fill="x", pady=3)

    ctk.CTkButton(
      secondary,
      text="Открыть Genesis",
      height=38,
      fg_color=GENESIS_ELEVATED,
      hover_color=GENESIS_PANEL,
      border_width=1,
      border_color=GENESIS_ACCENT,
      command=self._open_dashboard,
    ).pack(fill="x", pady=3)

    self.stop_btn = ctk.CTkButton(
      secondary,
      text="Остановить систему",
      height=34,
      fg_color=GENESIS_ROSE,
      hover_color="#e11d48",
      command=self._on_stop,
    )
    self.stop_btn.pack(fill="x", pady=(6, 3))

    self.dev_frame = ctk.CTkFrame(self, fg_color=GENESIS_PANEL)
    self.dev_text = ctk.CTkTextbox(self.dev_frame, width=400, height=160, font=ctk.CTkFont(size=11))
    self.dev_text.pack(padx=8, pady=8)
    self.dev_text.configure(state="disabled")
    ctk.CTkButton(self.dev_frame, text="Журнал", command=lambda: LogDialog(self)).pack(pady=(0, 8))

    self.hint_label = ctk.CTkLabel(
      self, text="", wraplength=380, text_color=GENESIS_MUTED, font=ctk.CTkFont(size=11)
    )
    self.hint_label.pack(**pad)

    ctk.CTkLabel(
      self,
      text=f"Genesis · {build_info.BUILD_ID}",
      text_color="#52525b",
      font=ctk.CTkFont(size=11),
    ).pack(side="bottom", pady=6)

  def _toggle_dev(self) -> None:
    self._dev_open = not self._dev_open
    if self._dev_open:
      self.dev_frame.pack(fill="x", padx=20, pady=4)
    else:
      self.dev_frame.pack_forget()

  def _set_textbox(self, box: ctk.CTkTextbox, content: str) -> None:
    box.configure(state="normal")
    box.delete("1.0", "end")
    box.insert("1.0", content)
    box.configure(state="disabled")

  def _update_ceo_metrics(self, mc: dict | None, health_running: bool) -> None:
    if not mc:
      lines = [
        "💰 Доход сегодня:          —",
        "💰 Доход за месяц:         —",
        "💼 Активных проектов:      —",
        "🤖 AI сотрудников:         —",
        "📄 Продуктов создано:      —",
        "👥 Потенциальных клиентов: —",
        "⚙️ Система:                Запустите Genesis",
      ]
      self._set_textbox(self.overnight_box, "• Запустите Genesis для данных")
      self._set_textbox(self.decisions_box, "• —")
    else:
      journey = mc.get("first_customer_journey")
      if journey and not mc.get("demo_mode"):
        lines = [
          f"🎯 {journey.get('title', 'До первого клиента')}",
          f"   Прогресс: {journey.get('completed_count', 0)}/{journey.get('total_count', 0)}",
          "",
        ]
        for step in journey.get("steps", [])[:5]:
          mark = "☑" if step.get("done") else "☐"
          lines.append(f"   {mark} {step.get('label', '')}")
        lines.extend(
          [
            "",
            f"💼 Активных проектов:      {mc.get('active_projects', 0)}",
            f"🤖 AI сотрудников:         {mc.get('ai_employees_online', 0)} работают",
            f"⚙️ Система:                {mc.get('system_status_label', '—')}",
          ]
        )
      else:
        lines = [
          f"💰 Доход сегодня:          {mc.get('revenue_today_eur', 0):.0f} €",
          f"💰 Доход за месяц:         {mc.get('revenue_month_eur', 0):.0f} €",
          f"💼 Активных проектов:      {mc.get('active_projects', 0)}",
          f"🤖 AI сотрудников:         {mc.get('ai_employees_online', 0)} работают",
          f"📄 Продуктов создано:      {mc.get('products_count', 0)}",
          f"👥 Потенциальных клиентов: {mc.get('potential_clients', 0)}",
          f"⚙️ Система:                {mc.get('system_status_label', '—')}",
        ]
      self.greeting_label.configure(text=mc.get("greeting", f"Доброе утро, {self.config.owner_name}"))

      overnight = "\n".join(
        f"{e.get('icon', '•')} {e.get('message', '')}" for e in mc.get("overnight_events", [])
      )
      self._set_textbox(self.overnight_box, overnight or "• Пока без событий")

      decisions = mc.get("decisions_needed") or []
      if decisions:
        decision_text = "\n".join(f"• {d.get('label', '')}" for d in decisions)
      else:
        decision_text = "• Всё в порядке — решений не требуется"
      self._set_textbox(self.decisions_box, decision_text)

    for lbl, line in zip(self.metric_labels, lines):
      lbl.configure(text=line)

    if health_running and mc and mc.get("system_running"):
      self.status_label.configure(text="✔ Genesis полностью готов", text_color="#22c55e")
    elif mc and not mc.get("system_running"):
      self.status_label.configure(text="⚪ Остановлен", text_color="#9ca3af")

  def _apply_health_label(self, health) -> None:
    text, color = overall_label(health.overall, health.error_message)
    self.status_label.configure(text=text, text_color=color)
    if health.overall == "error":
      self._last_error = health.error_message or self._last_error
      self.hint_label.configure(text=health.error_message or self._last_error)
      self.fix_btn.pack(fill="x", pady=3, after=self.start_btn)
    elif health.overall == "running":
      self._last_error = ""
      self.fix_btn.pack_forget()
      self.hint_label.configure(text="Mission Control работает — можно закрыть пульт, Genesis останется в фоне")
    else:
      self.fix_btn.pack_forget()

  def _apply_status_snapshot(self, snapshot: StatusSnapshot) -> None:
    self._last_snapshot = snapshot
    health = snapshot.health
    mc = snapshot.mission_control

    if self.managed.backend and self.managed.backend.poll() is None and health.overall == "stopped":
      if mc is not None and health.frontend:
        health.overall = "running"
        health.error_message = ""
        self._last_error = ""

    self._apply_health_label(health)
    self._update_ceo_metrics(mc, health.overall == "running")

    if self._dev_open:
      self.dev_text.configure(state="normal")
      self.dev_text.delete("1.0", "end")
      try:
        dogfood = format_dogfooding_report(root=self._project_root)
      except OSError:
        dogfood = "Dogfooding: нет данных"
      self.dev_text.insert(
        "1.0",
        dogfood + "\n\n---\n" + "\n".join(health.details),
      )
      self.dev_text.configure(state="disabled")

    if snapshot.show_install_btn:
      self.install_btn.pack(fill="x", pady=3, after=self.start_btn)
    else:
      self.install_btn.pack_forget()

    if snapshot.dependency_hints:
      self.hint_label.configure(text=" · ".join(snapshot.dependency_hints))

  def refresh_status(self) -> None:
    if self._busy or self._status_busy:
      self.after(2000, self.refresh_status)
      return

    fe_exited = (
      self.managed.frontend is not None
      and self.managed.frontend.poll() is not None
    )
    if not fe_exited:
      from launcher.health import frontend_port_listening, probe_frontend_live

      if (
        self._launch_attempted
        and self.managed.frontend is not None
        and not frontend_port_listening()
        and not probe_frontend_live()
      ):
        fe_exited = True
    self._status_busy = True

    def work() -> None:
      try:
        snapshot = gather_status(
          self.managed,
          self._project_root,
          frontend_exited=fe_exited,
          launcher_idle=not self._launch_attempted and not self._busy,
        )
      except Exception as exc:
        append_log(f"Status check error: {exc}")
        snapshot = None

      def done() -> None:
        self._status_busy = False
        if snapshot is not None:
          self._apply_status_snapshot(snapshot)
        self.after(5000, self.refresh_status)

      self.after(0, done)

    threading.Thread(target=work, daemon=True).start()

  def _ensure_components_and_bootstrap(self) -> None:
    if self._busy:
      return

    def on_ready() -> None:
      self._bootstrap_genesis()

    ensure_launcher_components(self, self._project_root, on_ready)

  def _bootstrap_genesis(self) -> None:
    if self._busy:
      return
    if reconnect_managed(self.managed, self._project_root):
      append_log("Runtime Boot: reconnected (24/7)")
      self.refresh_status()
    if self.config.auto_start_on_open:
      self._trigger_runtime_boot()
    elif owner_ready_live():
      self.status_label.configure(text="✔ Genesis готов", text_color="#22c55e")

  def _trigger_runtime_boot(self) -> None:
    """Mission 1: automatic Runtime Boot on open — CEO does not start processes."""
    self._on_start()

  def _open_mission_control(self) -> tuple[bool, str]:
    """Open Mission Control in browser; always attempted on successful ▶."""
    self.status_label.configure(text="🟢 Открываю Mission Control...", text_color="#22c55e")
    browser_started = time.monotonic()
    ok, err = open_mission_control(
      COMMAND_CENTER_URL,
      surface=resolve_surface_mode(self.config.mission_control_surface),
    )
    browser_sec = time.monotonic() - browser_started
    record_browser_open(root=self._project_root, duration_sec=browser_sec, ok=ok)
    if ok:
      return True, ""
    hint = f"Откройте вручную: {COMMAND_CENTER_URL}"
    self.status_label.configure(text=hint[:72], text_color="#eab308")
    return False, err or hint

  def _on_install_frontend(self) -> None:
    if self._busy:
      return
    self._busy = True
    self.install_btn.configure(state="disabled")
    self.start_btn.configure(state="disabled")
    self.status_label.configure(text="🟡 Установка Mission Control...", text_color="#eab308")

    def work() -> None:
      ok, msg = ensure_frontend_ready(self._project_root)
      append_log(msg)

      def done() -> None:
        self._busy = False
        self.install_btn.configure(state="normal")
        self.start_btn.configure(state="normal")
        if not ok:
          self._last_error = msg
          _show_error(self, msg)
          self.refresh_status()
          return
        self.status_label.configure(text="🟢 Mission Control установлен", text_color="#22c55e")
        self._on_start()

      self.after(0, done)

    threading.Thread(target=work, daemon=True).start()

  def _on_start(self) -> None:
    if self._busy:
      self.status_label.configure(
        text="🟡 Запуск уже выполняется — подождите...",
        text_color="#eab308",
      )
      return

    if owner_ready_live():
      self._launch_attempted = True
      self._last_error = ""
      session_id, started = begin_launch_session(self._project_root)

      def open_ready() -> None:
        ok, err = self._open_mission_control()
        if ok:
          record_launch_success(session_id, started, root=self._project_root)
          self.status_label.configure(text="✔ Genesis полностью готов", text_color="#22c55e")
        else:
          record_launch_failure(session_id, started, root=self._project_root, error=err)
        self.refresh_status()

      self.after(0, open_ready)
      return

    def begin() -> None:
      self._start_genesis_workflow()

    ensure_launcher_components(self, self._project_root, begin)

  def _start_genesis_workflow(self) -> None:
    if self._busy:
      return
    self._busy = True
    self._launch_attempted = True
    self._last_error = ""
    self.status_label.configure(text="🟡 Подготовка Genesis...", text_color="#eab308")
    self.start_btn.configure(state="disabled")

    def work() -> None:
      session_id, started = begin_launch_session(self._project_root)

      def on_phase(phase: str) -> None:
        labels = {
          "backend": "🟡 Backend...",
          "install_frontend": "🟡 Mission Control — установка...",
          "build_frontend": "🟡 Mission Control — сборка...",
          "frontend": "🟡 Mission Control...",
        }
        label = labels.get(phase, "🟡 Подготовка Genesis...")
        self.after(0, lambda: self.status_label.configure(text=label, text_color="#eab308"))

      result = run_runtime_boot(
        self.managed,
        root=self._project_root,
        on_phase=on_phase,
        on_progress=lambda label: self.after(
          0, lambda l=label: self.status_label.configure(text=l, text_color="#eab308")
        ),
      )
      append_log(result.message or result.error)

      def done() -> None:
        self._busy = False
        self.start_btn.configure(state="normal")
        if result.success and result.ready:
          self._last_error = ""
          self.config.touch_launch()
          self.fix_btn.pack_forget()
          record_launch_success(session_id, started, root=self._project_root)
          self._open_mission_control()
          self.status_label.configure(text="✔ Genesis полностью готов", text_color="#22c55e")
        else:
          self._last_error = result.error or result.message
          record_launch_failure(
            session_id,
            started,
            root=self._project_root,
            error=self._last_error,
            critical=True,
          )
          self.fix_btn.pack(fill="x", pady=3, after=self.start_btn)
          headline = (result.cause or self._last_error)[:72]
          self.status_label.configure(text=headline, text_color="#ef4444")
          _show_boot_failure(self, result)
        self.refresh_status()

      self.after(0, done)

    threading.Thread(target=work, daemon=True).start()

  def _on_auto_fix(self) -> None:
    if self._busy:
      return
    if owner_ready_live():
      self._last_error = ""
      self.fix_btn.pack_forget()
      self._open_mission_control()
      self.status_label.configure(text="✔ Genesis полностью готов", text_color="#22c55e")
      return
    self._busy = True
    self._last_error = ""
    self.fix_btn.configure(state="disabled")
    self.start_btn.configure(state="disabled")
    self.status_label.configure(text="🟡 Исправление Genesis...", text_color="#eab308")

    def work() -> None:
      from launcher.startup_stages import repair_staged

      ok, msg = repair_staged(self.managed, self._project_root)
      append_log(f"Manual staged repair: {msg}")
      ready, err = (False, msg)
      if ok:
        ready, err = wait_until_ready(
          timeout=45.0,
          poll=0.8,
          managed=self.managed,
          root=self._project_root,
          on_progress=lambda label: self.after(
            0, lambda l=label: self.status_label.configure(text=l, text_color="#eab308")
          ),
          auto_repair=False,
        )

      def done() -> None:
        self._busy = False
        self.fix_btn.configure(state="normal")
        self.start_btn.configure(state="normal")
        if ok and ready:
          self._last_error = ""
          self.fix_btn.pack_forget()
          self._open_mission_control()
          self.status_label.configure(text="🟢 Genesis готов к работе", text_color="#22c55e")
        else:
          self._last_error = err or msg
          self.fix_btn.pack(fill="x", pady=3, after=self.start_btn)
          _show_error(self, self._last_error)
        self.refresh_status()

      self.after(0, done)

    threading.Thread(target=work, daemon=True).start()

  def _on_stop(self) -> None:
    if self._busy:
      return
    if not messagebox.askyesno(
      "Остановить Genesis",
      "Остановить Backend и Mission Control?\n\nДанные проекта сохранятся.",
    ):
      return
    self._busy = True
    self.stop_btn.configure(state="disabled")
    self.start_btn.configure(state="disabled")

    def work() -> None:
      stop_all(self.managed, root=self._project_root)
      append_log("Genesis stopped by owner")

      def done() -> None:
        self._busy = False
        self.stop_btn.configure(state="normal")
        self.start_btn.configure(state="normal")
        self._last_error = ""
        self.fix_btn.pack_forget()
        self.status_label.configure(text="⚪ Genesis остановлен", text_color="#9ca3af")
        self.refresh_status()

      self.after(0, done)

    threading.Thread(target=work, daemon=True).start()

  def _open_dashboard(self) -> None:
    open_mission_control(
      COMMAND_CENTER_URL,
      surface=resolve_surface_mode(self.config.mission_control_surface),
    )

  def _open_create(self) -> None:
    webbrowser.open(CREATE_URL)

  def _on_exit(self) -> None:
    running = (
      self._last_snapshot is not None
      and self._last_snapshot.health.overall == "running"
    )

    if running and self.config.keep_running_on_close:
      keep = messagebox.askyesno(
        "Genesis",
        "Закрыть пульт управления?\n\n"
        "Да — Genesis продолжит работать 24/7 в фоне.\n"
        "Нет — остановить Backend, Frontend и выйти.",
      )
      if keep:
        from launcher.runtime_state import sync_state
        from launcher.processes import _pid

        sync_state(_pid(self.managed.backend), _pid(self.managed.frontend), root=self._project_root)
        append_log("Launcher closed — Genesis keeps running 24/7")
        self.destroy()
      else:
        stop_all(self.managed, root=self._project_root)
        self.destroy()
      return

    if messagebox.askyesno("Выход", "Остановить Genesis и закрыть?"):
      stop_all(self.managed, root=self._project_root)
      self.destroy()


def _validate_path_helpers() -> None:
    for name in ("find_project_root", "log_dir", "memory_dir", "backend_dir", "frontend_dir"):
        helper = getattr(paths, name)
        if not callable(helper):
            raise TypeError(
                f"launcher.paths.{name} must be a function, got {type(helper).__name__}. "
                "Path helper was shadowed by a pathlib.Path variable."
            )


def main() -> None:
    try:
        _validate_path_helpers()
        app = GenesisLauncher()
        app.mainloop()
    except Exception as exc:
        import traceback

        try:
            paths.log_dir().mkdir(parents=True, exist_ok=True)
            log_file = paths.log_dir() / "genesis_launcher.log"
            log_file.write_text(
                traceback.format_exc(),
                encoding="utf-8",
            )
        except OSError:
            pass
        messagebox.showerror("Genesis", f"Не удалось запустить Genesis:\n\n{exc}")


if __name__ == "__main__":
  main()
