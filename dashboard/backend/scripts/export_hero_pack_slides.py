"""CEO slide deck — Hero Pack 2.0 backgrounds (Basic / Business / Premium)."""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

from app.factory.hero_pack import BASIC_SLOTS, BUSINESS_SLOTS, PREMIUM_SLOTS, slot_path
from app.factory.niche_profiles import known_niche_ids

OUT = Path(__file__).resolve().parents[1] / ".factory_ceo_package_previews" / "hero_pack_slides"
SHOW = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"


def _b64(path: Path) -> str | None:
    if not path.is_file():
        return None
    raw = path.read_bytes()
    if len(raw) > 2_500_000:
        # Prefer copying smaller preview for deck — still embed if under hard cap
        pass
    return base64.b64encode(raw).decode("ascii")


def _card(niche: str, tier: str, slot: str) -> str:
    src = slot_path(niche, tier, slot)
    # also copy into OUT for file-based browsing
    dest_dir = OUT / niche / tier
    dest_dir.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dest_dir / f"{slot}.jpg")
        rel = f"{niche}/{tier}/{slot}.jpg"
        return (
            f'<figure class="card" data-tier="{tier}">'
            f'<img src="{rel}" alt="{niche} {tier} {slot}" loading="lazy">'
            f"<figcaption><strong>{niche}</strong> · {tier} · {slot}</figcaption>"
            f"</figure>"
        )
    return (
        f'<figure class="card missing"><figcaption>{niche} · {tier} · {slot} — missing</figcaption></figure>'
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    slides: list[str] = []

    # Slide 1 — overview
    slides.append(
        """
<section class="slide intro">
  <h1>Hero Pack 2.0 — превью фонов</h1>
  <p>Virtus Core · Path A · перед живым Stripe-прогоном</p>
  <ul>
    <li><b>Basic</b> — hero_1, hero_2</li>
    <li><b>Business</b> — + background, CTA, services</li>
    <li><b>Premium</b> — + banner, gallery, showcase, calculator, footer</li>
  </ul>
  <p class="hint">Листайте → или фильтруйте по нише / пакету.</p>
</section>
"""
    )

    # One slide per niche: key visuals
    for niche in known_niche_ids():
        cards = []
        for tier, slots in (
            ("basic", ("hero_1", "hero_2")),
            ("business", ("cta", "services", "background_1")),
            ("premium", ("banner", "gallery", "showcase")),
        ):
            for slot in slots:
                cards.append(_card(niche, tier, slot))
        slides.append(
            f"""
<section class="slide niche" id="{niche}">
  <h2>{niche}</h2>
  <div class="grid">{"".join(cards)}</div>
</section>
"""
        )

    # Full inventory slide (compact)
    inv = []
    for niche in known_niche_ids():
        for tier, slots in (
            ("basic", BASIC_SLOTS),
            ("business", BUSINESS_SLOTS),
            ("premium", PREMIUM_SLOTS),
        ):
            for slot in slots:
                ok = slot_path(niche, tier, slot).is_file()
                inv.append(
                    f'<li class="{"ok" if ok else "bad"}">{niche}/{tier}/{slot}</li>'
                )
    slides.append(
        f"""
<section class="slide inventory">
  <h2>Инвентарь слотов</h2>
  <ul class="inv">{"".join(inv)}</ul>
</section>
"""
    )

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hero Pack 2.0 — CEO slides</title>
<style>
:root {{
  --bg: #0b1220; --panel: #151f33; --ink: #e8eefc; --muted: #93a4c3; --acc: #5b8def;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; font-family: "Segoe UI", system-ui, sans-serif;
  background: var(--bg); color: var(--ink);
}}
.toolbar {{
  position: sticky; top: 0; z-index: 20;
  display: flex; flex-wrap: wrap; gap: .75rem; align-items: center;
  padding: .75rem 1rem; background: rgba(11,18,32,.92); border-bottom: 1px solid #24314d;
  backdrop-filter: blur(8px);
}}
.toolbar button, .toolbar select {{
  background: var(--panel); color: var(--ink); border: 1px solid #334155;
  border-radius: 8px; padding: .45rem .8rem; cursor: pointer; font: inherit;
}}
.toolbar button:hover {{ border-color: var(--acc); }}
.deck {{ scroll-snap-type: y mandatory; height: calc(100vh - 56px); overflow-y: auto; }}
.slide {{
  min-height: calc(100vh - 56px); scroll-snap-align: start;
  padding: 1.5rem clamp(1rem, 3vw, 2.5rem) 2.5rem;
}}
.intro h1 {{ font-size: clamp(1.6rem, 4vw, 2.4rem); margin: 0 0 .5rem; }}
.intro ul {{ line-height: 1.7; color: var(--muted); }}
.hint {{ color: var(--acc); }}
.niche h2 {{ text-transform: capitalize; margin: 0 0 1rem; }}
.grid {{
  display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}}
.card {{
  margin: 0; background: var(--panel); border-radius: 12px; overflow: hidden;
  border: 1px solid #24314d;
}}
.card img {{ display: block; width: 100%; height: 150px; object-fit: cover; }}
.card figcaption {{
  padding: .55rem .75rem; font-size: .82rem; color: var(--muted);
}}
.card[data-tier="premium"] {{ border-color: #c9a22755; }}
.card[data-tier="business"] {{ border-color: #5b8def55; }}
.inv {{
  columns: 3; column-gap: 1.5rem; font-size: .8rem; color: var(--muted);
  list-style: none; padding: 0; margin: 0;
}}
.inv .ok::before {{ content: "✓ "; color: #34d399; }}
.inv .bad::before {{ content: "✗ "; color: #f87171; }}
@media (max-width: 800px) {{ .inv {{ columns: 1; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <strong>Hero Pack slides</strong>
  <button type="button" id="prev">←</button>
  <button type="button" id="next">→</button>
  <select id="niche">
    <option value="">Все ниши…</option>
    {"".join(f'<option value="{n}">{n}</option>' for n in known_niche_ids())}
  </select>
  <span id="pos" style="color:var(--muted);font-size:.9rem"></span>
</div>
<div class="deck" id="deck">
{"".join(slides)}
</div>
<script>
(function(){{
  const deck = document.getElementById('deck');
  const slides = Array.from(deck.querySelectorAll('.slide'));
  const pos = document.getElementById('pos');
  function idx() {{
    const top = deck.scrollTop;
    let best = 0, dist = Infinity;
    slides.forEach((s,i) => {{
      const d = Math.abs(s.offsetTop - top);
      if (d < dist) {{ dist = d; best = i; }}
    }});
    return best;
  }}
  function go(i) {{
    const t = Math.max(0, Math.min(slides.length-1, i));
    slides[t].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    pos.textContent = (t+1) + ' / ' + slides.length;
  }}
  document.getElementById('prev').onclick = () => go(idx()-1);
  document.getElementById('next').onclick = () => go(idx()+1);
  document.getElementById('niche').onchange = (e) => {{
    const v = e.target.value;
    if (!v) return go(0);
    const el = document.getElementById(v);
    if (el) el.scrollIntoView({{ behavior: 'smooth' }});
  }};
  deck.addEventListener('scroll', () => {{ pos.textContent = (idx()+1) + ' / ' + slides.length; }});
  go(0);
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown') go(idx()+1);
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(idx()-1);
  }});
}})();
</script>
</body>
</html>
"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(OUT / "index.html")
    print("niches", len(known_niche_ids()))


if __name__ == "__main__":
    main()
