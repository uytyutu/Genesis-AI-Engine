# Factory Golden Demo Set

Эталонные генерации Path A (Basic) для регрессии до/после изменений Factory.

Ниши: dental · beauty · auto · restaurant · law

В каждой папке: `questionnaire.json`, `meta.json`, `index.html`, `delivery.zip`, `MANIFEST.json`.

Пересобрать:

```bash
py -3.12 scripts/generate_factory_golden_demos.py
```

Проверка регрессии:

```bash
py -3.12 -m pytest dashboard/backend/tests/test_factory_golden_demos.py -q
```
