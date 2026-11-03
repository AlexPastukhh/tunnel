# Runtime source map

`runtime/` contains source, candidates and historical snapshots; changing a file here does not install it into Windows or alter a running Docker container. Current installed/runtime facts must be checked independently.

## Current Repo1/Repo2 Windows worker source

- The canonical worker chain, shared Guard policy, manifest, dispatcher and offline tests are in [windows-repo/README.md](windows-repo/README.md).
- Shared policy: `windows-repo/current/launchers/shared/FortisContainerPolicy.ps1`.
- Repo1-specific behavior: `windows-repo/current/launchers/chatgpt-repo-mode/`.
- Repo2-specific Guard/quiet launcher: `windows-repo/current/launchers/FortisRepoPlus2/`; orchestration: `windows-repo/current/launchers/FortisRDGLauncherV2/`.
- `tunnel` owns these workers and Guards. `script-control-center` owns the UI, thin adapters, resolver and paired Windows updater; it does not own a second active copy of the Guard policy.
- Windows profiles, keys, ACLs, logs, shortcuts and Tunnel Client binaries remain Windows-local and are not source files.

See [Guard review before Docker/worker restart](../docs/FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md) for the trigger checklist. See [Script Center's Windows update runbook](https://github.com/AlexPastukhh/script-control-center/blob/main/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md) for the paired Windows pull/Preview/Apply procedure.

## Other runtime areas

- G2 guest entry and supporting source: [host-g2](host-g2/); G2/old HOST notes are historical and must not be treated as the current Repo1/Repo2 launcher chain.
- Snapshot Broker: [source/runbook](broker/README.md).

## Исторический текст README

Следующий блок сохранён для происхождения и прежних этапов. Его пути E38, Bridge, G2 и статусы на 2026-10-10 не являются инструкцией для текущей Repo1/Repo2 Windows worker chain.

## Старый текст README (исторический)

### Датированные копии исходников

Копии действующих source files на 2026-10-10, не новый автоматический installer.

Live Repo: C:\Users\alexa\chatgpt-repo-mode; установленный MCP bridge: /workspace/repo/.fortis/mcp-bridge.mjs.
Live HOST: C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1 и C:\Tools\desktop-commander\desktop-commander-trusted.cmd.

workspace-config.example.json фиксирует существующую machine identity; для другой машины/нового контейнера нельзя переиспользовать ID без inspect и проверки. Dockerfile задаёт базовый image; mounts/network/limits задаются при container create, не самим Dockerfile. Проверенный набор ограничений см. CURRENT_STATE.md и probe.mjs.

Одноразовый `configure-tunnel.ps1` удалён 2026-10-11 из live Repo и этой копии: профили уже зарегистрированы и используют сохранённый ключ. Старый исходник остаётся в истории Git и в локальной резервной копии вне Git. Новую регистрацию проводить отдельно по проверенной процедуре, без перезаписи существующего профиля. См. INSTRUCTIONS.md и ACCESS.md.

После изменения runtime source обязательно синхронизировать нужный live path / volume, проверить, перезапустить только затронутый контур и обновить docs. Credential files не входят в эту папку.
