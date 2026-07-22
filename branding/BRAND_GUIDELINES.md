# Virtus Core Brand Guidelines

**Brand Architecture (strategy):** `docs/VIRTUS_BRAND_ARCHITECTURE_v1.md` — **v1.0 ACCEPTED** (CEO 2026-07-22).

## Hierarchy

| Role | Name | Public |
|------|------|--------|
| Company / Platform | **Virtus Core** | Yes |
| AI Business Employee | **Vector** | Yes |
| Signature | **Powered by Virtus Core** / **by Virtus Core** | Yes |
| Internal engine | Genesis | No — code/runtime only |

Public product face for ChatBot: **Vector** (not “чат-бот Virtus”).

## Signature

```
Meet Vector
Your AI Business Employee
Powered by Virtus Core
```

Compact:

```
Vector
by Virtus Core
```

## Logo & Icon

- **Master icon:** `branding/vector/vector-app-icon.svg` — **Confluence** symbol
- **Concept exploration:** `branding/concepts/` + `ICON_CONCEPTS.md`
- **Compact / favicon:** `branding/vector/vector-mark-compact.svg`
- **Wordmark:** `branding/virtus-core/virtus-core-logo.svg`
- All raster assets are exported from SVG — never use AI bitmaps as source.

### Icon philosophy

The mark is **not** a letter V. Two sculpted streams converge on a core; the **hidden V** lives in the negative space between them (second-discovery effect). No robots, brains, chat bubbles, or generic AI clipart.

Regenerate:

```bash
py scripts/generate_virtus_brand_assets.py
```

## Colors

See `branding/design-tokens.json`.

- Void `#050508` — backgrounds
- Text `#ECECF1` — primary copy
- Accent `#7C8FD4` — focus, links, mark core
- Muted `#8B8B9A` — secondary copy

## Typography

- Display: Segoe UI Variable, SF Pro Display, system-ui
- Body: Segoe UI Variable, SF Pro Text, system-ui
- Use generous letter-spacing on signatures (`tracking-[0.2em]`)

## Rules

1. Users talk to **Vector**, not Genesis — and not to module names (CRM, Knowledge, License).
2. **Virtus Core** is the platform brand; **Vector** is the AI Business Employee.
3. Never expose Genesis in public UI, favicons, shortcuts, or marketing.
4. One mark everywhere — Windows, web, Android, iOS, Linux.
5. Minimal, premium, timeless — no robots, brains, or generic AI clipart.
6. Marketing may say “Meet Vector” / “Ask Vector”; platform trust line stays “Powered by Virtus Core.”
