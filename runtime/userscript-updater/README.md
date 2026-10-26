# Project Checker — Windows working copy and independent installation

Current route: [personal V1 plan](../../docs/userscript-updater/PLAN.md), [current handoff](../../docs/userscript-updater/HANDOFF_CURRENT_V1_20261025.md), [implementation evidence](../../docs/userscript-updater/IMPLEMENTATION_LOG.md). Full A4 scope remains. Source/Docker checks never grant owner PASS or external update authority.

## Working development Check workflow

- Persisted schema-versioned JSON registry: Unicode, last selection, file/files/folder/mixed, explicit relative mappings and check-only. Atomic save, corrupt-file preservation and concurrent editor refusal.
- Tk registration editor/pickers and shared policy editor: create, direct edit, independent copy, link/unlink/rebind. Invalid effective configuration preserves the old pack. A successful shared edit invalidates every consumer report. Used packs must be unbound before deletion.
- Actual ESLint/Semgrep config validation: built-in/enabled rule IDs, real compile/load, safe fixtures, duplicate/conflicting/disabled/missing rules and language coverage failures.
- Explicit development-profile Check button: background snapshot -> captured effective policy -> real pinned CLI -> file/rule findings -> fresh source/policy/tool comparison -> local report. Target/state/policy/app/tool intersections are refused before Check starts, so evidence cannot alter a registered target tree. The Docker development GUI requires an explicit profile; the Windows working launcher prepares its own profile. **Development profiles cannot enable Update.**
- Progress, bounded job/analyzer timeout, cancel and child-tree cleanup; stale callbacks and double-starts refused. POSIX cleanup has actual child-process tests. Windows Job Object containment source has NOT been native-tested.
- File findings include original source names, rule IDs and line/column. File coverage distinguishes clean files, findings, missing engines and unsupported material. Loaded-rule lists are separate and do not pretend to prove every rule ran on every file.
- Raw CLI JSON/stderr, snapshot manifest, hashes and structured report are saved only in job-owned development state. They are historical evidence, not transferable authorization.
- Read-only target preview: full create/modify/delete/unchanged/preserve, text diff, binary sizes/hashes, bound project/registration/snapshot/policy/tool/target/managed set and job identity. Confirmation/apply/result/history/inverse-preview/recovery run through background workers.
  The Windows working context supplies a registered-target functional writer; independent owner acceptance uses a separate installed context.
- Windows structural path preflight always requires separate native final-path/ACL/route verification.

V1-3 includes managed ownership, staged checked bytes, journal/readback, exact
one-shot consent and reviewed rollback/conflict recovery.
[Promotion contract](../../docs/userscript-updater/PROMOTION_CORE.md).

Selections declare code/dependency/resource/data and exact directory-relative
exclusions. Empty source directories are inventoried and created; missing selected
files/folders become visible deletion candidates only for prior managed paths.
Unavailable source roots and access errors remain errors. Resource bytes are
hashed but never reported as analyzed code; unsupported code blocks updating.

WindowsIO/InstalledAuthority/WindowsTarget are **source candidates, WINDOWS_NOT_RUN**.
The development GUI has no native authority. Offline package contents, side-by-side
installer, native probes, owner-operated GUI fixture and elevated acceptance/rollback
are in [release/WINDOWS_ACCEPTANCE.md](release/WINDOWS_ACCEPTANCE.md). The normal
launcher uses isolated Python/explicit ._pth, protected complete closure/receipts,
normal owner identity, native ACL/final-path checks and approved roots.

Exact executed tests, failures/fixes and package receipt belong only to the
[implementation log](../../docs/userscript-updater/IMPLEMENTATION_LOG.md).
Neither Docker tests nor ZIP hashes are Windows acceptance. The old devtools
transaction lab is not imported or installed as a writer.

## Запуск рабочей копии в Windows

Checker запускается процессом Windows из обычной папки репозитория. Docker
используется для разработки; отдельного Docker backend/transport нет.

Из корня Windows-репозитория один раз выполните в **обычном PowerShell**:

