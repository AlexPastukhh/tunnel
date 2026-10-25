"""Strict adapters for machine-readable ESLint/Semgrep results (no code execution)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .inventory import Snapshot, digest
from .review import ReviewBinding

Status = Literal["STRUCTURAL_CLEAR", "NOT_AUTHORIZED", "FINDINGS", "ERROR", "INCOMPLETE", "UNSUPPORTED"]
SUPPORTED = {"eslint", "semgrep"}


@dataclass(frozen=True)
class Finding:
    path: str
    rule_id: str
    line: int
    column: int
    message: str


@dataclass(frozen=True)
class EngineReport:
    engine: str
    status: Status
    expected: tuple[str, ...]
    scanned: tuple[str, ...]
    findings: int
    detail: str
    issues: tuple[Finding, ...] = ()


@dataclass(frozen=True)
class ScanReport:
    status: Status
    registration_sha256: str
    snapshot_id: str
    policy_sha256: str
    source_files: int
    reports: tuple[EngineReport, ...]
    uncovered: tuple[str, ...]
    binding: ReviewBinding | None = None


def _report_path(name: str, scanner_workdir: Path) -> str:
    """Resolve relative scanner output against its recorded working directory."""
    path = Path(name)
    return str((path if path.is_absolute() else scanner_workdir / path).absolute())


def parse_eslint(stdout: str, exit_code: int, expected: tuple[Path, ...], scanner_workdir: Path) -> EngineReport:
    wanted = tuple(str(path.absolute()) for path in expected)
    try:
        rows = json.loads(stdout)
        if not isinstance(rows, list) or not rows:
            raise ValueError("Missing ESLint JSON rows")
        paths = []
        count = 0
        fatal = False
        issues = []
        for item in rows:
            if not isinstance(item, dict) or not isinstance(item.get("filePath"), str):
                raise ValueError("Missing filePath")
            suppressed = item.get("suppressedMessages", [])
            if not isinstance(suppressed, list):
                raise ValueError("Malformed suppression list")
            messages = item.get("messages")
            if not isinstance(messages, list):
                raise ValueError("Missing messages")
            paths.append(_report_path(item["filePath"], scanner_workdir))
            if any(not isinstance(msg, dict) for msg in messages):
                raise ValueError("Malformed message")
            # Suppressed findings are not proof of a clean scan.
            if suppressed:
                fatal = True
            for msg in messages:
                issues.append(Finding(_report_path(item["filePath"], scanner_workdir),
                    str(msg.get("ruleId") or "parser"), int(msg.get("line") or 0),
                    int(msg.get("column") or 0), str(msg.get("message") or "")))
            count += len(messages)
            fatal |= any(bool(msg.get("fatal")) for msg in messages)
            if item.get("fatalErrorCount", 0):
                fatal = True
        if exit_code not in (0, 1) or fatal:
            status = "ERROR"
        elif len(paths) != len(set(paths)) or set(paths) != set(wanted):
            status = "INCOMPLETE"
        elif count:
            status = "FINDINGS"
        elif exit_code != 0:
            status = "ERROR"
        else:
            status = "STRUCTURAL_CLEAR"
        return EngineReport("eslint", status, wanted, tuple(paths), count,
                            f"exit={exit_code}; messages={count}", tuple(issues))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return EngineReport("eslint", "ERROR", wanted, (), 0, f"Invalid JSON: {exc}")


def parse_semgrep(stdout: str, exit_code: int, expected: tuple[Path, ...], scanner_workdir: Path) -> EngineReport:
    wanted = tuple(str(path.absolute()) for path in expected)
    try:
        result = json.loads(stdout)
        if not isinstance(result, dict):
            raise ValueError("Missing Semgrep result object")
        paths = result.get("paths")
        if not isinstance(paths, dict):
            raise ValueError("Missing targeting information")
        scanned = paths.get("scanned")
        skipped = paths.get("skipped", [])  # Optional in the published output schema.
        findings = result.get("results")
        errors = result.get("errors")
        skipped_rules = result.get("skipped_rules", [])
        if (not isinstance(scanned, list) or not isinstance(skipped, list)
                or not isinstance(findings, list) or not isinstance(errors, list)
                or not isinstance(skipped_rules, list)):
            raise ValueError("Incomplete Semgrep JSON schema")
        if any(not isinstance(path, str) for path in scanned) or any(not isinstance(item, dict) for item in skipped):
            raise ValueError("Unexpected scanned path type")
        issues = []
        for finding in findings:
            if not isinstance(finding, dict):
                raise ValueError("Malformed Semgrep finding")
            start = finding.get("start", {})
            extra = finding.get("extra", {})
            path = finding.get("path")
            if not isinstance(start, dict) or not isinstance(extra, dict):
                raise ValueError("Malformed Semgrep finding metadata")
            issues.append(Finding(_report_path(path, scanner_workdir) if isinstance(path, str) else "",
                str(finding.get("check_id") or "unknown"), int(start.get("line") or 0),
                int(start.get("col") or 0), str(extra.get("message") or "")))
        visited = tuple(_report_path(path, scanner_workdir) for path in scanned)
        if exit_code not in (0, 1) or errors:
            status = "ERROR"
        elif skipped or skipped_rules or len(visited) != len(set(visited)) or set(visited) != set(wanted):
            status = "INCOMPLETE"
        elif findings:
            status = "FINDINGS"
        elif exit_code != 0:
            status = "ERROR"
        else:
            status = "STRUCTURAL_CLEAR"
        return EngineReport("semgrep", status, wanted, visited, len(findings),
                            f"exit={exit_code}; results={len(findings)}; errors={len(errors)}; skipped={len(skipped)}; skipped_rules={len(skipped_rules)}", tuple(issues))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return EngineReport("semgrep", "ERROR", wanted, (), 0, f"Invalid JSON: {exc}")


def summarize(snapshot: Snapshot, policy_sha256: str,
              reports: tuple[EngineReport, ...], *,
              binding: ReviewBinding | None = None) -> ScanReport:
    """PASS needs full manifest covered and no analyzer problems."""
    if binding is not None:
        binding.validate_snapshot(snapshot)
        if binding.policy_sha256 != policy_sha256:
            raise ValueError("Report policy differs from review binding")
    expected = {str((snapshot.root / item.snapshot_relative).absolute()) for item in snapshot.records}
    covered = set()
    damaged = []
    for item in snapshot.records:
        path = snapshot.root / item.snapshot_relative
        if not path.is_file() or digest(path.read_bytes()) != item.sha256:
            damaged.append(str(path))
    invalid_reports = []
    for report in reports:
        if report.engine not in SUPPORTED or not set(report.expected).issubset(expected):
            invalid_reports.append(report.engine)
        elif (report.status in ("STRUCTURAL_CLEAR", "FINDINGS")
              and (set(report.scanned) != set(report.expected)
                   or len(report.scanned) != len(set(report.scanned)))):
            invalid_reports.append(report.engine)
        covered.update(report.expected)
    uncovered = tuple(sorted(expected - covered))
    if damaged or invalid_reports or any(r.status == "ERROR" for r in reports) or not policy_sha256:
        status = "ERROR"
    elif uncovered or not reports or any(r.status in ("UNSUPPORTED", "INCOMPLETE") for r in reports):
        status = "INCOMPLETE" if reports else "UNSUPPORTED"
    elif any(r.status == "FINDINGS" for r in reports):
        status = "FINDINGS"
    else:
        # Parser output alone is not evidence of an approved installed scanner.
        status = "NOT_AUTHORIZED"
    return ScanReport(status, snapshot.registration_sha256, snapshot.snapshot_id,
                      policy_sha256, len(expected), reports, uncovered, binding)
