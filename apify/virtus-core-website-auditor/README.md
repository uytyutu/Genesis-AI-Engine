# Virtus Core Website Auditor

**Brand name (always):** `Virtus Core Website Auditor`  
Never publish as a generic "Website Auditor".

## What it is

Answers the owner question:

> What exactly should I fix to make my website better?

Two modes, one engine (`dashboard/backend/app/integration/vc_auditor/`):

| Mode | Input | Fix buttons |
|------|--------|-------------|
| **Public** | Any URL | CTA → Virtus Core order |
| **Virtus Core** | Factory package / order | **Исправить** if live, else **Coming R3.x** |

## Scores

- Overall Business Score (0–100)
- Website: SEO · Performance · Accessibility · Mobile · Security
- Germany Legal: Impressum · Datenschutz · Cookie · Kontakt
- Business: CTA · Forms · Maps · Social · Trust · Reviews
- AI Summary (rule-based, honest)

## Export

`json` · `csv` · `markdown` · `pdf`

## HTTP API (Virtus Core backend)

```http
POST /api/public/vc-auditor
{ "url": "https://company.de", "locale": "de" }

GET /api/public/vc-auditor/{report_id}/export?format=pdf
```

In-platform:

```http
GET /api/client/orders/{order_id}/vc-auditor
GET /api/client/orders/{order_id}/vc-auditor/export?format=markdown
```

Public UI: `/tools/website-auditor`

## Apify Store packaging (next)

Publish this Actor as:

**Virtus Core Website Auditor**

Input: `startUrl`  
Output dataset: full report JSON + markdown summary  
Same scoring engine — do not fork a second auditor.

## Rule

Never invent Fix success for modules that are not live.
