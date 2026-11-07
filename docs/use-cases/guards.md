# Windows guards

## UC-TUN-001

**Когда:** меняется Source/Mirror, Repo1/Repo2 worker или требуется Guard Preview.

**Цель:** сохранить точные ACL/mount/source/provenance границы worker.

**Как:** прочитать [runtime/windows-repo](../../runtime/windows-repo/README.md),
[Guard operations](../FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md)
и выполнить read-only сверку фактического runtime. [CURRENT_STATE](../CURRENT_STATE.md)
сохраняет исторический срез, не текущий Guard verdict. Проверить exact owner-approved
manifest/Windows clone; source update не равен live reconnect. Общие GitHub
эффекты — только по UC-CONT-003. Не переписывать девять pinned manifest SHA в UC.

**Готово:** exact owner readback подтверждён или чёткий STOP; исторический
Guard audit не выдан за текущий.
