# ChatGPT Snapshot Transfer — private Bridge transport

**Start here:** [CHATGPT_START_HERE.md](CHATGPT_START_HERE.md)  
**Canonical workflow:** [docs/CHATGPT_BRIDGE_WORKFLOW.md](docs/CHATGPT_BRIDGE_WORKFLOW.md)

Private snapshot-first transport between the Windows local Git working tree, Secure MCP Tunnel, GitHub Actions Artifact and the current ChatGPT filesystem.

**Verified 2026-10-09:** Real `obs-planning-docs` working tree snapshot (1169 files, all per-file SHA-256 verified after download to ChatGPT), and private-transport `test-private` `apply -CheckOnly → apply → already_applied`. Source working-tree Git modifications were not committed or pushed to source remotes.

### Discoverability

Start with the on-Windows `C:\Users\alexa\chatgpt-bridge\Bridge.ps1` commands `guide`, `discover`, `list`. Then `register`, `preview`, `enable`, `snapshot`, `status`, `apply`, or `disable` as needed. See the canonical Russian guide above for usage and safety.

### Privacy and retention

This repository is **private**, but snapshot ZIP files are committed to its Git history, which persists even after Actions Artifacts expire after 7 days. Restrict access and do not make the repository public without auditing full Git history. Existing secret scans are best-effort, not a complete confidentiality audit.

Only the separate transport clone is committed for shipping snapshots; source projects are not committed by Bridge.
