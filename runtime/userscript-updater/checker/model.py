"""Source registrations and serializable policy bindings (candidate schema v1)."""
from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath


class ContractError(ValueError):
    pass


def relative_target(raw: str) -> str:
    """Target mapping is relative to separately approved destination root."""
    if not isinstance(raw, str) or not raw or "\\" in raw or "\0" in raw:
        raise ContractError("Target mapping must be a nonempty POSIX relative path")
    parts = raw.split("/")
    if any(not part or part.endswith((".", " ")) or any(ord(ch) < 32 for ch in part) for part in parts):
        raise ContractError("Empty, trailing-dot/space or control-code target component")
    if any(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:[.].*)?", part) for part in parts):
        raise ContractError("Windows device name not allowed in target")
    p = PurePosixPath(raw)
    if p.is_absolute() or any(part in (".", "..") for part in raw.split("/")):
        raise ContractError(f"Unsafe target path: {raw}")
    if any(ch in raw for ch in ':*?"<>|') or raw.startswith("//"):
        raise ContractError(f"Unsafe target path: {raw}")
    return p.as_posix()


@dataclass(frozen=True)
class Selection:
    """File maps to a file; directory maps to a destination subdirectory."""
    kind: str
    source: str
    target: str | None = None
    content: str = "code"
    excluded_paths: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.kind not in ("file", "directory"):
            raise ContractError(f"Unknown selection kind: {self.kind}")
        if not isinstance(self.source, str) or ".." in self.source.replace("\\", "/").split("/") or not Path(self.source).is_absolute():
            raise ContractError("Source must be an absolute path")
        if self.content not in ("code", "dependency", "resource", "data"):
            raise ContractError("Unknown content classification")
        if (not isinstance(self.excluded_paths, tuple) or any(not isinstance(p, str) for p in self.excluded_paths)
                or (self.excluded_paths and self.kind != "directory")
                or len(set(self.excluded_paths)) != len(self.excluded_paths)):
            raise ContractError("Exclusions must be unique directory-relative paths")
        for excluded in self.excluded_paths:
            relative_target(excluded)
        if self.target is not None:
            relative_target(self.target)


@dataclass(frozen=True)
class Registration:
    registration_id: str
    name: str
    selections: tuple[Selection, ...]
    policy_pack_ids: tuple[str, ...]
    target_root: str | None = None

    def validate(self) -> None:
        if not isinstance(self.registration_id, str) or not self.registration_id or not isinstance(self.name, str) or not self.name.strip():
            raise ContractError("ID and name required")
        if not self.selections or not self.policy_pack_ids or any(not isinstance(x, str) or not x for x in self.policy_pack_ids):
            raise ContractError("At least one selection and policy pack required")
        if len(self.policy_pack_ids) != len(set(self.policy_pack_ids)):
            raise ContractError("Duplicate policy pack ID")
        for entry in self.selections:
            entry.validate()
        sources = [entry.source for entry in self.selections]
        if len(sources) != len(set(sources)):
            raise ContractError("Duplicate sources")
        if self.target_root is not None:
            if not isinstance(self.target_root, str) or ".." in self.target_root.replace("\\", "/").split("/") or not Path(self.target_root).is_absolute():
                raise ContractError("Target root must be absolute")
            if any(sel.target is None for sel in self.selections):
                raise ContractError("Every target mapping required when promotion enabled")
        elif any(sel.target is not None for sel in self.selections):
            raise ContractError("Check-only registration must not specify targets")

    def to_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, indent=2)

    def fingerprint(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, text: str) -> "Registration":
        value = json.loads(text)
        if set(value) != {"registration_id", "name", "selections", "policy_pack_ids", "target_root"}:
            raise ContractError("Unexpected registration schema")
        if not isinstance(value["selections"], list) or any(
            not isinstance(item, dict) or not {"kind", "source", "target"} <= set(item)
            or set(item) - {"kind", "source", "target", "content", "excluded_paths"}
            or ("excluded_paths" in item and not isinstance(item["excluded_paths"], list))
            for item in value["selections"]
        ):
            raise ContractError("Unexpected selection schema")
        if not isinstance(value["policy_pack_ids"], list):
            raise ContractError("Policy pack IDs must be a list")
        registration = cls(
            registration_id=value["registration_id"], name=value["name"],
            selections=tuple(Selection(**{**s, "excluded_paths": tuple(s.get("excluded_paths", ()))})
                             for s in value["selections"]),
            policy_pack_ids=tuple(value["policy_pack_ids"]),
            target_root=value["target_root"],
        )
        registration.validate()
        return registration
