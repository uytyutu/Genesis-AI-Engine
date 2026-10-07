# ANON — product architecture

**Brand:** ANON  
**Positioning:** Say what you don't dare — then leave a living digital memory  
**Promise:** Secrets & moments today. **ANON DNA** as the unique long-term core.

Not a chat clone. Not a family album. Not a calendar. Not a card shop.

**North star:** [`ANON_DNA.md`](./ANON_DNA.md) — interactive digital DNA of a person; secrets / drops / open-later / games orbit it.

## Pillars

1. **🔐 Secrets & SEND** — anonymous notes, drops, moments (Live)  
2. **🔒 OPEN WHEN** — time-locked messages (seed of Living Message)  
3. **🧬 ANON DNA** — voice, stories, photos, answers → interactive “me” (Coming)  
4. **Play** — games gather people; then return to memory & moments  
5. **Reply Economy** — open/reply free; boosts paid; mutual reveal only

## Business model (4 lanes)

1. **Micro-gifts** €0.99–€9.99  
2. **ANON** anonymous + chat + Reveal Moment €1.99 (mutual consent)  
3. **Social** reply gifts, questions, post-game gifts  
4. **Premium packs** Party €9.99 · Event €49.99 · Custom Event €99+ (catalog ready)

## Game engine (v1)

Modes are modules in `src/lib/games/catalog.ts` + `engine.ts`.

**Playable now:** Who Did It · Majority · Find the Liar · Speed · Caption War · Random 5  

**Scaffolded:** Secret Roles · 5×5 Battle · Target · Hidden Clues  

Rooms: `POST /api/games/rooms` → `/r/:code`  
Rank / XP: `/rank` · leagues bronze→legend  

After a game: CTA to gift the winner or leave ANON note.

## Gift pricing (EUR)

| SKU | Price |
|-----|------:|
| Moment / Joke | €0.99 |
| One Question | €1.49 |
| Surprise / ANON / Reveal Moment | €1.99 |
| Open When | €2.49 |
| Time Capsule | €2.99 |
| Story | €4.99 |
| Big Moment | €9.99 |
| Party Pack | €9.99 |
| Event Pack | €49.99 |

## Reveal Moment

Not “pay to see a name”. Flow:

1. Both sides consent  
2. Optional paid Reveal Moment (€1.99)  
3. Cinematic countdown → real display name only if identity exists server-side  

## Legal (DE)

Routes: `/impressum` `/datenschutz` `/cookies` `/agb`  

Operator data is **never invented**. Sources:

1. Virtus public legal API (`ANON_LEGAL_SOURCE_URL` / `GENESIS_PUBLIC_URL`)  
2. `content/legal/entity.json` — copied from project Legal Foundation example  
3. Same `GENESIS_LEGAL_*` ENV keys as Virtus  

Footer on all public pages includes Legal + `© ANON · Impressum · Datenschutz · AGB`.

## Stack

Next.js · SQLite · Stripe Checkout + webhooks · HMAC sessions · i18n  

Standalone under `anon/` — does not mount into Virtus sales/ledger. Reuses Stripe ENV names.

## Local

```bash
cd anon
npm install
npm run dev   # :3100 — webpack (Turbopack hangs with monorepo lockfiles)
# pwsh scripts/start_local.ps1
```

Sandbox: `ANON_PAYMENT_SANDBOX=1`  
Smoke: `npm run test:smoke`  
OVH: `pwsh scripts/deploy_ovh.ps1` + `docker compose` in `anon/` (needs SSH to VPS)
