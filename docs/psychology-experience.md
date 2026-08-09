# Psychology Experience — Digital Experience Profile

Не «ещё один шаблон». Доказательство Design DNA: опыт **под профессию** + эталон Virtus Core по качеству (не клон).

См. также: [`design-dna.md`](design-dna.md).

## Правила

| Не делать | Делать |
|-----------|--------|
| Белые пустые секции | Rhythm: ink / tint / glass / photo / gradient |
| Starter «как черновик» | Finished Hero + atmosphere даже на 199 € |
| Business слабее Virtus | Business ≥ Virtus quality floor |
| Premium = Business + padding | Premium WOW + DNA depth |
| Клон `/site` Virtus | Другие цвета, эмоция, композиция |

## Acceptance (без подписей)

1. За 3–5 с: дорого / профессия / не стыдно на любом тире  
2. Нет пустых секций; нет трёх светлых подряд  
3. Premium ≫ Business ≫ Starter  
4. Не выглядит как Virtus Core App Store  
5. `data-dna-style` и fingerprint присутствуют  

## Rebuild

```text
py -3.12 scripts/sync_public_package_previews.py --tiers basic,business,premium --folders psychology --websites-only
py -3.12 scripts/sync_public_package_previews.py --stores-only --store-tiers basic,business,premium --store-folders psychology
```

Смотреть: `http://127.0.0.1:3001/package-previews/...`
