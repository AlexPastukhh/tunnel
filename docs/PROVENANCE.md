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

2026-10-11 устаревший `configure-tunnel.ps1` (инициализатор с env-key reference) удалён из live `chatgpt-repo-mode` и `runtime/repo-mode`: существующие профили уже используют сохранённый file-key reference. Перед удалением проверены идентичность обеих копий и отсутствие вызовов из активных скриптов; резервная копия live файла сохранена вне Git в `chatgpt-repo-mode/backups/retired-initializer-20261011/`, прежняя Git-версия остаётся в истории. Работающие профили и ключ не менялись (INSTRUCTIONS.md).

Для Site code source-of-truth — его Sites Git; SITES.md фиксирует проверенные project/plugin/version/HEAD. Нет копий временных source credentials, auth files или secret upstream URL.

## Что не переносилось в Git

Runtime key и реальные tunnel YAML profiles, snapshots/ZIP, VHD/ISO, runtime backups, payload logs, Git credentials, node_modules, private upstream endpoints. Snapshot export permissions не менялись. Содержимое других проектов в этот repo не включалось.
