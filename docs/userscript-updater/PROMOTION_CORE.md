# V1-3: ядро точного переноса и восстановления

Срез 25.10.2026. Реализованы transaction core, полный GUI review/confirmation/result/recovery и
native Windows I/O/installed-context candidate. **Native acceptance pending;
development profile не включает Update.** Windows working context предназначен
для отдельной функциональной проверки владельцем из рабочей папки. Приёмка Windows остаётся gate, см. [PLAN](PLAN.md);
выполненные прогоны — [журнал](IMPLEMENTATION_LOG.md).

## Цепочка

1. PromotionService принимает CheckResult из памяти приложения: registration/snapshot/policy/tool identities, clear engine reports и полное coverage. JSON-импорт отчёта и scanner exit0 не дают OS-полномочий.
2. Повторно сверяет source inventory/bytes, snapshot, shared packs и tool/config/Node hashes. Читает managed-state и actual target; показывает create/modify/delete/unchanged/preserve, diff/hashes/sizes и наличие target root.
3. Review fingerprint связывает весь plan, snapshot, registration, policy/tools и managed-state token. Новая review инвалидирует старые confirmations. Confirmation одноразовая; input drift требует новой проверки/просмотра.
4. Apply требует отдельный mutation backend, отсутствие pending transaction и повторную full-byte сверку, в том числе после staging. Копируется только сохранённый staged buffer с немедленной проверкой hash/size.
5. Journal фиксирует намерение до каждой мутации. После операции выполняется readback. COMPLETED возможен только после полной сверки target, source/policy/tool freshness и сохранения managed entries.

Confirmation — acknowledgement точной review, **не аутентификация владельца и не OS-authority**. Default service без backend отказывает даже с правильным confirmation. В profile нет флага, включающего native Update.

## Управляемый состав

ManagedStore хранит versioned entries project ID + target root + явно управляемые files. Общий root допустим для непересекающихся проектов. Чужие managed paths/ancestors конфликтуют; target-only files/dirs сохраняются. Смена target root не очищает старую область скрыто.

Первый импорт mapped existing files требует явного adopted_existing. Это не previous-managed deletion scope: удаление ограничено настоящим прежним составом. Read-only GUI «Просмотр первого импорта» включает только существующие явно сопоставленные назначения и показывает полный эффект.

Case-only rename требует отдельной миграции. Для отсутствующего target root parent должен существовать; скрытое создание ancestors вне показанного root запрещено.

## Journal и recovery

PREPARING → PREPARED → APPLYING → COMPLETED; ошибки приводят к ABORTED, ROLLING_BACK, ROLLED_BACK, ROLLED_BACK_WITH_EXTERNAL_DRIFT или RECOVERY_BLOCKED. Portable JSON/fsync/replace проверены в Docker; native Windows crash durability не доказана.

После прерывания до target intent recovery закрывает подготовку. После intent сопоставляет фактические bytes с pre/post-images. Подмена
backup/stage/journal или ownership conflict блокируют запись. Сторонние/частичные
bytes требуют отдельного conflict preview: пользователь видит current→backup
hashes/sizes/diff, подтверждает точные наблюдённые bytes; перед восстановлением
они сохраняются в отдельный проверенный backup. Без этого default recovery
отказывает. Незатронутые owner changes не откатываются. Внешний drift не маскируется под точное восстановление дерева.

Удаляются только известные созданные транзакцией пустые каталоги с совпадающей identity. Заменённый, неизвестный или непустой каталог сохраняется; recursive target cleanup нет. Разрыв mkdir→journal может оставить пустой каталог с external-drift исходом.

Completed transaction не откатывается автоматически. Отдельные review_rollback/rollback связывают acknowledgement с текущими target/state/journal. Stale/repeated rollback отклоняется; восстанавливается только свой managed entry, другие проекты сохраняются.

## Native source candidate и установленный контекст

