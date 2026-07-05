# Corporate Email — Mission 1 Runbook

**Mission:** EL3 · unblock `contact_email` + reliable client receipts  
**Horizon (не сейчас):** Communication Center (`ceo@`, `partners@`, triage, auto-replies)

Cursor подготовил конфигурацию и инструкции. **CEO-only:** домен, DNS в панели регистратора, Resend verify, Railway env/volume.

---

## Рекомендация для Mission 1

**Один официальный адрес** на **вашем домене** через **Resend** (уже в проекте):

| Адрес (выберите один) | Роль |
|----------------------|------|
| `hello@yourdomain.com` | Универсальный (рекомендуется) |
| `contact@yourdomain.com` | Контакты / legal |
| `support@yourdomain.com` | Поддержка |

Позже добавите `sales@`, `partners@` и т.д. — без смены кода.

**Не Gmail** как постоянная почта компании. Временный личный email допустим **только** если домена ещё нет и нужно срочно снять блокер на 48 ч — затем заменить.

---

## Путь A — Правильный (≈30–60 мин)

### CEO — шаги только вы

| # | Действие | Где |
|---|----------|-----|
| A1 | Домен есть? Если нет — купить (Namecheap, Cloudflare, etc.) | Регистратор |
| A2 | Resend → **Domains** → Add domain → скопировать DNS-записи | [resend.com](https://resend.com) |
| A3 | Вставить DNS у регистратора (см. таблицу ниже) | DNS панель |
| A4 | Дождаться **Verified** в Resend | Resend |
| A5 | Railway → Variables: `GENESIS_EMAIL_FROM` | Railway |
| A6 | Railway → Volume `/data` → `memory/public_launch.json` → `contact_email` | Railway |
| A7 | Проверка API (см. Verification) | Браузер |

### DNS (типично Resend)

Resend покажет точные значения. Обычно:

| Тип | Имя | Назначение |
|-----|-----|------------|
| TXT | `@` или домен | SPF (Resend) |
| CNAME | `resend._domainkey` | DKIM |
| TXT | `_dmarc` | `v=DMARC1; p=none;` (старт) |

**Cursor не может** добавить записи в DNS — только вы.

### Railway — переменные

```env
GENESIS_EMAIL_FROM=Genesis <hello@yourdomain.com>
RESEND_API_KEY=re_...   # уже есть
```

`contact_email` в **`/data/memory/public_launch.json`** (не только в git):

```json
{
  "contact_email": "hello@yourdomain.com",
  "company_name": "Genesis",
  "legal_note": "Impressum / Kontakt — EU"
}
```

Если volume пустой после первого деплоя — файл может лежать в образе; **запись на volume** переживает redeploy.

**Как обновить на Railway:**

1. Dashboard → Service → **Volumes** → mount `/data`
2. **Settings** → если есть Shell/CLI — отредактировать файл  
   **Или:** одноразово через Railway CLI / временный deploy hook  
   **Или:** CEO вставляет JSON через Railway file editor (если доступен)

После правки:

```
GET https://genesis-ai-engine-production.up.railway.app/api/owner/public-launch
→ checks[id=legal].state = "ok"
```

---

## Путь B — Быстрый unblock (если домена ещё нет)

Только чтобы **не стопорить** Stripe Live + внутренний тест:

1. CEO называет **рабочий email** (можно существующий).
2. Cursor обновляет репо `public_launch.json` + вы дублируете на Railway volume.
3. `GENESIS_EMAIL_FROM` остаётся на Resend test (`onboarding@resend.dev`) **до verify домена** — письма клиентам только на email, добавленный в Resend test allowlist.

**Ограничение:** outreach незнакомцам лучше после Пути A (домен + verified sender).

---

## Verification (после настройки)

| Проверка | URL / действие | Ожидание |
|----------|----------------|----------|
| Legal | `/api/owner/public-launch` | `legal` → ok |
| Email config | `/api/sales/email-status` | `configured: true` |
| Receipt | Test/live order с вашим email | Inbox |
| Reply-to path | Ответ на `contact_email` | CEO получает |

---

## Что Cursor сделает после вашего решения

Напишите **одной строкой**:

```
Домен: genesis-ai.com (или «домена нет»)
Email: hello@genesis-ai.com (или временный)
```

Cursor:

1. Обновит `dashboard/backend/app/memory/public_launch.json` в репо.
2. Обновит `deploy.env.example` с примером `GENESIS_EMAIL_FROM`.
3. При необходимости — минимальное отображение контакта на `/site` (только если попросите Brief; сейчас не трогаем без email).

---

## Horizon — структура почты (после EL3)

| Адрес | Назначение |
|-------|------------|
| `ceo@` | Только CEO |
| `partners@` | Партнёры |
| `invest@` | Инвесторы |
| `support@` | Клиенты |
| `sales@` | Продажи |
| `legal@` | Юридика |
| `press@` | СМИ |

**Communication Center:** классификация → проверка → риски → отчёт CEO → авто-отказ по правилам GOS для типовых писем. EL4+.

---

*Связано: `Genesis_Progress.md` · `First_Customer_Plan_v1.md` §5*