```powershell
Set-Location .\runtime\userscript-updater
py -3 -m checker.gui --prepare-source-runtime --registry "$env:LOCALAPPDATA\ProjectChecker-Test\projects.json"
```

Это явная ручная подготовка владельцем: проверенный offline ZIP из .artifacts
используется только как источник зависимостей. Создаются отдельный Python 3.13
с Tk, Windows Semgrep/PyYAML и Node/ESLint в новой версии каталога
%LOCALAPPDATA%\ProjectChecker-Test\runtimes. Выполняются offline pip с hashes,
npm ci с integrity и реальные проверки конфигураций на безопасных JS/Python.
Инсталлятор Python проверяется через Authenticode. Права ACL не меняются.
При ошибке прежний готовый runtime/реестр не заменяется; путь незавершённой
версии виден в выводе подготовки. Не удаляйте существующий реестр для повтора.

Если зависимости уже установлены и сбой произошёл на финальной проверке
после появления source-profile.json, продолжите её без переустановки. Укажите
существующий каталог из строки Preparing runtime (замените ID):

```powershell
py -3 -m checker.gui --resume-source-runtime "$env:LOCALAPPDATA\ProjectChecker-Test\runtimes\ID" --registry "$env:LOCALAPPDATA\ProjectChecker-Test\projects.json"
```

Resume проверяет принадлежность профиля этому каталогу/реестру, сохранённые
хеши tool/config и isolated Python paths; затем повторяет реальную валидацию
и только при успехе сохраняет указатель готового runtime. Install/pip/npm
повторно не запускаются; profile/registry/policies не перезаписываются.
При повторном FAIL прежний ready pointer сохраняется.

Во время финальной проверки выводятся фазы ESLint/Semgrep START/COMPLETE.
Проверяется явный Python CLI Semgrep (--legacy), с одним worker; все файлы/правила
по-прежнему обязательны. Deadline не увеличен: 30 секунд на команду, 180 на
подготовку конфигураций. Последний результат сохраняется в
%LOCALAPPDATA%\ProjectChecker-Test\state\setup-validation-report.json
(для собственного --registry используется его соседний state).

После owner-диагностики Windows Semgrep был обнаружен отказ нативного OCaml
`socketpair` ещё до анализа: прежний TEMP/TMP указывал на глубокий каталог
`setup-validation-*/effective/checker-policy-*`; AF_UNIX socket path имеет
ограничение 108 байт. Для каждого CLI теперь создаётся отдельный приватный
временный каталог непосредственно внутри `state_root`; только его дочерний
process environment получает TEMP/TMP/TMPDIR. Длина самого временного пути
проверяется по UTF-8 (не символам): более 80 байт — явный отказ до запуска
анализатора, без fallback на глобальный TEMP. Scratch удаляется после команды,
включая deadline/cancel cleanup; source, target и app не перемещаются.
Это исправление в исходниках не является подтверждённым Windows PASS.

После первого повтора с коротким TEMP владелец снова получил 30-секундный
Semgrep deadline, без stdout/stderr и без прежней ошибки socketpair. Причина
нового зависания не установлена. Для следующего повторного resume добавлена
узкая диагностика безопасных config fixtures: `parent_phase` и
`phase_markers` в JSON показывают запуск управляющего процесса, передачу
команды и начало Python CLI Semgrep. Они не означают успешный анализ и не
содержат source/argv/environment. При новом FAIL передайте весь отчёт,
особенно эти два поля; прежний runtime, зависимости и реестр сохраняются.

Если Resume снова завершился ERROR/тайм-аутом, покажите этот отчёт:

```powershell
Get-Content "$env:LOCALAPPDATA\ProjectChecker-Test\state\setup-validation-report.json" -Raw -Encoding UTF8
```

Отчёт содержит фазу, время, ошибку и ограниченные хвосты stdout/stderr безопасной
проверки. Он не является owner acceptance receipt. При тайм-ауте готовность
runtime не публикуется; длительность не заменяет реальную проверку.

Обычный запуск из той же папки:

```powershell
py -3 -m checker.gui --registry "$env:LOCALAPPDATA\ProjectChecker-Test\projects.json"
```

