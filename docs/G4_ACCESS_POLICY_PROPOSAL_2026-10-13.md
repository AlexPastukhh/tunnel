# Предложение: удобные доступы G2 и Repo, 2026-10-13

**Датированное предложение, не enforcement и не обязательный список новых компонентов.** [Актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) уточняет принятую политику: existing Workspace допустим как baseline; новые grants — по задаче, универсальный ACL manager/GUI — CONDITIONAL, собственные guest GUI/clipboard разрешены. Ниже сохранён исходный design с явными уточнениями; его варианты не становятся обязательными без потребности.

**DRAFT / NOT APPLIED.** Это проект политики, не действующая настройка. Текущая проверенная точка — [G2 runtime acceptance](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md). На дату этого предложения дополнительные рабочие roots ещё не были выбраны; последующий Workspace baseline и остаток приёмки описаны в актуальном плане. ACL, процессы, Docker, GUI, браузер и буфер этим документом не менялись.

## Цель и сохранённые возможности

G2 остаётся стандартным Windows-пользователем FortisHostG1 с PowerShell/Python/Git, Windows API и диагностикой в пределах его настоящих прав. Repo остаётся основной Docker-средой разработки. Предлагается сохранять работу с файлами, сборками, тестами, пользовательскими приложениями G2 и нужным интернетом; защищать credentials, личные сессии, ценные данные и пути выполнения от владельца.
Браузерные задачи — будущая отдельная возможность: свой рабочий профиль под G2 или отдельным ограниченным principal, без cookies/passwords основного пользователя. Защищаем основной owner GUI/экран/clipboard alexa; свои guest GUI/экран/clipboard разрешены. Политика и remaining gates поддерживаются в актуальном плане.

## Удобное управление — предлагаемая реализация

Один конфиг с абсолютными путями и именованными режимами: «работа — чтение/запись», «справка — только чтение», «закрыто». Новая папка добавляется в таблицу, затем Preview показывает точные изменения для SID 1009 и обоих маршрутов. Сам конфиг и исполняющий код должны быть owner-controlled, вне G2/Repo RW-каталогов; кандидат в Git не применяется автоматически.
Отдельный доверенный PowerShell-скрипт: Preview без мутаций, Apply только владельцем с нужными правами, Rollback по точному backup. Сохранять затронутые ACL в owner-private backup, проверять before-state перед записью, отклонять неопределённые/reparse paths и конфликтующие вложенные правила. После применения — actual G2 token, shell/file/child тесты и проверка другого маршрута.
Существующий protect-shared-runtime.ps1 меняет ровно четыре runtime DACL; он не является универсальным менеджером рабочих/личных папок. Новый механизм ещё не реализован. Графическую локальную панель с выбором папки и режима можно добавить поверх того же конфига; не создавать доступный G2 owner-admin HTTP endpoint.
NTFS ACL ограничивают G2; для Repo нужны Docker mounts/permissions/network. Windows deny SID 1009 не является deny для Linux UID 1000 и Windows Docker backend. Изменение mounts требует контролируемого recreate/restart и отдельной проверки; текущие Repo чаты заранее сохраняем.

## Предлагаемая стартовая матрица

| Область | G2 | Repo | Что именно выбрать/проверить |
|---|---|---|---|
| Выбранные проекты, папка обмена, результаты/временные файлы | RW | RW на нужные projects/exchange | Можно использовать выбранные существующие папки либо отдельный workspace вне private home. Не открывать весь owner profile. |
| Справочные документы и исходные данные | RO | RO либо отсутствуют в mounts | RO разрешает чтение содержимого, поэтому не подходит для секретов. |
| Системные программы и shared runtime | Чтение/запуск по необходимым правам, без изменения | Только действительно нужные инструменты | Не менять массово ACL C:\Windows/Program Files. Защита проверенных C:\Tools runtime уже применена; другие пути отдельно проверять. |
| Данные приложений владельца | DENY | Не монтировать | C:\Users\alexa\AppData: личные browser profiles, mail/messenger/password-manager state, cached tokens, credentials, history. Проверять существующую изоляцию, не рекурсивно переписывать весь home. |
| Credentials вне AppData и в проектах | DENY для выбранных credential объектов | Вне доступных mounts/checkout | .ssh, .aws, .azure, .kube, .config/gcloud, .git-credentials, credential-bearing .npmrc/.env; это примеры классов, наличие/содержимое не проверялось. |
| Личные документы/фото, финансовые файлы, recovery codes, приватные архивы | DENY на явно выбранные roots | Не монтировать | Сначала выбрать области по назначению. Downloads/Desktop/Documents часто смешанные; не закрывать их целиком без исключений и проверки потребностей. |
| Backups и административные конфиги/launcher/policy | Backups DENY; runtime/policy без записи G2 | Вне RW mounts | Резервные копии не должны удаляться через любой AI route. Canonical policy не хранить только в доступном обоим агентам Repo. |
| Рабочий browser G2 | Свой профиль и минимальные service permissions | По необходимости отдельный browser route | Личные mail/password manager/банковские сессии владельца не переносить. Доступ к logged-in account является самостоятельным полномочием. |

