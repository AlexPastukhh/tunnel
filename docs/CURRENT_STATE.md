# Текущее состояние

Сверено 2026-10-10 с Windows-файлами, Docker inspect, ACL ключа и исходниками существующих Site. Это датированный снимок: состояние процессов меняется после запуска/остановки.

| Контур | Идентичность | Назначение и граница |
|---|---|---|
| Native HOST | profile desktop-commander; tunnel_6ac4a7249a4081918eb0881c870acf07 | Windows Desktop Commander, широкий доступ HOST; не sandbox |
| Native Repo | profile repo-mode; tunnel_6ac9e4dc9e688191ae1838e858424e8d | Desktop Commander внутри fortis-repo-test |
| HOST Site | Desktop Commander · prot, версия 4 | Отдельный HTTP MCP proxy к upstream; Site-аудитория — отдельная граница |
| Repo Site | Fortis · Repo Mode, версия 7 | Отдельный диагностический Site; его file/terminal gate ещё не активирован |

Native Repo работает независимо от настройки Site. Нельзя заключать «Docker-туннель не работает» по ответу не настроенного Site.

## Docker

| Windows | Linux | Доступ |
|---|---|---|
| C:\Users\alexa\Repos | /workspace/repos | bind, чтение и запись |
| C:\Users\alexa\Workfiles | /workspace/files | bind, чтение и запись |
| Docker volume fortis-repo-workspace | /workspace/repo | внутреннее хранилище |

Контейнер **fortis-repo-test**, ID **c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a**. Рабочий каталог /workspace/repos. Сеть **fortis-repo-egress**, исходящий интернет включён; опубликованных портов нет. uid/gid 1000:1000, root filesystem read-only, cap-drop ALL, no-new-privileges, без Docker socket, 2 CPU, 1 GiB RAM, pids limit 256, restart policy no.

HOME и /tmp — временные tmpfs. Git safe.directory добавляется для конкретных Git-корней, не глобальным wildcard; core.autocrlf=true соответствует HOST. Настройки и ограничения проверяет probe.mjs перед запуском.

На проверке в ходе переноса документации контейнер **running=true**, но Repo Tunnel не был найден локальным control.ps1. Это не постоянная настройка; актуальный ответ даёт Status.

Старый контейнер **fortis-repo-test-before-access-20261010t112331268z** оставлен остановленным для отката. Данные volume сохранены.

## Проверено ранее сегодня

Двусторонние тестовые записи в обоих bind-каталогах; чтение Git-корней; HTTPS GitHub/NPM; схемы и MCP presentation; запрет файлового чтения вне разрешённых каталогов. Контрольные файлы удалены. Это не доказательство невозможности доступа shell к сетевым службам HOST.

Windows Git credentials в контейнер не перенесены. Для private push нужна отдельная настройка авторизации.

## Что пока не реализовано

- Repo Site ещё не подключён к подходящему upstream endpoint и не разблокирован.
- Sandbox GUI / Windows VM — планы, не установленная возможность.
- Нет отдельной изоляции каждого чата и универсальной веб-панели управления разрешениями.
- Site Repo README/deployment snapshot и некоторые его тексты отстают от текущих Windows mounts / интернета / saved key. Их нельзя использовать для восстановления текущего контейнера. В этом изменении Site не перепубликовывался.

[Управление](OPERATIONS.md) · [Site и версии](SITES.md) · [Обновление слоёв](INSTRUCTIONS.md)
