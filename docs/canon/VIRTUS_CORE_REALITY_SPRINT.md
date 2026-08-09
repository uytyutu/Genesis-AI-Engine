# Virtus Core — Reality Sprint (Canon)

**Status:** CANON · supersedes internal PASS as the primary quality bar.

## One question

> If we show this to a real business owner in Germany, will they say:  
> **«Ja — genau so einen Auftritt will ich.»**

Not: more modules. Not: JSON green. **Eyes.**

## Reality Sprint — 10 Real Companies Test

No more “internal PASS” as the finish line. Only human judgment.

### TEST 1 — 5-Second Niche

Open the site. Cover the logo. Within 5 seconds:

> What does this company do?

If unclear → **FAIL**.

### TEST 2 — Price Perception

Show someone who does not know Virtus Core:

> What would a studio charge for this site?

| Answer | Verdict |
| --- | --- |
| 300–700 € | **FAIL** |
| 1000–2000 € | Good |
| «Looks like a real studio site» | **PASS** |

### TEST 3 — German Company Test

Must feel like a real German firm (e.g. DachKlar in Berlin):

> «Diese Firma arbeitet wohl wirklich hier.»

Not: «Das ist ein Demo.»

### TEST 4 — Portfolio Test

> Would I put this in the Virtus Core portfolio?

If even slightly ashamed → **REBUILD**.

### TEST 5 — Business Identity Test (no reading)

Answer without reading body copy:

- Character?
- Cheap or expensive?
- Family or corporate?
- Local or national?
- Modern or dated?

If answers are blurry → Identity not manifested → **FAIL**.

## Law №4 — No Repeated Companies

> **Factory must not recreate a company that already exists in memory.**

Not “different colors.” Different:

- composition · architecture · typography · rhythm  
- media · Hero · cards · forms · contact · gallery · menu · structure  

If two sites can be confused → diversity insufficient → **REBUILD**.

## Studio Collection (internal etalons)

Not client templates. Internal quality bar:

```
Virtus Core Studio Collection
├── Top websites (target 100)
├── Top stores (target 50)
├── Top clinics (target 20)
├── Top restaurants (target 20)
├── Top Handwerk (target 20)
└── Top lawyers (target 20)
```

Before export, Factory asks:

> Is this site **better than** our best work — or worse?

If worse → **do not export**.

## Sprint gate

```
≥8 / 10 sites pass Tests 1–5 by owner eye  → continue
<8 / 10                                     → stop features; fix generation only
Any Law №4 confuse-pair                     → REBUILD pair
```

Commercial status remains **PENDING_OWNER** until Reality Sprint is signed by eye.

## Implementation

- `app/factory/reality_sprint.py` — scorecards (human-filled)
- `app/factory/studio_collection.py` — etalon registry + compare
- `app/factory/visual_intelligence/design_memory.py` — Law №4 similarity
- `scripts/reality_sprint_10.py` — generate 10 niches + checklist for eyes
