# Fortis Repo 1/2: переход на runtime v0.0.21

Этот runbook описывает общий Windows runtime двух независимых профилей.
Канонические версия, upstream commit, URL архива и два SHA-256 находятся в
[`FortisContainerPolicy.ps1`](../runtime/windows-repo/current/launchers/shared/FortisContainerPolicy.ps1).
Git-коммит, установка EXE, переключение процесса и проверка MCP — отдельные этапы.

## Причина исправления

В инциденте Repo 1 16.11.2026, 02:41 UTC+07:00, MCP успешно вернул результат,
его отправка в control plane завершилась `unexpected EOF`, затем завершилась
stdio-команда и runtime остановил туннель. Polling перед остановкой уже восстановился.
Это отдельный инцидент после прежней ошибки `401 token_invalidated`.

В изолированном стенде официальный narrow runtime v0.0.15 воспроизвёл тот же
механизм: неполный HTTP-ответ на POST результата вызвал закрытие общего stdio
и остановку всего runtime. На v0.0.21 та же инъекция сохраняет stdio;
следующий вызов проходит. Счётчик синтетического инструмента подтверждает
однократное исполнение, хотя отправка одного ответа выполнялась трижды.

Стенд использует loopback HTTP и безвредный MCP. Он проверяет обработку
ошибки транспорта, но не устанавливает причину первоначального разрыва TLS
в реальной сети. Совпадение версий двух Repo не означает совпадение их
HTTP-соединений или момента отправки ответа.

## Контракт запуска и диагностики

Оба launcher вызывают `Invoke-FortisRepoRuntime` из общей policy. Только
проверенный hash EXE допускается к запуску. CLI явно задаёт
`--mcp.stdio-failure-policy=restart`, JSON/debug-лог, запрет raw HTTP и
health listener `127.0.0.1:0`. Docker exec остаётся привязан к проверенному
полному Container ID. Конфигурация контейнера и фильтр MCP logging notifications
этим обновлением не меняются.

| Repo | Каталог диагностических файлов |
| --- | --- |
| Repo 1 | `C:\Users\alexa\chatgpt-repo-mode` |
| Repo 2 | `%LOCALAPPDATA%\FortisRepoPlus2` |

Каждый запуск печатает `RunId=` и `RuntimeLog=`. Stdout/stderr одновременно
поступают в Control Center и `runtime-diag-<RunId>.jsonl`; файл создаётся
без перезаписи и сбрасывается после каждой строки. Отдельный
`runtime-pid-<RunId>.txt` создаёт сам runtime. Обёртка записывает Repo,
версию, путь, hash, launcher PID, наблюдённый runtime PID и код выхода.
При принудительном Stop завершающая строка может отсутствовать; событие
остановки и результат процесса также проверяются в Control Center.

`restart` восстанавливает неожиданно потерянный дочерний MCP-процесс.
Он не восстанавливает потерянный результат уже выполненной команды.
Legacy caller после замены дочернего процесса должен повторить MCP
инициализацию; до неё runtime отклоняет legacy-вызов. Уже начатые команды
автоматически не переигрываются. При неопределённом результате мутации
сначала проверить её фактический эффект.

В одной точке времени допускается только один runtime на один Tunnel ID.
Раздельные Repo 1 и Repo 2 сохраняют свои профили, ключи и аккаунты.

## Проверки исходников и артефактов

Из корня `tunnel`:

```bash
python3 -B runtime/windows-repo/test_release_contract.py
python3 -B runtime/windows-repo/test_shared_policy_contract.py
python3 -B runtime/broker/test_worker.py
pwsh -NoLogo -NoProfile -File runtime/windows-repo/test_fortis_container_policy.ps1
pwsh -NoLogo -NoProfile -File runtime/windows-repo/test_runtime_install.ps1
```

В текущем Docker для двух PowerShell-тестов используется установленный
`/workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh` с
`DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1`. Это ограничение тестовой Linux-среды.
Проверка Windows ACL и production owner SID выполняется только в Windows.
Offline-тест изменяет ACL исключительно своего временного fixture-каталога;
production installer ACL не меняет.

Воспроизводимый транспортный тест с реальными upstream-бинарниками:

```bash
python3 -B runtime/windows-repo/prepare_test_runtimes.py --platform linux-amd64 --directory /tmp/fortis-runtime-fixtures-NEW
python3 -B runtime/windows-repo/test_runtime_resilience.py --runtime /tmp/fortis-runtime-fixtures-NEW/v0.0.15/tunnel-client-runtime --expect-old-failure
python3 -B runtime/windows-repo/test_runtime_resilience.py --runtime /tmp/fortis-runtime-fixtures-NEW/v0.0.21/tunnel-client-runtime
```

