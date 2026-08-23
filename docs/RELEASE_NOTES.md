# Virtus Core — Release Notes

## Roadmap (Owner lock)

```text
RC1 Certification (A/B/C/D)
      ↓
CR1 Commercial Ready
      ↓
5–10 €/day ads → first 5 clients
      ↓
Website Control Owner PASS + commit
      ↓
Chatbot → Social → Marketing
```

Ads **not yet**. Scale only after Owner ~499 € shame-test  
(`docs/CR1_COMMERCIAL_READINESS.md`).

---

## RC1.0 — Stability Sprint (in certification)

**Certification: NOT PASS** — awaiting Owner RC1-A…D (`docs/RC1_CERTIFICATION.md`).

### Shipped toward certification (engineering)

- Launcher: no auto-rebuild on cold boot; soft restart failed FE only; Health ms + Last Crash
- CEO `/executive`: core first paint (Today Focus + Health); Farm + Deployment lazy
- Farm: lite-first, quieter polling
- Health Center rows + crash breadcrumbs
- Canon: Stability Gate + Commercial Readiness (CR1) + Defect→QA law

### Known Issues

- 3D still evolving — not a release claim
- Video Pipeline not ready
- Website Control on branch — Owner Test pending; commit only after RC1 Certification + WC Owner PASS
- Store Control / Chatbot / Social / Marketing — frozen until order above
- Vitrine / 10 etalon demos — CR1 work, not done

### Next

1. Owner: RC1-A…D in real use  
2. Media QA hard gate + Image Pipeline on Provider Gateway  
3. Website Control Owner PASS → commit  
4. 10 etalon demos + `/site` Commercial Ready  
5. 5–10 €/day ads → first 5 clients → feedback  

### Architecture locked (scaffold)

- Provider Gateway foundation (`app/integration/provider_gateway/`)
- Backend import preflight (Launcher) + `tests/test_backend_import.py`
- **P0 Image Pipeline contract:** Generate → Media QA → regenerate (max 3) → hard failure  
  (`media_qa.py`, `image_pipeline.py` + DoD unit tests). Live provider E2E **after RC1 PASS**.
- Order: RC1 → Image QA → Video → 3D → Social

---

Older audits: `dashboard/Release_Audit_*.md`. Living log from RC1.0 onward: this file.
