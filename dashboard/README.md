# Command Center

**Genesis ABOS — панель управления для владельца** (не для программиста).

## Запуск (рекомендуется)

**Дважды щёлкните ярлык «Genesis» на рабочем столе** или `launcher\StartGenesis.bat`.

В окне Launcher нажмите **🟢 Запустить Genesis** — всё остальное автоматически.

- Панель: http://localhost:3000
- API: http://localhost:8000/docs

Подробнее: `launcher/README.md`

## Node.js

Для панели управления нужен **Node.js 20+**. Если не установлен — Launcher покажет кнопку **Скачать Node.js**.

## Ручной запуск (для разработки)

### Backend

```powershell
cd D:\Games\Genesis-AI-Engine\dashboard\backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd D:\Games\Genesis-AI-Engine\dashboard\frontend
npm install
npm run dev
```

## Factory

**Не начат.** Сначала пройдите Owner Acceptance в браузере.
