# Checkliste — Gewerbe Dresden + Mission 1 Launch

**Genesis Business Registration Kit v1**

---

## Phase A — Persönliche Daten einsetzen (Etappe 2)

- [ ] Alle `{{...}}` in DOCX/PDF/Markdown ersetzen
- [ ] `{{START_DATE}}` festlegen (Gewerbebeginn)
- [ ] `{{MAIN_OR_SIDE_BUSINESS}}` entscheiden (Haupt- oder Nebenerwerb)
- [ ] Personalausweis / Reisepass bereit
- [ ] Meldebescheinigung (falls nötig)
- [ ] Aufenthaltstitel-Kopie (nur Nicht-EU, falls erforderlich)

---

## Phase B — Gewerbeanmeldung Dresden

- [ ] Online-Portal öffnen: https://gewerbe.buergerdienste-online.de/dresden/webclient/app/m/14612000/gewerbeanzeige
- [ ] Felder aus `01_GewA1_Felder_Antworten.md` eintragen
- [ ] Tätigkeitstext aus `02_Taetigkeitsbeschreibung_Genesis.md` kopieren
- [ ] Gebühr zahlen (~20–40 €)
- [ ] Bestätigung / Gewerbeschein aufbewahren
- [ ] **Nicht** automatisch senden lassen — selbst auf «Absenden» klicken

---

## Phase C — Finanzamt

- [ ] Fragebogen zur steuerlichen Erfassung abwarten (kommt per Post)
- [ ] Innerhalb **1 Monat** zurücksenden
- [ ] Steuernummer notieren → `{{TAX_ID}}`
- [ ] Kleinunternehmerregelung prüfen (§ 19 UStG) — mit Steuerberater klären

---

## Phase D — Jobcenter (bei Bürgergeld / Leistungsbezug)

**v2 Reihenfolge:** Informationsgespräch **kann vor Gewerbe** — siehe `Mission1_Payment_and_Launch_Strategy_v1.md`.

- [ ] **Optional zuerst:** Kurze Anfrage beim Jobcenter (welche Schritte, wann melden?) — ohne ganze Genesis-Geschichte
- [ ] Schreiben aus `04_Jobcenter_Selbststaendigkeit_Anziege.md` — **erst wenn** Gewerbe geplant/feststeht
- [ ] `Genesis_Business_Plan_v2.md` als Anlage vorbereiten (ehrliche Zahlen)
- [ ] Gewerbeschein-Kopie nachreichen sobald vorhanden

---

## Phase E — Website rechtlich absichern

- [ ] Impressum veröffentlichen (`05_Impressum_Vorlage.md`)
- [ ] Datenschutz veröffentlichen (`06_Datenschutzerklaerung_Vorlage.md`)
- [ ] AGB veröffentlichen (`07_AGB_Vorlage.md`) — optional vor erstem Fremdkunden
- [ ] Links im Footer der Website setzen
- [ ] Plattform-Abos auf `/pricing`: nur Anzeige — **kein aktiver Verkauf** bis Platform Launch Gate

---

## Phase F — Markt testen (ohne Live-€)

**Erlaubt vor Gewerbe/Stripe Live** (nach JC-Klarheit):

- [ ] Acquisition Studio: Leads, Analyse, Angebote — CEO Approve
- [ ] Stripe **Test** für technischen Checkout
- [ ] 25 Unternehmen listen (`First_Customer_Plan_v1.md`)
- [ ] Personalisierte Nachrichten (manuell / Approve)
- [ ] **Keine** Live-Zahlungen bis Phase H

---

## Phase G — Gewerbe + Stripe Live (bei realem Auftrag / Kunde)

- [ ] Gewerbe anmelden (wenn JC / Situation es erfordert)
- [ ] Stripe KYC · `sk_live` · Live Webhook
- [ ] CEO: **Approve Business Launch** → env switch
- [ ] Smoke: eine echte Zahlung (Refund ok)

---

## Phase H — EL3 (nicht = Stripe fertig)

- [ ] Erster **Fremdkunde** zahlt freiwillig echtes Geld
- [ ] Story #5 dokumentieren
- [ ] Deep Review · Evidence vs Prognose

*EL3 = unabhängiger zahlender Kunde — Stripe ist nur das Werkzeug.*

---

## Dokumente aufbewahren

| Dokument | Aufbewahrungsort |
|----------|------------------|
| Gewerbeschein | Physisch + Scan |
| Finanzamt-Bescheid | Scan |
| Rechnungen / Stripe-Exports | Digital (10 Jahre) |
| Kundenverträge / AGB | Digital |

---

## Risiken / Nicht vergessen

| Risiko | Maßnahme |
|--------|----------|
| Gewerbe ohne Impressum online | Impressum **vor** Outreach live schalten |
| Test-Keys in Production | `live_mode` API prüfen |
| Jobcenter nicht informiert | Anzeige **rechtzeitig** |
| USt-IdNr. fehlt bei EU-Kunden | Nach Finanzamt-Bescheid klären |

---

*Kit-Version: v1.2 · Stand: 2026-07-04 (Strategic Review v2) · Siehe `Genesis_Strategic_Review_Report_v2.md`*
