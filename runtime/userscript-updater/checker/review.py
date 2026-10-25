"""Immutable development review identity; has no approval/authorization power."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from .inventory import Snapshot, digest
from .model import ContractError, Registration, relative_target


def managed_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(relative_target(path) for path in paths)
    if len({p.casefold() for p in normalized}) != len(normalized):
        raise ContractError("Duplicate previously managed paths")
    return tuple(sorted(normalized, key=str.casefold))


def manifest_fingerprint(snapshot: Snapshot) -> str:
    return digest(json.dumps(snapshot.manifest(), sort_keys=True,
                             ensure_ascii=False).encode("utf-8"))


@dataclass(frozen=True)
class ReviewBinding:
    job_id: str
    project_id: str
    registration_sha256: str
    snapshot_id: str
    manifest_sha256: str
    source_files: int
    policy_sha256: str
    tool_fingerprints: tuple[tuple[str, str], ...]
    target_root: str | None
    previously_managed: tuple[str, ...]

    @classmethod
    def capture(cls, project: Registration, snapshot: Snapshot, policy_sha256: str,
                tool_fingerprints: tuple[tuple[str, str], ...],
                previously_managed: tuple[str, ...] = ()) -> "ReviewBinding":
        project.validate()
        if snapshot.registration_sha256 != project.fingerprint():
            raise ContractError("Snapshot refers to different registration")
        if not policy_sha256:
            raise ContractError("Captured policy identity required")
        tools = tuple(sorted(tool_fingerprints))
        if (any(kind not in ("eslint", "semgrep") or not token for kind, token in tools)
                or len({kind for kind, _ in tools}) != len(tools)):
            raise ContractError("Invalid or duplicate tool references")
        earlier = managed_paths(previously_managed)
        if project.target_root is None and earlier:
            raise ContractError("Check-only review cannot manage target paths")
        return cls(str(uuid.uuid4()), project.registration_id, project.fingerprint(),
                   snapshot.snapshot_id, manifest_fingerprint(snapshot), len(snapshot.records),
                   policy_sha256, tools, project.target_root, earlier)

    def validate_snapshot(self, snapshot: Snapshot) -> None:
        if (self.snapshot_id != snapshot.snapshot_id
                or self.registration_sha256 != snapshot.registration_sha256
                or self.manifest_sha256 != manifest_fingerprint(snapshot)
                or self.source_files != len(snapshot.records)):
            raise ContractError("Review binding refers to different snapshot/manifest")
