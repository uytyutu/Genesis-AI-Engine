# Beta / Preview — тестовая среда для внешних тестировщиков

**Цель:** постоянная ссылка (не localhost), отдельно от production, обновляется после push в ветку разработки.

**Production (не трогать):**
- Frontend: https://genesis-ai-engine.vercel.app
- Backend: https://genesis-ai-engine-production.up.railway.app

**Beta (создать):** ветка `cursor/mission1-genesis-brain-public-layer` → отдельный backend + frontend.

**CEO checklist (≈30 мин, один раз):**

| # | Где | Действие |
|---|-----|----------|
| 1 | Railway | New service `genesis-beta` → branch `cursor/mission1-genesis-brain-public-layer` → Root `.` → Dockerfile |
| 2 | Railway | `GENESIS_CORS_ORIGINS` = `https://beta.virtuscore.ai` (или ваш beta URL) |
| 3 | Vercel | Домен `beta.virtuscore.ai` → проект frontend (root `dashboard/frontend`) |
| 4 | DNS | CNAME `beta` → Vercel (см. **DNS ниже** — сейчас записи **нет**) |
| 5 | Vercel | Env: `NEXT_PUBLIC_API_URL` + `NEXT_PUBLIC_SITE_URL` = beta URLs |
| 6 | GitHub | Secrets `BETA_FRONTEND_URL`, `BETA_BACKEND_URL` → auto smoke после push |
| 7 | Тестерам | **`https://beta.virtuscore.ai/site`** — ссылка постоянная |

---

## Рекомендуемая схема (Вариант 1)

```text
git push → ветка cursor/mission1-...
    ↓
Railway service "genesis-beta" (Dockerfile, auto-deploy)
    ↓
Vercel Preview или beta.virtuscore.ai → frontend
    ↓
Стабильная ссылка для жены / тестировщиков
```

---

## Шаг A — Railway: backend beta

