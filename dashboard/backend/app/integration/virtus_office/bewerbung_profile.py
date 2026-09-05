"""Structured Bewerbung profile — normalize, extract (no invent), missing-field gate."""

from __future__ import annotations

import re
from typing import Any

from app.integration.virtus_office.bewerbung_ssot import (
    BEWERBUNG_ACTION_IDS,
    PROFILE_FIELD_LABELS_DE,
    empty_bewerbung_profile,
)

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_PHONE_RE = re.compile(r"(?:\+|00)?\d[\d\s\-/()]{6,}\d")
_DATE_RE = re.compile(
    r"(?:(?:0?[1-9]|1[0-2])[./])?(?:19|20)\d{2}\s*[-–—bis]+\s*(?:heute|aktuell|(?:0?[1-9]|1[0-2])[./])?(?:19|20)\d{2}|(?:0?[1-9]|1[0-2])[./](?:19|20)\d{2}",
    re.I,
)


def normalize_profile(raw: dict[str, Any] | None) -> dict[str, Any]:
    base = empty_bewerbung_profile()
    if not isinstance(raw, dict):
        return base

    pers_in = raw.get("personal") if isinstance(raw.get("personal"), dict) else {}
    pers = base["personal"]
    for key in pers:
        val = pers_in.get(key)
        if val is None and key in raw:
            val = raw.get(key)
        if isinstance(val, str):
            val = val.strip() or None
        if val is not None:
            pers[key] = val

    if raw.get("photo_material_id"):
        base["photo_material_id"] = str(raw["photo_material_id"])

    base["experience"] = [_norm_exp(x) for x in (raw.get("experience") or []) if isinstance(x, dict)]
    base["experience"] = [x for x in base["experience"] if x]
    base["education"] = [_norm_edu(x) for x in (raw.get("education") or []) if isinstance(x, dict)]
    base["education"] = [x for x in base["education"] if x]
    base["certificates"] = [
        _norm_cert(x) for x in (raw.get("certificates") or []) if isinstance(x, dict)
    ]
    base["certificates"] = [x for x in base["certificates"] if x]
    base["languages"] = [
        _norm_lang(x) for x in (raw.get("languages") or []) if isinstance(x, (dict, str))
    ]
    base["languages"] = [x for x in base["languages"] if x]
    skills = raw.get("skills") or []
    if isinstance(skills, str):
        skills = [s.strip() for s in re.split(r"[,;\n]", skills) if s.strip()]
    base["skills"] = [str(s).strip() for s in skills if str(s).strip()][:40]
    lic = raw.get("drivers_license") or raw.get("fuehrerschein") or []
    if isinstance(lic, str):
        lic = [s.strip() for s in re.split(r"[,;\s]+", lic) if s.strip()]
    base["drivers_license"] = [str(s).strip().upper() for s in lic if str(s).strip()][:12]

    vac_in = raw.get("vacancy") if isinstance(raw.get("vacancy"), dict) else {}
    for key in base["vacancy"]:
        val = vac_in.get(key)
        if isinstance(val, str):
            val = val.strip() or None
        if val is not None:
            base["vacancy"][key] = val

    for key in ("motivation_notes", "source_cv_text", "anlagen_notes"):
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            base[key] = val.strip()[:20000]

    base["honesty"] = {
        "no_invention": True,
        "no_job_guarantee": True,
        "disclaimer_de": (base.get("honesty") or {}).get("disclaimer_de")
        or empty_bewerbung_profile()["honesty"]["disclaimer_de"],
    }
    return base


