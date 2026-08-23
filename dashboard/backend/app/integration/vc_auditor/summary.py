"""Rule-based AI Summary — answers: what should the owner fix first?"""

from __future__ import annotations

from typing import Any


def build_ai_summary(
    *,
    overall: int,
    findings: list[dict[str, Any]],
    website: dict[str, int],
    locale: str = "de",
) -> str:
    de = (locale or "de").lower().startswith("de")
    highs = [f for f in findings if f.get("severity") == "high"]
    meds = [f for f in findings if f.get("severity") == "medium"]

    if de:
        if overall >= 90 and not highs:
            return (
                "Ihr Auftritt wirkt professionell und weitgehend bereit für Kunden. "
                "Feintuning bei SEO und Trust-Signalen kann die Sichtbarkeit noch steigern."
            )
        parts = [
            f"Overall Business Score: {overall}/100.",
        ]
        if highs:
            top = "; ".join(str(f.get("message")) for f in highs[:3])
            parts.append(f"Priorität: {top}.")
        elif meds:
            top = "; ".join(str(f.get("message")) for f in meds[:3])
            parts.append(f"Nächste Verbesserungen: {top}.")
        weak = min(website.items(), key=lambda kv: kv[1])
        parts.append(
            f"Technisch am schwächsten: {weak[0].upper()} ({weak[1]}/100)."
        )
        parts.append(
            "Nach Korrektur der Prioritätspunkte ist eine spürbare Qualitätssteigerung zu erwarten."
        )
        return " ".join(parts)

    parts = [f"Overall Business Score: {overall}/100."]
    if highs:
        parts.append(
            "Priority: " + "; ".join(str(f.get("message")) for f in highs[:3]) + "."
        )
    elif meds:
        parts.append(
            "Next improvements: " + "; ".join(str(f.get("message")) for f in meds[:3]) + "."
        )
    weak = min(website.items(), key=lambda kv: kv[1])
    parts.append(f"Weakest technical area: {weak[0].upper()} ({weak[1]}/100).")
    parts.append("Fixing priority items should improve quality noticeably.")
    return " ".join(parts)
