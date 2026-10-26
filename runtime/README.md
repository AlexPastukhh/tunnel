# Runtime source map

`runtime/` содержит исходники-копии; изменение Git source не обновляет Windows, Docker volume или Site автоматически. Доставку и факт установки различать по [INSTRUCTIONS](../docs/INSTRUCTIONS.md); installed paths/fingerprints Repo принадлежат [security-реестру](../docs/agent-workflow/TUNNEL_SECURITY_ISOLATION.md).

| Компонент | Source / владелец |
| --- | --- |
| Repo1 Direct launcher PR-A-15 | [two-profile/reboot candidate](host-g2/runtime-api-migration/repo-run-tunnel-two-profile-reboot.candidate.ps1); статус установки — security V-07 |
| Repo1 quiet-log canary PR-A-17 | [отдельный launcher](host-g2/runtime-api-migration/repo-run-tunnel-quiet-logs.candidate.ps1), [читаемый preload](repo-mode/quiet-log-preload.mjs), [тесты](repo-mode/test-quiet-log-preload.mjs); owner Repo1 canary smoke PASS(scope), default Preview, [приёмка/owner-план](../docs/agent-workflow/reviews/repo-tunnel-outage-20261026.md#проверочный-вариант-pr-a-17-source-only) |
| Repo1 control | [control source](host-g2/runtime-api-migration/repo-control.ps1) |
| Repo2 Direct guard | [guard candidate](host-g2/runtime-api-migration/repo2-direct-guard.candidate.ps1); launcher/installed evidence — security V-08 |
| Repo2 quiet preparer WF-060 (SOURCE ONLY) | [side-by-side preparer](host-g2/runtime-api-migration/repo2-quiet-preparer.candidate.ps1) default Preview; original Windows launcher/guard unchanged; [review](../docs/agent-workflow/reviews/repo-tunnel-outage-20261026.md#wf-060-repo2-quiet-preparer-source-only); Windows parser/Preview/Stage/Run NOT_RUN |
| G2 | [guest entry](host-g2/runtime-api-migration/start-g2-guest-session.ps1), [gate](host-g2/g2-stdio-gate.py), [G2 plan](../docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) |
| Project Checker | [source README](userscript-updater/README.md) |
| Broker | [runbook](broker/README.md) |

E38 `repo-run-tunnel.ps1`, старые `repo-mode/run/control`, Bridge и `probe.mjs` — предыдущие этапы; не считать их текущей Direct цепочкой и не запускать как fallback. Dockerfile/source config не доказывают actual mounts/flags. Ни один source-файл сам по себе не разрешает Windows install/restart.

## Старый текст README (исторический)

### Датированные копии исходников

Копии действующих source files на 2026-10-10, не новый автоматический installer.

Live Repo: C:\Users\alexa\chatgpt-repo-mode; установленный MCP bridge: /workspace/repo/.fortis/mcp-bridge.mjs.
Live HOST: C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1 и C:\Tools\desktop-commander\desktop-commander-trusted.cmd.

workspace-config.example.json фиксирует существующую machine identity; для другой машины/нового контейнера нельзя переиспользовать ID без inspect и проверки. Dockerfile задаёт базовый image; mounts/network/limits задаются при container create, не самим Dockerfile. Проверенный набор ограничений см. CURRENT_STATE.md и probe.mjs.

Одноразовый `configure-tunnel.ps1` удалён 2026-10-11 из live Repo и этой копии: профили уже зарегистрированы и используют сохранённый ключ. Старый исходник остаётся в истории Git и в локальной резервной копии вне Git. Новую регистрацию проводить отдельно по проверенной процедуре, без перезаписи существующего профиля. См. INSTRUCTIONS.md и ACCESS.md.

После изменения runtime source обязательно синхронизировать нужный live path / volume, проверить, перезапустить только затронутый контур и обновить docs. Credential files не входят в эту папку.
