# CEO Setup — genesis-ai-engine.com (≈15 min + DNS propagation)

**Выбрано:** `genesis-ai-engine.com` · `hello@genesis-ai-engine.com`  
**Cursor обновил репо:** `public_launch.json`, `deploy.env.example`  
**CEO-only:** регистрация, DNS, Railway production volume

---

## 1. Зарегистрировать домен

Рекомендация: **Cloudflare Registrar** (at-cost .com ~$10/год) или Namecheap.

Домен: **`genesis-ai-engine.com`**

Проверьте в корзине — RDAP показывал свободным 2026-07-04.

---

## 2. Resend — верификация домена

1. [resend.com](https://resend.com) → **Domains** → **Add** → `genesis-ai-engine.com`
2. Скопируйте DNS-записи из Resend в панель DNS (Cloudflare/Namecheap)
3. Дождитесь **Verified**

Типичные записи (точные — только из Resend):

| Тип | Имя | Значение |
|-----|-----|----------|
| TXT | `@` | SPF (Resend) |
| CNAME | `resend._domainkey` | DKIM |
| TXT | `_dmarc` | `v=DMARC1; p=none;` |

---

## 3. Railway — переменные

```
GENESIS_EMAIL_FROM=Genesis <hello@genesis-ai-engine.com>
RESEND_API_KEY=re_...   # уже есть
```

После verify домена в Resend — **redeploy** или restart service.

---

## 4. Railway — `public_launch.json` на volume

Путь: **`/data/memory/public_launch.json`** (если `GENESIS_MEMORY_DIR=/data`)

```json
{
  "contact_email": "hello@genesis-ai-engine.com",
  "company_name": "Genesis AI Engine",
  "legal_note": "Impressum / Kontakt — EU. Domain: genesis-ai-engine.com"
}
```

Без volume файл из образа сбросится при redeploy — **запись на volume обязательна**.

---

## 5. Проверка

```
https://genesis-ai-engine-production.up.railway.app/api/owner/public-launch
→ checks[id=legal].state = "ok"

https://genesis-ai-engine-production.up.railway.app/api/sales/email-status
→ configured: true
```

Тестовый заказ → письмо с `hello@genesis-ai-engine.com` как From.

---

## 6. Stripe Live (после или параллельно)

См. `First_Customer_Plan_v1.md` §5 — `sk_live`, live webhook, smoke €.

---

## Позже (Horizon — не сейчас)

| Тема | Когда |
|------|--------|
| `app.` / `api.` / `docs.` subdomains | После EL3 или custom domain на Vercel |
| `support@`, `partners@`, `invest@` | Resend aliases / routing — EL4+ |
| Защита бренда (короткий Genesis.*) | Стабильный доход |
| **Домены клиентов** | Клиент платит сам ИЛИ «купить через Genesis» (оплата клиента, не Genesis) |

---

**Напишите Cursor:** `Домен куплен` / `Resend verified` — проверим production API.
