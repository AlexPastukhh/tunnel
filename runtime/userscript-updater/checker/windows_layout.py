"""Windows deployment boundary *planning* checker; never a security authorization.

It treats all strings (including alleged final paths) as UNTRUSTED input.
Native Windows CreateFile/OpenFileById, reparse/NTFS ACL and process write-route
checks MUST be independently performed after owner manual install.
"""
from __future__ import annotations

import ntpath
import re
from dataclasses import dataclass

from .model import ContractError

ROLES = {"app", "tools", "policies", "state", "approved", "source", "agent_write"}
TRUSTED = {"app", "tools", "policies", "state", "approved"}
DRIVE = re.compile(r"(?i)^[a-z]:[\\/]")
WINDOWS_DEVICE = re.compile(r"(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:[.].*)?$")


def normalize_windows_path(value: str) -> str:
    """Structural-only normalisation; does NOT resolve junctions or hardlinks."""
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ContractError("Missing or invalid Windows path")
    # We require ordinary DOS absolute drive paths. UNC, extended-length device
    # paths, NT device/namespace and environment-variable placeholders are refused
    # until separately supported by a native Windows handle-check implementation.
    if (not DRIVE.match(value) or value.startswith(("\\\\", "//")) or
            "%" in value or "$" in value or any(ord(c) < 32 for c in value)):
        raise ContractError("Only literal absolute drive Windows paths supported")
    path = value.replace("/", "\\")
    segments = path[3:].split("\\")
    if any(not part or part in (".", "..") or part.endswith((".", " "))
           or ":" in part or "/" in part or WINDOWS_DEVICE.fullmatch(part)
           for part in segments):
        raise ContractError("Ambiguous Windows path component")
    if segments == [""]:
        # Current production design intentionally disallows volume roots.
        raise ContractError("Volume root cannot be a runtime directory")
    collapsed = ntpath.normcase(ntpath.normpath(path))
    if not ntpath.isabs(collapsed) or not DRIVE.match(collapsed):
        raise ContractError("Not an absolute Windows drive path")
    if collapsed.endswith("\\"):
        raise ContractError("Volume root cannot be a runtime directory")
    return collapsed


def overlapping(first: str, second: str) -> bool:
    first, second = normalize_windows_path(first), normalize_windows_path(second)
    return first == second or first.startswith(second + "\\") or second.startswith(first + "\\")


@dataclass(frozen=True)
class RootSpec:
    role: str
    path: str


@dataclass(frozen=True)
class BoundaryFinding:
    severity: str
    code: str
    details: str


@dataclass(frozen=True)
class BoundaryReview:
    """No READY/PASS state exists: even collision-free paths need host checks."""
    status: str
    findings: tuple[BoundaryFinding, ...]
    trusted_roots: tuple[str, ...]
    source_roots: tuple[str, ...]


def review_windows_layout(roots: tuple[RootSpec, ...]) -> BoundaryReview:
    """Reject obvious unsafe placements before commissioning manual Windows tests.

    Does NOT make installer usable, and does not accept fabricated attestation
    from the user project or an AI-managed JSON file.
    """
    findings: list[BoundaryFinding] = []
    trusted: list[tuple[str, str]] = []
    sources: list[str] = []
    agents: list[str] = []
    by_role: dict[str, list[str]] = {}
    for root in roots:
        if root.role not in ROLES:
            findings.append(BoundaryFinding("BLOCK", "UNKNOWN_ROLE", root.role))
            continue
        try:
            path = normalize_windows_path(root.path)
        except ContractError as exc:
            findings.append(BoundaryFinding("BLOCK", "INVALID_PATH",
                                            f"{root.role}: {exc}"))
            continue
        by_role.setdefault(root.role, []).append(path)
        if root.role in TRUSTED:
            trusted.append((root.role, path))
        elif root.role == "source":
            sources.append(path)
        else:
            agents.append(path)
    for required in ("app", "tools", "policies", "state", "approved", "source", "agent_write"):
        if not by_role.get(required):
            findings.append(BoundaryFinding("BLOCK", "MISSING_ROOT",
                                            f"Missing {required} root"))
    if any(len(by_role.get(single, ())) != 1 for single in ("app", "tools", "policies", "state")):
        findings.append(BoundaryFinding("BLOCK", "ROOT_CARDINALITY",
                                        "One root required for app/tools/policies/state"))
    for role, trusted_path in trusted:
        for writable in agents:
            if overlapping(trusted_path, writable):
                findings.append(BoundaryFinding(
                    "BLOCK", "AGENT_WRITE_OVERLAP",
                    f"{role}={trusted_path} overlaps agent-write root {writable}"
                ))
        for source in sources:
            if overlapping(trusted_path, source):
                findings.append(BoundaryFinding(
                    "BLOCK", "SOURCE_TRUSTED_OVERLAP",
                    f"{role}={trusted_path} overlaps source {source}"
                ))
    # Approved copies are not installation executables or policy/state dirs.
    # A trusted app may keep tools/policies/state in distinct subfolders, but
    # consuming an approved copy inside those protected roots is disallowed.
    for role, path in trusted:
        if role == "approved":
            for other_role, other_path in trusted:
                if other_role != "approved" and overlapping(path, other_path):
                    findings.append(BoundaryFinding(
                        "BLOCK", "APPROVED_INSTALL_OVERLAP",
                        f"approved={path} overlaps {other_role}={other_path}"
                    ))
    if not findings:
        findings.append(BoundaryFinding(
            "GATE", "WINDOWS_HANDLE_ACL_EVIDENCE_REQUIRED",
            "Text paths do not prove final kernel paths, NTFS ACLs, junction/reparse, "
            "hardlink, imports/dependencies or denial of agent write routes."
        ))
    return BoundaryReview(
        "BLOCKED" if any(f.severity == "BLOCK" for f in findings)
        else "NEEDS_NATIVE_WINDOWS_VERIFICATION",
        tuple(findings), tuple(path for _, path in trusted), tuple(sources)
    )
