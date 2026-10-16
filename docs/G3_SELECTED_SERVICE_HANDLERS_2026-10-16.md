# G3 — selected service user-defined controls: source/metadata, 2026-10-16 04:33

> Исправление E41: [actual G2 query](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md) подтвердил MySQL80 под NetworkService; E03 также записывал NetworkService. Raw E30 SystemAccount=true не позволял вывести LocalSystem. Прежнее описание исправлено, raw observations сохранены; никаких изменений службы не выполнялось.

**5.4 PARTIAL: эффекты просмотренных handlers уточнены; live controls не отправлялись.**
[Structured evidence E30](G3_SELECTED_SERVICE_HANDLERS_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты.

E03 уже подтвердил SERVICE_USER_DEFINED_CONTROL ALLOW для GoodbyeDPI/MySQL80 и DENY выбранных
start/stop/change-config/delete/ACL rights. Сам ALLOW не доказывает выполнение owner/admin команды.
В этом этапе не повторяли denied-rights matrix, не меняли права и не отправляли control codes.

| Служба | Windows metadata | Что даёт source review |
|---|---|---|
| MySQL80 | Running, Auto, SystemAccount=true (точный StartName в E30 не записан); mysqld.exe8.0.44.0, Oracle Corporation, SHA45796B4F… | В mysql-8.0.44 статический NTService handler останавливает службу только по STOP/SHUTDOWN. Другие codes идут в SetStatus с текущим состоянием; произвольного command execution в этой ветке нет |
| GoodbyeDPI | Stopped, Auto, LocalSystem; приватный/нестандартный executable path не выводился и не читался | SCM не передаёт controls остановленной службе. Выбранный upstream handler также обрабатывает STOP/SHUTDOWN, остальные codes заканчиваются сообщением статуса. Соответствие установленному binary не установлено |

У MySQL version/company/hash получены для указанного installed executable. Это не attestation сборки
и не доказательство точного соответствия running image исходнику. У GoodbyeDPI поле raw
ExecutableExists=false означало «проверка не выполнялась» в ветке PATH_WITHHELD_NOT_READ:
нормализованное значение unknown/null, а не новый PATH_NOT_FOUND или DENY.
Его прежний missing-path результат E03 остаётся отдельным историческим наблюдением.

## Вывод и оставшаяся неопределённость

В просмотренных handler branches не найден путь выполнения произвольной административной команды
для user-defined codes128–255. Live exploitation не проверялась и не утверждается.
Версионный/source binding MySQL неполон; версия/действительный binary GoodbyeDPI не проверены.
Остановленная Auto-служба — датированный факт, не обещание, что она всегда будет остановлена.

Нет основания устраивать live control-code fuzzing или менять service ACL только из-за ALLOW.
Если конкретная служба/версия/путь существенны для final threat scope, завершить адресную проверку
именно этого остатка; не расширять до полного аудита Windows и не читать лишние owner файлы.

## Первичные источники

- [MySQL handler mysql-8.0.44](https://github.com/mysql/mysql-server/blob/mysql-8.0.44/sql/nt_servc.cc),
  Git blob6a923d05f54859c0bfcfc64d31d5d007139a22cf.
- [MySQL NTService declaration](https://github.com/mysql/mysql-server/blob/mysql-8.0.44/sql/nt_servc.h),
  blobd67b6d66f82c3d7d009469511949f9997e8763da.
- [GoodbyeDPI upstream service.c](https://github.com/ValdikSS/GoodbyeDPI/blob/master/src/service.c),
  просмотренный blob4de164a073b21329d70a5f6e4d5a318fc4996bd0; master не является installed-version pin.
- [ControlService contract](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-controlservice):
  user-defined range и обработка STOPPED state.
