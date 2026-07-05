# Mission Brief — Domain Selection (Mission 1)

**Evidence Level:** EL2 → EL3 blocker removal  
**CEO-only:** регистрация, оплата, DNS в панели регистратора  
**Cursor:** подбор, инфраструктура, конфиг после выбора

---

## Критерии выбора

| Критерий | Вес |
|----------|-----|
| Совпадение с текущим брендом (`genesis-ai-engine.vercel.app`) | Высокий |
| Цена (.com ~$10–14/год vs .ai ~$160 за 2 года мин.) | Высокий |
| Произношение / запоминание (DE + EN рынок) | Средний |
| Риск путаницы с Genesis Embodied AI / genesis.ai | Средний |
| Доступность (RDAP, 2026-07-04) | Обязательно |

**Не используем:** голый `genesis.com` (дорого/занят), `genesis.ai` (занят крупным игроком).

---

## TOP-20 (проверка RDAP где отмечено)

| # | Домен | RDAP | Оценка ~1-й год | Комментарий |
|---|-------|------|-----------------|-------------|
| **1** | **genesis-ai-engine.com** | **свободен** | ~$10–14 | **Рекомендация #1** — 1:1 с Vercel URL |
| 2 | hello-genesis.com | свободен | ~$10–14 | Дружелюбно для B2B outreach |
| 3 | genesis-partner.com | свободен | ~$10–14 | Совпадает с «партнёр» Mission 1 |
| 4 | genesiscompany.io | свободен | ~$45 | Коротко, «компания» |
| 5 | genesisdigital.co | свободен | ~$22–27 | .co промо у регистраторов |
| 6 | genesisstack.io | свободен | ~$45 | Tech-оттенок |
| 7 | usegenesis.io | свободен | ~$45 | SaaS-стиль |
| 8 | genesis-ai-engine.io | не проверен | ~$45 | Если .com заняли до вас |
| 9 | getgenesisengine.com | не проверен | ~$10–14 | Маркетинговый |
| 10 | genesisengine.co | не проверен | ~$22 | Короче без дефисов |
| 11 | genesis-engine.co | не проверен | ~$22 | Риск путаницы с genesis-engine.tech |
| 12 | genesishq.com | не проверен | ~$10–14 | «Штаб» |
| 13 | genesisshift.com | не проверен | ~$10–14 | Бренд «смена» |
| 14 | genesislaunch.com | не проверен | ~$10–14 | Public launch |
| 15 | genesis-pilot.com | не проверен | ~$10–14 | Пилот / эксперимент |
| 16 | genesisworks.com | не проверен | ~$10–14 | Услуги |
| 17 | genesis-forge.com | не проверен | ~$10–14 | Factory-метафора |
| 18 | genesisos.com | **занят** | — | Пропустить |
| 19 | genesisaiengine.com | **занят** | — | Пропустить |
| 20 | getgenesisai.com | **занят** | — | Пропустить |

*Цены ориентировочные: Cloudflare/Namecheap, без наценки на premium.*

**Перед оплатой:** проверьте домен в корзине регистратора (RDAP может отставать на минуты).

---

## Рекомендация Chief Architect / Cursor

### 🥇 Выбор: `genesis-ai-engine.com`

**Почему:**

- Уже используете `genesis-ai-engine.vercel.app` — нулевой ребрендинг.
- `.com` — ~$10/год, не `.ai` (~$160 / 2 года).
- RDAP: свободен на момент проверки.
- Email: `hello@genesis-ai-engine.com` или `contact@genesis-ai-engine.com`.

**После покупки:**

1. Resend → Add domain `genesis-ai-engine.com` → DNS записи.
2. Railway: `GENESIS_EMAIL_FROM=Genesis <hello@genesis-ai-engine.com>`.
3. `public_launch.json`: `"contact_email": "hello@genesis-ai-engine.com"`.
4. (Позже) Vercel custom domain — **не блокер EL3**, можно после первого €.

---

## Если у CEO уже есть просроченный домен

**Вариант 1 (быстрейший):** напишите название → Cursor подготовит DNS/Resend под него → вы только продлите.

---

## Вариант 3 — временный unblock (компромисс)

Если домен покупаете через 2–3 дня:

```
Домен: домена нет (временно)
Email: ваш_рабочий@gmail.com
```

Снимает `legal=error` сейчас; outreach незнакомцам — после корпоративного `hello@`.

---

## CEO — 10 минут после выбора домена

| # | Действие | Где |
|---|----------|-----|
| 1 | Зарегистрировать домен (рекомендуем **Cloudflare Registrar** — at-cost .com) | cloudflare.com / namecheap.com |
| 2 | Resend → Domains → Add → скопировать DNS | resend.com |
| 3 | DNS у регистратора (SPF, DKIM, DMARC) | DNS panel |
| 4 | Railway variables + `/data/memory/public_launch.json` | Railway |
| 5 | Проверка: `/api/owner/public-launch` → legal ok | браузер |

Полная почта: `Corporate_Email_Mission1_Runbook.md`

---

## Horizon

`ceo@`, `partners@`, `invest@`, Communication Center — после EL3.

---

## Следующее действие CEO

**Одна строка:**

```
Выбираю: genesis-ai-engine.com
```

или

```
У меня домен: _________
```

или (временно)

```
Домен: нет · Email: _________
```

Cursor обновит `public_launch.json` и пришлёт точные значения для Railway.
