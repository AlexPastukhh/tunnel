# G3 — выбранные owner TCP/IPC поверхности, 16 октября 2026

> Продолжение: [E34](G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.md) завершил Repo-only Preview, ReadyForApply=false. Датированные наблюдения и прежний NEXT ниже сохранены; текущая очередь — в плане.

**5.8 PARTIAL: новых TCP слушателей в выбранной цепочке не обнаружено; известные owner API не закрыты.**
[Полные результаты E33](G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты. Это read-only уточнение поверхности, не исправление доступа.

## Наблюдения на Windows

Через owner HOST выполнен только агрегированный запрос process/listener metadata.
Это требовалось для owner SID/creation/EXE witness, недоступного обычному guest.
Owner файлы и настройки не менялись. G2 и Repo не останавливались этой проверкой; непрерывная доступность не измерялась.

| Роль | PID / Parent | SID / Session | TCP listeners |
|---|---|---|---|
| Временный owner HOST | 13520 / 18904 | 1001 / 1 | 127.0.0.1:8080 |
| Сохраняющийся owner Repo | 22488 / 4452 | 1001 / 1 | 127.0.0.1:59183 |
| Owner Desktop Commander Node | 24724 / 16092 | 1001 / 1 | Нет |
| Промежуточный cmd.exe | 16092 / 13520 | 1001 / 1 | Нет |

Первые три exact creation fingerprints и public EXE hashes совпали с ожидаемыми E22/E25.
Full EXE SHA1946DE55…; Node SHA2FFE3ACC…. Отдельный запрос подтвердил связь HOST→cmd.exe→Node.
Для промежуточного процесса не читались executable contents/path, argv, environment или profile.
Основной snapshot: 2026-10-15T22:02:30.4391495Z; companion cmd snapshot: 2026-10-15T22:03:33.3138872Z.
Это два адресных среза, не непрерывный контроль. Другие owner processes и named pipes не перечислялись.

## Что уже доказано и что не требуется повторять

E13 уже подтвердил guest cross-session достижимость owner loopback API. E15 разобрал настоящие routes,
loopback-only guard и sensitive/mutating функции исходника. Новый GET того же пути не дал бы
нового решения; HTTP в этом этапе вообще не использовался.
Ни live owner mutation/RCE, ни чтение owner private bodies этими evidence не утверждаются.

Для выбранных Node/cmd процессов нет TCP debug/управляющего listener в наблюдавшихся срезах.
Это не полный аудит Windows IPC, future listeners или остальных processes.
Нет основания автоматически добавлять полный скан всех портов/pipes или повторять E22 DUP_HANDLE.
При новом конкретном broker/debug пути проверить именно его.

## Оставшаяся работа и соразмерный следующий шаг

Известные owner HTTP listeners остаются на месте с прежними full binaries.
Отдельная Windows-сессия G2 сама по себе не закрывает TCP loopback. Значит, общий owner API gate
4.10 не принят. E33 не подтверждает ни новую защиту, ни полноценную возможность эксплуатации.

- Для прежнего HOST: завершить применимую G2 acceptance и подготовить согласованный retirement,
  затем проверить прекращение listener/обходного route. Отдельная HOST runtime-only migration не нужна.
- Для сохраняющегося Repo: подготовить отдельный protection/compatibility Preview с существующими
  candidate run-tunnel/control и явным учётом monitor/health/private metadata. Не применять общий
  all-three switch. Runtime-only удаляет admin-модуль, но сам по себе не доказывает безопасность
  оставшихся health/metrics bodies; эту часть нельзя объявить закрытой.
- Независимые data routes и backups остаются 7.6. Их не заменяет запрет runtime file writes E32.

Preview/подготовка допустимы без остановок. Actual owner launcher change, выбранный способ защиты
и прерывание общего Repo требуют конкретного отдельного решения. Никаких таких изменений в E33 нет.
Ключи и profiles в Docker/GitHub не переносятся.

## Воспроизводимость и проверка

[Test-G3SelectedOwnerTcpListeners.ps1](../runtime/host-g2/runtime-api-migration/Test-G3SelectedOwnerTcpListeners.ps1),
3815 байт, SHA256 `0DEAF24A50A7AA0CDB710A6F53B8A4B4BF1CB49BB4AF2210F4F9F52772CA9A06`.
Repo AST PASS; Windows metadata invocation завершён с ObservationComplete=true.
Source проверен SHA в памяти перед исполнением; на owner диск не записывался.
Supplementary bounded metadata command сохранён в JSON; он лишь привязан к observed Node/parent.
Private argv/env/keys/response bodies не читались; HTTP requests=0, ACL writes=0, runtime restarts=0.
