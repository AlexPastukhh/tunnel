# V1-3: ядро точного переноса и восстановления

Срез 25.10.2026. Реализован portable transaction core и read-only GUI preview. **Native Windows mutation backend отсутствует; Update отключён. V1-3 целиком ещё IN_PROGRESS.**

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

После прерывания до target intent recovery закрывает подготовку. После intent сопоставляет фактические bytes с pre/post-images. Подмена backup/stage/journal, сторонняя правка touched file или ownership conflict блокируют запись. Незатронутые owner changes не откатываются. Внешний drift не маскируется под точное восстановление дерева.

Удаляются только известные созданные транзакцией пустые каталоги с совпадающей identity. Заменённый, неизвестный или непустой каталог сохраняется; recursive target cleanup нет. Разрыв mkdir→journal может оставить пустой каталог с external-drift исходом.

Completed transaction не откатывается автоматически. Отдельные review_rollback/rollback связывают acknowledgement с текущими target/state/journal. Stale/repeated rollback отклоняется; восстанавливается только свой managed entry, другие проекты сохраняются.

## Контракт будущего native backend

Backend не выбирается из project config/import path/boolean JSON. Его должен выдать независимо установленный owner-controlled компонент после native gate. В текущем GUI backend=None и native_update_available=False.

- authorize: проверенная граница App/Tools/Policies/State/Approved и agent-write routes, final paths/file IDs/ancestors, reparse/hardlink/alias refusal и live owner authority.
- read/metadata: стабильное чтение и восстановимые metadata через verified root/handles.
- replace/remove с expected_sha256: CAS под защищёнными handles/эксклюзивностью, без path/race подмены preimage; create ожидает отсутствие файла, lock/error не success.
- mkdir: атомарное создание отсутствующего показанного каталога и identity; rmdir_if_owned_empty удаляет только тот же известный пустой каталог.
- NTFS ACL/attributes/named-stream contract, backup/readback/durability и crash/locked/reparse tests обязательны до активации.

Native source/snapshot/state handles и полный analyzer dependency closure также обязательны. Один target adapter недостаточен. POSIX mode/mtime из tests не доказывают NTFS metadata preservation.

## Evidence и оставшийся scope

tests/promotion_support.py — строго временный synthetic adapter вне checker, приложение его не импортирует. devtools/fixture_transactions.py не переносился и не подключён. Unit receipts синтетические; отдельный test_promotion_cli.py использует настоящие ESLint/Semgrep для folder+file/mixed, двух Check, apply/delete и rollback только в private TemporaryDirectory.

Не убраны из A4: source empty-directory contract, delete-only/empty-source handling, explicit resource/exclusion/dependency/data classification, native backend/issuer, UI confirmation/recovery после native gate, multi-root/volume semantics и Windows owner acceptance. Сейчас неподдержанное явно отказывает, не становится PASS. Сохранение existing empty target dirs не означает копирование source empty dirs.

Docker tests, acknowledgement/hash и view-only GUI не разрешают реальный Windows перенос. Reviewed package ручной установки готовится после оставшейся разработки.