checker/windows_io.py закрепляет цепочку ancestors через CreateFileW, проверяет
final path/identity/reparse/single-link и ADS. Source/snapshot чтение использует
held handles. checker/installed.py проверяет normal owner SID, app/data ACL,
полный установленный dependency closure, защищённые native/GUI/route receipts,
профиль и явно разрешённые approved roots. Python запускается -I -S с ._pth
только установленного комплекта; CLI environment/cwd фиксированы, UTF-8 явный.
Проверка effective configs и CLI output temps находятся в job-owned store.

WindowsTarget выдаётся только InstalledAuthority; JSON development profile и
scanner report его не создают. Полная проверка повторяется перед записью.
DesktopApp получает native context только из отдельного installed launcher.
QA fixture writer лежит вне checker/import path и ограничен новой временной
папкой; он не является accepted installed writer.

WorkingContext/WorkingWindowsTarget — отдельный внутренний путь обычного
Windows-запуска из рабочей папки. Регистрация сверяется с сохранённым реестром;
точный выбранный source не смешивается с его широким parent. Writer принимает
только зарегистрированные назначения и отказывает при пересечении с любым
зарегистрированным source. Все review/consent/freshness/stage/backup/readback/
recovery контракты выше сохраняются. Общие файловые операции вынесены в
WindowsFileOperations; installed owner/receipt/closure guard не ослаблен.
Working результат имеет scope WINDOWS_WORKING_COPY_TEST и не становится
OWNER_INSTALLED_WINDOWS или OWNER_ACCEPTED.
[Запуск и подготовка](../../runtime/userscript-updater/README.md).

Existing Windows file обновляется через тот же эксклюзивно открытый handle:
CAS по ожидаемым bytes, DACL/identity сохраняются, timestamps/attributes
восстанавливаются, FlushFileBuffers/readback. Это **не atomic replace файла**.
Прерывание во время write может потребовать отдельного conflict recovery.
Создание использует CREATE_NEW, удаление — held handle disposition. Metadata
вне поддержанного профиля/иной owner и active locks явно отказывают.
NTFS/local fixed-volume, normal owner, native race/sharing/metadata/Job Object
проверки обязательны; код не является доказательством их прохождения.

Отрицательные marker probes и полный список внешних agent routes — наблюдение
и attestation владельца. Программа проверяет declared overlap/ACL/неизменность
markers, но не обнаруживает скрытые внешние сервисы и не доказывает отсутствие
неперечисленного маршрута. Широкий write API с owner SID не изолируется ACL
той же identity; приёмка должна это отклонить.

## Folder/mixed и явный состав

В snapshot/fingerprint входят пустые source directories и явные exclusions.
Пустая существующая папка может дать delete-only plan для прежних managed files;
config validation выполняется и при отсутствии code files, без выдуманного scan.
Ресурс имеет явную классификацию/профиль suffix, hash/size и отметку «не анализировался
как код». Dependency требует analyzer coverage как code. Data и исключённые пути
не копируются/не удаляются и видны в preview. Один data destination не может
одновременно быть copied mapping. Нет скрытого исключения .git/cache/deps.

Показанные source empty dirs создаются; rollback убирает только известные
созданные пустые dirs с той же identity. Старые/existing target directories,
включая устаревшие пустые, явно сохраняются. File deletions ограничены прежними
managed paths; newly adopted existing file не становится прошлым deletion scope.
Case-only миграции отказывают. Source/target inventories имеют явные size/entry
лимиты; превышение — ERROR, не silent skip.

Один target root на регистрацию, много явных mappings и source roots.
Независимые destinations — независимые регистрации/consents/journals, без
гарантии global atomicity через root/volume. Результат partial/recovered честный.

## Проверка и доставка

tests/promotion_support.py — synthetic adapter только для private TemporaryDirectory.
Real-CLI integration выполняет mixed Check/apply/modify/delete/rollback и
resource-only/delete-only continuation. Actual Tk workflow проверяет consent
cancel/apply/result/history/inverse-preview/rollback; это Linux widgets с
injected chooser/messagebox, не Windows.

[Offline package и ручные native probes](../../runtime/userscript-updater/release/WINDOWS_ACCEPTANCE.md)
подготовлены отдельно; Windows install/ACL/GUI/route/consumer operations агент
не выполняет. Ни Linux tests, ни хеш ZIP не дают OWNER_ACCEPTED.
