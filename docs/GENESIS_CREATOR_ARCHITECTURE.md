# Genesis Creator — Architecture (preparation only)

**Status:** Design document · **not implemented** in v0.5 Stable  
**Rule:** Genesis Core stays with the owner. Creator is a separate product.

## Purpose

Genesis Creator lets subscribers run a **user-scoped** copy of the Genesis experience: Mission Control, Factory skills, and AI departments — without access to the owner's Core, kernel, or platform secrets.

## Two-tier model

| Layer | Owner | Subscriber (Creator) |
|-------|--------|----------------------|
| Genesis Core | Full kernel, Brain, integration, launcher | **No access** |
| Genesis Creator | Product you sell | Sandboxed tenant instance |
| Data | `memory/`, sandbox, finance truth | Tenant-isolated `memory/{tenant_id}/` |
| Updates | Owner approves platform changes | Receives approved Creator builds only |

## Boundaries (non-negotiable)

1. **No agent may modify Core without owner approval** (see `docs/GUARDIAN.md`).
2. Creator tenants cannot call owner-only endpoints (`/api/owner/*` with owner token).
3. Payment Hub for Creator subscriptions is a **separate** commerce rail from owner Factory revenue.
4. Skills ship as packages; Core loads them through the Skills host (`docs/SKILLS_PLATFORM.md`).

## Proposed components (future)

```
Owner Genesis Core
├── kernel/          # task → plan → agents (frozen for tenants)
├── integration/     # owner services
├── creator-gateway/ # (future) tenant routing, billing, limits
└── creator-runtime/ # (future) per-tenant Mission Control + Factory slice
```

### creator-gateway (future)

- Tenant provisioning (subdomain or desktop bundle)
- Subscription state (active / trial / suspended)
- Usage quotas (products/month, AI tasks/day)
- No direct filesystem access to owner repo

### creator-runtime (future)

- Read-only or forked UI from `dashboard/frontend` with feature flags
- Tenant `memory/` and `sandbox/` roots
- Same Factory skill interface, different data partition

## Approval flow for platform changes

Aligns with Owner Experience and Guardian rules:

1. Agent or Cursor proposes change
2. Validator / second agent reviews
3. Architect produces plan + diff summary
4. **Owner sees proposal in Mission Control**
5. Owner ✔ → apply; Owner ✘ → discard

Creator subscribers never participate in step 4 for Core.

## Migration path (after v0.5 Stable)

1. **R-slot:** Feature flags in frontend (`NEXT_PUBLIC_GENESIS_TIER=owner|creator`)
2. **R-slot:** Tenant ID in API context (read-only prep in `IntegrationContext`)
3. **R-slot:** Creator gateway stub + health check only
4. **Post-R1:** First paid Creator trial with one Skill (Landing only)

## References

- `docs/NORTH_STAR.md`
- `docs/SKILLS_PLATFORM.md`
- `docs/ECONOMY.md`
- `docs/MARKETPLACE.md`
- `CURSOR_AUTONOMY_RULES.md`
