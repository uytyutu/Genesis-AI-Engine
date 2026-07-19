# Research 3D workshop (isolated from Path A)
#
# 10 niches x 5 examples = 50 CC0 presets with PBR materials.
# Scene engine (studio light + auto-orbit + scroll): runtime/scene_engine.html
#
# Serve locally (CDN Three.js needs http, not file:// for modules sometimes):
#   cd dashboard/backend/_research_3d
#   py -3.12 -m http.server 8765
#   open http://127.0.0.1:8765/runtime/scene_engine.html
#
# Regenerate:
#   py -3.12 scripts/generate_research_3d_presets.py
#
# Gate one example:
#   py -3.12 scripts/research_3d_gate.py --scene dashboard/backend/_research_3d/scenes/dental
#
# 3d_premium checkout remains WAITLIST.