Каталог fixtures должен быть новым. Download helper проверяет отдельно ZIP и
извлечённый бинарник; в Windows CI используется `windows-amd64` и EXE.
Стенд не читает реальные credentials/profiles, не обращается к рабочему
control plane и не запускает Docker. Дочерний процесс и счётчик синтетические.
`401/403` вводятся на один poll, затем стенд восстанавливает корректный ответ:
этот тест не означает автоматического исправления недействительного ключа.

В Windows CI проверяются PowerShell 5.1, guard matrix, доверие к архиву/EXE,
негативные ACL/reparse fixtures, версия/flavor EXE, воспроизведение старой
ошибки и исправленное поведение. Отдельный Source CI Script Center собирает
WinForms в STA без запуска GUI и workers. Все результаты относятся к
точному SHA, проверенному соответствующим GitHub run. CI не заменяет
Preview действующей установки и проверку каждого аккаунта.

## Установка EXE до обновления source pins

Новый EXE устанавливается рядом с v0.0.15. Установщик
[`Install-FortisRuntime.ps1`](../runtime/windows-repo/Install-FortisRuntime.ps1)
не запускает workers, не меняет профили/ключи/ACL и не управляет Docker.
Он требует исходного owner и обычный, не elevated Windows PowerShell,
проверяет доверие к существующим родительским каталогам, отсутствие reparse
points, обе суммы и PE amd64. Присутствующий правильный EXE даёт
`FORTIS_RUNTIME_ALREADY_INSTALLED_HASH_PASS`; несовпадающий не перезаписывается.

### Совместимость с действующей ACL общего runtime

Owner readback обнаружил существующие `Authenticated Users: Modify` и отдельный
запрет SID `S-1-5-21-303538662-3368424508-2654684973-1009` (FortisHostG1).
Это согласованная ранее [схема shared runtime](G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md).
Установщик сохраняет эту границу: owner должен быть доверенным; пишущие grants
допускаются для owner/SYSTEM/Administrators либо для Authenticated Users в пределах
Modify, если перед ними в фактическом порядке DACL уже стоит полный guest DENY
маски `0xD0156`. Неизвестные writers, FullControl для AU, неполный/чужой DENY,
noncanonical/null DACL и неподдерживаемые права отклоняются с путём и SID.

Для существующего runtime parent и version directory дополнительно обязательны
`ContainerInherit + ObjectInherit` без `NoPropagateInherit`: запрет должен дойти
до нового version directory и EXE. Оба созданных объекта проверяются повторно.
Inherit-only `CREATOR OWNER` принимается только как шаблон будущего владельца;
владелец каждого создаваемого объекта проверяется отдельно.

Это проверка конкретной принятой схемы ACL, а не общий Windows AccessCheck и не
обещание изоляции от всех остальных authenticated accounts. Их существующие
Modify grants сохраняются. Installer не вызывает Set-Acl, не добавляет grants,
не удаляет DENY и не требует менять ACL `C:\Tools` или запускать его elevated.
Windows CI проверяет синтетические отрицательные случаи и реальное наследование
на временных NTFS-каталогах. Live owner Preview и staged Repo acceptance остаются
отдельными шагами.

До переключения source pins новый бинарник должен уже существовать.
Для первого перехода использовать owner-reviewed bootstrap bundle,
сформированный из опубликованного проверенного commit: installer,
`current/launchers/shared/FortisContainerPolicy.ps1` с сохранённым относительным
путём и оригинальный официальный runtime ZIP. Bundle не заменяет Windows
Git clones и не содержит ключей. Передача и конкретный SHA-256 — по
workspace README, через `docker cp` из выделенного task directory.
Владелец сначала сверяет опубликованный source/CI и hash переданных байтов.

Из распакованного bundle, обычный Windows PowerShell:

```powershell
.\Install-FortisRuntime.ps1 -ArchivePath .\tunnel-client-runtime-v0.0.21-windows-amd64.zip
.\Install-FortisRuntime.ps1 -ArchivePath .\tunnel-client-runtime-v0.0.21-windows-amd64.zip -Apply
```

Ожидаются `FORTIS_RUNTIME_INSTALL_PREVIEW_PASS`, затем
`FORTIS_RUNTIME_INSTALL_APPLY_PASS` и версия/flavor установленного EXE.
Отсутствующий parent, чужой owner, пишущая ACL вне описанной выше границы,
reparse point, неверная архитектура/hash/состав ZIP или занятый target — STOP.
Не обходить это запуском с elevation или ослаблением ACL.
Каталог v0.0.15 сохраняется. При ошибке после записи нового файла прежняя
версия остаётся доступна; повтор не должен незаметно заменять новый target.

