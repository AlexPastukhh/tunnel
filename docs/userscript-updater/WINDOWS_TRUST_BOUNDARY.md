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

## Текущий source candidate и ручная процедура

checker/windows_io.py реализует Windows held-handle source/snapshot/target I/O,
final path/identity/reparse/hardlink/ADS refusal, sharing/CAS, file security и
timestamps/attributes. checker/installed.py — normal-owner installed context:
полный closure/ACL/receipt/profile/approved-root checks перед native writer.
Development-профиль/JSON scan/exit0 такой контекст не создают.

Installed Python запускается из отдельного launcher с -I -S и фиксированным
._pth без site/.pth/usercustomize, CLI — с явным безопасным environment/cwd.
App/tool closure защищён для SYSTEM/Administrators; mutable owner state/policies
и approved roots должны оставаться вне agent write routes.

Код и подготовленные native probes — **SOURCE_CANDIDATE / WINDOWS_NOT_RUN**.
Конкретные offline install, native/GUI/marker probes, acceptance и rollback
описаны [рядом с пакетом](../../runtime/userscript-updater/release/WINDOWS_ACCEPTANCE.md).
Результаты выполненных проверок — [журнал](IMPLEMENTATION_LOG.md), этап — [PLAN](PLAN.md).

Owner receipts фиксируют наблюдённые write routes и отрицательные markers.
Программа проверяет declared paths/ACL/неизменность challenges, но не может
обнаружить скрытый внешний сервис. Одинаковая owner/agent identity с широким
native write API требует реального ограничения маршрута/другой identity,
а не выдуманного DENIED. Probe matrix охватывает app, data/state/policies и
каждый approved root. Пробы только на специально подготовленных markers.

Existing native files записываются через тот же held handle; это journaled
write, не atomic replace. Неизвестные partial/foreign bytes автоматически не
затираются: отдельный conflict preview/consent сначала сохраняет их backup.
NTFS/local fixed-volume, поддерживаемые metadata/owner и настоящие Windows
lock/race/recovery/Job Object tests обязательны. Подробный контракт:
[PROMOTION_CORE](PROMOTION_CORE.md).

Никаких host install/ACL/mount/GUI/Loader/actual external writes агент не
выполнял. До native/route/installed walkthrough нет OWNER_ACCEPTED.
