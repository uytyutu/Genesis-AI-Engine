# Owner Eye — NordLicht Autohaus (Client Form + 3D)

**Do not commit.** Live eye pass 2026-08-08.

## Owner Test

| Surface | Score | Note |
| --- | ---: | --- |
| Autohaus website | 7.2/10 | WebGL + unique gallery help; car mesh still blocky; About text-heavy; copy repeats |
| Care Shop | 5.5/10 | Catalog works; product names generic (Starter Pack…); photos duplicate / wrong niche feel |
| Beauty / Restaurant / Psychology / Dental | — | not rebuilt this pass |

## Website checklist
- [x] Hero ~full viewport
- [x] WebGL works (Three.js wait-for-load + transparent `.lx-band`)
- [~] Car / light / motion — particles + floor yes; mesh not “studio car”
- [~] Every section own image — gallery yes; About weak
- [x] Gallery unique photos (12 Cursor scenes)
- [~] No Hero spam — improved
- [x] No Pillow in gallery
- [x] Photo band images load
- [~] Contrast / readable — hero OK; repeated promise text FAIL

## Store checklist
- [x] Catalog loads (`/store/catalog.html`)
- [ ] Same brand as Autohaus luxury showroom — FAIL (generic shop cards)
- [ ] Product photos unique & auto-care — FAIL

## German studio question
> Without Virtus logo — expensive German digital studio?

**Website:** almost, not yet. **Store:** no.

Verdict: **FAIL — do not commit.**

## Open locally
```
http://127.0.0.1:3456/package-previews/client-forms/nordlicht-autohaus/website/
http://127.0.0.1:3456/package-previews/client-forms/nordlicht-autohaus/store/catalog.html
```
