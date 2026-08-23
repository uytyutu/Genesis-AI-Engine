"""Patch store HTML onerror fallback product.jpg -> missing.jpg."""
from pathlib import Path

root = Path("dashboard/frontend/public/package-previews/stores/premium")
n = 0
for html in root.rglob("*.html"):
    t = html.read_text(encoding="utf-8", errors="ignore")
    nt = t.replace(
        "this.src='assets/images/product.jpg'",
        "this.src='assets/images/missing.jpg';this.alt='Bild fehlt'",
    ).replace(
        'this.src="assets/images/product.jpg"',
        'this.src="assets/images/missing.jpg";this.alt="Bild fehlt"',
    )
    if nt != t:
        html.write_text(nt, encoding="utf-8")
        n += 1
print("patched_html", n)
