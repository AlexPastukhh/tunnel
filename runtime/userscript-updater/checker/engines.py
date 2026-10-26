"""Development CLI runner: fixed argv, optional job control; never authorizes promotion."""
from __future__ import annotations

import os
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .inventory import Snapshot, digest
from .reports import EngineReport, parse_eslint, parse_semgrep
from .processes import execute, RunControl


@dataclass(frozen=True)
class EngineConfig:
    kind: str
    executable: Path
    executable_sha256: str
    config: Path
    config_sha256: str
    node: Path | None = None

    def fingerprint(self) -> str:
        self.validate()
        return digest(json.dumps([self.kind, str(self.executable), self.executable_sha256,
            str(self.config), self.config_sha256, str(self.node),
            digest(self.node.read_bytes()) if self.node else None]).encode())

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


def build_argv(config: EngineConfig, files: tuple[Path, ...], *,
               diagnostics: bool = False) -> list[str]:
    """No shell and no flags or candidate paths from project configuration."""
    if config.kind == "eslint":
        return [
            str(config.node), str(config.executable), "--no-config-lookup",
            "--no-inline-config", "--no-ignore", "--format", "json",
            "--config", str(config.config), "--", *(str(file) for file in files),
        ]
    if config.kind == "semgrep":
        # Only safe, owner-run setup diagnostics print fixed startup labels.
        # Never expose scanned source/command/environment in these markers.
        script = ("import os,sys; from pathlib import Path; "
                  "_dll=os.add_dll_directory(str(Path(sys.executable).parent.parent/'pydeps/pywin32_system32')) if os.name=='nt' else None; "
                  + ("sys.stderr.write('checker-semgrep:import_start\\n'); sys.stderr.flush(); "
                     if diagnostics else "")
                  + "from semgrep.console_scripts.entrypoint import main; "
                  + ("sys.stderr.write('checker-semgrep:cli_start\\n'); sys.stderr.flush(); "
                     if diagnostics else "")
                  + "sys.argv[0]='semgrep'; main()")
        prefix = ([str(config.executable), "-I", "-S", "-B", "-c", script]
                  if config.executable.name.casefold() in ("python.exe", "pythonw.exe")
                  else [str(config.executable)])
        return [
            # Select the pinned Python CLI explicitly; its default native frontend
            # may re-enter Python through external launchers on Windows.
            *prefix, "scan", "--legacy", "--jobs=1", "--config", str(config.config),
            "--json", "--error", "--strict", "--metrics=off", "--no-git-ignore",
            "--disable-nosem", "--disable-version-check", "--no-autofix",
            "--oss-only", "--max-target-bytes=0", "--",
            *(str(file) for file in files),
        ]
    raise ValueError("Unknown engine")


MAX_ARG_CHARS = 24000  # Below CreateProcessW's UTF-16 command-line limit, including quoting.


def command_batches(config, files):
    batches, current = [], []
    for path in files:
        proposed = (*current, path)
        units = len(subprocess.list2cmdline(build_argv(config, proposed)).encode("utf-16-le")) // 2
        if units > MAX_ARG_CHARS:
            if not current:
                raise ValueError("One analyzer command exceeds the explicit argument limit")
            batches.append(tuple(current))
            current = [path]
            if len(subprocess.list2cmdline(build_argv(config, tuple(current))).encode("utf-16-le")) // 2 > MAX_ARG_CHARS:
                raise ValueError("One analyzer path exceeds the argument limit")
        else:
            current.append(path)
    if current:
        batches.append(tuple(current))
    return tuple(batches)


def run_dev_engine(snapshot: Snapshot, config: EngineConfig, *, timeout: int = 30,
                   required_rules: tuple[str, ...] = (), control: RunControl | None = None,
                   validation=None, evidence_dir: Path | None = None,
                   temporary_parent: Path | None = None) -> EngineReport:
    """Development Check only; no protected dependency closure/Windows ACL authority."""
    extensions = {".js", ".mjs", ".cjs"} if config.kind == "eslint" else {".js", ".mjs", ".cjs", ".py"}
    requested = tuple(
        snapshot.root / record.snapshot_relative
        for record in snapshot.records if record.content in ("code", "dependency") and Path(record.source_path).suffix.lower() in extensions
    )
    if not requested:
        return EngineReport(config.kind, "UNSUPPORTED", (), (), 0, "No applicable files")
    try:
        config.validate()
        from .policy_validation import validate_engine_config
        validation = validation or validate_engine_config(config, required_rules=required_rules,
                                                           timeout=timeout, control=control,
                                                           temporary_parent=temporary_parent)
        if (validation.status != "VALIDATED_DEVELOPMENT"
                or validation.tool_fingerprint != config.fingerprint()
                or set(required_rules) - set(validation.effective_rules)):
            raise ValueError(f"Effective policy validation failed: {validation.detail}")
        for record in snapshot.records:
            path = snapshot.root / record.snapshot_relative
            if not path.is_file() or digest(path.read_bytes()) != record.sha256:
                raise ValueError("Snapshot changed after capture")
        from .environment import analyzer_environment
        env = analyzer_environment(snapshot.root, config)
        batches = command_batches(config, requested)
        results = []
        parser = parse_eslint if config.kind == "eslint" else parse_semgrep
        for index, batch in enumerate(batches):
            process = execute(
                build_argv(config, batch), shell=False, cwd=snapshot.root,
                capture_output=True, text=True, errors="replace",
                timeout=timeout, env=env, check=False, control=control,
                temporary_parent=temporary_parent,
            )
            if evidence_dir is not None:
                evidence_dir.mkdir(parents=True, exist_ok=True)
                stem = config.kind if len(batches) == 1 else f"{config.kind}-{index:04d}"
                (evidence_dir / (stem + ".json")).write_text(process.stdout, encoding="utf-8")
                (evidence_dir / (stem + ".stderr.txt")).write_text(process.stderr, encoding="utf-8")
            results.append(parser(process.stdout, process.returncode, batch, snapshot.root))
        if len(results) == 1:
            result = results[0]
        else:
            status = next((state for state in ("ERROR", "INCOMPLETE", "UNSUPPORTED", "FINDINGS")
                           if any(report.status == state for report in results)), "STRUCTURAL_CLEAR")
            result = EngineReport(config.kind, status,
                tuple(p for report in results for p in report.expected),
                tuple(p for report in results for p in report.scanned),
                sum(report.findings for report in results),
                f"batches={len(results)}; " + "; ".join(report.detail for report in results),
                tuple(issue for report in results for issue in report.issues))
            if evidence_dir is not None:
                (evidence_dir / (config.kind + "-batches.json")).write_text(json.dumps({
                    "batches": [[str(p) for p in batch] for batch in batches],
                    "status": result.status}, ensure_ascii=False, indent=2), encoding="utf-8")
        # File input is checked again; changed scanner input invalidates the evidence.
        for record in snapshot.records:
            path = snapshot.root / record.snapshot_relative
            if not path.is_file() or digest(path.read_bytes()) != record.sha256:
                raise ValueError("Snapshot changed during scan")
        if config.fingerprint() != validation.tool_fingerprint:
            raise ValueError("Tool/config changed during scan")
        return result
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return EngineReport(config.kind, "ERROR", tuple(str(path) for path in requested), (),
                            0, f"CLI execution/verification failed: {type(exc).__name__}: {exc}")
