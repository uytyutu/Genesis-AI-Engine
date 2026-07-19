# Research 3D workshop (isolated from Path A)
#
# Goal: one optimized scene per niche; markets reuse mesh + Path A legal/copy.
# NOT wired to Stripe / SalesOrder / FactoryService.build_landing.
#
# Quick gate:
#   py -3.12 scripts/research_3d_gate.py
#   py -3.12 scripts/research_3d_gate.py --fixture
#
# Layout:
#   niches/     niche → scene slot map
#   markets/    market notes (legal stays Path A)
#   scenes/<niche_id>/   put hero.glb + LICENSE.txt + CREDITS.txt here
#   runtime/    WebGL fail → CSS fallback demo HTML
#   artifacts/  gate reports (gitignored)
