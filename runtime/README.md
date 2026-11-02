# Runtime source copies — current AFTER и исторические BEFORE

Копии не деплоятся автоматически. Repo E38 current AFTER Windows
[run](host-g2/runtime-api-migration/repo-run-tunnel.ps1) и
[control](host-g2/runtime-api-migration/repo-control.ps1).
Старые repo-mode/run-tunnel.ps1 и repo-mode/control.ps1 — BEFORE, не current deployed.
[Bridge source](repo-mode/fortis-mcp-bridge.mjs) совпал hash с live volume в E44,
но source edit не меняет live /workspace/repo/.fortis.
G2 [entry](host-g2/runtime-api-migration/start-g2-guest-session.ps1),
[gate](host-g2/g2-stdio-gate.py), [ACL source](host-g2/protect-shared-runtime.ps1).
Owner HOST retired E43, recovery intentional only. Dockerfile не задаёт actual mounts/flags.
[Итог/source map](../docs/ISOLATION_GUIDE.md).

## Repo1/Repo2 Windows source mirror (paired release)

The byte-exact Windows worker/launcher mirror, pinned manifest, read-only
Preview/Start dispatcher, inventory and release tests live in
[windows-repo/README.md](windows-repo/README.md). Script Center adapters resolve
this source only from the sibling Windows Git clone
`%USERPROFILE%\Repos\tunnel\runtime\windows-repo\current`; they validate
the approved clean `main` clone and all nine SHA-256 values before execution.
Windows Tunnel Client binaries, profiles, keys, ACLs and logs remain local and
are not part of this source mirror. The paired Script Center adapter change
must also be pulled before the new delegation is active on Windows.

## Старый текст README (исторический)

### Датированные копии исходников

Копии действующих source files на 2026-10-10, не новый автоматический installer.

Live Repo: C:\Users\alexa\chatgpt-repo-mode; установленный MCP bridge: /workspace/repo/.fortis/mcp-bridge.mjs.
Live HOST: C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1 и C:\Tools\desktop-commander\desktop-commander-trusted.cmd.

workspace-config.example.json фиксирует существующую machine identity; для другой машины/нового контейнера нельзя переиспользовать ID без inspect и проверки. Dockerfile задаёт базовый image; mounts/network/limits задаются при container create, не самим Dockerfile. Проверенный набор ограничений см. CURRENT_STATE.md и probe.mjs.

Одноразовый `configure-tunnel.ps1` удалён 2026-10-11 из live Repo и этой копии: профили уже зарегистрированы и используют сохранённый ключ. Старый исходник остаётся в истории Git и в локальной резервной копии вне Git. Новую регистрацию проводить отдельно по проверенной процедуре, без перезаписи существующего профиля. См. INSTRUCTIONS.md и ACCESS.md.

После изменения runtime source обязательно синхронизировать нужный live path / volume, проверить, перезапустить только затронутый контур и обновить docs. Credential files не входят в эту папку.
