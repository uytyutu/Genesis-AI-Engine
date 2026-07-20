"""CEO gallery — niche hero stills for Factory ZIP (no dental)."""

from __future__ import annotations

import shutil
from pathlib import Path

SHOWCASES = Path(__file__).resolve().parents[1] / "_research_3d" / "showcases"
OUT = Path(__file__).resolve().parents[1] / ".factory_ceo_package_previews" / "niche_heroes"
SKIP = {"dental"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cards: list[str] = []
    for niche_dir in sorted(SHOWCASES.iterdir()):
        if not niche_dir.is_dir() or niche_dir.name in SKIP:
            continue
        src = niche_dir / "preview.jpg"
        if not src.is_file():
            continue
        dest = OUT / f"{niche_dir.name}.jpg"
        shutil.copy2(src, dest)
        cards.append(
            f'<figure><img src="{niche_dir.name}.jpg" alt="{niche_dir.name}">'
            f"<figcaption>{niche_dir.name}</figcaption></figure>"
        )
    html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Niche hero backgrounds</title>
<style>
body{{margin:0;font-family:system-ui;background:#0f172a;color:#e2e8f0;padding:1.5rem}}
h1{{font-size:1.25rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-top:1rem}}
figure{{margin:0;background:#1e293b;border-radius:12px;overflow:hidden}}
img{{display:block;width:100%;height:180px;object-fit:cover}}
figcaption{{padding:.75rem 1rem;font-weight:600;text-transform:capitalize}}
.note{{color:#94a3b8;font-size:.9rem}}
</style></head><body>
<h1>Фоны по нишам (Factory ZIP hero) — без стоматологии</h1>
<p class="note">Эти preview.jpg копируются в ZIP как assets/hero.jpg. 3D-модели — позже.</p>
<div class="grid">
{chr(10).join(cards)}
</div>
</body></html>
"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(OUT / "index.html")
    print("niches", len(cards))


if __name__ == "__main__":
    main()
