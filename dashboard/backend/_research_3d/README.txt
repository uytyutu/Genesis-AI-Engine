# Research 3D workshop (isolated from Path A)
#
# One niche = one approved preset + PBR material. IDs = Factory known_niche_ids().
# Markets reuse the same mesh; legal/copy stay Path A.
#
# All 10 niches READY (original CC0 meshes, ~2–5 KB each):
#   dental CeramicGloss | auto TireRubberMetal | law BrushedGold | beauty GlossBottle
#   energy SolarGlass | green LeafSatin | computer DeviceAnodized | appliance ApplianceSteel
#   handwerk ToolSteelWood | generic StorefrontMatte
#
# Commands (repo root):
#   py -3.12 scripts/generate_research_3d_presets.py
#   py -3.12 scripts/research_3d_gate.py --scene dashboard/backend/_research_3d/scenes/dental
#
# CEO phone FPS: FPS_CHECKLIST_DENTAL.txt (same method for any scenes/<niche>/hero.glb)
# Checkout 3d_premium remains WAITLIST until you approve production flip.
