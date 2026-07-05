# GewA 1 — Gewerbeanmeldung Dresden (Einzelunternehmen)

**Formular:** Gewerbe-Anmeldung nach § 14 GewO  
**Zuständig:** Landeshauptstadt Dresden, Ordnungsamt, Abt. Gewerbeangelegenheiten  
**Gemeindekennzahl Dresden:** 14612000  
**Online-Portal:** https://gewerbe.buergerdienste-online.de/dresden/webclient/app/m/14612000/gewerbeanzeige

---

## Abschnitt: Betriebsinhaber

| Feld | Antwort |
|------|---------|
| **1** Handelsregister-Name mit Rechtsform | *leer lassen* (Einzelunternehmen, nicht eingetragen) |
| **2** Ort/Nr. Handelsregister | *leer lassen* |
| **3** Geschäftsbezeichnung (wenn abweichend) | **Genesis AI Engine** |

---

## Abschnitt: Person (Inhaber)

| Feld | Antwort |
|------|---------|
| **4** Name | `{{LAST_NAME}}` |
| **5** Vornamen | `{{FIRST_NAME}}` |
| **6** Geschlecht | `{{GENDER}}` |
| **7** Geburtsname | *nur ausfüllen wenn abweichend* |
| **8** Geburtsdatum | `{{DATE_OF_BIRTH}}` |
| **9** Geburtsort und -land | `{{BIRTH_PLACE}}` |
| **10** Staatsangehörigkeit | `{{NATIONALITY}}` |
| **11** Anschrift Wohnung | `{{ADDRESS}}` |
| **12** Telefon | `{{PHONE}}` |
| Telefax | *leer* |
| **E-Mail** | `{{EMAIL}}` |

---

## Abschnitt: Betrieb

| Feld | Antwort |
|------|---------|
| **13** Betriebsstätte — Anschrift | `{{ADDRESS}}` *(bei Homeoffice = Wohnadresse)* |
| Betriebsstätte Telefon | `{{PHONE}}` |
| Betriebsstätte E-Mail | **hello@genesis-ai-engine.com** |
| Betriebsstätte Website | **https://genesis-ai-engine.com** |
| **14** Hauptniederlassung | *gleiche Adresse wie Betriebsstätte* |
| **15** Frühere Betriebsstätte | *leer* (Neugründung) |

---

## Angemeldete Tätigkeit (Schwerpunkt)

**Feld 16 — Text für Formular (kopieren — identisch mit `02_Taetigkeitsbeschreibung`):**

```
Ich biete als Einzelunternehmer unter der Bezeichnung „Genesis AI Engine“
die Entwicklung und Bereitstellung von Websites und digitalen Online-Auftritten
für kleine Unternehmen an. Schwerpunkte: Konzeption, Umsetzung und — nach
Vereinbarung — Pflege von Landing Pages; Beratung zu Online-Präsenz und
einfachen digitalen Prozessen (Kontakt, Buchung, Zahlung). Die Tätigkeit wird
von zu Hause aus (Homeoffice) in Dresden erbracht. Keine erlaubnispflichtige
Tätigkeit, kein Handwerksbetrieb. Zielgruppe: lokale KMU in Deutschland.
```

**WZ-Codes (für Finanzamt / eigene Notizen):**

| Code | Bezeichnung |
|------|-------------|
| **62.09.0** | Sonstige Dienstleistungen der Informationstechnologie *(Hauptschwerpunkt)* |
| **62.01.Z** | Programmierungstätigkeiten *(optional, Zusatz)* |

| Feld | Antwort |
|------|---------|
| **17** Nebenerwerb? | `{{MAIN_OR_SIDE_BUSINESS}}` — *wählen: Ja (Nebenerwerb) oder Nein (Hauptberuf)* |
| **18** Beginn der Tätigkeit | `{{START_DATE}}` |
| **19** Art des Betriebes | ☑ **Sonstiges** — ☐ Industrie ☐ Handwerk ☐ Handel |
| **20** Zahl tätiger Personen (ohne Inhaber) | **0** |
| Vollzeit / Teilzeit | **0 / 0** |
| **21** Anmeldung für | ☑ **Neugründung** |
| | ☐ Wiedereröffnung ☐ Reisegewerbe ☐ Zweigniederlassung |
| **22** Grund Neugründung | *Neugründung — keine Übernahme* |
| **26** Früherer Gewerbetreibender | *leer* |

---

## Erlaubnisse / Handwerk / Ausländer

| Feld | Antwort |
|------|---------|
| **28** Erlaubnis erforderlich? | **Nein** |
| **29** Handwerkskarte? | **Nein** *(kein Handwerksbetrieb Anlage A HwO)* |
| **30** Aufenthaltstitel? | *Nur bei Nicht-EU:* `{{RESIDENCE_PERMIT}}` |
| **31** Erwerbsbeschränkung im Titel? | *Nur wenn zutreffend* |

---

## Beiblatt — weitere Tätigkeiten (optional)

Falls das Portal zusätzliche Tätigkeiten abfragt:

1. Konzeption und Umsetzung von Landing Pages
2. Einrichtung von Kontaktformularen und Online-Buchungslinks
3. Technische Wartung und Hosting-Koordination (über Drittanbieter)

---

## Benötigte Unterlagen (mitbringen / hochladen)

- [ ] Personalausweis oder Reisepass (Kopie)
- [ ] Meldebescheinigung (falls verlangt)
- [ ] Aufenthaltstitel-Kopie *(nur bei Nicht-EU, wenn erforderlich)*
- [ ] Zahlungsmittel für Gebühr (~20–40 €)

**Nicht erforderlich für diese Tätigkeit:**

- Handwerkskarte
- Gewerbeerlaubnis / Konzession
- Handelsregisterauszug

---

## Nach der Anmeldung

Das Finanzamt sendet automatisch den **Fragebogen zur steuerlichen Erfassung**.  
Frist: **innerhalb eines Monats** zurücksenden.

Steuernummer `{{TAX_ID}}` — eintragen falls bereits vorhanden; sonst leer lassen.
