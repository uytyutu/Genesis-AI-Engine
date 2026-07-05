# Final Pre-Submission Audit v1 — Bericht

**Datum:** 2026-07-04  
**Geprüft:** Genesis Business Registration Kit v1  
**Ergebnis:** ⚠️ **Nicht PASSED** — 6 Punkte behoben in **v1.1**

---

## Prüfperspektiven

| Rolle | Urteil v1 |
|-------|-----------|
| Gewerbeamt | ✅ Grundsätzlich OK — **1 Widerspruch** zwischen GewA1-Feld 16 und Tätigkeitstext |
| Jobcenter | ⚠️ § 60 SGB I zu eng — Bürgergeld = SGB II |
| Finanzamt | ✅ WZ 62.09.0 passend — interner Jargon „Factory-Pipeline“ entfernt |
| DSGVO-Anwalt | ⚠️ AVV-Formulierung, Cookies, Widerspruchsrecht ergänzt |
| IT-Kleinunternehmer | ⚠️ AGB: Widerruf für Verbraucher fehlte; Impressum DDG |

---

## Gefundene Probleme → v1.1 Fixes

| # | Problem | Risiko | Fix in v1.1 |
|---|---------|--------|-------------|
| 1 | `01_GewA1` Feld 16 enthält noch „Automatisierung und digitale Geschäftsprozesse“, `02` hat milderen Text | Widerspruch bei Gewerbeamt | Feld 16 = identisch mit `02` Freitext |
| 2 | Jobcenter-Brief nur § 60 SGB I | Falsche Norm bei Bürgergeld | § 60 SGB I **und** § 60 SGB II ergänzt |
| 3 | Impressum verweist nur auf § 5 TMG | TMG teils durch DDG ersetzt (2024) | § 5 DDG ergänzt |
| 4 | Datenschutz: „AVV bestehen“ ohne Vorbehalt | Unwahre Angabe auf Live-Website | „werden geschlossen“ + CEO-Hinweis |
| 5 | Datenschutz: keine Cookies, kein Widerspruch Art. 21 | DSGVO-Lücke | Abschnitte ergänzt |
| 6 | AGB: kein Widerrufsrecht für Verbraucher | Abmahnrisiko B2C | § 11 Widerruf + B2B-Hinweis |
| 7 | Impressum: Steuernummer optional | Steuernummer nicht ins Impressum | Zeile entfernt / nur USt-IdNr. |

---

## Was bereits gut war (unverändert)

- Einzelunternehmen / Sonstiges / keine Handwerkskarte — korrekt
- Tätigkeit ehrlich formuliert (Websites, keine KI-Plattform)
- Keine erlaubnispflichtige Tätigkeit
- Homeoffice = Wohnadresse — Standard
- Jobcenter-Brief nur bei Leistungsbezug — klar markiert
- Platzhalter `{{...}}` — korrekt für Etappe 2

---

## CEO vor Live-Schaltung (nicht im Kit automatisierbar)

- [ ] DPAs mit Vercel, Railway, Resend, Stripe **tatsächlich** abschließen
- [ ] Kleinunternehmer § 19 UStG im Finanzamt-Fragebogen klären
- [ ] USt-IdNr.-Zeile im Impressum **entfernen**, bis erteilt
- [ ] Bei Bürgergeld: Jobcenter-Brief mit **SGB II**-Bezug verwenden

---

## v1.1 Ergebnis

✅ **Final Audit PASSED (v1.1)** — nach obigen Fixes.

Für Gewerbeamt verwenden: `01_GewA1` + `02_Taetigkeit` (identische Freitexte).
