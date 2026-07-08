# Media Engine — Research Notes

**Governance:** Architecture Freeze active. **No Production code.**

**Index:** `INDEX.json` · **Template:** `_note_template.json` · **Notes:** `notes/`

## When to add notes

Only when Mission 1 is not blocked. Passive research during downtime or explicit CEO request.

## How Cursor adds a note

1. Pick next `pending` id from `INDEX.json` or create new id.
2. Copy `_note_template.json` → `notes/NNN-slug.json`.
3. Fill relevance, value, comparison, conclusion, sources.
4. Set `INDEX.json` entry `status: complete` and `file`.

## Planned queue (empty until filled)

| # | Topic | Module |
|---|-------|--------|
| 001 | Video generation models | Media Factory |
| 002 | TTS by language | Media Factory |
| 003 | YouTube / TikTok / Instagram APIs | Publisher |
| 004 | FFmpeg vs rendering tools | Media Factory |
| 005 | Cost per short by AI model | Revenue Optimizer |
| 006 | Observable performance & prediction models | Algorithm Intelligence Engine |
| 007 | Subtitles & STT models | Media Factory |
| 008 | Multimodal AI | Content Architect |

*Directive:* `docs/Genesis_Media_Engine_Architecture_Freeze_Directive.md` · Algorithm Intelligence: `docs/Genesis_Algorithm_Intelligence_Engine_Future_Directive.md`