Credential-bearing файлы в доступном Repo остаются читаемыми несмотря на .gitignore или запрет G2. Размещение кода в RW папке подразумевает возможность его изменения/удаления. Для особо ценных исходников нужны отдельные backups. Свои scoped Git/API credentials рабочего principal тоже доступны коду этого principal; не считать их равными секретам основного владельца.
Отдельный Windows-пользователь дополняет защиту user-bound DPAPI; это не гарантия для всех способов хранения — machine-bound DPAPI и plaintext copies имеют другие свойства. Права проверять без чтения реальных секретов.

## Буфер, GUI и браузер

Предлагаемый режим: автоматическое чтение общего owner clipboard запрещено; обмен — пользователь явно передаёт выбранный фрагмент в чат/файл обмена. Будущий broker может передавать один выбранный фрагмент после локального разрешения владельца, без постоянного разрешения читать весь буфер и без обходного прямого owner API.
В Windows clipboard принадлежит window station; отдельный SID/виртуальный desktop сами по себе не доказывают его изоляцию. WINSTA_ACCESSCLIPBOARD — отдельное OS-право. С текущими свободными PowerShell/Python описание инструмента «спросить сначала» не является enforcement: код может вызвать API напрямую, если OS доступ разрешён.
Нужна проверенная OS-изоляция G2 от owner clipboard: отдельная window station/сессия или подходящий ACL-механизм после отдельного synthetic теста; альтернативно VM/Sandbox с отключённым clipboard sharing. Отдельный desktop в той же window station не создаёт отдельный буфер. Текущий G2 clipboard deny НЕ ПРОВЕРЕН; реальный clipboard не читался.
Рабочий browser-profile сохраняет полезные web-задачи. Однако широкий shell того же principal не гарантирует сокрытие его собственных browser secrets/sessions; для этой более сильной цели нужен отдельный browser principal/изолированная среда и ограниченный посредник. Owner CDP/debug/automation endpoints тоже должны быть недоступны G2.
В Windows Sandbox clipboard sharing включён по умолчанию; отключается явно. Sandbox/VM — вариант для browser/GUI сценариев, не автоматическая замена Windows HOST для задач над самим компьютером.

## Диагностика и сеть

Предлагается оставить версии ОС/ПО, CPU/RAM, свободное место, состояние рабочих процессов и необходимую сетевую диагностику. Не ограничивать все сведения о ПК только ради того, чтобы скрыть credentials.
Credentials Wi-Fi/VPN/SSH/cloud, owner session data, private shares и управляющие endpoints — отдельные защищаемые ресурсы. Интернет для нужных задач можно оставить, но следует закрыть ненужные owner/LAN management endpoints; сеть настраивается отдельно от папок.
Со свободным shell нельзя обещать сокрытие всех стандартно доступных сведений ОС, ограничение внешних действий только UI-подтверждением или запрет передачи разрешённого к чтению содержимого через открытый интернет. Если нужны такие гарантии, требуется ограниченный broker/сетевое enforcement либо иной режим исполнения.

## Следующие решения и критерий приёмки

Сначала согласовать named roots и требуемые browser/clipboard capabilities, без secret contents. Перед production G4 закрыть G3 owner local APIs/широкие chat routes и проверить оставшиеся services/SMB. Затем подготовить точный Preview и rollback, выполнить отдельную приёмку реальных RO/RW/DENY областей.
Сохранение текущих owner чатов остаётся требованием. Ни выбор @G2, ни закрытие folder только одному SID не отменяют доступ того же чата через owner HOST или Repo mount.

## Официальные основания

- [NTFS ACL, icacls save/restore](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls).
- [Window station содержит clipboard](https://learn.microsoft.com/en-us/windows/win32/winstation/about-window-stations-and-desktops) и [WINSTA_ACCESSCLIPBOARD / object ACL](https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-security-and-access-rights).
- [Windows Sandbox configuration / clipboard redirection](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file).
- [DPAPI user-bound/machine-bound поведение](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).
- [Отдельный Edge user data directory](https://learn.microsoft.com/en-us/deployedge/edge-learnmore-create-user-directory-vars).

Дата источников и предложения: 2026-10-13. Это документированный дизайн, не security acceptance.
