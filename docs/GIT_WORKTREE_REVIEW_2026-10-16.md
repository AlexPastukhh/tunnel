# Git worktree review / публикация после E44 — 2026-10-16

Это проверка **содержимого Git-репозитория** Fortis Repo. Она не означает применение runtime, пересмотр Windows ACL или полную security acceptance G5. Рабочий checkout: /workspace/repos/tunnel (Windows-bound Git); /workspace/repo — отдельный внутренний Docker volume, не Git checkout.

## Что оставляем в приватном GitHub

- Исторические и датированные G2/G3 свидетельства, включая checkpoint 12 октября, результаты guest Session 3 и исходный handoff 16 октября. На устаревших сводках стоят предупреждения: после E43 старый owner HOST остановлен, а E44 документирует bounded metadata/docs.
- Исходники-копии runtime/host-g2 и window-isolation, включая prototype/preflight scripts, Test-G3* и C# probe. Это **не** доказательство их установки, не приглашение использовать ACL-changing launcher.
- Observatory: P1 исходники и отдельный Repo monitor, статическая страница и unit tests. Датированные Windows интеграционные факты — только в уже существующих evidence; здесь проверялись offline unit tests.
- Исторический Broker bridge-v2-windows.patch и policy.example.json. Патч **не применять** к исправленному live Broker: это исходник истории, не текущая команда.
- Намеренное удаление устаревшего runtime/repo-mode/configure-tunnel.ps1 из копии, уже описанное в PROVENANCE и INSTRUCTIONS. Файл остаётся в Git history. Это не удаление установленного Windows runtime, и профиль/ключ не изменялись.
- Поправки навигации, архивных предупреждений и ссылки на реестр E01–E44.

## Что не публикуем

- Каталог agent-io-test/: тривиальные результаты разового I/O smoke (не source code и не meaningful acceptance evidence); сохранён локально, игнорируется.
- Runtime backup runtime/host-g2/runtime-api-migration/*.before-*.ps1.bak: точный локальный BEFORE-вариант, ранее упомянутый в E## evidence. Сохранён для recovery, но не копируется в Git. Актуальный источник и дата его изменения находятся в документации/Git.
- observatory/data/, incident history/logs, pycache/pyc; любые реальные ключи, credentials, payload snapshots и runtime profiles. Правила в корневом .gitignore и observatory/.gitignore; существующие ignored files не извлекались и не публиковались.

## Проверки перед коммитом

- Git source pins: все три launcher candidate файла совпадают с migration-plan.json; выбранные window-isolation pinned sources совпадают с hash guards.
- Offline unit tests: Observatory 11/11 PASS, Broker 12/12 PASS.
- Python AST, JSON parsing, JavaScript node --check: PASS для выбранных новых/изменённых файлов соответствующих типов.
- Поиск в предназначенных к публикации файлах: PEM/private keys, распространённые API/token signatures, Bearer values, credentials-in-URL и присваивания environment secrets — совпадений не обнаружено. Это **ограниченный pattern scan**, не гарантия отсутствия всех возможных секретов.
- Markdown local links и fragment links перепроверяются после добавления отчёта, до push. Две устаревшие ссылки на отсутствующие observability-ui-prototype-0/1 в history/prot/docs/observability/README.md относятся к неполному историческому snapshot и **оставлены без фальсификации архива**; новые docs имеют рабочие ссылки.
- Проверка git diff --cached --check и точного staging обязательна перед публикацией. Push обновляет приватный Git, **не** запущенные Windows/Docker/Site runtime.

## Что нельзя утверждать

Не выполнялись native Windows PowerShell/C# smoke, Docker security audit, проверка всех GUI/IPC/services или автоматическое применение Windows policy. Датированные документы могут содержать исторические NEXT/PENDING — для текущего принятого scope использовать [ISOLATION_GUIDE](ISOLATION_GUIDE.md), [CURRENT_STATE](CURRENT_STATE.md) и [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md).
