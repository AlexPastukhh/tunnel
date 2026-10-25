# Project Checker: рабочий Check в среде разработки

Срез 25.10.2026. Это V1-2 source/Docker workflow, не инструкция устанавливать доверенное приложение на Windows. Действующее направление — [PLAN](PLAN.md), граница — [WINDOWS_TRUST_BOUNDARY](WINDOWS_TRUST_BOUNDARY.md), результаты — [IMPLEMENTATION_LOG](IMPLEMENTATION_LOG.md).

## Подготовка профиля

GUI получает два явных пути: --registry для регистраций и --development-settings для тестовых инструментов/правил/состояния. Профиль — JSON-данные, а не подхват настроек из кандидата. Без development-профиля Check и редактор пакетов выключены. Update выключен всегда.

```json
{
  "schema_version": 1,
  "state_root": "/absolute/development/state",
  "policy_root": "/absolute/development/policies",
  "source_roots": ["/absolute/candidate/source"],
  "tools": [
    {
      "kind": "eslint",
      "executable": "/absolute/tools/node_modules/eslint/bin/eslint.js",
      "executable_sha256": "REPLACE_WITH_ACTUAL_SHA256",
      "config": "/absolute/tools/base-eslint.config.cjs",
      "config_sha256": "REPLACE_WITH_ACTUAL_SHA256",
      "node": "/absolute/tools/node"
    },
    {
      "kind": "semgrep",
      "executable": "/absolute/tools/semgrep-venv/bin/semgrep",
      "executable_sha256": "REPLACE_WITH_ACTUAL_SHA256",
      "config": "/absolute/tools/base-semgrep-rules.yaml",
      "config_sha256": "REPLACE_WITH_ACTUAL_SHA256",
      "node": null
    }
  ],
  "required_for_suffix": {
    ".js": ["eslint", "semgrep"],
    ".cjs": ["eslint", "semgrep"],
    ".mjs": ["eslint", "semgrep"],
    ".py": ["semgrep"]
  },
  "timeout_seconds": 120
}
```

Пути абсолютные, state/policies/tools отдельно от candidate source; target не может пересекаться с state/policies/app/tools. Иначе Check отклоняется до запуска, чтобы evidence не записывалось в дерево назначения. Пример содержит placeholders и не готов к запуску без фактических hashes. Base config pins проверяются как вход tool profile; фактические configs job создаёт из captured packs как JSON-данные. Полный closure анализаторов и native Windows окружение этим профилем НЕ подтверждаются. Поддержка прочих языков требует отдельного проверенного capability/fixture профиля; unknown file не пропадает из отчёта.

## Пользовательский путь

1. В «Правила» создать пакет: встроенные ESLint rules в JSON и локальные Semgrep rules в YAML/JSON. «Проверить и сохранить пакет» в фоне валидирует сам пакет и каждую отличающуюся композицию потребителей. До успеха старые bytes сохраняются; ошибки/конфликты/missing tools/timeouts блокируют запись.
2. В «Проекты» создать регистрацию: имя, pack IDs, файлы/папки/смешанный состав, необязательный target root и явные относительные mappings. Отмена не сохраняет полуготовый выбор. Для check-only target пустой.
3. Нажать «Проверить (тестовая среда)». GUI остаётся отзывчивым; доступны прогресс и отмена. Source читается как данные, не исполняется; Repo configs/plugins/npm scripts не загружаются, autofix нет. Job использует неизменённую captured policy.
4. Просмотреть findings с rule/file/line/column, вкладки покрытия файлов и действующих правил. Список loaded rule IDs не доказывает per-rule-per-file execution или смысловую полноту. Missing/unsupported/skipped/error не дают clear.
5. Evidence остаётся в state_root/jobs/JOB_ID/evidence: исходные engine JSON/stderr и report.json с registration, snapshot manifest, SHA-256, configs/tools/rules, coverage. Не класть такие реальные данные в Git или чат по умолчанию.
6. Повторить после перезапуска. Регистрация и последняя выбранная запись восстанавливаются; Check запускается отдельно заново. Старый отчёт не получает новых полномочий.

Прямая правка общего пакета действует сразу для всех привязок и инвалидирует их отчёты. Копия получает другой ID; link/unlink/«Только этот пакет» меняют привязки через сохраняемый реестр. Удалить используемый пакет нельзя: сперва нужно заменить/убрать привязки. Одновременно действует одна background-операция. Смена проекта при Check отменяет текущий job; stale callback не восстанавливает старый отчёт.

## Проверка и ограничения

Полный Python suite использует настоящие Docker ESLint 10.13.0/Semgrep CE 1.182.1 и PyYAML 6.0.3. devtools/gui_workflow_smoke.py отдельно проверяет реальные Tk widgets под виртуальным Xvfb: create/edit/copy/bind/delete, mixed registry/cancel, async Check/responsiveness, restart, finding locations и отмену. Chooser results/message boxes инъецированы; это не проверка native Windows chooser и не visual acceptance.

QA-only Debian packages загружены через apt --download-only и распакованы в /workspace/repo/project-checker-devtools/tk-qa/root без системной установки. Для relocatable Xvfb изменён только путь xkbcomp в отдельной QA-копии (/usr/bin → /tmp/xqa); системные binaries не менялись. Виртуальный сервер остановлен после теста. QA logs: tk-qa/gui-smoke.log, tk-qa/xvfb.log. Эта QA-обвязка не входит в будущий Windows release.

RunControl завершает POSIX process group вместе с дочерними процессами; отдельный тест проверяет настоящий spawned child. Windows Job Object source использует изолированный handshake перед CLI launch, но Windows cleanup/env/native compatibility ещё NOT_RUN. Пользователь выполняет Windows установку, ACL и consumer-проверки отдельно вручную.

После Check всегда NOT_AUTHORIZED либо findings/error/incomplete/unsupported; external Update недоступен. История проверки явно относится к snapshot, не обещает непрерывную актуальность live source. Перед будущим promotion обязательны независимая full-byte/source/policy/tool/target сверка, защищённый snapshot и exact owner confirmation. Timestamp-based late UI invalidation не является такой проверкой.
