# Virtus Core Studio Era

**Product:** AI Digital Studio — Creative Identity → digital surfaces  
**Not:** Website Builder

Ideology: [`docs/VIRTUS_CORE_STUDIO_ERA_MANIFEST.md`](./VIRTUS_CORE_STUDIO_ERA_MANIFEST.md)

## Sprint: Creative Identity Generation

Think like a **€50k creative agency director**.

- Human first (founder, why them, must-feel) — niche word later  
- Named theme: Silent Forest / Morning Light / Fire & Smoke / …  
- Brand DNA chain: Story → Emotion → Promise → Metaphor → Theme → Scene → Motion → Type → Color → Interaction  
- **Creative Conflict** → FAIL if incoherent  
- **No idea → no HTML**

## Reality Benchmark — FAIL

Marketing HTML frozen. Owner Preview = Creative Identity deck.

```text
py -3.12 scripts/reality_benchmark.py
```

## Modules

| Piece | Path |
|-------|------|
| Creative Identity | `design_dna/creative_identity.py` |
| Brand DNA (from identity) | `design_dna/brand_dna.py` |
| HTML freeze gate | `design_dna/concept_gate.py` |
| Art Director | `design_dna/art_director.py` |
