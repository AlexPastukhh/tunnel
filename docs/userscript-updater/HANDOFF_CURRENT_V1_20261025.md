# Project Checker — действующий хендофф для нового чата

**Срез:** 25.10.2026. **Назначение:** самостоятельное продолжение разработки полной личной Windows V1 через **Fortis Repo**. Документ — рабочая точка входа, а не утверждение, что программа готова или установлена. Пользователь просил передать работу другому чату без потери исходного направления.

## 0. Что прочитать прежде, чем делать изменения

1. В Fortis Repo открыть /workspace/repos/tunnel/AGENTS.md; /workspace/repos/tunnel/README.md; /workspace/repos/tunnel/docs/README.md; /workspace/repos/tunnel/docs/CURRENT_STATE.md; инструкции по разрешениям и Git.
2. Читать **текущий** docs/userscript-updater/PLAN.md целиком: это основной рабочий маршрут V1-1 → V1-4.
3. Читать docs/userscript-updater/CANDIDATE_PREWORK_V4_READING_COPY.md: **полная сохранённая reading copy CPW-PC-20261025/v4/A4**, секции 1–14. Особенно 10–12, 14.1–14.10. Эта копия исторически **Candidate / Not canonical / НЕ BASELINE COMMITTED**. Нельзя незаметно объявить все предложения официально принятым baseline.
4. Читать docs/userscript-updater/IMPLEMENTATION_LOG.md (последние факты), docs/userscript-updater/WINDOWS_TRUST_BOUNDARY.md (условия независимой установки), runtime/userscript-updater/README.md (запуск тестов), docs/userscript-updater/REQUIREMENTS.md (legacy userscript-specific требования).
5. docs/userscript-updater/HANDOFF.md и PLAN_LEGACY_USERSCRIPTS_20261025.md — **история узкого кейса**, не текущий план и не приказ начинать с Notifier/Helper. Эти проекты — необязательные поздние потребители.

Все файлы в относительных ссылках находятся в /workspace/repos/tunnel. Другой чат не обязан видеть прежнее вложение или эту переписку; достаточно Fortis Repo и указанного набора файлов.

## 1. Полномочия и подтверждённые пользовательские решения

**Разрешено:** разрабатывать, исправлять, добавлять необходимые зависимости, собирать и тестировать **внутри Fortis Repo / Docker**, вести относящиеся к этой задаче документы и локальные Git-коммиты после проверки индекса. Пользователь явно разрешил такую работу, затем попросил продолжать и принял перестройку порядка для личной V1. Нет нужды повторно спрашивать разрешение на очередную обычную Docker-разработку и нет основания возвращаться в режим «только pre-work» из старого A4.

**Не разрешено автоматически:** устанавливать/запускать доверенную программу на Windows, менять host ACL/mounts/Junction, Tampermonkey Loader/профили/GM secrets, реальные user-consumed внешние копии, выполнять отправки от лица владельца, stage/commit чужие файлы, push или развёртывание на других проектах. Windows install и проверка независимости — **ручной этап владельца** после подготовки reviewed package.

Уже решены F-U-01, F-U-02, F-U-03, F-U-04 и F-U-05; заново не спрашивать:
- Программа **полная личная V1**, не demo/MVP и не универсальный OS блокиратор всех запусков.
- Проверка файлов без назначения возможна (check-only), дополнительно контролируемое обновление внешней копии.
- Пакет правил редактируется **на месте**, общие изменения сразу относятся ко всем проектам-потребителям; для других правил владелец **копирует** пакет.
- Один файл/много файлов/папка/смешанный набор с явными source→target mappings.
- Перед обновлением показывать **все последствия** относительно реального target: create, modify, delete, unchanged, сохранённые чужие файлы/данные, diff или old/new hashes и размеры. Исчезновение ранее управляемого source может предложить удаление target **только после просмотра и подтверждения**.
- Две раздельные кнопки: «Проверить» **не обновляет**, «Обновить» доступно только после подтверждённого актуального допуска. Автоматического переноса после ESLint/Semgrep exit0 нет.

Рабочий план V1 **не урезает состав A4**, меняет только порядок для одного пользователя: сначала реальный Check GUI, потом checked-byte promotion, при параллельной подготовке Windows acceptance.

## 2. Где работать и что сейчас реально есть

**Основной Repo:** /workspace/repos/tunnel. **Исходники Project Checker:** /workspace/repos/tunnel/runtime/userscript-updater/. Python 3.11, Tkinter **не установлен в Repo Docker** (нельзя заявлять visual Windows GUI PASS). Источник/код на Docker RW /workspace/repos — **недоверенный**; /workspace/repo — отдельный Docker volume, **тоже agent-writeable**. В этой среде tests/devtools лежат по абсолютным путям ниже, но другой контейнер может отличаться.

