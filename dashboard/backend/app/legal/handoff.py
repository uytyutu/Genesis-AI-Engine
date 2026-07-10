"""Post-payment handoff explanations — Vector must communicate honestly in plain language."""

from __future__ import annotations

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME


def one_time_purchase_handoff() -> str:
    return (
        f"**Nach der Zahlung (Einmalkauf) — in einfachen Worten:**\n\n"
        "**Was Sie bekommen:**\n"
        "• das fertige Projekt (Website, Dokumente — je nach gebuchter Leistung)\n"
        "• Quellcode, soweit zur Leistung gehörend (HTML, CSS, JS)\n"
        "• ein ZIP-Archiv zum Download\n"
        "• Anleitungen, wie Sie alles nutzen und veröffentlichen können\n\n"
        "**Welche Rechte Sie haben:**\n"
        "• Nutzungsrechte gemäß unseren Bedingungen und dem gewählten Paket\n"
        "• Sie dürfen das Ergebnis für Ihr Business einsetzen\n"
        "• Details stehen in den AGB und unter Urheberrecht & Nutzungsrechte\n\n"
        f"**Was danach passiert:**\n"
        f"• {BRAND_NAME} ist für **diese Bestellung abgeschlossen**\n"
        "• Wir verwalten Ihr Projekt nicht weiter — es liegt bei Ihnen\n"
        "• Support nach Übergabe nur, wenn Sie das separat buchen\n\n"
        "**Domain — zwei häufige Fälle:**\n"
        "• **Domain über uns gekauft:** Sie erhalten Zugangsdaten und eine kurze Anleitung. "
        "Die Domain wird auf Sie als Inhaber übertragen — wir bleiben nicht Eigentümer.\n"
        "• **Domain gehört Ihnen bereits:** Wir zeigen Ihnen, welche DNS-Einträge Sie setzen "
        "müssen (z. B. A-Record oder CNAME), damit Ihre neue Website unter Ihrer Domain erreichbar ist.\n\n"
        "Fragen zur Übergabe? Schreiben Sie uns — wir erklären jeden Schritt ohne Fachchinesisch."
    )


def subscription_handoff() -> str:
    return (
        f"**Mit dem Abonnement — in einfachen Worten:**\n\n"
        "**Ihr Projekt bleibt bei uns:**\n"
        f"• das Projekt lebt weiter **innerhalb** von {BRAND_NAME}\n"
        "• Sie müssen nichts selbst hosten oder archivieren\n\n"
        f"**{ASSISTANT_NAME} bleibt an Ihrer Seite:**\n"
        f"• Sie arbeiten weiter mit {ASSISTANT_NAME} — Chat, Dateien, Stimme\n"
        "• die komplette **Projekthistorie** bleibt erhalten\n"
        "• **Projektspeicher**: alles, was wir gemeinsam erarbeitet haben, ist abrufbar\n\n"
        "**Was im Abo enthalten ist:**\n"
        "• fortlaufende Verbesserungen und neue Versionen im Rahmen Ihres Plans\n"
        "• Begleitung bei Änderungen — kein Neustart von null\n"
        "• das ist **kein Rabatt** auf einen Einmalkauf, sondern ein anderes Modell\n\n"
        "Kündigen Sie das Abo, bleiben Ihre bisherigen Ergebnisse nach den Bedingungen Ihres Plans "
        "erhalten — Details in den AGB."
    )


def handoff_rules_for_vector() -> str:
    return f"""## Nach Zahlung — Übergabe menschlich erklären

{ASSISTANT_NAME} **muss** nach Zahlung in **einfacher Sprache** erklären, was der Kunde erhält.
Kein Juristendeutsch. Kein Verstecken.

**Einmalkauf — Pflichtpunkte:**
• was der Kunde bekommt (Projekt, Code, ZIP, Anleitungen)
• welche Nutzungsrechte
• dass {BRAND_NAME} das Projekt danach **nicht mehr verwaltet**
• Domain: Fall „über uns gekauft“ vs. „Kunde besitzt Domain“ — beide erklären können

**Abonnement — Pflichtpunkte:**
• Projekt bleibt in {BRAND_NAME}
• Historie und Projektspeicher bleiben
• {ASSISTANT_NAME} begleitet weiter
• Verbesserungen im Rahmen des Abos

**Einmalkauf:**
{one_time_purchase_handoff()}

**Abonnement:**
{subscription_handoff()}

Nicht vermischen. Nicht andeuten, dass Abo = „günstiger Website-Kauf“."""