def merge_profiles(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Overlay user/form data onto draft — never invent missing overlay fields."""
    a = normalize_profile(base)
    b = normalize_profile(overlay)
    out = normalize_profile(a)
    for k, v in b["personal"].items():
        if v:
            out["personal"][k] = v
    if b.get("photo_material_id"):
        out["photo_material_id"] = b["photo_material_id"]
    if b["experience"]:
        out["experience"] = b["experience"]
    if b["education"]:
        out["education"] = b["education"]
    if b["certificates"]:
        out["certificates"] = b["certificates"]
    if b["languages"]:
        out["languages"] = b["languages"]
    if b["skills"]:
        out["skills"] = b["skills"]
    if b["drivers_license"]:
        out["drivers_license"] = b["drivers_license"]
    for k, v in b["vacancy"].items():
        if v:
            out["vacancy"][k] = v
    for key in ("motivation_notes", "source_cv_text", "anlagen_notes"):
        if b.get(key):
            out[key] = b[key]
    return out


def extract_profile_draft_from_text(text: str, *, filename: str = "") -> dict[str, Any]:
    """Best-effort extraction — only clear signals; leave gaps empty (no invent)."""
    profile = empty_bewerbung_profile()
    raw = text or ""
    if not raw.strip():
        return profile

    emails = _EMAIL_RE.findall(raw)
    if emails:
        profile["personal"]["email"] = emails[0]
    phones = _PHONE_RE.findall(raw)
    if phones:
        profile["personal"]["phone"] = re.sub(r"\s+", " ", phones[0]).strip()

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    # Name heuristic: first non-header line without digits, short
    for ln in lines[:8]:
        low = ln.lower()
        if any(x in low for x in ("lebenslauf", "curriculum", "bewerbung", "email", "@", "tel")):
            continue
        if len(ln) < 60 and not re.search(r"\d{3,}", ln) and len(ln.split()) <= 5:
            profile["personal"]["full_name"] = ln
            break

    # Experience blocks: line with date range + following title/employer-ish lines
    for i, ln in enumerate(lines):
        if not _DATE_RE.search(ln):
            continue
        dates = _DATE_RE.search(ln)
        start, end = _split_date_range(dates.group(0) if dates else "")
        employer = None
        title = None
        rest = _DATE_RE.sub("", ln).strip(" –—-|")
        if rest:
            if "," in rest:
                parts = [p.strip() for p in rest.split(",", 1)]
                title, employer = parts[0], parts[1] if len(parts) > 1 else None
            else:
                title = rest
        if i + 1 < len(lines) and not employer:
            nxt = lines[i + 1]
            if not _DATE_RE.search(nxt) and len(nxt) < 80:
                employer = nxt
        if employer or title:
            profile["experience"].append(
                {
                    "employer": employer,
                    "title": title,
                    "start": start,
                    "end": end,
                    "city": None,
                    "bullets": [],
                }
            )
        if len(profile["experience"]) >= 8:
            break

    # Education keywords
    for i, ln in enumerate(lines):
        low = ln.lower()
        if not any(k in low for k in ("ausbildung", "studium", "schule", "universität", "bachelor", "master", "abitur")):
            continue
        school = ln
        degree = None
        start = end = None
        if i > 0 and _DATE_RE.search(lines[i - 1]):
            start, end = _split_date_range(_DATE_RE.search(lines[i - 1]).group(0))
        m = _DATE_RE.search(ln)
        if m:
            start, end = _split_date_range(m.group(0))
            school = _DATE_RE.sub("", ln).strip(" –—-|") or school
        profile["education"].append(
            {
                "school": school[:120],
                "degree": degree,
                "start": start,
                "end": end,
                "city": None,
            }
        )
        if len(profile["education"]) >= 6:
            break

    # Languages: "Deutsch — C1" style only when explicit
    for ln in lines:
        m = re.search(
            r"\b(Deutsch|Englisch|Ukrainisch|Russisch|Polnisch|Französisch|Spanisch|Türkisch|Arabisch)\b"
            r"\s*[-–—:/]\s*(A1|A2|B1|B2|C1|C2|Muttersprache|fließend|Grundkenntnisse)",
            ln,
            re.I,
        )
        if m:
            profile["languages"].append(
                {"language": m.group(1), "level": m.group(2)}
            )

    if filename and not profile["personal"].get("full_name"):
        stem = re.sub(r"[_\-]+", " ", (filename.rsplit(".", 1)[0]))
        if 2 <= len(stem.split()) <= 4 and not re.search(r"\d{4}", stem):
            profile["personal"]["full_name"] = stem.title()

    profile["source_cv_text"] = raw[:20000]
    return normalize_profile(profile)


def missing_fields_for_action(action_id: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    """Return structured missing parameters — never invent to fill gaps."""
    action = (action_id or "").strip().lower()
    if action not in BEWERBUNG_ACTION_IDS:
        return []
    p = normalize_profile(profile)
    missing: list[str] = []

    if not (p["personal"].get("full_name") or "").strip():
        missing.append("personal.full_name")
    email = (p["personal"].get("email") or "").strip()
    phone = (p["personal"].get("phone") or "").strip()
    if not email and not phone:
        missing.append("personal.contact")
    if not (p["personal"].get("city") or "").strip():
        missing.append("personal.city")

    if action in {"lebenslauf_create", "lebenslauf_improve", "bewerbung_paket"}:
        exp_ok = _experience_complete(p["experience"])
        edu_ok = _education_complete(p["education"])
        if not exp_ok and not edu_ok:
            missing.append("experience_or_education")
        else:
            if p["experience"] and not exp_ok:
                missing.extend(_experience_gaps(p["experience"]))
            if p["education"] and not edu_ok and not exp_ok:
                missing.extend(_education_gaps(p["education"]))

    if action == "lebenslauf_improve":
        if not (p.get("source_cv_text") or "").strip() and not p["experience"] and not p["education"]:
            missing.append("source_cv")

    if action in {"bewerbungsschreiben", "bewerbung_paket"}:
        vac = p.get("vacancy") or {}
        title = (vac.get("title") or "").strip()
        company = (vac.get("company") or "").strip()
        text = (vac.get("text") or "").strip()
        if not title and not text:
            missing.append("vacancy.text_or_title")
        if not company and not title:
            missing.append("vacancy.company")

    # Deduplicate preserve order
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for fid in missing:
        if fid in seen:
            continue
        seen.add(fid)
        out.append(
            {
                "id": fid,
                "label_de": PROFILE_FIELD_LABELS_DE.get(fid, fid),
            }
        )
    return out


def profile_facts_index(profile: dict[str, Any]) -> dict[str, Any]:
    """Canonical facts for QA — only user-provided strings."""
    p = normalize_profile(profile)
    employers = [str(x.get("employer")) for x in p["experience"] if x.get("employer")]
    titles = [str(x.get("title")) for x in p["experience"] if x.get("title")]
    schools = [str(x.get("school")) for x in p["education"] if x.get("school")]
    degrees = [str(x.get("degree")) for x in p["education"] if x.get("degree")]
    langs = [f"{x.get('language')}:{x.get('level')}" for x in p["languages"]]
    dates = []
    for x in p["experience"] + p["education"]:
        for k in ("start", "end"):
            if x.get(k):
                dates.append(str(x[k]))
    contacts = [
        c
        for c in (
            p["personal"].get("email"),
            p["personal"].get("phone"),
            p["personal"].get("full_name"),
            p["personal"].get("city"),
        )
        if c
    ]
    return {
        "employers": employers,
        "titles": titles,
        "schools": schools,
        "degrees": degrees,
        "languages": langs,
        "dates": dates,
        "contacts": contacts,
        "skills": list(p["skills"]),
        "vacancy_title": (p["vacancy"] or {}).get("title"),
        "vacancy_company": (p["vacancy"] or {}).get("company"),
        "has_photo": bool(p.get("photo_material_id")),
    }


def _norm_exp(x: dict[str, Any]) -> dict[str, Any] | None:
    employer = _s(x.get("employer"))
    title = _s(x.get("title") or x.get("position"))
    start = _s(x.get("start") or x.get("from"))
    end = _s(x.get("end") or x.get("to") or x.get("until"))
    if not employer and not title:
        return None
    bullets = x.get("bullets") or x.get("tasks") or []
    if isinstance(bullets, str):
        bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
    return {
        "employer": employer,
        "title": title,
        "start": start,
        "end": end,
        "city": _s(x.get("city")),
        "bullets": [str(b).strip() for b in bullets if str(b).strip()][:12],
    }


def _norm_edu(x: dict[str, Any]) -> dict[str, Any] | None:
    school = _s(x.get("school") or x.get("institution"))
    degree = _s(x.get("degree") or x.get("field"))
    if not school and not degree:
        return None
    return {
        "school": school,
        "degree": degree,
        "start": _s(x.get("start") or x.get("from")),
        "end": _s(x.get("end") or x.get("to")),
        "city": _s(x.get("city")),
    }


def _norm_cert(x: dict[str, Any]) -> dict[str, Any] | None:
    name = _s(x.get("name") or x.get("title"))
    if not name:
        return None
    return {
        "name": name,
        "issuer": _s(x.get("issuer")),
        "year": _s(x.get("year") or x.get("date")),
    }


def _norm_lang(x: Any) -> dict[str, Any] | None:
    if isinstance(x, str):
        parts = re.split(r"[-–—:/]", x, maxsplit=1)
        if not parts[0].strip():
            return None
        return {
            "language": parts[0].strip(),
            "level": parts[1].strip() if len(parts) > 1 else None,
        }
    lang = _s(x.get("language") or x.get("name"))
    if not lang:
        return None
    return {"language": lang, "level": _s(x.get("level"))}


def _s(v: Any) -> str | None:
    if v is None:
        return None
    t = str(v).strip()
    return t or None


def _split_date_range(raw: str) -> tuple[str | None, str | None]:
    parts = re.split(r"\s*[-–—]|bis\s+", raw, maxsplit=1, flags=re.I)
    start = parts[0].strip() if parts else None
    end = parts[1].strip() if len(parts) > 1 else None
    return (start or None, end or None)


def _experience_complete(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return any(
        (r.get("employer") and r.get("title") and r.get("start")) for r in rows
    )


def _education_complete(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return any((r.get("school") and (r.get("degree") or r.get("start"))) for r in rows)


def _experience_gaps(rows: list[dict[str, Any]]) -> list[str]:
    gaps: list[str] = []
    for r in rows:
        if not r.get("employer"):
            gaps.append("experience.employer")
        if not r.get("title"):
            gaps.append("experience.title")
        if not r.get("start"):
            gaps.append("experience.start")
    return gaps[:3]


def _education_gaps(rows: list[dict[str, Any]]) -> list[str]:
    gaps: list[str] = []
    for r in rows:
        if not r.get("school"):
            gaps.append("education.school")
        if not r.get("degree") and not r.get("start"):
            gaps.append("education.degree")
    return gaps[:3]
