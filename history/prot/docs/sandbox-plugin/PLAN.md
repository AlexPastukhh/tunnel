# Sandbox plugin — documentation and implementation plan

Статус: planning.

Подробная техническая основа: [../../SANDBOX-GUI-PLAN.md](../../SANDBOX-GUI-PLAN.md)

## Phase 0 — verify platform

- проверить Windows Sandbox feature;
- заново проверить актуальную документацию выбранного automation mechanism;
- подтвердить реальные ограничения focus/input/screenshot;
- не менять рабочий tunnel во время эксперимента.

## Phase 1 — isolated prototype

- Sandbox без sensitive host mappings;
- screenshot;
- открыть простое приложение;
- UI inspection;
- text input/click только внутри guest;
- проверить влияние на основной desktop пользователя.

## Phase 2 — restricted broker

- отдельный capability surface;
- никаких arbitrary host shell operations;
- sandbox.start/stop/run;
- sandbox.inspect/invoke/set_value;
- sandbox.send_keys/click;
- sandbox.screenshot/record;
- controlled folder sharing только через локальное подтверждение.

## Phase 3 — security acceptance

Проверить:
- plugin не может screenshot/click/type на HOST desktop;
- runtime key не доступен guest;
- host paths не видны без explicit mapping;
- writable mapping рассматривается как реальный host write access;
- закрытие/restart корректно отзывает session capability;
- observability видит Sandbox session, но не расширяет её полномочия.

## Phase 4 — documentation

Когда prototype стабилен, заполнить:
- ARCHITECTURE.md;
- CAPABILITIES.md;
- SECURITY.md;
- OPERATIONS.md;
- TESTING.md;
- RUNBOOKS/.

## Exit criterion

Production подключение возможно только после независимой проверки isolation boundary и отдельного решения о том, как Sandbox plugin сосуществует с HOST Maintenance connector.