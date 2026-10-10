# План переноса репозиториев в единый корень

Статус: подготовка / частичная очистка выполнена
Дата: 2026-10-07

## Цель

Собрать рабочие репозитории в:

`C:\Users\alexa\Documents\Repos`

Это станет authoritative постоянным repo root для будущего изолированного Repo Mode.

## Правила миграции

- Не переносить всё одной массовой командой.
- Перед переносом каждого repo фиксировать branch, HEAD, status, remote и worktrees.
- Не терять незакоммиченные изменения.
- Не перезаписывать существующий repo с тем же именем.
- После переноса проверять `git status`, HEAD, origin и релевантные tests/build.
- Junction использовать только как временный compatibility bridge, когда реально есть зависимость от старого пути.

## Git worktrees

Проведена очистка OBS ReplacementPackageApp worktrees.
Старые clean worktrees без полезного преимущества были удалены.
Оставшиеся полезные изменения были сведены в `main`, dirty изменения закоммичены.
Для проверенных repo сейчас должен оставаться только основной worktree.
## Tampermonkey / абсолютные runtime paths

Перед переносом отдельно учесть loaders, использующие `@require file://...`.

Известные зависимости:
- `study-tab-launcher`;
- `text-file-download-widget`;
- `tabnotifier-fileautosend-autochat`;
- `chatgpt_session_timer`;
- `obs-planning-docs`.

Для таких проектов migration flow:
1. зафиксировать старый путь;
2. перенести repo;
3. при необходимости временно оставить junction со старого пути;
4. обновить Tampermonkey `@require`;
5. перезагрузить userscript;
6. пользователь визуально проверяет работу;
7. после подтверждения удалить compatibility junction.

## Особые репозитории

Не переносить вслепую:
- `gdoc`: были несколько checkout одного origin, нужен отдельный выбор authoritative copy;
- `gd-cap`: ранее был backup и worktree history;
- `enman`: основной checkout сильно dirty и рядом есть копия;
- HOI4 mods: могут требовать физическое расположение в игровом каталоге;
- `.codex` checkout'ы: служебное состояние, не рабочие проекты.
## Предлагаемые этапы

### Phase 1 — инвентаризация
- повторно найти все Git roots под `C:\Users\alexa` и пользовательскими каталогами `C:\`;
- классифицировать: рабочий / backup / download / tool-internal / game-mod;
- выявить collisions имён в `Documents\Repos`;
- выявить абсолютные path dependencies.

### Phase 2 — простой batch
Перенести standalone repos без worktrees/collisions/runtime path dependencies.
После каждого: status, HEAD, remote, tests/build.

### Phase 3 — зависимые repos
Переносить Tampermonkey-зависимые проекты с временным compatibility bridge и последующим обновлением loader path.

### Phase 4 — сложные случаи
Отдельно решить `gdoc`, `gd-cap`, `enman`, backups, downloads и game mods.

### Phase 5 — финальная проверка
- все рабочие repos либо находятся под `Documents\Repos`, либо имеют задокументированную причину оставаться снаружи;
- нет потерянных commits/dirty changes;
- нет старых broken worktrees;
- Tampermonkey tools работают;
- абсолютные runtime paths обновлены;
- Repo Mode получает только единый root.

## Связь с изоляцией

Не включать строгий Repo Mode как основной до завершения основной миграции.
Иначе реальные рабочие repos, оставшиеся снаружи `Documents\Repos`, окажутся недоступны в обычном режиме.
