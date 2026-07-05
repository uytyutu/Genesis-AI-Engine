# CEO Steps — Resend + Cloudflare (genesis-ai-engine.com)

**Goal:** `legal: ok` + send from `Genesis <hello@genesis-ai-engine.com>`

**Already done in repo:** `public_launch.json`, `deploy.env.example`  
**Production still needs:** DNS verify + Railway volume/env (see Step 4–5)

---

## Шаг 1 — Resend: добавить домен

1. Откройте [resend.com/domains](https://resend.com/domains)
2. **Add Domain**
3. Введите: `genesis-ai-engine.com` (root domain — OK для Mission 1)
4. Region: оставьте по умолчанию
5. **Add** — Resend покажет вкладку **DNS Records**

**Не нажимайте Verify**, пока не вставите записи в Cloudflare (Шаг 2).

---

## Шаг 2 — Cloudflare: DNS записи

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **genesis-ai-engine.com**
2. Слева **DNS** → **Records** → **Add record**

Для **каждой** строки из Resend (вкладка Records) — **Add record**:

| Resend показывает | В Cloudflare |
|-------------------|--------------|
| Type | Type (TXT / MX / CNAME) |
| Name / Host | Name (часто `@` или `send` или `resend._domainkey`) |
| Value / Content | Content (копировать целиком) |
| TTL | Auto |
| Proxy | **DNS only** (серое облако ☁️) — **обязательно для email-записей** |

### Типичный набор Resend (пример — **ваши значения будут другими**)

Resend выдаёт **уникальные** значения. Обычно 3–4 записи:

1. **TXT** `@` — SPF (`v=spf1 include:... ~all`)
2. **MX** `send` (или return path subdomain) — `feedback-smtp...`
3. **CNAME** `resend._domainkey` → `...dkim.amazonses.com` (или несколько DKIM CNAME)
4. **TXT** `_dmarc` — `v=DMARC1; p=none;` (Resend может предложить; если нет — добавьте вручную после verify)

**Важно Cloudflare:**

- Имя `genesis-ai-engine.com` в Resend = `@` в Cloudflare
- Имя `send.genesis-ai-engine.com` = `send` в Cloudflare
- **Proxy OFF** (DNS only) на всех email-записях

3. Сохраните все записи.

---

## Шаг 3 — Resend: Verify

1. Вернитесь в Resend → Domains → `genesis-ai-engine.com`
2. **Verify DNS Records**
3. Статус: `pending` → через 1–15 мин (иногда до 48 ч) → **`verified`**

Если `failed` — в Cloudflare проверьте: proxy off, имя хоста, лишние кавычки в TXT.

**Проверка DNS (опционально):**

```powershell
nslookup -type=TXT genesis-ai-engine.com
nslookup -type=TXT _dmarc.genesis-ai-engine.com
```

---

## Шаг 4 — Railway: production env + memory

### 4a. Variables

Railway → **genesis-ai-engine-production** → **Variables**:

```env
GENESIS_EMAIL_FROM=Genesis <hello@genesis-ai-engine.com>
RESEND_API_KEY=re_...    # уже должен быть
```

**Deploy** / redeploy после изменения.

### 4b. `public_launch.json` на volume

Если есть volume `/data`:

Файл: **`/data/memory/public_launch.json`**

```json
{
  "contact_email": "hello@genesis-ai-engine.com",
  "company_name": "Genesis AI Engine",
  "legal_note": "Impressum / Kontakt — EU. Domain: genesis-ai-engine.com"
}
```

**Как попасть в файл:**

- Railway CLI / one-off shell, **или**
- Временно: задеплоить с volume mount и отредактировать через поддерживаемый способ Railway

Без этого файла на volume → `legal` останется **error**, даже если в git уже заполнено.

---

## Шаг 5 — Проверки (Cursor / CEO)

После Шагов 3–4 откройте:

| Проверка | URL | Ожидание |
|----------|-----|----------|
| Legal | `https://genesis-ai-engine-production.up.railway.app/api/owner/public-launch` | `checks` → `legal` → **state: ok** |
| Email | `.../api/sales/email-status` | `configured: true` |
| Receipt | Тестовый заказ на **ваш** email | From: `Genesis <hello@genesis-ai-engine.com>` |

Напишите Cursor: **`Resend verified`** + **`Railway updated`** — повторим API check.

---

## Шаг 6 — Stripe Live

После `legal: ok` + email smoke → `First_Customer_Plan_v1.md` §5 (sk_live, webhook, live €).

---

## DMARC (рекомендация после verify)

Когда SPF+DKIM verified, в Cloudflare:

| Type | Name | Content |
|------|------|---------|
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:hello@genesis-ai-engine.com` |

Позже `p=quarantine` — после стабильной доставки.

---

## Horizon (не сейчас)

- `support@`, `partners@` — aliases в Resend или Google Workspace
- `app.` / `api.` subdomains на Vercel
- Домены клиентов — платит клиент
