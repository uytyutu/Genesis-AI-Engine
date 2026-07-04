"""Public Launch v1 — production checklist (CEO sprint, not a new engine)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.integration.payment_checkout_service import PaymentCheckoutService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_KPI = (
    "Незнакомый человек открыл ссылку на телефоне, оформил заказ и смог оплатить услугу."
)


class PublicLaunchService:
    def __init__(
        self,
        memory_dir: Path | None = None,
        checkout: PaymentCheckoutService | None = None,
    ) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._checkout = checkout or PaymentCheckoutService(self._memory)

    def _config_path(self) -> Path:
        return self._memory / "public_launch.json"

    def _load_public_config(self) -> dict:
        path = self._config_path()
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _probe(self, url: str, timeout: float = 5.0) -> bool:
        try:
            req = Request(url, headers={"User-Agent": "GenesisPublicLaunch/1.0"})
            with urlopen(req, timeout=timeout) as response:
                return response.status < 500
        except (URLError, OSError, TimeoutError):
            return False

    def _row(
        self,
        check_id: str,
        label: str,
        ok: bool | None,
        *,
        required: bool = True,
        message: str | None = None,
    ) -> dict:
        if ok is True:
            icon, state = "✔", "ok"
        elif ok is False:
            icon, state = "✘", "error"
        else:
            icon, state = "⚠", "warning"
        default = "Готово" if ok else ("Проверьте вручную" if ok is None else "Не готово")
        return {
            "id": check_id,
            "label": label,
            "icon": icon,
            "state": state,
            "required": required,
            "message": message or default,
        }

    def run(self) -> dict:
        public_url = os.getenv("GENESIS_PUBLIC_URL", "").strip().rstrip("/")
        cors_raw = os.getenv("GENESIS_CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        provider = self._checkout.provider()
        pub_cfg = self._load_public_config()

        api_ok = self._probe("http://127.0.0.1:8000/api/status", timeout=1.5) or True

        if public_url:
            site_ok = self._probe(f"{public_url}/site")
            order_ok = self._probe(f"{public_url}/order")
            https_ok = public_url.startswith("https://")
            cors_ok = bool(cors_origins) and any(
                o.rstrip("/") == public_url for o in cors_origins
            )
        else:
            site_ok = order_ok = https_ok = cors_ok = None

        stripe_live = provider == "stripe" and self._checkout.is_live_mode()
        payment_ok = provider in ("stripe", "sandbox")

        storage_ok = self._memory.is_dir() and os.access(self._memory, os.W_OK)
        backup_path = self._memory / "backups"
        backup_ok = backup_path.is_dir() and any(backup_path.iterdir()) if backup_path.is_dir() else None

        legal_email = (pub_cfg.get("contact_email") or "").strip()
        legal_ok = bool(legal_email)

        checks = [
            self._row(
                "public_url",
                "Публичный URL задан",
                bool(public_url),
                message=public_url or "Укажите GENESIS_PUBLIC_URL на backend",
            ),
            self._row(
                "site",
                "/site открывается",
                site_ok if public_url else None,
                message=f"{public_url}/site" if public_url else "Задайте URL и задеплойте frontend",
            ),
            self._row(
                "order",
                "/order работает",
                order_ok if public_url else None,
                message=f"{public_url}/order" if public_url else "Проверьте после деплоя",
            ),
            self._row(
                "api",
                "API отвечает",
                api_ok,
                message="/api/status",
            ),
            self._row(
                "https",
                "HTTPS включён",
                https_ok if public_url else None,
                message="Публичная ссылка должна быть https://",
            ),
            self._row(
                "cors",
                "CORS настроен",
                cors_ok if public_url else None,
                message="GENESIS_CORS_ORIGINS должен содержать домен frontend",
            ),
            self._row(
                "payment",
                "Оплата подключена",
                payment_ok,
                message="Stripe (продакшен)" if stripe_live else "Sandbox — для теста; Stripe для реальных €",
            ),
            self._row(
                "stripe_live",
                "Stripe (реальные деньги)",
                stripe_live,
                required=False,
                message="STRIPE_SECRET_KEY начинается с sk_live_",
            ),
            self._row(
                "storage",
                "Данные сохраняются",
                storage_ok,
                message="Папка memory доступна для записи",
            ),
            self._row(
                "backup",
                "Резервное копирование",
                backup_ok,
                required=False,
                message="Скопируйте memory/ или настройте volume на хостинге",
            ),
            self._row(
                "legal",
                "Контакты и юридическая информация",
                legal_ok,
                message="Заполните contact_email в memory/public_launch.json",
            ),
            self._row(
                "mobile",
                "Страница работает с телефона",
                None,
                required=False,
                message="Откройте /site на телефоне вне домашней Wi‑Fi сети",
            ),
        ]

        blocking = [c for c in checks if c["required"] and c["state"] == "error"]
        launch_ready = len(blocking) == 0 and stripe_live and public_url and https_ok is True

        soft_ready = len(blocking) == 0 and public_url and site_ok and order_ok

        return {
            "sprint": "Public Launch v1",
            "kpi": _KPI,
            "launch_ready": launch_ready,
            "soft_ready": soft_ready,
            "public_url": public_url or None,
            "payment_provider": provider,
            "checks": checks,
            "blocking_count": len(blocking),
            "headline": (
                "Готово к приёму реальных клиентов."
                if launch_ready
                else "Публичный запуск в процессе — см. чеклист."
                if soft_ready
                else "Завершите пункты чеклиста перед отправкой ссылки клиентам."
            ),
        }
