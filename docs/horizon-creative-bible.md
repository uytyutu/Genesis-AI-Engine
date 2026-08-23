# Horizon Media Engine — Creative Bible (SSOT)

> **Positioning:** Horizon создаёт не «AI-видео», а готовую рекламу коммерческого уровня.
> Зритель не должен подумать: «это сделал ИИ».

## Stage

- **Internal Only** — реклама Virtus Core и собственных продуктов.
- Клиентская продажа — только после месяцев доказанного качества на себе.
- Video generation / Export MP4 — **выключены** в Phase D Proof (оболочка + правила).

## Product name

**Horizon Studio — AI Creative Director**  
(Virtus Core Horizon — автоматическая студия рекламных кампаний)

Не позиционировать как «AI Video Generator».

## Studio order (Prompt last)

1. Площадка  
2. Цель  
3. Аудитория  
4. Длительность  
5. Жанр  
6. Стиль монтажа  
7. Озвучка  
8. Музыка  
9. Материалы (AI Mode / User Assets)  
10. Брендинг  
11. **Prompt Director**

## Principles

- Пользователь принимает творческие решения; Horizon исполняет.
- Media Orchestrator — без привязки к одному видеодвижку.
- Универсальный Media Engine (TikTok, Reels, Shorts, YouTube, LinkedIn, X, Pinterest).
- Quality Gate обязателен до Export.
- Director Cut: перегенерация слабых сцен, не всего ролика.
- Creative Control: несколько вариантов (A/B/C/D), затем точечные правки.
- Quality Target: Economy / Business / Premium / Cinema.

## Quality Gate

1. Character Consistency  
2. Motion Consistency  
3. Story Consistency  
4. Transition Engine  
5. Audio Sync  
6. Subtitle Quality  
7. Brand Safety  
8. AI Artifact Detector  

Commercial Ready: Story · Motion · Audio · Brand · Subtitle · Artifact · Export.

## Tiers (later commercial)

- **Horizon Ads** — 15–60 сек  
- **Horizon Promo** — 30–120 сек  
- **Horizon Studio** — бренд-фильмы / запуски  

## Factory hook (planned)

Website → Generate Promo → multi-platform pack.

## Code

- Manifest: `dashboard/backend/app/integration/horizon_studio.py`
- API: `GET /api/owner/horizon`
- UI: `/horizon`
- Related publish stub: `/tiktok-horizon`