Компоненты:
- checker/model.py — регистрация, Selection (file/directory), check-only, optional target_root;
- checker/inventory.py — инвентаризация/снимок/хеши, прототип Linux, НЕ доказанные native Windows handles;
- checker/policies.py — schema, shared mutable pack capture/edit/copy; структурная schema; отдельный policy_validation.py проверяет фактические engine configs;
- checker/engines.py и reports.py — Docker-only CLI и JSON adapters, структурный результат **не даёт owner PASS**;
- checker/coverage.py — пофайловое покрытие, требуемые engines/unsupported;
- checker/preview.py — **read-only** план целевого дерева, manifest и fingerprint;
- checker/review.py — immutable job/project/snapshot/policy/tool/target/managed-set binding; checker/policy_validation.py — real effective-config compilation/validation, deterministic shared-pack composition;
- checker/ui_model.py и gui.py — state и исходник Tkinter, обе кнопки Check/Update отключены; checker/registry.py и registration_editor.py — versioned JSON persistence/last selection и file/files/folder/mixed chooser/editor; --registry включает сохранение; corrupt config не заменяется пустым;
- checker/windows_layout.py — только проверка строк путей; без реального Windows ACL/reparse evidence;
- devtools/fixture_transactions.py — **отдельная СИНТЕТИЧЕСКАЯ лаборатория записи/backup/journal/rollback**. Не импортировать как trusted updater;
- tests/ — синтетические отрицательные и реальные CLI fixture tests;
- policies/demo/ — небезопасные demo-конфиги для fixtures, не installed owner policies.

**Текущий агрегированный результат scanner reports — NOT_AUTHORIZED**, даже если один CLI возвращает structural clear. Ни JSON анализатора, ни sandbox fixture не разрешают owner target writes.

**Фактическая проверка этого хендоффа:** заново запущено 123/123 Python unittest с обоими настоящими CLI (ESLint 10.13.0; Semgrep CE 1.182.1) в Docker: PASS без skips. Проверка GUI-модели печатает PROMOTION DISABLED. Нет теста Windows/Tkinter rendering, host boundary/ACL, настоящего owner target или installed source→PASS→approved chain.

Для воспроизведения в текущем Docker:
~~~bash
cd /workspace/repos/tunnel/runtime/userscript-updater
UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js \
UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs \
UPDATER_DEV_SEMGREP=/workspace/repo/project-checker-devtools/semgrep-venv/bin/semgrep \
UPDATER_DEV_SEMGREP_CONFIG=/workspace/repo/project-checker-devtools/semgrep-rules.yaml \
PYTHONDONTWRITEBYTECODE=1 /workspace/repo/project-checker-devtools/semgrep-venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m checker.gui --model-smoke
~~~
При переносе в новый контейнер сначала проверять наличие версий/исполняемых файлов и demo configs; отсутствие = NO TEST, не скрытый skip-as-PASS. Не гонять анализаторы по личным скриптам, пока нет согласованных защищённых правил.

**История коммитов по checker:** initial 24b5234; hardening af816d0; real Semgrep 1e098a1; preview d231451; lab 7f6e11c; view-only UI 4a832b8; план личной V1 144db14. Текущий HEAD может быть более новым из-за **параллельной работы других агентов**: ни один из этих хешей не является требованием откатывать HEAD.

## 3. V1-1 завершён в исходниках и Docker

Три известных дефекта исправлены и покрыты регрессиями. ReviewPresenter принимает только preview/scan с активным ReviewBinding выбранного проекта: registration hash, snapshot ID/manifest, captured policy, tool references, target/managed set и уникальный job ID. Edit/cancel/new job/shared-pack edit инвалидируют контекст. Чужой preview с тем же target отвергается. В preview GUI видны old/new hashes и **размеры в байтах**, включая 0 и отсутствующие файлы.

PolicyPack.validate остаётся schema-проверкой. Отдельный policy_validation.py загружает действующий ESLint config в настоящем API, проверяет core IDs/включённые required rules на JS/CJS/MJS; Semgrep CE реально компилирует правила на безопасных JS/Python и сверяет loaded IDs/coverage. Invalid YAML/patterns/duplicates/skips/disabled required/missing tools/timeouts → ERROR. run_dev_engine отказывает до project scan при невалидном config. Составление shared packs выявляет конфликты, без last-write-wins.

