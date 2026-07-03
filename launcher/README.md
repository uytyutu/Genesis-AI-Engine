# Genesis Launcher

Запуск Genesis **без терминала** — для владельца бизнеса.

## Быстрый старт

1. Дважды щёлкните **`launcher\StartGenesis.bat`**
2. В окне нажмите **🟢 Запустить Genesis**
3. Браузер откроется на http://localhost:3000

## Сборка .exe (один раз)

```powershell
cd D:\Games\Genesis-AI-Engine
.\launcher\build.ps1
.\launcher\install_shortcut.ps1
```

На рабочем столе появится ярлык **Genesis**.

## Что делает Launcher

- Проверяет Python и Node.js
- Устанавливает зависимости при первом запуске
- Запускает Backend и Frontend автоматически
- Показывает статус человеческим языком
- Кнопки: скачать Python / Node.js, журнал, настройки
- Мастер настройки при первом запуске

## Node.js

Без Node.js работает только Backend (API). Для панели управления установите Node.js 20+ — Launcher покажет кнопку **Скачать Node.js**.
