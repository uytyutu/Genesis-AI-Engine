# Showcase Registry (research → future Premium)

## Layout

  _research_3d/showcases/<niche>/
    quality.json
    model.glb
    preview.jpg|webp

Index: showcases/index.json

## Delivery rules

| Tier | Behavior |
|------|----------|
| Basic | No showcase block |
| Business | Preview image (3D not required) |
| Premium | Interactive Three.js **only if** quality=approved\|premium + client_facing_3d |
| Else | Preview fallback — site stays complete, never empty/broken viewer |

## Demo

  py -3.12 scripts/open_research_3d.py

http://127.0.0.1:8765/runtime/demos/dental_sold/index.html?tier=premium

Dental is temporarily `approved` for research verification (`research_demo_approved`).
Other niches: placeholder → preview only.

## Code

- app/factory/research_3d/showcase_registry.py
- runtime/demos/dental_sold/sold_client.js (preview-first, lazy 3D, timeouts, camera framing)

Path A Stripe 3d_premium = WAITLIST.
