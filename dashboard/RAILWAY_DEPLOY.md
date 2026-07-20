# Railway Deploy — Genesis API (Public Launch v1)

## Root cause (типичная ошибка)

Backend (`dashboard/backend`) импортирует пакеты из **корня репозитория**:

- `brain/`
- `kernel/`
- `agents/`

Если в Railway указать **Root Directory = `dashboard/backend`**, в образ попадает только папка backend.  
Сборка или старт падают с `ModuleNotFoundError` / импорт не найден.

## Правильная конфигурация

| Параметр | Значение |
|----------|----------|
| **Root Directory** | `.` (корень репозитория) |
| **Builder** | Dockerfile (`/Dockerfile`) |
| **Healthcheck** | `/health` |

## Переменные окружения

```
GENESIS_MEMORY_DIR=/data
GENESIS_PUBLIC_URL=https://beta.genesis-ai-engine.com
GENESIS_CORS_ORIGINS=https://beta.genesis-ai-engine.com
STRIPE_SECRET_KEY=sk_live_...   # or sk_test_ on staging
STRIPE_WEBHOOK_SECRET=whsec_...
```

Volume: mount `/data` → `GENESIS_MEMORY_DIR=/data`

## Проверка после деплоя

```
https://YOUR-RAILWAY-URL.up.railway.app/api/status
https://YOUR-RAILWAY-URL.up.railway.app/api/sales/packages
```

## Локальная проверка (без Docker)

```powershell
cd dashboard\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

## Для будущих Genesis-проектов (COO rule)

Перед деплоем monorepo на Railway:

1. Есть ли импорты **вне** root directory сервиса?
2. Если да → Root Directory = корень репо + Dockerfile копирует все зависимости.
3. Healthcheck на лёгкий endpoint (`/api/status`).
4. Persistent data → volume + `GENESIS_MEMORY_DIR`.
