"""Factory v0.1 — Landing Page production department (sandbox only)."""

from __future__ import annotations

import io
import json
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.landing_patcher import try_patch
from app.factory.landing_builder import build_landing_html
from app.factory.validator import owner_review_check, validate_landing

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SANDBOX = _BACKEND_ROOT / "sandbox"
_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_DEPLOY_README = """# Как опубликовать сайт за 5 минут

1. Распакуйте этот архив.
2. Откройте index.html в браузере — проверьте, что всё выглядит правильно.
3. Загрузите index.html на хостинг:
   - Netlify: перетащите папку на app.netlify.com/drop
   - GitHub Pages: загрузите в репозиторий и включите Pages
   - Ваш хостинг: через FTP или панель «Файловый менеджер»

Сайт состоит из одного файла — дополнительная сборка не нужна.

Создано Genesis Factory.
"""


class FactoryService:
    def __init__(self, memory_dir: Path | None = None, sandbox_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        if sandbox_dir is not None:
            self._sandbox = sandbox_dir
        elif memory_dir is not None:
            self._sandbox = memory_dir / "sandbox"
        else:
            self._sandbox = _DEFAULT_SANDBOX
        self._memory.mkdir(parents=True, exist_ok=True)
        self._sandbox.mkdir(parents=True, exist_ok=True)

    def build_landing(self, description: str, intent_id: str | None = None) -> dict:
        product_id = intent_id or str(uuid.uuid4())
        analysis = analyze(description)
        html = build_landing_html(analysis)
        validation = validate_landing(html)

        product_dir = self._sandbox / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        (product_dir / "index.html").write_text(html, encoding="utf-8")

        meta = {
            "product_id": product_id,
            "intent_id": intent_id,
            "product_type": "Landing Page",
            "description": description,
            "niche": analysis.niche,
            "template_id": analysis.template_id,
            "business_name": analysis.business_name,
            "status": "completed",
            "quality_percent": validation.quality_percent,
            "validation_passed": validation.passed,
            "technical_checks": validation.technical_checks,
            "owner_approved": False,
            "owner_approved_at": None,
            "revision": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "style_flags": {"modern": False, "blue_boost": False, "calculator": False},
        }
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def improve(self, product_id: str, feedback: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")

        flags = dict(meta.get("style_flags", {}))
        lower = feedback.lower()
        product_dir = self._sandbox / product_id
        existing_html = (product_dir / "index.html").read_text(encoding="utf-8")

        patched_html, patches = try_patch(existing_html, feedback)
        if patches:
            html = patched_html
            flags["last_patches"] = patches
        else:
            if any(w in lower for w in ("син", "blue", "голуб")):
                flags["blue_boost"] = True
            if any(w in lower for w in ("современ", "modern", "минимал")):
                flags["modern"] = True
            if any(w in lower for w in ("калькулятор", "calculator", "расчёт", "расчет")):
                flags["calculator"] = True
            if any(w in lower for w in ("отзыв", "review")):
                flags["testimonials"] = True
            if any(w in lower for w in ("крупн", "заголовок")):
                flags["large_headline"] = True

            analysis = analyze(meta["description"])
            html = build_landing_html(
                analysis,
                modern=flags.get("modern", False),
                blue_boost=flags.get("blue_boost", False),
                calculator=flags.get("calculator", False),
                include_testimonials=flags.get("testimonials", False),
                large_headline=flags.get("large_headline", False),
            )

        validation = validate_landing(html)

        (product_dir / "index.html").write_text(html, encoding="utf-8")

        meta["revision"] = int(meta.get("revision", 0)) + 1
        meta["quality_percent"] = validation.quality_percent
        meta["validation_passed"] = validation.passed
        meta["technical_checks"] = validation.technical_checks
        meta["owner_approved"] = False
        meta["owner_approved_at"] = None
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        meta["last_feedback"] = feedback.strip()
        meta["style_flags"] = flags
        meta["status"] = "completed"
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def approve(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        meta["owner_approved"] = True
        meta["owner_approved_at"] = datetime.now(timezone.utc).isoformat()
        meta["status"] = "owner_approved"
        (self._sandbox / product_id / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def publish(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        meta["published"] = True
        meta["published_at"] = datetime.now(timezone.utc).isoformat()
        meta["status"] = "published"
        meta["public_url"] = f"/api/factory/products/{product_id}/preview"
        product_dir = self._sandbox / product_id
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        published_root = self._sandbox.parent / "published"
        published_root.mkdir(parents=True, exist_ok=True)
        dest = published_root / product_id
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(product_dir, dest)
        self._touch_milestone("published", True)
        return self._product_summary(meta)

    def build_export_zip(self, product_id: str) -> tuple[bytes, str]:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        if not meta.get("published"):
            raise ValueError("not_published")
        product_dir = self._sandbox / product_id
        html_path = product_dir / "index.html"
        if not html_path.is_file():
            raise ValueError("product_not_found")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", html_path.read_text(encoding="utf-8"))
            archive.writestr("КАК_ОПУБЛИКОВАТЬ.txt", _DEPLOY_README)

        meta["export_downloaded_at"] = datetime.now(timezone.utc).isoformat()
        meta["updated_at"] = meta["export_downloaded_at"]
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        slug = self._zip_slug(meta.get("business_name") or "", product_id)
        return buf.getvalue(), f"{slug}-genesis.zip"

    def mark_delivered(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        if not meta.get("published"):
            raise ValueError("not_published")
        now = datetime.now(timezone.utc).isoformat()
        meta["delivered_to_client"] = True
        meta["delivered_at"] = now
        meta["status"] = "delivered"
        meta["updated_at"] = now
        product_dir = self._sandbox / product_id
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        published = self._sandbox.parent / "published" / product_id / "meta.json"
        if published.is_file():
            try:
                pub_meta = json.loads(published.read_text(encoding="utf-8"))
                pub_meta.update(
                    {
                        "delivered_to_client": True,
                        "delivered_at": now,
                        "status": "delivered",
                        "updated_at": now,
                    }
                )
                published.write_text(json.dumps(pub_meta, ensure_ascii=False, indent=2), encoding="utf-8")
            except (json.JSONDecodeError, OSError):
                pass
        self._touch_milestone("delivered_to_client", True)
        self._touch_milestone("owner_tested", True)
        return self._product_summary(meta)

    def _zip_slug(self, name: str, product_id: str) -> str:
        ascii_name = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
        ascii_name = re.sub(r"-{2,}", "-", ascii_name).strip("-")
        if ascii_name:
            return ascii_name[:40]
        return product_id[:12]

    def _client_handoff_message(self, meta: dict) -> str:
        name = meta.get("business_name") or "ваш сайт"
        return (
            f"Здравствуйте!\n\n"
            f"Ваш сайт «{name}» готов.\n\n"
            f"Во вложении — архив ZIP с файлом index.html и короткой инструкцией, "
            f"как разместить сайт в интернете.\n\n"
            f"Кратко:\n"
            f"1. Распакуйте архив\n"
            f"2. Откройте index.html в браузере и проверьте\n"
            f"3. Загрузите на хостинг (Netlify, GitHub Pages или ваш провайдер)\n\n"
            f"Если нужна помощь с размещением — напишите.\n\n"
            f"С уважением"
        )

    def _handoff_checklist(self, meta: dict) -> list[dict[str, str | bool]]:
        return [
            {"id": "preview", "label": "Просмотреть превью", "done": True},
            {
                "id": "approved",
                "label": "Одобрить для клиента (Owner Approved)",
                "done": bool(meta.get("owner_approved")),
            },
            {
                "id": "published",
                "label": "Подготовить к передаче (Publish)",
                "done": bool(meta.get("published")),
            },
            {
                "id": "download",
                "label": "Скачать ZIP и проверить файлы",
                "done": bool(meta.get("export_downloaded_at")),
            },
            {
                "id": "message",
                "label": "Отправить клиенту (WhatsApp / email + ZIP)",
                "done": bool(meta.get("delivered_to_client")),
            },
            {
                "id": "delivered",
                "label": "Передано клиенту",
                "done": bool(meta.get("delivered_to_client")),
            },
        ]

    def _touch_milestone(self, key: str, value: bool | int | str = True) -> None:
        path = self._memory / "owner_milestones.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data[key] = value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_product(self, product_id: str) -> dict | None:
        meta = self._load_meta(product_id)
        return self._product_summary(meta) if meta else None

    def list_products(self, limit: int = 50) -> list[dict]:
        items: list[dict] = []
        if not self._sandbox.exists():
            return items
        for path in sorted(self._sandbox.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            meta = self._load_meta(path.name)
            if meta:
                items.append(self._product_summary(meta))
            if len(items) >= limit:
                break
        return items

    def latest_product(self) -> dict | None:
        products = self.list_products(limit=1)
        return products[0] if products else None

    def read_preview_html(self, product_id: str) -> str | None:
        html_path = self._sandbox / product_id / "index.html"
        if not html_path.exists():
            return None
        return html_path.read_text(encoding="utf-8")

    def _load_meta(self, product_id: str) -> dict | None:
        meta_path = self._sandbox / product_id / "meta.json"
        if not meta_path.exists():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _product_summary(self, meta: dict) -> dict:
        pid = meta["product_id"]
        approved = bool(meta.get("owner_approved"))
        checks = list(meta.get("technical_checks", []))
        checks.append(owner_review_check(approved))
        return {
            "product_id": pid,
            "product_type": meta.get("product_type", "Landing Page"),
            "business_name": meta.get("business_name", ""),
            "description": meta.get("description", ""),
            "status": meta.get("status", "completed"),
            "status_label": self._status_label(meta),
            "quality_percent": int(meta.get("quality_percent", 0)),
            "checks": checks,
            "owner_approved": approved,
            "owner_approved_at": meta.get("owner_approved_at"),
            "published": bool(meta.get("published")),
            "published_at": meta.get("published_at"),
            "public_url": meta.get("public_url"),
            "revision": int(meta.get("revision", 0)),
            "niche": meta.get("niche", "generic"),
            "template_id": meta.get("template_id", ""),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "preview_url": f"/api/factory/products/{pid}/preview",
            "delivered_to_client": bool(meta.get("delivered_to_client")),
            "delivered_at": meta.get("delivered_at"),
            "client_message": self._client_handoff_message(meta),
            "handoff_checklist": self._handoff_checklist(meta),
        }

    def _status_label(self, meta: dict) -> str:
        if meta.get("delivered_to_client"):
            return "Передано клиенту"
        if meta.get("published"):
            return "Published"
        if meta.get("owner_approved"):
            return "Owner Approved"
        if meta.get("status") == "completed":
            return "Completed"
        return str(meta.get("status", "completed"))
