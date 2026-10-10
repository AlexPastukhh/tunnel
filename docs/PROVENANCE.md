# Происхождение и перенос

Документы актуализированы 2026-10-10. Проверка: Windows runtime files, Docker inspect и control Status, ACL runtime.key (без чтения содержимого), read-only исходники двух Site версий. Стандартные инструкции найдены в установленных Sites / Plugin Creator skills; их текст здесь не размножается.

## Перенесённые документы

- Из C:\Users\alexa\Documents\prot: инфраструктурные root README/планы и все прежние docs/.
- Из C:\Users\alexa\chatgpt-repo-mode: WORKSPACE.md.
- Из C:\Users\alexa\chatgpt-bridge: README.md.

Оригинальные байты сохранены в history/. На прежних путях оставлены короткие указатели на актуальные документы и архив. Launcher/scripts, prototypes, Bridge policies/registry, данные, logs и credential backups не перемещены.

Tracked документы из chatgpt-snapshot-transfer скопированы как датированная справочная история; их owning repo и оригиналы сохранены. Они не удаляются из другого Git repo ради централизации.

history/migration-manifest.json содержит source/destination и SHA-256 оригинальных документов. Исторические относительные ссылки могут указывать на прежнее дерево; актуальные рабочие пути описаны в docs/, прототипы остаются на HOST.

## Копии текущих исходников

runtime/repo-mode: выбранные Docker/MCP/launcher/probe/control/test sources и workspace-config.example.json (датированный machine snapshot, не portable default). runtime/host: HOST secure launcher и trusted wrapper.

Исполняемые live paths остаются C:\Users\alexa\chatgpt-repo-mode и C:\Tools / Documents\prot. Для deployment копии нужно сравнить с live, применить намеренные изменения и проверить; Git push не обновляет автоматически запущенный процесс.

configure-tunnel.ps1 сохранён как существующий source: его env-key initializer устарел относительно текущего saved-file profile. Не использовать его для пересоздания текущего профиля без исправления и проверки (INSTRUCTIONS.md).

Для Site code source-of-truth — его Sites Git; SITES.md фиксирует проверенные project/plugin/version/HEAD. Нет копий временных source credentials, auth files или secret upstream URL.

## Что не переносилось в Git

Runtime key и реальные tunnel YAML profiles, snapshots/ZIP, VHD/ISO, runtime backups, payload logs, Git credentials, node_modules, private upstream endpoints. Snapshot export permissions не менялись. Содержимое других проектов в этот repo не включалось.
