# Knowledge Intake Engine — developer map

**Audience:** developers / Cursor agents only — not user-facing copy.  
**Status:** Foundation scaffold · first module = attachment PDF (after Transparency slice).  
**Code:** `dashboard/backend/app/integration/knowledge_intake.py` · `attachment_policy.py` · `feature_registry.py`

---

## Purpose

Single platform layer: turn **any external source** into knowledge Vector can use.

Sources (roadmap): PDF, DOCX, images, URL, GitHub, Figma, Notion, YouTube, Excel/CSV, audio, video, …

Today: upload + filename only. Pipeline slots exist; parsers plug in per source.

---

## Pipeline (canonical)

```text
Source          IntakeDescriptor + Upload Gate
   ↓
Normalizer      mime detect, charset, metadata, tier check
   ↓
Parser          bytes/url → structured text (+ optional vision summary)
   ↓
Chunker         split for context window / future retrieval
   ↓
Embedding       [SLOT — not implemented] vector index per tenant
   ↓
Memory          persist chunks under MemoryRoot / visitor or tenant scope
   ↓
Reasoning       select relevant chunks for this turn (rules → RAG later)
   ↓
Vector          Genesis Brain prompt block + public reply
```

**Phase 1 (AI-1):** Source → Normalizer → Parser → **prompt inject** (skip Chunker/Embedding/Memory persist).  
**Phase 2+:** enable Chunker → Memory → Reasoning; Embedding when retrieval needed.

---

## Gates (do not duplicate)

| Gate | Module | Rule |
|------|--------|------|
| Upload | `attachment_policy.AttachmentPolicy.check_upload` | tier size/count/mime |
| Parse | `attachment_policy.AttachmentPolicy.check_parse` | tier parse kind + `FeatureRegistry` |
| Feature | `feature_registry.FeatureRegistry` | `attachment_pdf`, `intake_url`, … all default **off** |
| Capability | `capability_registry.CapabilityRegistry` | read-only snapshot for owner diagnostics |

Free tier PDF teaser (when `attachment_pdf` on): 1 doc/day, 5 pages, 4 MB.

---

## Module map

| Stage | Responsibility | Code today | Next slice |
|-------|----------------|------------|------------|
| **Source** | Accept descriptor | `IntakeDescriptor`, `PublicChatAttachmentService` | Transparency |
| **Normalizer** | Validate + normalize input | `PipelineStage.NORMALIZE` stub | AI-1 PDF |
| **Parser** | Extract text | `IntakeSource.ingest()` per kind | `AttachmentPdfSource` |
| **Chunker** | Split text | `KnowledgeChunk` dataclass only | After Memory |
| **Embedding** | Vector index | `PipelineStage.EMBED` stub — **no op** | Horizon |
| **Memory** | Store intake artifacts | `MemoryRoot`, `memory/knowledge_intake/` (future path) | F3 wired |
| **Reasoning** | Pick context for turn | Brain `assemble_messages` + intake block | RAG phase |
| **Vector** | Reply | `GenesisAIService.chat` | unchanged contract |

---

## Registering a new source

1. Add `IntakeSourceKind` in `knowledge_intake.py` (if new kind).
2. Add feature flag `intake_<kind>` in `feature_registry.py` — **enabled: false**.
3. Implement `IntakeSource` class: `can_handle` + `ingest`.
4. Register on `KnowledgeIntakeRegistry` at app startup (integration context).
5. Wire tier limits in `attachment_policy.TIER_LIMITS` if uploads apply.
6. Tests: gate + parser + prompt block shape.

Example future flags:

```text
attachment_pdf      → AI-1
attachment_docx     → AI-2
attachment_vision   → images
intake_url          → fetch + extract
intake_github       → repo readme / files
intake_figma        → API export
```

---

## Memory layout (planned)

```text
memory/
  knowledge_intake/
    {visitor_id}/
      {intake_id}/
        meta.json
        raw/          # optional retained bytes
        parsed.txt
        chunks.jsonl
        embeddings/   # Phase 2+ — empty until EMBED stage on
```

Owner platform tenant uses legacy flat `memory/` until customer tenants ship (`memory/tenants/{id}/`).

---

## Integration point (Vector)

Parsed content becomes a **context block** — never raw file bytes in the public API:

```python
result.to_context_block()  # → prepended to user turn in GenesisAIService
```

Do **not** change Truth Pass commerce rules when adding intake.

---

## Slices (execution order — frozen)

```text
Foundation ✅
↓ Knowledge Intake — Transparency
↓ Knowledge Intake — AI-1 PDF (Source → Normalizer → Parser → Vector)
↓ DOCX → TXT/CSV → Vision → Audio → ZIP
↓ URL / GitHub / Notion / Figma / …
↓ Workspace → Co-Creation → Specialists → Subscriptions → Business Automation
```

---

## What not to rewrite

- `security.py` API tiers  
- `public_truth_catalog` / Mission 1 commerce  
- `GenesisBrain` personality pipeline  
- `FeatureRegistry` / `CapabilityRegistry` pattern — extend only  

---

## References

- `docs/SKILLS_PLATFORM.md` — Factory skills (downstream of intake for builds)  
- `docs/VIRTUS_WORKSPACE_ARCHITECTURE_DIRECTIVE.md` — Platform → Workspace → Project  
- `docs/GENESIS_CREATOR_ARCHITECTURE.md` — tenant memory partition  
