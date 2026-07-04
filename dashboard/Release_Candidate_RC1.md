# Mission: Release Candidate (RC1)

**Статус:** ✅ **PASSED** (production re-audit 2026-07-04) → `Release_Audit_RC1_Production.md`  
**Цель:** Genesis готов показать **первому незнакомому клиенту** без стыда после Gewerbe + Stripe Live.

**Foundation / Horizon:** без изменений. Executive, Marketplace, Digital Employees — 🔒.

---

## Фильтр задач

Каждая задача отвечает **да** хотя бы на один вопрос:

1. Понятнее?
2. Красивее?
3. Быстрее?
4. Надёжнее?
5. Выше шанс первого клиента?

Иначе → Horizon.

---

## 🟥 Priority A — Release Quality

| Область | Задача | Статус |
|---------|--------|--------|
| **Site** | Все публичные страницы без MC-nav | ✅ |
| **Site** | Мобильная / планшет | 🔄 audit |
| **Site** | Тёмная тема (единый стиль) | ✅ базово |
| **Site** | SEO meta, OG | ✅ |
| **Site** | favicon | ✅ |
| **Site** | robots.txt, sitemap.xml | ✅ |
| **Site** | 404 / 500 | ✅ |
| **Order** | Header, шаги, валидация, итог | ✅ |
| **Email** | HTML receipt + заказ получен | ✅ |
| **Trust** | Impressum, Datenschutz, AGB, FAQ, Kontakt | ✅ |
| **Design** | Logo, footer, кнопки, skeleton | ✅ базово |

## 🟨 Priority B — Product Polish

UI kit, design tokens, transitions — после A.

## 🟨 Priority C — Code Quality

Дубли, мусор, безопасность — после A.

## 🟨 Priority D — Release Audit

- [x] Автоматическая проверка production URL + API
- [x] Отчёт `dashboard/Release_Audit_RC1.md`
- [x] Demo Mode (путь клиента)
- [x] Исправления H1–H4 в коде
- [ ] Re-audit после deploy
- [ ] Ручной mobile/tablet pass

---

## ❌ Не сейчас

Marketplace · Digital Employees · Android · Windows · Multi-Agent · Executive Dashboard · новые большие модули

---

## Gate (CEO)

```
Kit OK ✅ → Gewerbe ⏳ → Stripe Live ⏳ → Outreach 25 → EL3
```

RC1 **не заменяет** gate — готовит продукт к моменту outreach.
