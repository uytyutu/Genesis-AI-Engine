# Commerce Layer — Architecture (preparation only)

**Status:** Design document · **no automatic sales** in v0.5 Stable  
**Gate:** Real Payment Hub wiring remains after first real client (see `PROJECT_STATE.md`).

## Purpose

Prepare Genesis so revenue modules can be added **without breaking** the stable integration layer: Factory, Finance, Mission Control, and owner memory.

## Commerce modules (future)

| Module | Role | Touches today |
|--------|------|----------------|
| **AI Sales** | Leads, outreach, proposals | `opportunity_service`, narrative feed |
| **Marketing** | Campaigns, channels | `growth_service`, analytics UI |
| **CRM** | Clients, pipeline | `finance_service.clients`, mission-control metrics |
| **Subscriptions** | Creator / SaaS billing | New `commerce/subscriptions/` (future) |
| **Ads** | Spend vs ROAS | Growth center extensions |
| **Product publish** | Public URLs + paywall | `factory_service.publish`, payment webhook |

## Integration principles

1. **Single money truth:** `finance_service` remains the ledger; other modules emit events, not balances.
2. **Payment Hub callback:** `POST /api/webhooks/payment` stays the only path to confirmed revenue (owner confirms in UI).
3. **No silent charges:** Every commercial action surfaces in Mission Control with reason + owner gate.
4. **Demo mode isolation:** `demo_mode` in `finance_config.json` must never mix with live Payment Hub state.

## Event bus (lightweight prep)

Future modules should write to `memory/commerce_events.jsonl`:

```json
{"at":"ISO8601","type":"lead_created","source":"ai_sales","payload":{}}
```

Mission Control already consumes `commercial_events` — wire real events there instead of scripted copy when modules go live.

## API extension pattern (future)

```
/api/commerce/leads          # AI Sales
/api/commerce/campaigns      # Marketing
/api/commerce/subscriptions  # Creator billing
```

All routes:

- Live under `app/integration/` or `app/commerce/` (not in kernel)
- Use `IntegrationContext` — no new global singletons
- Return Pydantic schemas in `app/schemas.py`

## Owner approval matrix

| Action | Auto? | Owner |
|--------|-------|-------|
| Record demo payment | Demo only | N/A |
| Record live payment | Webhook + confirm | ✔ confirm in Finance |
| Publish product | Factory | ✔ approve + publish |
| Start ad spend | Future | ✔ always |
| Change pricing | Future | ✔ always |

## References

- `docs/ECONOMY.md`
- `docs/MARKETPLACE.md`
- `dashboard/backend/app/integration/finance_service.py`
- `dashboard/backend/app/factory/factory_service.py`
