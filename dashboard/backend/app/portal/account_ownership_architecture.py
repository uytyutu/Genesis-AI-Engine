"""R3.12.1 — Account Ownership Architecture notes (domain only).

Not runtime policy. Documents boundaries for later R3.12 slices.

## Entity map

```text
Client          — commercial party (buyer / company)
Website         — managed site; Website.client_id → Client (commercial)
Account         — human platform subject (will authenticate later)
WebsiteOwnership— Account ↔ Website portal access (role)
WebsiteInvitation — intent to grant Ownership (no email yet)
```

Access path after later R3.12 slices:

```text
Email → Account → WebsiteOwnership[] → Website → Dashboard
```

Commercial path (unchanged):

```text
Order → Client → Website.client_id
```

## Binding rule — Account never owns Client

```text
Account → WebsiteOwnership → Website → Client   ✅
Account → Client                                 ❌
```

An Account reaches a Client only *through* Website(s) it can access.
This keeps agency / multi-tenant paths open: one Account may hold
Ownership on Websites belonging to different Clients without becoming
the commercial owner of those companies.

## Boundary: domain vs auth

| Layer | Owns |
|-------|------|
| Domain (this slice) | Account, Ownership, Invitation shapes |
| Auth (later) | password hash, sessions, tokens, cookies |
| Delivery (later) | SMTP, activation links |

Domain must not import auth/delivery. Auth will *use* these entities.
"""

from __future__ import annotations

from app.portal.ownership import FUTURE_ROLES

ENGINE_ID = "account_ownership_architecture_v1"

# Re-export for discoverability in architecture review.
OWNERSHIP_FUTURE_ROLES = FUTURE_ROLES
