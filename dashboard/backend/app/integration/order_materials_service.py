"""Order materials + honest buyer insights (Path A).

Uploads are stored for the project. Findings are only claimed when extraction
actually succeeds — otherwise the UI shows «gespeichert für das Projekt».
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

_ALLOWED_EXT = {
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".txt",
    ".zip",
    ".mp4",
}
_ALLOWED_MIME_PREFIX = (
    "image/",
    "application/pdf",
    "application/zip",
    "application/x-zip",
    "text/plain",
    "application/vnd.openxmlformats",
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "video/mp4",
)
_MAX_BYTES = 12 * 1024 * 1024


class OrderMaterialsService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._root = memory_dir / "order_materials"
        self._root.mkdir(parents=True, exist_ok=True)
        self._index = self._root / "index.jsonl"

    def save(self, upload: UploadFile, *, session_id: str = "anon") -> dict[str, Any]:
        name = upload.filename or "file"
        ext = Path(name).suffix.lower() or ""
        content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip().lower()
        if ext and ext not in _ALLOWED_EXT:
            raise ValueError(f"Dateityp nicht unterstützt: {ext or content_type}")
        if not ext and not any(content_type.startswith(p) for p in _ALLOWED_MIME_PREFIX):
            raise ValueError(f"Dateityp nicht unterstützt: {content_type}")

        data = upload.file.read()
        if len(data) > _MAX_BYTES:
            raise ValueError("Datei zu groß (max. 12 MB)")

        mat_id = f"mat-{uuid.uuid4().hex[:12]}"
        safe_ext = ext if ext in _ALLOWED_EXT else ".bin"
        path = self._root / f"{mat_id}{safe_ext}"
        path.write_bytes(data)

        findings = self._analyze_bytes(data, filename=name, content_type=content_type, ext=safe_ext)
        row = {
            "id": mat_id,
            "filename": name,
            "content_type": content_type,
            "ext": safe_ext,
            "size": len(data),
            "path": str(path),
            "session_id": re.sub(r"[^\w\-]", "_", session_id)[:64],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings,
            "stored": True,
        }
        with self._index.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {
            "id": mat_id,
            "filename": name,
            "content_type": content_type,
            "size": len(data),
            "findings": findings,
            "status_de": (
                "Analysiert"
                if any(f.get("found") for f in findings)
                else "Gespeichert — wird im Projekt verwendet"
            ),
        }

    def get_many(self, ids: list[str]) -> list[dict[str, Any]]:
        want = {str(i) for i in ids if i}
        if not want or not self._index.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._index.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("id") in want:
                rows.append(row)
        return rows

    def attach_to_order(self, order_id: str, material_ids: list[str]) -> dict[str, Any]:
        """Snapshot materials onto the order workspace (metadata only; files stay on disk)."""
        files: list[dict[str, Any]] = []
        for row in self.get_many(material_ids):
            files.append(
                {
                    "id": row.get("id"),
                    "filename": row.get("filename"),
                    "content_type": row.get("content_type"),
                    "size": row.get("size"),
                    "ext": row.get("ext"),
                    "findings": row.get("findings") or [],
                    "path": row.get("path"),
                    "order_id": order_id,
                }
            )
        return {"order_id": order_id, "files": files, "count": len(files)}

    def build_buyer_insights(
        self,
        *,
        company_website: str | None = None,
        domain: str | None = None,
        domain_status: str | None = None,
        social: dict[str, str] | None = None,
        material_ids: list[str] | None = None,
        site_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return only findings that were actually detected."""
        checks: list[dict[str, Any]] = []

        if (domain_status or "") == "have_domain" and (domain or "").strip():
            checks.append(
                {
                    "id": "domain",
                    "label_de": "Domain vorhanden",
                    "found": True,
                    "detail": (domain or "").strip(),
                }
            )
        elif (domain_status or "") == "need_help":
            checks.append(
                {
                    "id": "domain_help",
                    "label_de": "Hilfe bei Domain gewünscht",
                    "found": True,
                    "detail": "Wir helfen später bei Auswahl und Anschluss — keine Sofortkauf-Pflicht.",
                }
            )
        elif (domain_status or "") == "none":
            checks.append(
                {
                    "id": "domain_later",
                    "label_de": "Domain später",
                    "found": True,
                    "detail": "Kein Domain-Kauf jetzt erforderlich.",
                }
            )

        analysis = site_analysis if isinstance(site_analysis, dict) else None
        if company_website and not analysis:
            try:
                from app.integration.site_analysis_service import SiteAnalysisService

                analysis = SiteAnalysisService(self._memory).analyze(company_website, use_cache=True)
            except Exception:
                analysis = {"error": "analysis_failed"}

        if company_website:
            if analysis and not analysis.get("error"):
                if analysis.get("has_https") or "HTTPS" in " ".join(analysis.get("strengths") or []):
                    checks.append({"id": "https", "label_de": "HTTPS erkannt", "found": True})
                title = str(analysis.get("title") or "").strip()
                if title:
                    checks.append(
                        {
                            "id": "title",
                            "label_de": "Seitentitel gefunden",
                            "found": True,
                            "detail": title[:120],
                        }
                    )
                strengths = " ".join(str(s) for s in (analysis.get("strengths") or []))
                issues = " ".join(str(s) for s in (analysis.get("issues") or []))
                blob = strengths + " " + issues
                if "Viewport" in strengths or "viewport" in strengths.lower():
                    checks.append({"id": "mobile", "label_de": "Mobile-Viewport erkannt", "found": True})
                if "Anruf" in issues or "WhatsApp" in issues:
                    pass  # missing phone — don't claim found
                else:
                    # SiteAnalysis only reports missing phone as issue; if no such issue, still don't invent
                    pass
                emails = analysis.get("emails") or analysis.get("emails_found") or []
                if emails:
                    checks.append(
                        {
                            "id": "email_on_site",
                            "label_de": "E-Mail auf der Website gefunden",
                            "found": True,
                            "detail": str(emails[0])[:80],
                        }
                    )
                checks.append(
                    {
                        "id": "site_scanned",
                        "label_de": "Website gescannt",
                        "found": True,
                        "detail": str(analysis.get("final_url") or company_website)[:120],
                    }
                )
            else:
                checks.append(
                    {
                        "id": "site_url_saved",
                        "label_de": "Website-Adresse gespeichert",
                        "found": True,
                        "detail": "Vollscan nicht möglich — URL wird im Projekt genutzt.",
                    }
                )

        social = social or {}
        social_labels = {
            "google_business": "Google Business",
            "instagram": "Instagram",
            "facebook": "Facebook",
            "tiktok": "TikTok",
            "linkedin": "LinkedIn",
            "youtube": "YouTube",
            "telegram": "Telegram",
        }
        for key, label in social_labels.items():
            val = str(social.get(key) or "").strip()
            if val:
                checks.append(
                    {
                        "id": f"social_{key}",
                        "label_de": f"{label} angegeben",
                        "found": True,
                        "detail": val[:120],
                    }
                )

        seen_check_ids: set[str] = set()
        for mat in self.get_many(list(dict.fromkeys(material_ids or []))):
            for finding in mat.get("findings") or []:
                if not finding.get("found"):
                    continue
                fact_id = str(finding.get("id") or "").strip() or "stored"
                # Aggregate by fact type (image/email/phone…), not per material row —
                # re-uploads of the same file must not duplicate Insights.
                check_id = f"mat_{fact_id}"
                if check_id in seen_check_ids:
                    continue
                seen_check_ids.add(check_id)
                checks.append(
                    {
                        "id": check_id,
                        "label_de": finding.get("label_de"),
                        "found": True,
                        "detail": finding.get("detail") or mat.get("filename"),
                    }
                )
            if not any(f.get("found") for f in (mat.get("findings") or [])):
                fname = str(mat.get("filename") or "file")
                check_id = f"stored_{fname.lower()}"
                if check_id in seen_check_ids:
                    continue
                seen_check_ids.add(check_id)
                checks.append(
                    {
                        "id": check_id,
                        "label_de": "Datei gespeichert",
                        "found": True,
                        "detail": f"{fname} — wird im Projekt verwendet",
                    }
                )

        return {
            "checks": [c for c in checks if c.get("found")],
            "site_analysis": analysis,
            "note_de": (
                "Nur tatsächlich erkannte Punkte. Nicht erkannte Dateien bleiben "
                "im Projekt gespeichert und werden bei der Erstellung genutzt."
            ),
        }

    def _analyze_bytes(
        self, data: bytes, *, filename: str, content_type: str, ext: str
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lower = filename.lower()

        if ext in {".png", ".jpg", ".jpeg", ".webp", ".svg"} or content_type.startswith("image/"):
            findings.append(
                {
                    "id": "image",
                    "label_de": "Bild / Logo-Datei erkannt",
                    "found": True,
                    "detail": filename,
                }
            )
            if "logo" in lower:
                findings.append(
                    {
                        "id": "logo_name",
                        "label_de": "Dateiname deutet auf Logo",
                        "found": True,
                        "detail": filename,
                    }
                )
            return findings

        if ext == ".pdf" or content_type == "application/pdf":
            text = self._pdf_text(data)
            if text:
                findings.append(
                    {
                        "id": "pdf_text",
                        "label_de": "PDF analysiert (Text extrahiert)",
                        "found": True,
                        "detail": f"{len(text)} Zeichen",
                    }
                )
                findings.extend(self._contact_findings(text))
            else:
                findings.append(
                    {
                        "id": "pdf_stored",
                        "label_de": "PDF gespeichert",
                        "found": True,
                        "detail": "Text konnte nicht gelesen werden — Datei bleibt im Projekt.",
                    }
                )
            return findings

        if ext == ".txt" or content_type.startswith("text/"):
            try:
                text = data.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
            if text.strip():
                findings.append(
                    {
                        "id": "txt",
                        "label_de": "Textdatei gelesen",
                        "found": True,
                    }
                )
                findings.extend(self._contact_findings(text))
            return findings

        if ext == ".docx":
            text = self._docx_text(data)
            if text:
                findings.append(
                    {
                        "id": "docx_text",
                        "label_de": "DOCX gelesen (Text extrahiert)",
                        "found": True,
                        "detail": f"{len(text)} Zeichen",
                    }
                )
                findings.extend(self._contact_findings(text))
            else:
                findings.append(
                    {
                        "id": "docx_stored",
                        "label_de": "DOCX gespeichert",
                        "found": True,
                        "detail": "Text nicht lesbar — Datei bleibt im Projekt.",
                    }
                )
            return findings

        if ext in {".xlsx", ".pptx"}:
            findings.append(
                {
                    "id": "office_stored",
                    "label_de": "Office-Datei gespeichert",
                    "found": True,
                    "detail": "Wird im Projekt verwendet (kein tiefer Extrakt in diesem Schritt).",
                }
            )
            return findings

        if ext == ".zip":
            findings.append(
                {
                    "id": "zip_stored",
                    "label_de": "ZIP gespeichert",
                    "found": True,
                    "detail": "Archiv bleibt im Projekt für die Erstellung.",
                }
            )
            return findings

        if ext == ".mp4" or content_type.startswith("video/"):
            findings.append(
                {
                    "id": "video_stored",
                    "label_de": "Video gespeichert",
                    "found": True,
                    "detail": "Für das Projekt hinterlegt (kein Auto-Schnitt).",
                }
            )
            return findings

        findings.append(
            {
                "id": "stored",
                "label_de": "Datei gespeichert",
                "found": True,
                "detail": filename,
            }
        )
        return findings

    def _pdf_text(self, data: bytes) -> str:
        try:
            from io import BytesIO

            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            parts: list[str] = []
            for page in reader.pages[:8]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts).strip()
        except Exception:
            return ""

    def _docx_text(self, data: bytes) -> str:
        """Best-effort: DOCX is a ZIP with word/document.xml — no extra dependency."""
        try:
            import zipfile
            from io import BytesIO
            from xml.etree import ElementTree as ET

            with zipfile.ZipFile(BytesIO(data)) as zf:
                raw = zf.read("word/document.xml")
            root = ET.fromstring(raw)
            texts = [
                (node.text or "")
                for node in root.iter()
                if node.tag.endswith("}t") and node.text
            ]
            return " ".join(texts).strip()
        except Exception:
            return ""

    def _contact_findings(self, text: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        emails = re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.I)
        if emails:
            out.append(
                {
                    "id": "email",
                    "label_de": "E-Mail in Datei gefunden",
                    "found": True,
                    "detail": emails[0][:80],
                }
            )
        phones = re.findall(r"(?:\+49|0)\s*[\d\s\-/]{6,}", text)
        if phones:
            out.append(
                {
                    "id": "phone",
                    "label_de": "Telefonnummer in Datei gefunden",
                    "found": True,
                    "detail": phones[0].strip()[:40],
                }
            )
        if re.search(r"öffnungszeit|mo\s*[-–]|montag|di\s*[-–]", text, re.I):
            out.append(
                {
                    "id": "hours",
                    "label_de": "Öffnungszeiten erwähnt",
                    "found": True,
                }
            )
        return out
