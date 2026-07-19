# Research 3D — как открыть Scene Engine

НЕ открывайте scene_engine.html двойным кликом (file://) — браузер блокирует модули.

Из корня репозитория:

  py -3.12 scripts/open_research_3d.py

Скрипт поднимет http://127.0.0.1:8765 и откроет браузер.
Страница: http://127.0.0.1:8765/runtime/scene_engine.html

Если порт занят — просто откройте этот URL вручную.

Перегенерация 50 примеров:
  py -3.12 scripts/generate_research_3d_presets.py

3d_premium в checkout = WAITLIST (Path A не тронут).
