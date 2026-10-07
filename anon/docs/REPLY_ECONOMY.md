# ANON Reply Economy

## Law

```text
Sender paid for create/send → recipient opens content with NO second paywall.
Plain text reply is always free.
Money only for boosts: hint request, reveal request, voice, Moment/Drop reply.
Identity reveal is voluntary (mutual). Never forced. Never from private data.
```

Not: “Pay to read.”  
Yes: “Someone wrote to you. Want to deepen the mystery? Here are boosts.”

## Free vs paid

| Action | Who pays | Price |
| --- | --- | --- |
| Open received Secret / Drop / Moment | — | Free |
| Reply with text (anonymous) | — | Free |
| Stay anonymous | — | Free |
| Ask for a voluntary hint | Recipient | €0.99 (`ASK_HINT`) |
| Ask sender to reveal (request only) | Recipient | €0.99 (`ASK_REVEAL`) |
| Sender sends voluntary hint | — | Free |
| Mutual cinematic Reveal Moment | After both consent | €1.99 (`SEND_REVEAL`) |
| Reply Drop / Premium Moment | Recipient | existing SKUs |
| Voice reply | Recipient | Coming (flag off) |

## Forbidden

- Paywall on open/read
- “Buy to reply” for plain text
- Auto-reveal of name / IP / email / location
- Hints generated from private account data

## Flow

1. Sender creates paid (or free secret) message.
2. Recipient opens free.
3. Recipient may reply free, or buy a boost.
4. Sender is notified; chooses stay anon / hint / consent reveal.
5. Reveal of identity only when mutual consent (+ optional paid cinematic).

## Code

- Products: `ASK_HINT`, `ASK_REVEAL` in `src/lib/pricing.ts`
- API: `POST /api/gifts/[id]/engage`
- UI: `OpenExperience` free-first + boost shelf; `/engage/[id]` for sender
- Fulfillment: `markOrderPaid` → engage notification (does not re-lock gift)
