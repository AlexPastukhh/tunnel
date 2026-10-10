# Fortis Repo workspace

Host -> container (read-write):
- C:\Users\alexa\Repos -> /workspace/repos
- C:\Users\alexa\Workfiles -> /workspace/files

/workspace/repo remains the original Docker volume for internal files. Changes in the two host mounts directly change Windows files.

Outgoing internet: enabled via fortis-repo-egress. No ports published. The container runs as uid 1000, with a read-only root filesystem and no Docker socket. Other Windows folders and credentials are not mounted.

Start access with the existing Repo Tunnel shortcut. The repo-mode profile uses the previously saved Windows runtime-key file; no repeated key prompt is required. The runner validates the configured container identity, restores MCP directory restrictions and Git safe.directory entries after container restarts. External website availability is not required for starting access.

Local control: run Fortis-Repo-Control.cmd. Stop access disconnects ChatGPT without deleting files; Stop container stops only the configured Repo container. HOST Desktop Commander is separate.

Internet diagnostic from PowerShell:
& "C:\Tools\desktop-commander-runtime\node.exe" "C:\Users\alexa\chatgpt-repo-mode\probe.mjs" --check-internet

Git credentials are not inherited from Windows; remote authentication must be configured separately before pushing private repos. Existing host linked worktrees outside Repos, including the obs-planning-docs Temp worktrees, are not mounted. Do not prune or rewrite their metadata from Linux solely because Windows paths are inaccessible.

Rollback container (stopped): fortis-repo-test-before-access-20261010t112331268z
Configuration/source backups: C:\Users\alexa\chatgpt-repo-mode\backups\access-20261010T112331268Z
