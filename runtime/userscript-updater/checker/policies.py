"""Mutable, shareable *candidate* rule packs. Storage is not protected inside Repo."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .model import ContractError, Registration

PACK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


@dataclass(frozen=True)
class PolicyPack:
    pack_id: str
    name: str
    eslint_core_rules: dict[str, str]
    semgrep_rules_text: str = ""

    def validate(self) -> None:
        if not isinstance(self.pack_id, str) or not PACK_ID.fullmatch(self.pack_id):
            raise ContractError("Invalid rule pack ID")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContractError("Rule pack name required")
        if not isinstance(self.eslint_core_rules, dict):
            raise ContractError("eslint_core_rules must be an object")
        if any(not re.fullmatch(r"[a-z][a-z0-9-]*", name) or level not in ("off", "warn", "error")
               for name, level in self.eslint_core_rules.items()):
            raise ContractError("Invalid built-in ESLint rule level/name")
        if not isinstance(self.semgrep_rules_text, str):
            raise ContractError("Semgrep rules must be text")
        if not self.eslint_core_rules and not self.semgrep_rules_text.strip():
            raise ContractError("Empty pack is not a validated policy")

    def serialize(self) -> bytes:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")

    def fingerprint(self) -> str:
        return hashlib.sha256(self.serialize()).hexdigest()

    @classmethod
    def parse(cls, raw: bytes) -> "PolicyPack":
        obj = json.loads(raw)
        if not isinstance(obj, dict) or set(obj) != {"pack_id", "name", "eslint_core_rules", "semgrep_rules_text"}:
            raise ContractError("Wrong policy pack schema")
        pack = cls(**obj)
        pack.validate()
        return pack


@dataclass(frozen=True)
class CapturedPolicies:
    registration_sha256: str
    packs: tuple[tuple[str, str, bytes], ...]
    combined_sha256: str


class PolicyStore:
    """Prototype store for scenarios. Trusted install needs ACL, no-follow and process locks."""
    def __init__(self, root: Path):
        self.root = root

    def _path(self, pack_id: str) -> Path:
        if not PACK_ID.fullmatch(pack_id):
            raise ContractError("Invalid pack ID")
        return self.root / f"{pack_id}.json"

    def create(self, pack: PolicyPack) -> None:
        raw = pack.serialize()
        self.root.mkdir(parents=True, exist_ok=True)
        # Explicit creation; never overwrite another shared pack by accident.
        with self._path(pack.pack_id).open("xb") as file:
            file.write(raw)

    def load(self, pack_id: str) -> PolicyPack:
        value = PolicyPack.parse(self._path(pack_id).read_bytes())
        if value.pack_id != pack_id:
            raise ContractError("Pack identity mismatch")
        return value

    def update(self, pack: PolicyPack, expected_sha256: str) -> None:
        pack.validate()
        old = self.load(pack.pack_id)
        if old.fingerprint() != expected_sha256:
            raise ContractError("Pack changed since edit started")
        raw = pack.serialize()
        temporary = self.root / f".update-{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as file:
                file.write(raw)
                file.flush()
                os.fsync(file.fileno())
            # Prototype only: separate check+replace needs an external edit lock in Windows.
            os.replace(temporary, self._path(pack.pack_id))
        finally:
            temporary.unlink(missing_ok=True)

    def clone(self, source_id: str, new_id: str, new_name: str) -> None:
        old = self.load(source_id)
        self.create(PolicyPack(new_id, new_name, dict(old.eslint_core_rules), old.semgrep_rules_text))

    def capture(self, registration: Registration) -> CapturedPolicies:
        registration.validate()
        entries = []
        for pack_id in registration.policy_pack_ids:
            pack = self.load(pack_id)
            raw = pack.serialize()
            entries.append((pack_id, hashlib.sha256(raw).hexdigest(), raw))
        token = json.dumps([(item[0], item[1]) for item in entries], sort_keys=True).encode()
        return CapturedPolicies(registration.fingerprint(), tuple(entries), hashlib.sha256(token).hexdigest())

    def still_current(self, registration: Registration, captured: CapturedPolicies) -> bool:
        try:
            current = self.capture(registration)
            return (current.registration_sha256 == captured.registration_sha256
                    and current.combined_sha256 == captured.combined_sha256)
        except (OSError, ContractError):
            return False
