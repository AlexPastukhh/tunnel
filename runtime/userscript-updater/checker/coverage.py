"""Per-file scanner accounting for the future review UI.

A coverage matrix describes *reported* processing. It never authorizes
promotion or proves that a rule set is semantically sufficient. Required engine
mappings must ultimately be generated from independently trusted policies.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .inventory import Snapshot
from .reports import EngineReport, Status, SUPPORTED


@dataclass(frozen=True)
class FileCoverage:
    source_path: str
    target_relative: str | None
    snapshot_relative: str
    required_engines: tuple[str, ...]
    scanned_by: tuple[str, ...]
    status: Status
    reason: str


@dataclass(frozen=True)
class CoverageMatrix:
    status: Status
    files: tuple[FileCoverage, ...]
    unexpected_scanned: tuple[str, ...]


def _aggregate(states: list[Status]) -> Status:
    for error in ("ERROR", "INCOMPLETE", "UNSUPPORTED", "FINDINGS"):
        if error in states:
            return error  # type: ignore[return-value]
    # Complete scanner accounting is NOT a trusted installation decision.
    return "NOT_AUTHORIZED"


def build_coverage_matrix(
    snapshot: Snapshot,
    reports: tuple[EngineReport, ...],
    required_for_suffix: dict[str, tuple[str, ...]],
) -> CoverageMatrix:
    """Every selected file must have independent expected analyzer(s).

    In the installed version, required_for_suffix must be derived from validated,
    user-controlled pack applicability, not supplied by the candidate project.
    """
    report_by_engine: dict[str, EngineReport] = {}
    duplicates = set()
    for report in reports:
        if report.engine in report_by_engine:
            duplicates.add(report.engine)
        report_by_engine[report.engine] = report

    expected_paths = {
        str((snapshot.root / record.snapshot_relative).absolute()) for record in snapshot.records
    }
    extra = set()
    for report in reports:
        extra.update(set(report.scanned) - expected_paths)

    rows = []
    for record in snapshot.records:
        suffix = Path(record.source_path).suffix.lower()
        needed = required_for_suffix.get(suffix, ())
        filename = str((snapshot.root / record.snapshot_relative).absolute())
        scanned_by = tuple(sorted(
            report.engine for report in reports if filename in report.scanned
        ))
        states: list[Status] = []
        reason = []
        if not needed:
            states.append("UNSUPPORTED")
            reason.append("No trusted analyzer applicability declared for this file suffix")
        for engine in needed:
            if engine not in SUPPORTED or engine in duplicates:
                states.append("ERROR")
                reason.append(f"Unknown/duplicate required engine: {engine}")
            elif engine not in report_by_engine:
                states.append("INCOMPLETE")
                reason.append(f"Missing required scanner report: {engine}")
            else:
                report = report_by_engine[engine]
                if report.status == "ERROR":
                    states.append("ERROR")
                    reason.append(f"Scanner failed: {engine}")
                elif report.status in ("UNSUPPORTED", "INCOMPLETE"):
                    states.append("INCOMPLETE")
                    reason.append(f"Scanner incomplete: {engine}")
                elif filename not in report.expected or filename not in report.scanned:
                    states.append("INCOMPLETE")
                    reason.append(f"File not accounted for: {engine}")
                elif report.status == "FINDINGS":
                    precise = bool(report.issues) and all(issue.path in report.scanned for issue in report.issues)
                    if not precise or any(issue.path == filename for issue in report.issues):
                        states.append("FINDINGS")
                        reason.append(f"Scanner reported findings: {engine}")
                    else:
                        states.append("NOT_AUTHORIZED")
                elif report.status == "STRUCTURAL_CLEAR":
                    states.append("NOT_AUTHORIZED")
                else:
                    states.append("ERROR")
                    reason.append(f"Unexpected status: {engine}")
        if extra:
            states.append("ERROR")
            reason.append("At least one scanner reported a file outside the snapshot")
        status = _aggregate(states)
        rows.append(FileCoverage(record.source_path, record.target_relative,
                                 record.snapshot_relative, needed, scanned_by,
                                 status, "; ".join(reason)))
    final_status = _aggregate([row.status for row in rows])
    if duplicates or extra or not rows:
        final_status = "ERROR"
    return CoverageMatrix(final_status, tuple(rows), tuple(sorted(extra)))
