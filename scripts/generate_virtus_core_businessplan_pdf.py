#!/usr/bin/env python3
"""Virtus Core Businessplan PDF — branded presentation edition (DE).

Structure mirrored from Oltiiev sample + investor-grade visuals:
brand cover, charts, screenshots, SWOT, BMC, roadmap, KPI, tech, legal.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from fpdf import FPDF  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "business" / "assets"
SHOTS = ASSETS / "screenshots"
CHARTS = ASSETS / "charts"
BRAND = ASSETS / "brand"
OUT_DESKTOP = Path.home() / "Desktop" / "Virtus_Core_Businessplan_Oltiiev.pdf"
OUT_REPO = ROOT / "docs" / "business" / "Virtus_Core_Businessplan_Oltiiev.pdf"

FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_B = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_I = Path(r"C:\Windows\Fonts\ariali.ttf")

# Live product brand (dark UI + emerald accent)
INK = (17, 24, 39)  # near-black text
MUTED = (100, 116, 139)
ACCENT = (0, 166, 126)  # #00A67E
ACCENT_DARK = (6, 95, 70)
NAVY = (11, 14, 17)
CARD = (248, 250, 252)
LINE = (226, 232, 240)
WHITE = (255, 255, 255)
SWOT_S = (16, 185, 129)
SWOT_W = (245, 158, 11)
SWOT_O = (59, 130, 246)
SWOT_T = (239, 68, 68)

W = 180
LEFT = 15


def _ensure_dirs() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    BRAND.mkdir(parents=True, exist_ok=True)


def _style_ax(ax) -> None:
    ax.set_facecolor("#F8FAFC")
    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")
    ax.tick_params(colors="#64748B", labelsize=9)
    ax.title.set_color("#0F172A")
    ax.yaxis.label.set_color("#334155")
    ax.xaxis.label.set_color("#334155")
    ax.grid(axis="y", color="#E2E8F0", linestyle="--", linewidth=0.8)


def build_charts() -> dict[str, Path]:
    _ensure_dirs()
    out: dict[str, Path] = {}
    years = ["Jahr 1", "Jahr 2", "Jahr 3"]
    # Umsatz unveraendert (Basis-Szenario)
    revenue = [11200, 45000, 73000]
    # Betriebsausgaben: kommerzielle Tarife fuer AI-Plattform (nicht Free-Tier)
    expenses = [4500, 12200, 20000]
    profit = [6700, 32800, 53000]
    mrr = [150, 450, 1200]

    # Revenue growth
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140)
    _style_ax(ax)
    bars = ax.bar(years, revenue, color="#00A67E", width=0.55, zorder=3)
    ax.plot(years, revenue, color="#0F172A", marker="o", linewidth=2, zorder=4)
    ax.set_title("Umsatzwachstum (Basis-Szenario, EUR)")
    ax.set_ylabel("EUR")
    for b, v in zip(bars, revenue):
        ax.text(b.get_x() + b.get_width() / 2, v + 1200, f"{v:,}".replace(",", "."), ha="center", fontsize=8, color="#0F172A")
    fig.tight_layout()
    p = CHARTS / "revenue_growth.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["revenue"] = p

    # Profit
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140)
    _style_ax(ax)
    ax.plot(years, profit, color="#00A67E", marker="o", linewidth=2.5, markersize=8)
    ax.fill_between(years, profit, color="#00A67E", alpha=0.18)
    ax.set_title("Betriebsergebnis (Basis-Szenario, EUR)")
    ax.set_ylabel("EUR")
    for x, v in zip(years, profit):
        ax.text(x, v + 1500, f"{v:,}".replace(",", "."), ha="center", fontsize=8)
    fig.tight_layout()
    p = CHARTS / "profit_growth.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["profit"] = p

    # Expenses bars
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140)
    _style_ax(ax)
    ax.bar(years, expenses, color="#64748B", width=0.55, zorder=3)
    ax.set_title("Betriebsausgaben (Orientierung, EUR)")
    ax.set_ylabel("EUR")
    for x, v in zip(years, expenses):
        ax.text(x, v + 400, f"{v:,}".replace(",", "."), ha="center", fontsize=8)
    fig.tight_layout()
    p = CHARTS / "expenses_bars.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["expenses"] = p

    # Expense pie Year 2 (~11.300 EUR)
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=140)
    labels = [
        "AI APIs",
        "Freelancer",
        "Marketing",
        "Admin/Ops",
        "Stripe",
        "Hosting/Cloud",
        "Dev-Tools",
        "E-Mail",
    ]
    sizes = [3000, 2400, 1800, 1740, 1125, 786, 876, 420]
    colors = ["#00A67E", "#64748B", "#34D399", "#0F172A", "#F59E0B", "#3B82F6", "#94A3B8", "#CBD5E1"]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90, textprops={"fontsize": 8}
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(8)
    ax.set_title("Kostenstruktur Jahr 2 (Beispielverteilung)")
    fig.tight_layout()
    p = CHARTS / "expenses_pie.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["pie"] = p

    # MRR forecast
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140)
    _style_ax(ax)
    ax.plot(years, mrr, color="#3B82F6", marker="s", linewidth=2.5, markersize=8)
    ax.fill_between(years, mrr, color="#3B82F6", alpha=0.15)
    ax.set_title("MRR-Prognose Ende Jahr (EUR / Monat, Basis)")
    ax.set_ylabel("EUR / Monat")
    for x, v in zip(years, mrr):
        ax.text(x, v + 40, str(v), ha="center", fontsize=8)
    fig.tight_layout()
    p = CHARTS / "mrr_forecast.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["mrr"] = p

    # Roadmap visual
    fig, ax = plt.subplots(figsize=(8.2, 3.8), dpi=140)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.set_facecolor("white")
    phases = [
        (1.2, "2026", "Launch\nFirst Clients", "#00A67E"),
        (3.4, "2027", "Germany\nAI Bots / MRR", "#059669"),
        (5.6, "2028", "DACH\nEurope", "#0F766E"),
        (7.8, "2029", "SaaS Platform\nMarketplace", "#0F172A"),
    ]
    ax.plot([1.2, 7.8], [2.2, 2.2], color="#CBD5E1", linewidth=4, zorder=1)
    for x, year, label, color in phases:
        ax.scatter([x], [2.2], s=420, color=color, zorder=3)
        ax.text(x, 3.15, year, ha="center", fontsize=11, fontweight="bold", color="#0F172A")
        ax.text(x, 1.05, label, ha="center", fontsize=8, color="#334155")
        ax.text(x, 2.2, "✓", ha="center", va="center", fontsize=10, color="white", fontweight="bold", zorder=4)
    ax.set_title("Roadmap 2026–2029", fontsize=12, fontweight="bold", color="#0F172A", pad=8)
    fig.tight_layout()
    p = CHARTS / "roadmap.png"
    fig.savefig(p, facecolor="white")
    plt.close(fig)
    out["roadmap"] = p

    return out


class BP(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4", unit="mm")
        self.set_margins(LEFT, 22, LEFT)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("F", "", str(FONT))
        self.add_font("F", "B", str(FONT_B))
        self.add_font("F", "I", str(FONT_I))

    def header(self) -> None:
        if self.page_no() <= 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 12, "F")
        self.set_xy(LEFT, 3)
        self.set_font("F", "B", 8)
        self.set_text_color(*WHITE)
        self.cell(120, 6, "VIRTUS CORE  ·  Businessplan")
        self.set_font("F", "", 8)
        self.cell(60, 6, "Ramish Oltiiev", align="R")
        self.set_text_color(*INK)
        self.set_y(16)
        self.set_x(LEFT)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_draw_color(*LINE)
        self.line(LEFT, self.get_y(), LEFT + W, self.get_y())
        self.set_y(-12)
        self.set_x(LEFT)
        self.set_font("F", "", 8)
        self.set_text_color(*MUTED)
        self.cell(W / 2, 8, "virtus-core  ·  vertraulich")
        self.cell(W / 2, 8, str(self.page_no()), align="R")

    def section_break(self) -> None:
        self.add_page()

    def h1(self, t: str) -> None:
        self.set_x(LEFT)
        self.set_fill_color(*ACCENT)
        self.rect(LEFT, self.get_y(), 3, 8, "F")
        self.set_xy(LEFT + 6, self.get_y())
        self.set_font("F", "B", 14)
        self.set_text_color(*INK)
        self.multi_cell(W - 6, 8, t)
        self.ln(2)

    def h2(self, t: str) -> None:
        self.set_x(LEFT)
        self.set_font("F", "B", 11)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(W, 7, t)
        self.set_text_color(*INK)
        self.ln(1)

    def p(self, t: str) -> None:
        self.set_x(LEFT)
        self.set_font("F", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(W, 5.8, t)
        self.ln(1.5)

    def bullets(self, items: list[str]) -> None:
        self.set_font("F", "", 10.5)
        for item in items:
            self.set_x(LEFT)
            self.set_text_color(*ACCENT)
            self.cell(5, 5.8, "●")
            self.set_text_color(*INK)
            self.multi_cell(W - 5, 5.8, item)
        self.ln(1.5)

    def callout(self, t: str) -> None:
        y = self.get_y()
        self.set_fill_color(*CARD)
        self.set_draw_color(*ACCENT)
        self.rect(LEFT, y, W, 18, "FD")
        self.set_xy(LEFT + 4, y + 3)
        self.set_font("F", "I", 10)
        self.set_text_color(*INK)
        self.multi_cell(W - 8, 5.5, t)
        self.set_y(y + 20)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        assert abs(sum(widths) - W) < 0.6
        self.set_x(LEFT)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("F", "B", 9)
        for i, h in enumerate(headers):
            self.cell(widths[i], 7, h, border=0, fill=True)
        self.ln()
        self.set_font("F", "", 8)
        self.set_text_color(*INK)
        for r_i, row in enumerate(rows):
            self.set_x(LEFT)
            if r_i % 2 == 0:
                self.set_fill_color(255, 255, 255)
            else:
                self.set_fill_color(*CARD)
            for i, cell in enumerate(row):
                txt = (cell or "").replace("\n", " ")
                if len(txt) > 58:
                    txt = txt[:55] + "..."
                self.cell(widths[i], 6.2, txt, border=0, fill=True)
            self.ln()
        self.ln(3)
        self.set_x(LEFT)

    def img(self, path: Path, h: float = 72) -> None:
        if not path.exists():
            self.p(f"[Bild fehlt: {path.name}]")
            return
        self.set_x(LEFT)
        # keep aspect
        with Image.open(path) as im:
            w_px, h_px = im.size
        aspect = w_px / max(h_px, 1)
        width = min(W, h * aspect)
        if width > W:
            width = W
            h = width / aspect
        x = LEFT + (W - width) / 2
        self.image(str(path), x=x, y=self.get_y(), w=width, h=h)
        self.ln(h + 4)

    def caption(self, t: str) -> None:
        self.set_x(LEFT)
        self.set_font("F", "I", 9)
        self.set_text_color(*MUTED)
        self.multi_cell(W, 5, t)
        self.set_text_color(*INK)
        self.ln(2)


def build() -> Path:
    charts = build_charts()
    pdf = BP()
    today = date.today().strftime("%d.%m.%Y")
    mark = BRAND / "mark.png"

    # ===== COVER =====
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 297, "F")
    # accent stripe
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, 8, 297, "F")
    if mark.exists():
        pdf.image(str(mark), x=78, y=42, w=54, h=54)
    pdf.set_xy(LEFT, 110)
    pdf.set_font("F", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.multi_cell(W, 12, "BUSINESSPLAN", align="C")
    pdf.set_font("F", "B", 18)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(W, 10, "VIRTUS CORE", align="C")
    pdf.ln(4)
    pdf.set_font("F", "", 12)
    pdf.set_text_color(200, 210, 220)
    pdf.multi_cell(
        W,
        7,
        "Digitale AI-Plattform & Services fuer KMU\n"
        "Einzelunternehmen · Dresden · Deutschland",
        align="C",
    )
    pdf.ln(16)
    pdf.set_font("F", "", 11)
    pdf.set_text_color(*WHITE)
    for line in (
        "Kunde: Herr Oltiiev Ramish",
        "Marke: Virtus Core  |  AI-Interface: Vector",
        f"Dokumentstand: {today}",
        "Version: Branded Presentation Edition 2026",
    ):
        pdf.set_x(LEFT)
        pdf.multi_cell(W, 7, line, align="C")
    pdf.set_y(260)
    pdf.set_font("F", "I", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(W, 5, "Keine Rechts- oder Steuerberatung. Zahlen = realistische Schaetzungen.", align="C")

    # ===== TOC =====
    pdf.add_page()
    pdf.h1("Inhaltsverzeichnis")
    toc = [
        "Executive Summary",
        "Screenshots of the Virtus Core Platform",
        "Ausfuehrungen zum Gruendungsvorhaben",
        "Geschaeftsidee · Leistungsangebot · Zeitplan",
        "Motivation und Leidenschaft",
        "Business Model Canvas",
        "SWOT-Analyse",
        "Roadmap 2026-2029",
        "Marktabgrenzung · Kompetenzen · Erfolgsfaktoren",
        "Risiken · Risikomanagement · Ziele Jahr 1",
        "KPI-Rahmen",
        "Technology Stack",
        "Legal & GDPR / DSGVO",
        "Investitionen · Rechtsform · Personal",
        "Konkurrenz · Marketing · Zielgruppe",
        "Finanzplanung & Diagramme",
        "Fazit",
        "Anhang",
    ]
    pdf.set_font("F", "", 11)
    for i, t in enumerate(toc, 1):
        pdf.set_x(LEFT)
        pdf.set_text_color(*ACCENT)
        pdf.cell(10, 7, f"{i:02d}")
        pdf.set_text_color(*INK)
        pdf.multi_cell(W - 10, 7, t)

    # ===== Executive Summary =====
    pdf.section_break()
    pdf.h1("Executive Summary")
    pdf.h2("Geschäftsvorhaben")
    pdf.p(
        "Ramish Oltiiev betreibt und entwickelt Virtus Core – eine digitale Plattform und "
        "AI-gestützte Dienstleistungsfirma mit Sitz in Dresden. Die Dienstleistungen werden "
        "deutschlandweit digital angeboten; perspektivisch auch international. Virtus Core "
        "ist keine klassische Webagentur und kein reiner Chatbot-Anbieter. Das Unternehmen "
        "baut eine operative digitale Infrastruktur für kleine und mittlere Unternehmen: "
        "moderne Websites, AI-Assistenten (Vector / AI Digital Employee), Website-Analyse "
        "und Reparatur sowie automatisierte Vertriebs- und Produktionsprozesse."
    )
    pdf.callout(
        "Status 2026: Arbeitsfähige Beta-Plattform live (beta.genesis-ai-engine.com). "
        "Mission 1: erster zahlender Fremdkunde. Finanzplanung bewusst ehrlich und szenariobasiert."
    )
    pdf.h2("Erfolgsfaktoren")
    pdf.bullets(
        [
            "Eigene produktive Plattform (Bestellflow, Produktion, Kundenbereich, AI-Beratung).",
            "Klare Preise DE: Basic 350 € · Business 650 € · Premium 1.200 €.",
            "AI Digital Employee: Setup ab 499 € + monatlich ab 99 €.",
            "Vector als digitaler Mitarbeiter – Differenzierung gegenüber ChatGPT und Agenturen.",
            "Lean-Kostenstruktur – kontrollierte Fixkosten, kommerzielle Tarife statt Free-Tier.",
        ]
    )
    pdf.h2("Markt & Go-to-Market")
    pdf.p(
        "Firmensitz: Dresden. "
        "Zielgruppe: KMU in Deutschland – bundesweit digital erreichbar; perspektivisch auch internationale Kunden. "
        "Kanäle: Storefront, Vector-Beratung, Acquisition Studio / Outreach, später Case Studies und Meta Ads. "
        "Wettbewerb: Baukästen, Agenturen, generische AI – Virtus Core liefert Paket + Status + Delivery."
    )

    # ===== SCREENSHOTS =====
    pdf.section_break()
    pdf.h1("Screenshots of the Virtus Core Platform")
    pdf.p(
        "Die folgenden Aufnahmen stammen von der öffentlichen Beta (Sprache: Deutsch, "
        "Markt: DE). Sie belegen: Virtus Core ist kein reines Konzeptpapier, sondern ein "
        "laufendes Produkt. Russische UI-Screenshots gehoeren nicht in diesen Businessplan."
    )
    shots = [
        (SHOTS / "01_home.png", "01 · Storefront / Hauptseite (/site) — DE"),
        (SHOTS / "07_products.png", "02 · Produktkatalog / Services — DE"),
        (SHOTS / "02_order.png", "03 · Bestellstrecke Website-Paket (/order) — DE"),
        (SHOTS / "06_bot_order.png", "04 · AI Digital Employee — Bot-Bestellung — DE"),
        (SHOTS / "05_vector.png", "05 · AI Vector — CTA auf der Storefront — DE"),
        (SHOTS / "03_impressum.png", "06 · Impressum (Legal) — DE"),
        (SHOTS / "04_datenschutz.png", "07 · Datenschutz / DSGVO — DE"),
    ]
    for path, caption in shots:
        if pdf.get_y() > 160:
            pdf.section_break()
            pdf.h1("Screenshots (Fortsetzung)")
        pdf.h2(caption)
        pdf.img(path, h=78)
        pdf.caption("Quelle: beta.genesis-ai-engine.com · Live-Produktstand")

    # ===== Gründung / Idee =====
    pdf.section_break()
    pdf.h1("Ausführungen zum Gründungsvorhaben")
    pdf.p(
        "Herr Oltiiev baut Virtus Core als Einzelunternehmen (Tornaer Straße 23, 01237 Dresden). "
        "Öffentliche Marke: Virtus Core; Vector ist das AI-Gesicht gegenüber Kunden. "
        "Virtus Core konzentriert sich vollständig auf Softwareentwicklung, digitale "
        "Dienstleistungen und KI-Automatisierung."
    )
    pdf.h1("Detaillierte Beschreibung der Geschäftsidee")
    pdf.h2("1. Professionelle Websites (Path A)")
    pdf.p("Paketierte Landing-Websites mit digitaler Lieferung; Domain/Hosting beim Kunden.")
    pdf.h2("2. AI Digital Employee / Business-Bots")
    pdf.p("Setup + Monatsgebühr → wiederkehrender Umsatz (MRR).")
    pdf.h2("3. Analyse & Reparatur")
    pdf.p("Kostenlose Analyse als Einstieg; Reparaturstufen als Alternative zum Neubau.")
    pdf.h2("4. Plattform-Asset")
    pdf.p("Eigene Engine für Beratung, Aufträge, Produktion und Outreach – Grundlage für spätere SaaS.")

    pdf.section_break()
    pdf.h1("Detailliertes Leistungsangebot")
    pdf.table(
        ["Paket", "Preis", "Inhalt"],
        [
            ["Website Basic", "350 EUR", "Landing, ZIP, Anleitung, Rechtsvorlagen"],
            ["Website Business", "650 EUR", "Basic + Go-live-Hilfe, 1 Korrekturrunde"],
            ["Website Premium", "1.200 EUR", "Premium-Design, Assisted Go-live"],
            ["Bot Starter", "499 + 99/Mo", "AI Digital Employee Einstieg"],
            ["Bot Business", "999 + 199/Mo", "Erweiterte Kanäle / Betreuung"],
            ["Bot Professional", "1.499 + 349/Mo", "Premium-Setup & Support"],
        ],
        [45, 40, 95],
    )
    pdf.h1("Zeitplan (Jahr 1)")
    pdf.bullets(
        [
            "Monate 0-3: Stabilisierung Beta, Rechtliches, erste Aufträge.",
            "Monate 4-6: Wiederholbare Delivery, erste Bot-MRR.",
            "Monate 7-9: Skalierung Outreach (Qualität vor Masse).",
            "Ab Monat 10: Konsolidierung DE, Prüfung SaaS-Bausteine.",
        ]
    )

    # ===== Motivation =====
    pdf.section_break()
    pdf.h1("Motivation und Leidenschaft")
    pdf.p(
        "Ziel: KMUs einen vollständigen digitalen Arbeitsweg geben – ohne Programmierer, "
        "Agentur und ChatGPT separat orchestrieren zu müssen. Vector führt das Projekt; "
        "die Plattform liefert sichtbare Ergebnisse."
    )
    pdf.h2("Technische Expertise")
    pdf.p(
        "Herr Oltiiev hat eine Full-Stack-Plattform aufgebaut und betreibt sie operativ: "
        "Frontend, Backend, AI-Routing, Bestell- und Delivery-Prozesse. Der Fokus liegt "
        "nicht auf Demo-Prototypen, sondern auf einem laufenden Produkt, das Kunden "
        "bestellen und erhalten koennen."
    )
    pdf.h2("Vision")
    pdf.p(
        "Virtus Core als digitale Firma, in der Vector der Partner des Kunden ist – "
        "nicht nur ein Textgenerator. Emotionaler Nordstern: „Wir haben das zusammen "
        "gebaut“ – nicht „die AI hat etwas generiert“."
    )
    pdf.h2("Strategisches Denken")
    pdf.p(
        "Prioritaet Mission 1 (erster zahlender Fremdkunde) vor Feature-Ueberbau. "
        "Horizon-Themen bleiben Design-only, bis Delivery und Vertrieb tragen. "
        "Persoenliche Treiber: Unabhaengigkeit, realer Kundennutzen in DE und Aufbau "
        "eines skalierbaren Software-Assets."
    )

    pdf.section_break()
    pdf.h1("Schilderung des Vorhabens")
    pdf.p(
        "Der Kunde spricht mit Vector, bestellt ein Paket, erhaelt ein sichtbares Ergebnis "
        "(Website / Bot / Analyse) und kann spaeter weitere Leistungen ueber dieselbe "
        "Beziehung beziehen. Herr Oltiiev verbindet Produktentwicklung, Betrieb und Vertrieb."
    )
    pdf.h1("Vorteile gegenueber anderen Branchen")
    pdf.bullets(
        [
            "Geringere Kapitalbindung als produktions- oder handelsintensive Branchen",
            "Digitale Lieferung ohne Lager und Fuhrpark",
            "Skalierung ueber Software und Vorlagen",
            "Projektumsatz + Recurring-Potenzial (Bots)",
            "Standortunabhaengigkeit (bundesweit / spaeter EU)",
        ]
    )

    # ===== BMC =====
    pdf.section_break()
    pdf.h1("Business Model Canvas")
    pdf.p("Klassisches Canvas – in Deutschland häufig erwartet bei Gründung und Finanzierung.")
    blocks = [
        ("Key Partners", "Cloud/Hosting (Vercel, Cloudflare), AI-API-Anbieter, Stripe, ggf. Freelancer Design/Delivery"),
        ("Key Activities", "Produktpflege, Delivery Websites/Bots, Outreach/Acquisition, Support via Vector"),
        ("Key Resources", "Eigene Plattform, Marke Virtus Core/Vector, Know-how des Gründers, Vorlagen"),
        ("Value Proposition", "Paketierte digitale Ergebnisse + AI-Mitarbeiter + Status/Delivery statt nur Chat"),
        ("Customer Relationships", "Self-Serve Checkout, Vector-Beratung, Kabinett/Workspace nach Kauf"),
        ("Channels", "Storefront, Outreach, Empfehlungen, Content/Case Studies, spaeter Ads"),
        ("Customer Segments", "KMU DE: Handwerk, Praxen, lokale Services, Gruender mit schnellem Online-Bedarf"),
        ("Cost Structure", "Kommerzielle Cloud/API/SaaS (AI, Hosting, Cursor, E-Mail, Stripe) + Sweat Equity; keine Free-Tier-Darstellung"),
        ("Revenue Streams", "Einmalige Website-Pakete + Setup-Gebuehren + monatliche Bot-MRR"),
    ]
    for title, body in blocks:
        y = pdf.get_y()
        if y > 250:
            pdf.section_break()
            pdf.h1("Business Model Canvas (Fortsetzung)")
        pdf.set_fill_color(*CARD)
        pdf.set_draw_color(*ACCENT)
        pdf.set_x(LEFT)
        h = 22
        pdf.rect(LEFT, pdf.get_y(), W, h, "FD")
        pdf.set_xy(LEFT + 3, pdf.get_y() + 2)
        pdf.set_font("F", "B", 10)
        pdf.set_text_color(*ACCENT_DARK)
        pdf.cell(W - 6, 5, title)
        pdf.ln(6)
        pdf.set_x(LEFT + 3)
        pdf.set_font("F", "", 9)
        pdf.set_text_color(*INK)
        pdf.multi_cell(W - 6, 4.5, body)
        pdf.ln(3)

    # ===== SWOT =====
    pdf.section_break()
    pdf.h1("SWOT-Analyse")
    pdf.p("Kompakte Matrix für Bank / Jobcenter / Investoren-Gespräche.")

    def swot_box(x: float, y: float, title: str, color: tuple[int, int, int], lines: list[str]) -> None:
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 88, 8, "F")
        pdf.set_xy(x + 2, y + 1.5)
        pdf.set_font("F", "B", 10)
        pdf.set_text_color(*WHITE)
        pdf.cell(84, 5, title)
        pdf.set_fill_color(*CARD)
        pdf.set_draw_color(*LINE)
        pdf.rect(x, y + 8, 88, 52, "FD")
        pdf.set_text_color(*INK)
        pdf.set_font("F", "", 8.5)
        pdf.set_xy(x + 3, y + 11)
        for line in lines:
            pdf.set_x(x + 3)
            pdf.multi_cell(82, 4.5, f"• {line}")

    y0 = pdf.get_y()
    swot_box(LEFT, y0, "Strengths (Staerken)", SWOT_S, [
        "Eigene AI-Plattform & Delivery",
        "Klare Paketpreise",
        "Lean Fixkosten",
        "Vector als Differenzierung",
    ])
    swot_box(LEFT + 92, y0, "Weaknesses (Schwaechen)", SWOT_W, [
        "Neuer Marke / geringe Awareness",
        "Noch kein Fremdumsatz",
        "Gruenderzentrierung",
        "Begrenzte Brand-Historie",
    ])
    swot_box(LEFT, y0 + 64, "Opportunities (Chancen)", SWOT_O, [
        "Wachstum AI- & Digitalmarkt",
        "KMU-Nachholbedarf Websites",
        "Recurring via Bots (MRR)",
        "EU-Expansion vorbereitet",
    ])
    swot_box(LEFT + 92, y0 + 64, "Threats (Risiken)", SWOT_T, [
        "Starke Konkurrenz (Baukaesten/Agenturen)",
        "API-/Cloud-Abhaengigkeit",
        "Conversion-Unsicherheit",
        "Compliance / Outreach-Reputation",
    ])
    pdf.set_y(y0 + 130)

    # ===== Roadmap =====
    pdf.section_break()
    pdf.h1("Roadmap 2026–2029")
    pdf.p("Mehrjährige Perspektive – nach Evidence skaliert, nicht vor dem ersten Euro.")
    pdf.img(charts["roadmap"], h=70)
    pdf.table(
        ["Jahr", "Schwerpunkt", "Meilensteine"],
        [
            ["2026", "Launch", "Beta stabil, First Clients, Delivery-Prozess"],
            ["2027", "Germany + Bots", "Wiederholverkauf DE, MRR aus AI Bots"],
            ["2028", "DACH / Europe", "Selektive Expansion, lokale Preise/Sprachen"],
            ["2029", "SaaS / Marketplace", "Plattform-Abo-Bausteine, Partner-Oekosystem"],
        ],
        [28, 45, 107],
    )

    # ===== Markt / Kompetenzen =====
    pdf.section_break()
    pdf.h1("Marktabgrenzung von Virtus Core")
    pdf.p(
        "Firmensitz ist Dresden (Einzelunternehmen). Die primäre Zielgruppe sind kleine und "
        "mittlere Unternehmen (KMU) in Deutschland. Durch die digitale Arbeitsweise können "
        "Dienstleistungen bundesweit erbracht werden. Perspektivisch ist auch die Betreuung "
        "internationaler Kunden möglich."
    )
    pdf.bullets(
        [
            "Sitz: Dresden (rechtlicher Firmensitz / Impressum).",
            "Markt: Deutschland bundesweit – digitale Lieferung ohne regionale Werkstattbindung.",
            "Perspektive: internationale Kunden bei skalierbarer digitaler Leistungserbringung.",
            "Zielgruppe: KMU ohne moderne Website / mit Bot-Bedarf (Handwerk, Praxen, lokale Services, Gruender).",
            "Leistung: nur verkaufbare Lieferpfade oeffentlich anbieten.",
            "Abgrenzung: fertige Lieferung + AI-Begleitung + Status.",
        ]
    )
    pdf.h1("Fachliche Kompetenzen")
    pdf.bullets(
        [
            "Full-Stack-Plattform (Frontend, Backend, AI-Routing)",
            "Produktisierung digitaler Services & Checkout",
            "Automation Outreach / Quality Gates",
            "Mehrsprachige Markt-/Preislogik",
        ]
    )
    pdf.h1("Kaufmännische Kompetenzen")
    pdf.bullets(
        [
            "Klare Preisarchitektur und Lean Finance",
            "Priorisierung Mission 1 vor Feature-Ueberbau",
            "Ehrliche Szenarien statt Fake-ARR",
        ]
    )
    pdf.h1("Erfolgsfaktoren")
    pdf.bullets(
        [
            "Produkt bereits live (Beta)",
            "Differenzierung Vector + Delivery",
            "Recurring-Potenzial Bots",
            "Niedrige Fixkosten",
        ]
    )

    # ===== Risiken =====
    pdf.section_break()
    pdf.h1("Risiken für Virtus Core")
    pdf.bullets(
        [
            "Conversion noch unbewiesen (pre-revenue)",
            "Wettbewerb Baukaesten/Agenturen",
            "Abhaengigkeit Cloud/AI-APIs",
            "Gruender-Ausfallrisiko",
            "Datenschutz / Outreach-Compliance",
        ]
    )
    pdf.h1("Risikomanagement")
    pdf.bullets(
        [
            "Quality Gate im Outreach",
            "Nur verkaufbare Produkte oeffentlich",
            "Kostenkontrolle: kommerzielle Tarife, Nutzung ueberwachen, kein kuenstliches Aufblaehen",
            "Stufenweise Expansion nach Evidence",
            "Rechtstexte: Impressum, AGB, Datenschutz",
        ]
    )
    pdf.h1("Ziele Jahr 1")
    pdf.bullets(
        [
            "Q1: Erster zahlender Fremdkunde",
            "Q2: 4-8 Websites kumuliert, erste Bot-MRR",
            "Q3: Wiederholbare Pipeline",
            "Q4: Infrastrukturkosten selbsttragend",
        ]
    )

    # ===== KPI =====
    pdf.section_break()
    pdf.h1("KPI-Rahmen (Key Performance Indicators)")
    pdf.p("Messgrößen für Steuerung und Reporting – Zielkorridore Jahr 1 (Orientierung).")
    pdf.table(
        ["KPI", "Definition", "Jahr-1-Ziel (Orientierung)"],
        [
            ["Website Sales", "Bezahlte Website-Pakete", "6-20 Auftraege"],
            ["AI Bots", "Aktive Bot-Setups", "1-5"],
            ["MRR", "Monatliche Bot-Umsaetze", "99-500 EUR/Mo Ende Jahr"],
            ["AOV", "Average Order Value Websites", "350-650 EUR"],
            ["CSAT", "Kundenzufriedenheit", "Case Studies + Feedback"],
            ["Retention", "Bot-Kuendigungsquote", "< 15%/Quartal anstreben"],
            ["Conversion", "Besucher -> Zahlung", "messen & verbessern"],
            ["Delivery Time", "Zeit bis Lieferung", "im Paketrahmen halten"],
        ],
        [40, 70, 70],
    )

    # ===== Tech Stack =====
    pdf.section_break()
    pdf.h1("Technology Stack")
    pdf.p("Technische Basis der Plattform – relevant für Glaubwürdigkeit als Tech-Geschäft.")
    pdf.table(
        ["Schicht", "Technologie", "Rolle"],
        [
            ["Backend", "Python / FastAPI", "API, Business-Logik, AI-Routing"],
            ["Frontend", "Next.js", "Storefront, Kabinett, UI"],
            ["Daten", "JSONL / DB-Layer", "Auftraege, Reviews, State"],
            ["Hosting FE", "Vercel", "Frontend-Deployment"],
            ["Edge / DNS", "Cloudflare", "DNS, Schutz, Edge"],
            ["Payments", "Stripe", "Checkout & Abrechnung"],
            ["AI", "AI APIs", "Vector / Bots / Analyse"],
            ["Ops", "Docker-faehig", "Reproduzierbare Runtime"],
            ["Desktop", "Genesis.exe / Launcher", "CEO-Tagespfad lokal"],
        ],
        [35, 45, 100],
    )
    pdf.callout("Stack-Hinweis: konkrete Provider koennen sich weiterentwickeln; Architektur bleibt Service-first.")

    # ===== Legal =====
    pdf.section_break()
    pdf.h1("Legal & GDPR / DSGVO")
    pdf.p("Deutschland-Fokus: rechtliche Sichtbarkeit ist Teil der Produktreife.")
    pdf.bullets(
        [
            "DSGVO / Datenschutz: oeffentliche Datenschutzseite und Cookie-Hinweise.",
            "Impressum: Ramish Oltiiev / Virtus Core, Dresden (Einzelunternehmen).",
            "AGB / Widerruf / Cookies / KI-Hinweis auf der Storefront verlinkt.",
            "SSL/TLS: HTTPS auf der oeffentlichen Beta.",
            "Secure Payments: Stripe Checkout.",
            "Hosting: EU-/westliche Cloud-Anbieter (Frontend Vercel, DNS Cloudflare).",
            "Datensparsamkeit: nur verkaufs- und lieferrelevante Daten im Prozess.",
        ]
    )
    pdf.p(
        "Dieser Abschnitt ersetzt keine Rechtsberatung. Vor Skalierung: laufende Prüfung "
        "von Auftragsverarbeitung, Newsletter/Outreach-Einwilligungen und AV-Verträgen."
    )

    # ===== Invest / Legal form / HR =====
    pdf.section_break()
    pdf.h1("Investitionen")
    pdf.p(
        "Virtus Core braucht keine Werkstatt oder Fahrzeugflotte. Die relevanten Kosten "
        "sind digitale Betriebsmittel einer AI-Plattform. Ansatz: realistische kommerzielle "
        "Tarife fuer den laufenden Betrieb – nicht kuenstlich aufgeblaeht, aber auch nicht "
        "als Free-Tier dargestellt."
    )
    pdf.p(
        "Für den professionellen Betrieb von Virtus Core werden mehrere KI-Dienste parallel "
        "eingesetzt. Dazu gehören API-Dienste für Kundenanwendungen sowie produktiv genutzte "
        "KI-Assistenzsysteme für Entwicklung, Dokumentation, Qualitätssicherung und Support."
    )
    pdf.h2("Laufende Betriebsmittel (Orientierung Monat)")
    pdf.table(
        ["Posten", "Monat ca.", "Kommentar"],
        [
            ["AI APIs", "80-150 EUR", "OpenAI / Anthropic / Gemini o.ae. Arbeitsbudget"],
            ["Cursor Pro", "ca. 19 EUR", "Entwicklung der Plattform (~20 USD)"],
            ["ChatGPT Plus / Pro", "ca. 23-25 EUR", "KI-Unterstuetzung fuer Entwicklung, Analyse, Dokumentation und Kundenkommunikation"],
            ["Vercel Pro", "ca. 19 EUR", "Frontend-Hosting kommerziell"],
            ["Backend-Hosting", "15-25 EUR", "Railway o.ae. fuer API/Services"],
            ["Cloudflare", "0-19 EUR", "DNS/CDN Free; Pro bei Bedarf"],
            ["Domains / DNS", "ca. 2 EUR", "ca. 15-25 EUR/Jahr"],
            ["Resend (E-Mail)", "ca. 19 EUR", "Transaktional + Outreach"],
            ["Monitoring / Backup", "10-20 EUR", "Uptime, Logs, Sicherungen"],
            ["Weitere SaaS", "15-30 EUR", "GitHub, Tools, Ops"],
            ["Buchfuehrung", "30-40 EUR", "Steuer/Admin Orientierung"],
        ],
        [50, 35, 95],
    )
    pdf.h2("Variable Kosten")
    pdf.bullets(
        [
            "Stripe-Gebuehren: typisch ca. 1,5% + 0,25 EUR je EU-Kartenzahlung (im Plan ca. 2,5% vom Umsatz als Pauschale).",
            "AI-API-Kosten steigen mit Kundennutzung (Vector, Bots, Analyse) – Arbeitsbudget, nicht Minimal-Tarif.",
            "Marketing: Jahr 1 organisch/Outreach plus kleine Meta-Ads-Tests nach ersten Referenzen; Ausbau nur bei positiver Wirtschaftlichkeit.",
            "Freelancer: nur bei Auslastung (Delivery/Design), nicht als Fixkostenblock Jahr 1.",
        ]
    )
    pdf.h2("Start / einmalig")
    pdf.table(
        ["Posten", "Schaetzung", "Kommentar"],
        [
            ["Domain-Registrierung", "15-25 EUR/Jahr", "aktuelle Beta-Domain, spaeter Virtus-Core-Domain"],
            ["Account-Setup Cloud/SaaS", "gering", "Zeitaufwand / Sweat Equity"],
            ["Hardware Buero", "vorhanden", "kein Sonderinvest noetig"],
            ["Sweat Equity", "hoch", "Hauptinvestition des Gruenders"],
        ],
        [55, 40, 85],
    )
    pdf.caption(
        "Hinweis: USD-Tarife (Cursor, ChatGPT, Vercel, Resend) sind in EUR gerundet. "
        "Exakte Betraege schwanken mit Wechselkurs und Nutzung."
    )
    pdf.h1("Wahl der Rechtsform")
    pdf.p("Einzelunternehmen – passend zur Frühphase. Später UG/GmbH prüfbar bei Umsatz/Haftung/Team.")
    pdf.h1("Personalplanung")
    pdf.p("Jahr 1: Gründer solo; bei Auslastung punktuelle Freelancer. Keine große feste Belegschaft.")

    # ===== Competition / Marketing / Audience =====
    pdf.section_break()
    pdf.h1("Konkurrenzanalyse")
    pdf.table(
        ["Typ", "Staerke", "Luecke vs Virtus Core"],
        [
            ["Website-Baukasten", "guenstig/schnell", "Kunde bleibt allein"],
            ["Agentur", "Design-Tiefe", "teurer/langsamer"],
            ["ChatGPT", "Texte/Ideen", "kein Delivery/Status"],
            ["Freelancer", "flexibel", "Qualitaet ungleich"],
        ],
        [40, 50, 90],
    )
    pdf.h1("Marketingstrategie")
    pdf.bullets(
        [
            "Storefront + Vector-Beratung",
            "Acquisition Studio / qualifizierter Outreach",
            "Case Studies nach ersten Lieferungen",
            "Meta Ads (Facebook/Instagram): geplanter Werbekanal nach den ersten Referenzprojekten. Kleine Testbudgets zum Kundengewinn, Ausbau nur bei positiver Wirtschaftlichkeit.",
        ]
    )
    pdf.h1("Zielgruppenanalyse")
    pdf.p(
        "Firmensitz: Dresden. Die primäre Zielgruppe sind kleine und mittlere Unternehmen "
        "(KMU) in Deutschland. Durch die digitale Arbeitsweise können Dienstleistungen "
        "bundesweit erbracht werden. Perspektivisch ist auch die Betreuung internationaler "
        "Kunden möglich."
    )
    pdf.bullets(
        [
            "Handwerk & lokale Services",
            "Praxen / Beratungsberufe",
            "Gruender mit Bedarf an schnellem Auftritt",
            "Nicht primaer: Konzerne mit eigener IT",
        ]
    )

    # ===== Finance + charts =====
    pdf.section_break()
    pdf.h1("Finanzplanung & Diagramme")
    pdf.p(
        "Grundsatz: ehrlich. Aktuell 0 EUR Fremdumsatz. Umsatz-Basis-Szenario unveraendert. "
        "Betriebsausgaben spiegeln kommerzielle Tarife einer AI-Plattform wider "
        "(APIs, Cursor, ChatGPT, Hosting, E-Mail, Stripe, Ops) – ohne kuenstliche Aufblaehung."
    )
    pdf.h2("Umsatzwachstum")
    pdf.img(charts["revenue"], h=68)
    pdf.h2("Betriebsergebnis")
    pdf.img(charts["profit"], h=68)

    pdf.section_break()
    pdf.h1("Finanzplanung (Fortsetzung)")
    pdf.h2("Betriebsausgaben")
    pdf.img(charts["expenses"], h=64)
    pdf.h2("Kostenstruktur Jahr 2")
    pdf.img(charts["pie"], h=78)

    pdf.section_break()
    pdf.h1("MRR-Prognose & Tabellen")
    pdf.img(charts["mrr"], h=64)
    pdf.table(
        ["Ertragsquelle", "Jahr 1", "Jahr 2", "Jahr 3"],
        [
            ["Websites", "8.000", "28.000", "40.000"],
            ["Bot Setup", "1.500", "6.000", "10.000"],
            ["Bot MRR (Jahr)", "1.200", "8.000", "18.000"],
            ["Analyse/Reparatur", "500", "3.000", "5.000"],
            ["Summe", "11.200", "45.000", "73.000"],
        ],
        [55, 40, 42, 43],
    )
    pdf.caption("Angaben in EUR, Basis-Szenario. Umsatzprognosen unveraendert. Konservativ Jahr 1: ca. 3-8 Tsd. Optimistisch: 25-45 Tsd.")

    pdf.h2("Betriebsausgaben nach Kostenart (Orientierung)")
    pdf.table(
        ["Kostenart", "Jahr 1", "Jahr 2", "Jahr 3"],
        [
            ["AI APIs (Arbeitsbudget)", "1.440", "3.000", "5.400"],
            ["Cursor Pro", "228", "228", "228"],
            ["ChatGPT Plus / Pro", "288", "288", "288"],
            ["Vercel Pro + Backend-Hosting", "408", "528", "648"],
            ["Cloudflare / Domains", "25", "258", "268"],
            ["Resend (E-Mail)", "228", "420", "600"],
            ["Monitoring / Backup / SaaS", "420", "660", "840"],
            ["Stripe-Gebuehren (ca.)", "280", "1.125", "1.825"],
            ["Buchfuehrung / Admin", "420", "960", "1.200"],
            ["Marketing (organisch + Meta Ads)", "500", "1.800", "3.300"],
            ["Freelancer (bei Bedarf)", "0", "2.400", "4.800"],
            ["Versicherung / Sonstiges", "263", "533", "603"],
            ["Summe Betriebsausgaben", "4.500", "12.200", "20.000"],
        ],
        [70, 36, 37, 37],
    )
    pdf.caption(
        "Jahr 1 Cloudflare Free (0 EUR) reicht fuer Start; Pro ab Jahr 2 bei Traffic/Schutzbedarf. "
        "AI-API = Arbeitsbudget fuer Vector/Bots/Analyse (Kundenanwendungen). "
        "Cursor und ChatGPT = produktiv genutzte KI-Assistenz fuer Entwicklung/Dokumentation/Support. "
        "Meta Ads: Jahr 1 ca. 300-600 EUR Testkampagnen nach ersten Referenzen; "
        "Jahr 2 ca. 1.200-2.000 EUR; Jahr 3 Wachstum entsprechend Umsatzentwicklung – "
        "Ausbau nur bei positiver Wirtschaftlichkeit."
    )

    pdf.table(
        ["Position", "Jahr 1", "Jahr 2", "Jahr 3"],
        [
            ["Umsatz", "11.200", "45.000", "73.000"],
            ["Betriebsausgaben", "4.500", "12.200", "20.000"],
            ["Betriebsergebnis ca.", "6.700", "32.800", "53.000"],
        ],
        [70, 36, 37, 37],
    )
    pdf.caption(
        "Betriebsergebnis vor Privatentnahmen, Steuern und Sozialversicherung. "
        "Bei schwacher Conversion sinkt der Umsatz zuerst – Fixkosten bleiben relativ niedrig und erklaerbar."
    )

    # ===== Fazit =====
    pdf.section_break()
    pdf.h1("Fazit")
    pdf.p(
        "Virtus Core ist ein zeitgemäßes Tech-Gründungsvorhaben mit live Beta, klaren Paketen "
        "und skalierbarem Plattform-Asset. Der naechste kritische Schritt ist der Marktbeweis: "
        "zahlende Kunden, stabile Delivery, ehrliche Lernkurve bei Vertriebskosten."
    )
    pdf.callout(
        "Dieses Dokument kombiniert den klassischen Businessplan-Rahmen mit Produktbelegen "
        "(Screenshots), Strategie-Tools (SWOT, Canvas, Roadmap) und Finanzdiagrammen – "
        "geeignet fuer Jobcenter, Bankgespraeche und Investoren-Erstkontakt."
    )

    # ===== Anhang =====
    pdf.section_break()
    pdf.h1("Anhang")
    pdf.h2("Öffentliche Identität")
    pdf.bullets(
        [
            "Marke: Virtus Core · AI: Vector",
            "Beta: https://beta.genesis-ai-engine.com",
            "E-Mail: hello@genesis-ai-engine.com",
            "Inhaber: Ramish Oltiiev, Einzelunternehmen, Dresden",
            "Adresse: Tornaer Strasse 23, 01237 Dresden",
        ]
    )
    pdf.h2("Hinweis zur öffentlichen Beta")
    pdf.p(
        "Die derzeitige öffentliche Beta läuft noch unter der technischen Domain "
        "beta.genesis-ai-engine.com sowie der E-Mail-Adresse hello@genesis-ai-engine.com. "
        "Im Zuge der weiteren Markenentwicklung wird die öffentliche Infrastruktur "
        "schrittweise auf die Marke Virtus Core (Domain und E-Mail) umgestellt. "
        "Diese technische Übergangsphase hat keinen Einfluss auf den Geschäftsbetrieb "
        "oder die angebotenen Leistungen."
    )
    pdf.h2("Positionierung")
    pdf.p(
        "Virtus Core ist ein digitales AI-/Software- und Serviceunternehmen für KMU: "
        "Websites, AI Digital Employee, Analyse/Reparatur und plattformgestützte Delivery "
        "unter einer Marke."
    )
    pdf.ln(8)
    pdf.set_font("F", "I", 9)
    pdf.set_text_color(*MUTED)
    pdf.set_x(LEFT)
    pdf.multi_cell(
        W,
        5,
        f"Ende · Virtus Core Businessplan Branded Edition · {date.today().isoformat()}\n"
        "Keine Rechts- oder Steuerberatung.",
    )

    OUT_DESKTOP.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPO.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_DESKTOP))
    pdf.output(str(OUT_REPO))
    return OUT_DESKTOP


if __name__ == "__main__":
    path = build()
    from pypdf import PdfReader

    n = len(PdfReader(str(path)).pages)
    print(f"OK desktop={path}")
    print(f"OK repo={OUT_REPO}")
    print(f"pages={n}")
    print(f"charts={CHARTS}")
    print(f"shots={list(SHOTS.glob('*.png'))}")
