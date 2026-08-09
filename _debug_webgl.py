from pathlib import Path
import json
PREVIEWS = Path("dashboard/frontend/public/package-previews")
for s in ["elektro","car_dealership","maler","family_psychology"]:
    b = json.loads((PREVIEWS/f"sites/premium/{s}/CREATIVE_BRIEF.json").read_text(encoding="utf-8"))
    print(s, {k:b.get(k) for k in ["niche_id","package_id","media_mode","recommends_webgl","experience_tier","offline_media","fingerprint"]})

# test invent live
import sys
sys.path.insert(0, "dashboard/backend")
from app.factory.creative_direction import invent_creative_brief, recommends_webgl_3d
print("recommends elektro", recommends_webgl_3d("elektro","premium"))
print("recommends car", recommends_webgl_3d("car_dealership","premium"))
c = invent_creative_brief(brand_name="X", niche_id="elektro", package_id="premium", diversity_salt="t")
print("live elektro", c.recommends_webgl, c.media_mode, c.package_id)
c2 = invent_creative_brief(brand_name="X", niche_id="car_dealership", package_id="premium", diversity_salt="t")
print("live car", c2.recommends_webgl, c2.media_mode, c2.package_id)
c3 = invent_creative_brief(brand_name="X", niche_id="maler", package_id="premium", diversity_salt="t")
print("live maler", c3.recommends_webgl, c3.media_mode)
