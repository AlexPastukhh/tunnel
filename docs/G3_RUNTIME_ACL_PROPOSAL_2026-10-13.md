# G3 — предложение защиты общего runtime ACL, 2026-10-13

**Применено пользователем 2026-10-13 в 14:12 Asia/Bangkok после явного согласия.** Изменены только согласованные четыре DACL; backup сохранён. Runtime gate проверен: [post-ACL evidence](G3_POST_ACL_VERIFICATION_2026-10-13.md). Ниже сохранён согласованный scope и порядок восстановления.
Обнаруженный результат: [G3 evidence](G3_READONLY_EVIDENCE_2026-10-13.md).

## Конкретный scope

Изменить только DACL четырёх каталогов, добавив запрет mutation rights только SID FortisHostG1 (1009):
1. C:\Tools — правило только на сам каталог, без наследования в посторонние подкаталоги.
2. C:\Tools\tunnel-client — ObjectInherit + ContainerInherit.
3. C:\Tools\desktop-commander-runtime — ObjectInherit + ContainerInherit.
4. C:\Tools\desktop-commander — ObjectInherit + ContainerInherit.

Маска 0xD0156: WriteData/CreateFiles, AppendData/CreateDirectories, WriteEA, DeleteChild, WriteAttributes, Delete, WriteDac, WriteOwner.
Чтение/list/execute SID 1009 сохраняются. Правила AU, Users, Administrators, SYSTEM, alexa и прочих identities не удаляются; owner, SACL, Windows groups и permissions других папок не изменяются.
Запрет на сам C:\Tools нужен, чтобы G2 не мог создавать там новые соседние runtime-объекты и удалять/переименовывать корень. C:\ root DeleteChild/WriteDac для G2 уже DENY.
Запреты трёх подкаталогов распространяются на их содержимое. Остальные существующие подкаталоги C:\Tools этим предложением не защищаются; это не полный аудит C:\Tools.

## Историческая read-only подготовка до применения

Owner inventory: tunnel-client — 9 объектов; desktop-commander-runtime — 2; desktop-commander — 22 747. В обследованных деревьях нет protected DACL или reparse points; ошибок enumeration/ACL-read — 0.
Это снимок, а не гарантия отсутствия будущих explicit ACE/inheritance exceptions.
На семи текущих ACL проверена добавленная ТОЛЬКО В ПАМЯТИ deny ACE 1009: AccessCheck для G2 оставляет read/execute ALLOW, а write/append/delete/WriteDac/WriteOwner переводит в DENY. Live ACL не изменены.
После реального применения необходимо проверить наследование и effective access; simulation не заменяет такой тест.

## Готовый script и порядок

[protect-shared-runtime.ps1](../runtime/host-g2/protect-shared-runtime.ps1) по умолчанию работает в режиме Preview — не пишет файлы и ACL.
Apply/Rollback допускаются только из PowerShell владельца alexa, вручную открытого с правами администратора; script сам не вызывает UAC/elevation.
Не запускать Apply до явного согласия владельца. Существующие HOST/Repo/G2 не требуется закрывать для изменения DACL; script их не останавливает.

1. Проверить Preview и scope четырёх каталогов.
2. В Apply сохранить исходные/планируемые DACL четырёх корней в уникальный JSON под LOCALAPPDATA владельца, FortisHostG2AclBackup. Backup содержит только ACL metadata.
3. Проверить отсутствие изменения DACL после preview, применить четыре правила и сверить root DACL readback. При ошибке STOP; сохранить backup, не делать слепой повтор.
4. Через реальный G2 проверить чтение/запуск ALLOW; write/create/append/delete/ACL-change DENY; отсутствие writable inheritance exceptions, неизменность binaries/hash и работоспособность старых HOST/Repo. Записи/удаления реального runtime не выполнять; для create/readback использовать отдельный заранее согласованный synthetic объект при необходимости.
5. Продолжить G3 только после успешной проверки.

Rollback принимает точный backup path, проверяет все четыре текущие DACL на соответствие Before/After и восстанавливает только сохранённую Access section. При посторонних ACL изменениях script прекращает rollback для ручного анализа. Owner/SACL не восстанавливаются и не меняются; backup не удаляется.
После rollback отдельно сверить inherited child ACLs. Rollback script подготовлен, но его live применение не тестировалось.

Синтаксис и Preview проверяются без Set-Acl. Credential/profile/UI configuration, services, tasks, mounts и production launchers в scope не входят.

## Проверка подготовленного script

PowerShell parser: PASS. Реальный вызов Mode Preview: PASS; после Preview все четыре live DACL равны Before. SHA-256 script: 0A7E0F496F314A7A5C272FEA9032DC6E4F274147E6E1AAEE3D2937E428CF5B76.
На этапе Preview Apply/Rollback не вызывались. Затем Apply выполнен владельцем; live Rollback не выполнялся. Post-ACL AccessCheck выполнен на всех 22 758 объектах трёх runtime деревьев.