Launcher сам запускает подготовленный isolated Python с текущими исходниками
из рабочей папки. Запуск после изменения кода берёт этот код без переустановки
зависимостей. До подготовки GUI показывает каталог и точную команду, а Check
остаётся отключён. Tk установленного системного Python не обязателен после
подготовки. Если папку приложения переместили, подготовьте runtime для нового
пути. Архив зависимостей и его frozen receipt не перезаписываются этим процессом.

starter добавляется только при отсутствии; пользовательские правки пакетов
и регистраций сохраняются. Доступные ID и названия видны в редакторе проекта.
После Check выберите полный просмотр (или явный первый импорт existing files),
проверьте строки/diff/размеры и отдельно подтвердите «Обновить».
Файлы меняются только внутри сохранённого target. Есть журнал и просмотр
отката/восстановления. Check-only не требует target.

Первый проход делайте на отдельном небольшом примере JS/Python с отдельным
пустым назначением. starter проверяет JS/Python на dynamic eval/exec; это не
универсальная политика всех языков. При выборе всего tunnel неизвестные типы,
dependencies, .git, archives и явно не исключённые материалы остаются в scope:
unsupported/coverage/size ошибки блокируют перенос, не превращаются в PASS.
Не добавляются скрытые исключения.

Режим помечен WINDOWS_WORKING_COPY_TEST. Защищённая независимая установка,
проверка agent write routes и OWNER_ACCEPTED остаются отдельным поздним шагом
по [процедуре](release/WINDOWS_ACCEPTANCE.md). Docker тесты не доказывают
совместимость Windows installer/Win32/Job Object/native chooser.

## Run in the authorized Docker environment

Python 3.11 + pinned PyYAML 6.0.3 from requirements.txt. Existing tools: ESLint 10.13.0 and Semgrep CE 1.182.1 under /workspace/repo/project-checker-devtools. Use the existing venv Python, which includes PyYAML:

```bash
cd /workspace/repos/tunnel/runtime/userscript-updater
export UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js
export UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs
export UPDATER_DEV_SEMGREP=/workspace/repo/project-checker-devtools/semgrep-venv/bin/semgrep
export UPDATER_DEV_SEMGREP_CONFIG=/workspace/repo/project-checker-devtools/semgrep-rules.yaml
PYTHONDONTWRITEBYTECODE=1 /workspace/repo/project-checker-devtools/semgrep-venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m checker.gui --model-smoke
```

[Development profile format and UI workflow](../../docs/userscript-updater/DEVELOPMENT_CHECK_WORKFLOW.md). With Tk and an appropriate test display:

```bash
python -m checker.gui --registry /absolute/path/projects.json --development-settings /absolute/path/development.json
```

On Linux, omitting --registry uses an explicitly labelled in-memory session; omitting --development-settings disables scanner and policy-edit actions. A corrupt registry/profile is reported, not silently replaced. An interrupted-save .lock requires review.

Baseline Docker Python still has no Tk. The existing isolated QA-only Debian
Tk/Xvfb tree runs devtools/gui_workflow_smoke.py with real CLIs and widgets.
Chooser/message-box results are injected; Windows dialogs/rendering and native
writes require the separate owner-run probes. No system/Windows installation
was performed by the agent.

## Build the offline candidate inside Docker

release/build_bundle.py requires the complete pinned Windows wheelhouse,
download receipts for the official Python installer and Node archive, plus
the installed ESLint npm closure/package-lock. It verifies wheel pins/internal
RECORDs, exact lock completeness, archive paths and binary hashes. It copies
checker into the application import path; QA fixture writers remain separate.
See the implementation log for the current local bundle/summary paths.

The owner manually installs a reviewed candidate outside all agent write routes
and executes the prepared native/GUI/marker probes before accepting it.
[Windows boundary](../../docs/userscript-updater/WINDOWS_TRUST_BOUNDARY.md).
Current capability/scale/metadata/root limitations are explicit in the release
procedure; no silent skip or global atomicity claim is made.
