# Genesis Strategic Review Report v2

**Datum:** 2026-07-04  
**Mission:** Strategic Review nach RC2, Desktop, Acquisition Studio, Company→Platform-Strategie  
**Prinzip:** Dokumente **genauer** zum echten Projekt — nicht „schöner auf Papier“.

---

## 1. Audit-Zusammenfassung

| Bereich | Ist-Zustand | Doku vor v2 | Nach v2 |
|---------|-------------|-------------|---------|
| Produktion Website/API | RC2 live, EL2 | ✅ | ✅ |
| Acquisition Studio | Code + `/acquisition` | Teilweise | ✅ Mission 1.5 doc |
| Desktop | 2.5 lokal, nicht pushed | ✅ | ✅ |
| Stripe | Test ✅, Live ⬜ | Gemischt | ✅ geklärt |
| Gewerbe / JC | ⬜ | Kit v1, alte Reihenfolge | ✅ v1.2 Kit + Plan v2 |
| Platform SaaS | Anzeige only | Widerspruch | ✅ geklärt |
| Icons | Fehlende PNG/ICO | — | ✅ Generator + Brand |

**Readiness:** ≈ 8,8/10 (`Genesis_Readiness_Scorecard_v1.md`)

---

## 2. Neu erstellt (v2)

| Dokument | Zweck |
|----------|-------|
| `Genesis_Business_Plan_v2.md` | Jobcenter, Gewerbe, intern |
| `Genesis_Why_Exists_v2.md` | Positionierung, nicht nur WHY.md technisch |
| `Genesis_Competitive_Analysis_v1.md` | Ehrlicher Wettbewerb |
| `Genesis_Competitive_Advantage_v1.md` | Warum Genesis vs. ChatGPT & Co. |
| `Genesis_Strategic_Analysis_Report_v1.md` | EL3 ≠ Stripe |
| `Genesis_Readiness_Scorecard_v1.md` | 8,8/10 + CEO mandate |
| `Genesis_Development_Priorities_v1.md` | A/B/C + Weekly template |
| `Mission1_Payment_and_Launch_Strategy_v1.md` | JC → Client → Gewerbe |
| `Mission_1_5_Business_Acquisition_Studio.md` | Sales foundation |
| `Genesis_Strategic_Review_Report_v2.md` | Dieser Bericht |

---

## 3. Aktualisiert (v2)

| Dokument | Änderung |
|----------|----------|
| `Genesis_Progress.md` | EL3-Kette, Readiness, Priorities |
| `Genesis_Development_Policy.md` | Line A/B, Cursor mandate |
| `Genesis_Business_Registration_Kit_v1/08_Checkliste` | Phasen F–H neu |
| `02_Taetigkeitsbeschreibung` | Kein SaaS-Verkauf klargestellt |
| `04_Jobcenter` | Informationsanfrage vor Gewerbe |
| `.cursor/rules/genesis-development.mdc` | Canonical 2026-07 |

---

## 4. Nicht gelöscht — bewusst parallel

| Alt | Warum behalten |
|-----|----------------|
| `WHY.md` | Technische Verfassung, EL-Definitionen |
| `docs/ROADMAP.md` R0–R14 | Engineering-Historie |
| `PROJECT_STATE.md` | R1 framing — **TODO:** leichte Sync-Zeile |
| `Genesis_Pricing_Strategy_v1.md` | Horizon — Preise unverändert |

---

## 5. Widersprüche behoben

| # | Thema | Fix |
|---|-------|-----|
| C1 | Outreach nach Stripe Live | Checkliste: Outreach **vor** Live (Phase F) |
| C2 | EL3 = Stripe setup | Überall: EL3 = Fremdkunde zahlt |
| C4 | Pricing display vs Horizon | Plan + Checkliste: Anzeige ≠ Verkauf |
| C6 | „Company verdient jetzt“ | Readiness legal 2/10 |

---

## 6. CEO-Entscheidungen offen

| # | Entscheidung |
|---|--------------|
| 1 | **Jobcenter** — Informationsanruf (jetzt) |
| 2 | Push 9 lokale Commits + Mission 1.5? |
| 3 | `/pricing` Tiers — Anzeige belassen oder „Coming soon“ stärker? |
| 4 | Rust installieren → Tauri Daily Driver |
| 5 | `GENESIS_OUTREACH_ENABLED` — wann nach JC |

---

## 7. Dokumente — Bereitschaft

| Zweck | Ready | Anmerkung |
|-------|-------|----------|
| **Jobcenter Info-Gespräch** | 🟡 | Vorlage in `04_` + `Business_Plan_v2` |
| **Jobcenter Anzeige** | 🟡 | Nach Gewerbe-Datum + Platzhalter |
| **Gewerbeamt** | 🟡 | Kit 01–02, CEO-Daten einsetzen |
| **Erster Kunde** | ⬜ | Outreach + legal |
| **Investor** | ⬜ | Nicht Ziel Mission 1 |

---

## 8. Cursor-Mandat (final v2)

1. **Priorities A → B → C** (`Genesis_Development_Priorities_v1.md`)
2. Filter: *erster € oder Produktqualität?*
3. Kein live pay / SaaS ohne CEO Approve
4. **Weekly Progress** — kurz, nützlich
5. Icon: RC2 GenesisMark (Gradient G)

---

## 9. Nächster Weekly (Vorlage)

Erste Datei: `dashboard/weekly/Genesis_Weekly_2026-07-04.md`

---

*Strategic Review v2 abgeschlossen. Keine Auto-Veröffentlichung. Keine Stripe-Live-Aktivierung.*
