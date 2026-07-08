# BLOCKER 7 — Production Security (API & Project Protection)

**Status:** Active gate before Public Launch  
**Automated check:** `python scripts/security_audit.py`  
**Cursor rule:** `.cursor/rules/genesis-production-security.mdc`

---

Перед Public Launch провести полный аудит безопасности. Genesis не должен раскрывать код, внутреннюю архитектуру или давать несанкционированный доступ к API.

> **Реалистичная цель:** не «невзламываемая» система — такой не существует. Цель — устойчивость к распространённым атакам и регулярная проверка.

## API Security

- Защитить все приватные API.
- Чётко разделить:
  - **Public API**
  - **Owner API**
  - **Internal API**
- Запретить прямой доступ к внутренним endpoint'ам извне.

## Authentication & Authorization

Проверить, что:

- Mission Control доступен только Owner.
- `/setup` доступен только Owner.
- Dev Mode только localhost или авторизованному Owner.
- Thinking Brief никогда не отдаётся пользователям.
- Workforce Reality никогда не отдаётся пользователям.
- Executive Trace никогда не отдаётся пользователям.
- Debug API полностью отключён в production.

## Secrets

Проверить, что невозможно получить через HTTP, ошибки сервера или статические файлы:

- API Keys · Workforce Keys · JWT Secrets · Session Secrets
- Genesis Memory · Owner Memory · Training datasets
- Configuration files · `.env` · `secrets/` · `memory/` · `logs/`

## Backend Protection

Проверить защиту от: SQL Injection · Command Injection · Path Traversal · Directory Listing · File Download Attack · XSS · CSRF (cookies) · SSRF · Prompt Injection · Rate Limit Bypass · Mass Requests (DoS) · Brute Force · API Enumeration

## Frontend Security

- Отсутствуют секреты в JavaScript bundle
- Dev Tools не раскрывают внутреннюю информацию
- Source Maps отключены в production
- Стек ошибок не показывается пользователю
- Внутренние названия модулей не раскрываются

## AI Security

Пользователь не должен заставить Genesis раскрыть: System Prompt · Thinking Brief · внутренние правила · API Keys · память других пользователей · Owner Memory · внутренние dev-команды · переключение Workforce. Genesis вежливо отказывает.

## Owner Isolation

Полностью изолировать память Owner от памяти пользователей. Публичный Genesis не знает: внутренние проекты · финансы · стратегию · разработки · планы Public Launch.

## Security Audit

Автоматическая проверка (`scripts/security_audit.py`):

- Broken Authentication · Broken Authorization · Secret Leakage
- Open Endpoints · Directory Traversal · Dependency Vulnerabilities
- Insecure Headers · CORS · CSP · Cookies · HTTPS Readiness · Docker Security

## Definition of Done

Не считать Production готовым, пока не выполнены:

- ✔ все публичные страницы работают (200)
- ✔ нет битых ссылок
- ✔ нет утечек секретов
- ✔ все приватные API защищены
- ✔ Owner полностью изолирован
- ✔ Debug полностью отключён
- ✔ Security Audit PASS
