# Beta — публичная среда для тестировщиков

**Цель:** постоянная ссылка в браузере (без Genesis.exe), отдельно от production, обновляется после `git push` в ветку разработки.

## Домены (genesis-ai-engine.com)

| Назначение | URL |
|------------|-----|
| Production (не трогать) | https://genesis-ai-engine.com · https://genesis-ai-engine.vercel.app |
| Production API | https://genesis-ai-engine-production.up.railway.app |
| **Beta (создать)** | **https://beta.genesis-ai-engine.com/site** |
| API Beta (опционально) | https://api-beta.genesis-ai-engine.com |

**Ссылка для жены / тестировщиков:** https://beta.genesis-ai-engine.com/site

**Ветка:** `cursor/mission1-genesis-brain-public-layer`

**DNS (2026-07-09):** `genesis-ai-engine.com` существует; `beta.genesis-ai-engine.com` — **ещё нет** (нужен CNAME в Cloudflare).

---

## CEO checklist (≈30 мин, один раз)

| # | Где | Действие |
|---|-----|----------|
| 1 | Railway | New service `genesis-beta` → ветка разработки → Root `.` → Dockerfile |
| 2 | Railway | Env из `deploy.beta.env.example`; volume `/data` **отдельный** от prod |
| 3 | Vercel | **Новый проект** `genesis-beta` (не production project) → root `dashboard/frontend` |
| 4 | Vercel | Env: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL` |
| 5 | DNS Cloudflare | CNAME `beta` → Vercel; опционально `api-beta` → Railway |
| 6 | Vercel | Domains → `beta.genesis-ai-engine.com` → Valid + HTTPS |
| 7 | GitHub | Secrets `BETA_FRONTEND_URL`, `BETA_BACKEND_URL` → auto smoke после push |
| 8 | Smoke | `py scripts/verify_beta_deploy.py --frontend ... --backend ...` |

---

## Схема

```text
git push → cursor/mission1-...
    ↓
Railway "genesis-beta" (auto-deploy, отдельный volume)
    ↓
Vercel project "genesis-beta" → beta.genesis-ai-engine.com
    ↓
https://beta.genesis-ai-engine.com/site
```

---

## Шаг A — Railway: backend beta

1. [railway.app](https://railway.app) → проект Genesis → **New Service** → GitHub repo.
2. **Service name:** `genesis-beta`
3. **Branch:** `cursor/mission1-genesis-brain-public-layer` (не `main`).
4. **Root Directory:** `.` · **Builder:** Dockerfile
5. **Variables:**

```env
GENESIS_MEMORY_DIR=/data
GENESIS_PUBLIC_URL=https://beta.genesis-ai-engine.com
GENESIS_CORS_ORIGINS=https://beta.genesis-ai-engine.com
GENESIS_GROQ_API_KEY=gsk_...   # Groq — required for beta parity (not GENESIS_LLM_API_KEY)
# Optional: GENESIS_GROQ_MODEL=llama-3.3-70b-versatile
```

6. Volume `/data` — отдельный от production.
7. *(Опционально)* Settings → **Custom Domain** → `api-beta.genesis-ai-engine.com` → CNAME в Cloudflare.

Проверка:

```text
https://YOUR-BETA.up.railway.app/api/status
https://YOUR-BETA.up.railway.app/api/public/genesis-ai/attachments/policy?visitor_id=test
```

`git_commit` в `/api/status` = последний коммит ветки.

---

## Шаг B — Vercel: frontend beta

**Важно:** создайте **отдельный** Vercel-проект (`genesis-beta`). Не меняйте env и домены production-проекта.

1. [vercel.com](https://vercel.com) → **Add New Project** → тот же GitHub repo.
2. **Project name:** `genesis-beta`
3. **Root Directory:** `dashboard/frontend`
4. **Production Branch:** `cursor/mission1-genesis-brain-public-layer`
5. **Environment Variables** (Production для этого проекта):

```env
NEXT_PUBLIC_API_URL=https://YOUR-BETA.up.railway.app
NEXT_PUBLIC_SITE_URL=https://beta.genesis-ai-engine.com
```

6. **Settings → Domains** → Add `beta.genesis-ai-engine.com`

Stripe webhooks на beta идут на beta backend через `next.config.ts` (`NEXT_PUBLIC_API_URL` при сборке).

---

## Шаг C — DNS (Cloudflare) — СТОП до подтверждения CEO

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **genesis-ai-engine.com** → DNS.
2. Добавить (точное значение Vercel покажет после Add Domain):

| Type | Name | Target |
|------|------|--------|
| CNAME | `beta` | `cname.vercel-dns.com` (или из Vercel) |

3. *(Опционально)* API на красивом домене:

| Type | Name | Target |
|------|------|--------|
| CNAME | `api-beta` | Railway custom domain target |

4. Дождаться **Valid Configuration** в Vercel (HTTPS автоматически).
5. Написать агенту: «DNS beta готов».

**Не трогать:** production Vercel/Railway и их env.

---

## Шаг D — CORS

`GENESIS_CORS_ORIGINS` на Railway beta = **точно** `https://beta.genesis-ai-engine.com` (без `/site`, без trailing slash).

Если frontend и API на разных доменах — CORS всё равно на **frontend** origin.

---

## Шаг E — Smoke test

```powershell
py scripts/verify_beta_deploy.py `
  --frontend https://beta.genesis-ai-engine.com `
  --backend https://YOUR-BETA.up.railway.app
```

Автоматически: `/api/status`, chat POST, attachments/policy, genesis-ai/status, TTS status, `/site`.

**Вручную в браузере** (на https://beta.genesis-ai-engine.com/site):

| Проверка | Ожидание |
|----------|----------|
| Чат | Ответ, не «нет связи» |
| PDF | Загрузка + вопрос по документу |
| Voice | Микрофон, ответ голосом (HTTPS обязателен) |
| Dictation | Диктовка в поле ввода |

Или GitHub → Actions → **Beta smoke** / **Beta post-push smoke**.

---

## Рабочий цикл

```text
1. Локально: Genesis.exe или pytest
2. git commit + git push (ветка cursor/mission1-...)
3. Подождать 3–8 мин (Railway + Vercel build)
4. Отправить: https://beta.genesis-ai-engine.com/site
5. Feedback → fix → push → та же ссылка обновится
```

---

## Что Cursor не может без вас

- Войти в Vercel / Railway / Cloudflare / GitHub
- Создать DNS-запись `beta` без доступа к Cloudflare
- Добавить secrets в GitHub

После шагов A–C пришлите beta URLs — запустим smoke автоматически.
