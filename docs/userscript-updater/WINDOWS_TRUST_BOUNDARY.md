# Project Checker: граница доверенной Windows-установки

**Дата:** 25.10.2026. **Статус:** архитектурный контракт; Windows NOT VERIFIED. Источник требований — A4/v4. Не инструкция устанавливать приложение сейчас.

## Зачем

ИИ разрабатывают проекты в условно опасном Fortis Repo/Docker. Пользователь запускает только независимую внешнюю копию, подготовленную контролируемым Windows-приложением после анализа, полного предварительного просмотра и отдельного разрешения. Исходники, Docker tools и весь agent-write space считаются недоверенными.

Доверенный компонент должен находиться **вне всех agent-write routes**: приложение, исполняемые движки и полный closure зависимостей, Python/Node, policies/configs, registration state, protected snapshot, journal, backups, previous-managed set, approval records. Никаких runtime imports, Config discovery, Repo npm scripts или auto-sync со стороны Repo. Разрешено только намеренное ЧТЕНИЕ исходников как данных.

Внешние user-consumed copies также располагаются вне agent-write routes и не должны быть junction/symlink/hardlink на исходники. Source изменения не влияют на эти копии до нового approved review.

## Structural preflight

Модуль checker/windows_layout.py принимает описания app, tools, policies, state, approved, source, agent_write. Проверяет литеральные абсолютные Windows drive-пути, запрещает неоднозначные UNC/device/extended/relative paths и пересечения доверенных roots с источником или записью ИИ. Это **только строковая проверка**, не финальный Windows path/ACL probe. Даже без коллизий возвращается NEEDS_NATIVE_WINDOWS_VERIFICATION, а не PASS.

## Условия будущей ручной Windows-приёмки

1. Независимая ручная установка под контролем владельца вне mounts; не запускать Repo source как installed app.
2. OS handle-based final path, file identity, parent/reparse/junction/hardlink проверка всех trusted installed roots и внешних copies; проверить aliases через другие mount/route.
3. ACL/effective rights для agent principals плюс реальные отрицательные write-probes в специально подготовленные проверочные markers. **Если agent bind writes используют Windows identity владельца, обычный ACL этой же identity сам по себе может НЕ изолировать агентский доступ.** Не проводить пробы над пользовательскими секретами, профилями и действующими executable files.
4. Полный инвентарь tool/application/module/import dependencies and hashes; никаких исполняемых plugin/config/deps из Repo; независимое trusted окружение и cwd.
5. Safe Windows file handles, reparse denial, source inventory and byte snapshot, полный source recheck сразу перед promotion; semantic rule coverage не следует из exit0.
6. Durable, exclusively protected policy packs, shared-pack invalidation, approval records. Связать snapshot/policies/tool identities/source/actual target/full create-modify-delete preview; после изменения любого input отменить approval.
7. Проверить staging, backup/readback/journal/recovery при блокировках, крашах, конкурирующих edits, multi-file partial failures. Гарантию global atomicity через volumes не заявлять.
8. После native GUI + consumer tests пользователь запускает именно внешние copies. Не заявлять OS запрет ВСЕХ иных запусков.

Эти пункты — будущие gates. ACL, Windows GUI, настоящие внешние paths, Browser/Tampermonkey, нетронутые данные и native source handles в этом чате не проверялись и не изменялись.

## Текущее source-only состояние

checker/gui.py: вкладки проектов, привязок правил, проверок, target preview, layout; JSON import только данные; registry.py/registration_editor.py добавляют versioned JSON persistence и chooser/editor, пока без Windows visual/ACL evidence; кнопки «Проверить» и «Обновить» выключены. Tkinter runtime в Docker отсутствует, визуальная Windows проверка NOT_RUN. checker/ui_model.py — presentation state и invalidation при изменении общего пакета. checker/windows_layout.py — string-only structural gate. checker/preview.py — только расчёт эффектов. devtools/fixture_transactions.py — синтетическая лаборатория, не подключённая к app и исключаемая из production install.

Следующий этап по актуальному PLAN — V1-2 shared-pack UI и реальный Check worker; native Windows handle/ACL/protected dependency design остаётся обязательным перед trusted approval. Persistence/picker/editor — только source/DOCKER_TESTED.

**Никакого реального PASS/внешнего обновления эта документация не разрешает.**