Если EXE уже установлен, при последующих проверках можно запускать installer
из опубликованного Windows `tunnel` clone. `-Apply` без `-ArchivePath`
скачивает только фиксированный официальный URL из policy с теми же проверками.

## Source update и переключение

1. Проверить зелёные CI на точных HEAD обоих PR. Владелец сливает их через
   GitHub UI, сначала Tunnel, затем Script Center. Docker main обновляется
   через typed `workspace.update_main_from_pr`.
2. Установить проверенный EXE по предыдущему разделу. Это ещё не переключает
   работающие v0.0.15 процессы.
3. Из `%USERPROFILE%\Repos\script-control-center` выполнить штатный paired updater:

   ```powershell
   .\tools\Update-Windows-ControlCenter.ps1
   .\tools\Update-Windows-ControlCenter.ps1 -Apply
   ```

   Apply разрешён после Preview PASS. Он обновляет Tunnel, затем Script Center,
   проверяет девять файлов/manifest, syntax, UI compile, оба Guard Preview и ярлык.
   Dirty/diverged/wrong-branch clone — STOP без reset/clean/stash.
4. Сохранить Repo 2 работающим. В Control Center остановить только Repo 1 и
   убедиться, что его прежний runtime завершён. Запустить Repo 1, проверить
   новые `RunId`, runtime path/version/PID и отсутствие второго экземпляра
   с тем же Tunnel ID.
5. В аккаунте Repo 1 выполнить initialize/tools list и не менее 10 безопасных
   чтений. Наблюдать минимум 30 минут обычной работы; проверить, что новые
   команды реально отвечают, а не только отображается «Работает».
6. После PASS аналогично переключить Repo 2, оставляя Repo 1 доступным.

Actual installation, guard identity, source SHA и MCP outcome фиксируются
отдельно для двух Repo. Доступный в одном аккаунте Repo 2 не доказывает
приёмку Repo 1 в другом. Рабочий Docker-контейнер не останавливать.

## Откат

Последняя проверенная исходная пара до этой задачи:

| Репозиторий | Baseline main |
| --- | --- |
| `tunnel` | `d4b32a88051f6d6a7c447478990df0b81a7b421b` |
| `script-control-center` | `88bf3cd048b4a031226f332a5731aebf23b0eaa4` |

Прежний EXE: `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe`,
SHA-256 `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`.

При сбое первого переключения сохранить второй runtime работающим.
В task worktrees подготовить согласованную пару revert PR на текущем main:
вернуть изменённые executable sources, девятифайловый manifest, dispatcher pin
и resolver pins к предыдущему согласованному контракту. Не откатывать
несвязанные новые изменения репозиториев. Проверить hashes/контракты и owner
GitHub merge; затем обычный Windows paired Preview/Apply и перезапуск только
затронутого worker. Не подменять один EXE при pins другой версии и не обходить
dispatcher запуском непроверенных исторических копий.

Новые stdio/PID/health параметры добавлены только общей функцией в source,
а не записаны в YAML или env. Поэтому согласованный source revert удаляет
их вместе с новым launcher. Сохранение v0.0.15 и проверка его обычного
запуска на стенде не доказывают выполненный rollback рабочей Windows-системы.
До второго переключения должен сохраняться рабочий первый туннель и owner
recovery path. Незакрытая эксплуатационная приёмка ведётся только в
[backlog](BACKLOG-IMPROVEMENTS.md).

## Первичные upstream-источники

- [Релиз v0.0.21](https://github.com/openai/tunnel-client/releases/tag/v0.0.21).
- [Stdio recovery и предел одного процесса на Tunnel ID](https://github.com/openai/tunnel-client/blob/714f2d67844b660af25754f1d19b0360b346b13b/docs/configuration.md#stdio-deployment-limits).
- [Обработка завершённого ответа](https://github.com/openai/tunnel-client/blob/714f2d67844b660af25754f1d19b0360b346b13b/pkg/dispatcher/internal/processor.go).
- [Serialized forwarding connection](https://github.com/openai/tunnel-client/blob/714f2d67844b660af25754f1d19b0360b346b13b/pkg/mcpclient/serialized_forwarding_transport.go).
- [Поведение использованного v0.0.15](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/dispatcher/internal/processor.go).

Контрольные суммы сверяются с опубликованными release assets и SHA256SUMS.
Проверка checksum не является проверкой Authenticode/Sigstore-подписи.