1. [Railway](https://railway.app) → проект Genesis → **New Service** → Deploy from GitHub repo.
2. **Service name:** `genesis-beta`
3. **Branch:** `cursor/mission1-genesis-brain-public-layer` (не `main`).
4. **Root Directory:** `.` (корень репо)
5. **Builder:** Dockerfile (`/Dockerfile`)
6. **Variables** (отдельно от production):

```env
GENESIS_MEMORY_DIR=/data
GENESIS_PUBLIC_URL=https://BETA-FRONTEND-URL
GENESIS_CORS_ORIGINS=https://BETA-FRONTEND-URL
GENESIS_LLM_API_KEY=...   # те же ключи, что для теста
```

7. Volume `/data` — отдельный от production (чтобы тесты не портят prod memory).
8. После деплоя проверить:

```text
https://YOUR-BETA.up.railway.app/api/status
https://YOUR-BETA.up.railway.app/api/public/genesis-ai/attachments/policy?visitor_id=test
```

`git_commit` в `/api/status` должен совпадать с последним коммитом ветки (сейчас `b61bddb`+).

---

## Шаг B — Vercel: frontend beta

### Вариант B1 — стабильный домен (лучше для жены)

1. [Vercel](https://vercel.com) → проект frontend (root: `dashboard/frontend`).
2. **Settings → Domains** → добавить `beta.virtuscore.ai` (или `preview.virtuscore.ai`).
3. DNS у регистратора: CNAME `beta` → `cname.vercel-dns.com` (Vercel покажет точное значение).
4. **Settings → Git** → Production Branch оставить `main`; для beta:
   - либо отдельный Vercel project `virtus-beta`, привязанный к ветке `cursor/mission1-...`;
   - либо Assign domain `beta.virtuscore.ai` к **Preview** этой ветки.

### Вариант B2 — Preview URL (быстрее, без DNS)

1. Vercel → Project → Settings → Git → включить **Preview Deployments** для всех веток.
2. После каждого `git push` появится URL вида:
   `https://genesis-ai-engine-git-cursor-mission1-....vercel.app`
3. Минус: URL длинный и меняется при смене ветки/форка. Для постоянного теста лучше B1.

### Environment Variables (Vercel → Preview или проект beta)

```env
NEXT_PUBLIC_API_URL=https://YOUR-BETA.up.railway.app
NEXT_PUBLIC_SITE_URL=https://beta.virtuscore.ai
```

Stripe webhooks на beta идут на **beta** backend через `next.config.ts` (читает `NEXT_PUBLIC_API_URL` при сборке). Production env в Vercel **не менять**.

---

## Шаг B2 — DNS для `beta.virtuscore.ai` (СТОП до подтверждения CEO)

**Проверка (2026-07-09):** `beta.virtuscore.ai` и `virtuscore.ai` **не резолвятся** в публичном DNS. Ссылка для тестировщиков **не откроется**, пока домен не зарегистрирован и не привязан к Vercel.

### Если домен `virtuscore.ai` уже куплен у регистратора

1. Войти в панель DNS (Cloudflare, Namecheap, IONOS, …).
2. Добавить запись (Vercel покажет точное значение после **Settings → Domains → Add**):

| Type | Name | Value |
|------|------|-------|
| CNAME | `beta` | `cname.vercel-dns.com` (или значение из Vercel) |

3. В Vercel → проект frontend → **Domains** → Add `beta.virtuscore.ai` → дождаться **Valid Configuration**.
4. Написать агенту: «DNS beta готов» — продолжим smoke test.

### Если домена `virtuscore.ai` ещё нет

1. Зарегистрировать `virtuscore.ai` у регистратора **или**
2. Временно использовать **Vercel Preview URL** (без красивого домена):

```text
https://genesis-ai-engine-git-cursor-mission1-....vercel.app/site
```

Тогда в Railway beta: `GENESIS_CORS_ORIGINS` = этот preview URL (без trailing slash).

**Не трогать production:** `genesis-ai-engine.vercel.app` и `genesis-ai-engine-production.up.railway.app`.

---

## Шаг C — CORS

Backend beta должен разрешать **точный** URL frontend beta в `GENESIS_CORS_ORIGINS`.

Если используете Preview URL Vercel — после первого деплоя скопировать URL и добавить в Railway beta variables. При каждой смене preview-домена обновлять CORS (ещё одна причина предпочесть `beta.virtuscore.ai`).

---

## Шаг D — CEO smoke test (перед ссылкой жене)

```powershell
py scripts/verify_beta_deploy.py --frontend https://beta.virtuscore.ai --backend https://YOUR-BETA.up.railway.app
```

Или GitHub → Actions → **Beta smoke** (ручной) / **Beta post-push smoke** (после push, если secrets заданы).

Открыть beta frontend → `/site`:

1. Текстовый вопрос — ответ (не «нет связи»).
2. PDF upload + вопрос по документу.
3. `https://YOUR-BETA.up.railway.app/api/status` → `git_commit` актуальный.

---

## Рабочий цикл для владельца

```text
1. Локально: Genesis.exe или pytest
2. git commit + git push (ветка cursor/mission1-...)
3. Подождать 3–8 мин (Railway + Vercel build)
4. Отправить одну ссылку: https://beta.virtuscore.ai/site
5. Собрать feedback → fix → push → та же ссылка обновится
```

---

## Вариант 3 — разовая демо (ngrok / Cloudflare Tunnel)

Только для «показать сегодня», не для жены на постоянке:

```powershell
# Терминал 1: backend уже на :8000
# Терминал 2: frontend на :3000
# Терминал 3:
ngrok http 3000
```

Минус: нужен запущенный ПК, URL меняется, микрофон/voice может требовать HTTPS.

---

## Что Cursor не может сделать без вас

- Войти в Vercel / Railway / DNS регистратора
- Создать `beta.virtuscore.ai` без доступа к домену virtuscore.ai
- Добавить secrets в GitHub (для полного CI)

После шагов A–B пришлите beta URLs — можно автоматизировать smoke-check в `scripts/verify_beta_deploy.py`.
