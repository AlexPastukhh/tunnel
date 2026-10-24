"""Demo CLI invocation: fixed argv; parses real JSON but cannot authorize promotion."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .inventory import Snapshot, digest
from .reports import EngineReport, parse_eslint, parse_semgrep


@dataclass(frozen=True)
class EngineConfig:
    kind: str
    executable: Path
    executable_sha256: str
    config: Path
    config_sha256: str
    node: Path | None = None

    def validate(self) -> None:
        if self.kind not in ("eslint", "semgrep"):
            raise ValueError("Unsupported engine")
        for target, expected in ((self.executable, self.executable_sha256),
                                 (self.config, self.config_sha256)):
            if not target.is_absolute() or not target.is_file():
                raise ValueError("Pinned tool/config file missing")
            if digest(target.read_bytes()) != expected:
                raise ValueError("Tool/config bytes differ from specified pin")
        if self.kind == "eslint" and (self.node is None or not self.node.is_absolute() or not self.node.is_file()):
            raise ValueError("Absolute Node executable is required")


def build_argv(config: EngineConfig, files: tuple[Path, ...]) -> list[str]:
    """No shell and no flags or candidate paths from project configuration."""
    if config.kind == "eslint":
        return [
            str(config.node), str(config.executable), "--no-config-lookup",
            "--no-inline-config", "--no-ignore", "--format", "json",
            "--config", str(config.config), "--", *(str(file) for file in files),
        ]
    if config.kind == "semgrep":
        return [
            str(config.executable), "scan", "--config", str(config.config),
            "--json", "--error", "--strict", "--metrics=off", "--no-git-ignore",
            "--disable-nosem", "--disable-version-check", "--no-autofix",
            "--oss-only", "--max-target-bytes=0", "--",
            *(str(file) for file in files),
        ]
    raise ValueError("Unknown engine")


def run_dev_engine(snapshot: Snapshot, config: EngineConfig, *, timeout: int = 30) -> EngineReport:
    """Tests ONLY. Not a trusted launcher, no dependency closure/Windows ACL validation."""
    extensions = {".js", ".mjs", ".cjs"} if config.kind == "eslint" else {".js", ".mjs", ".cjs", ".py"}
    requested = tuple(
        snapshot.root / record.snapshot_relative
        for record in snapshot.records if Path(record.source_path).suffix.lower() in extensions
    )
    if not requested:
        return EngineReport(config.kind, "UNSUPPORTED", (), (), 0, "No applicable files")
    try:
        config.validate()
        for record in snapshot.records:
            path = snapshot.root / record.snapshot_relative
            if not path.is_file() or digest(path.read_bytes()) != record.sha256:
                raise ValueError("Snapshot changed after capture")
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LC_ALL": "C.UTF-8",
            "NODE_OPTIONS": "",
            "SEMGREP_SEND_METRICS": "off",
            "SEMGREP_ENABLE_VERSION_CHECK": "false",
            "HOME": str(snapshot.root), # prototype only; installed tool needs separate trusted state
        }
        process = subprocess.run(
            build_argv(config, requested), shell=False, cwd=snapshot.root,
            capture_output=True, text=True, errors="replace",
            timeout=timeout, env=env, check=False,
        )
        parser = parse_eslint if config.kind == "eslint" else parse_semgrep
        result = parser(process.stdout, process.returncode, requested, snapshot.root)
        # File input is checked again; changed scanner input invalidates the evidence.
        for record in snapshot.records:
            path = snapshot.root / record.snapshot_relative
            if not path.is_file() or digest(path.read_bytes()) != record.sha256:
                raise ValueError("Snapshot changed during scan")
        return result
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return EngineReport(config.kind, "ERROR", tuple(str(path) for path in requested), (),
                            0, f"CLI execution/verification failed: {type(exc).__name__}: {exc}")