Зависимость PyYAML 6.0.3 установлена только в Docker venv; tests запускать указанным venv Python. VALIDATED_DEVELOPMENT не доказывает semantic effectiveness, full project coverage или owner PASS. Другие языки требуют отдельного fixture/capability профиля и пока дают явный отказ. Полный dependency closure и native Windows gates ещё не выполнены.

## 4. Точный следующий исполнительный шаг: V1-2

1. Проверить Git/index; сохранять чужую работу, особенно docs/agent-workflow, launcher, Observatory, Notifier/Helper. Не откатывать HEAD к старому срезу.
2. Persistence/last selection и picker/editor уже реализованы в source: 123/123 Docker tests. Native visual QA остаётся NOT_RUN. Следом реализовать shared-pack editor/copy/bind/rebind с реальной валидацией до сохранения; затем Check worker.
3. Подключить shared policy edit/copy/bind/rebind и effective validation, затем real Check worker с progress/cancel/timeout и stale callback protection.
4. Показать per-file/per-rule coverage/findings и source/policy/tool fingerprints. Сохранить aggregate NOT_AUTHORIZED до Windows host acceptance.
5. Обновлять plan/log/docs после значимых результатов и делать scoped local commits. Windows install/ACL/Loader/реальные внешние copies вручную выполняет владелец.

V1-1 DONE относится только к Docker/source. Не включать «Обновить» и не заявлять HOST_BOUNDARY_VERIFIED.

## 5. Дальнейшая последовательность и release gates

- **V1-2**: полный повторяемый check-only GUI: persistent versioned JSON registrations, source/target pickers, file/many/dir/mixed, shared policy edit/clone/bind/rebind и invalidation, effective configs, real CLI worker, progress/cancel/timeout, per-file+per-rule reports, source/policy fingerprint. Проверить save→restart→check→report и два проекта с общими правилами. До host acceptance report носит development-only статус.
- **V1-3**: exact source→scan→review→owner confirmation→promotion в доверенной цепочке; full actual target preview, managed deletes/preserved extras, staged bytes, backup/journal/recovery. Folder/mixed и explicit data/dependency/lock handling; не заимствовать devtools fixture lab как production writer.
- **V1-4**: готовый пакет и manifest/hashes/полная dependency closure, **ручная owner Windows install**, native final-path/ACL/agent-write-route negative probes, настоящие CLI/GUI tests, безопасный один файл и папка/mixed, consumer/Loader QA. Только подтверждённая отдельная установка/QA даёт OWNER_ACCEPTED.

**Параллельно:** можно готовить host verification scripts/templates и binary/deps closure ещё во время V1-2; Windows вручную делает владелец, никакого auto-apply из Repo. PR-08 (ранняя host validation) не является приказом урезать V1 до демо.

## 6. Что сохранить при завершении нового чата

- Обновить docs/userscript-updater/PLAN.md (точный gate/status), IMPLEMENTATION_LOG.md (что было действительно запущено, platform/results), README.md, HANDOFF_CURRENT_V1_20261025.md при изменении следующих шагов; синхронизировать docs/CURRENT_STATE.md и docs/INSTRUCTIONS.md по AGENTS.
- Раздельно отмечать source/DOCKER_TESTED и реальный WINDOWS_GUI_TESTED/HOST_BOUNDARY_VERIFIED/OWNER_ACCEPTED. Никогда не называть синтетические tests доказательством защищённой Windows среды.
- Не загружать секреты и не создавать/обновлять реальные внешние копии, пока owner-run native gate не завершён.
- Git status/index перед commit; не touch/commit чужие dirty files, no push без поручения. Чистое дерево после чужой работы нельзя предполагать.

## 7. Короткая команда новому чату

> Продолжай Project Checker через подключённый Fortis Repo. Прочитай AGENTS.md, docs/userscript-updater/HANDOFF_CURRENT_V1_20261025.md, актуальный PLAN.md, источник CANDIDATE_PREWORK_V4_READING_COPY.md и журнал; затем проверь live Git/status и текущие Docker tests. Пользователь разрешил разработку и установку зависимостей в Repo; Windows install/ACL/Loader/Approved target выполняются отдельно вручную владельцем. Не спрашивай снова F-U-01–F-U-05, не сокращай полный scope A4, но оптимизируй порядок под личную V1. V1-1 исправлен; V1-2 persistence/pickers source добавлены (123/123). Продолжай V1-2: shared packs и реальный Check worker, затем обнови docs и сделай scoped local commit. Не включай update/owner PASS и не трогай другие workstreams.
