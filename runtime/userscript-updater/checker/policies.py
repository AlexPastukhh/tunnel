"""Mutable, shareable *candidate* rule packs. Storage is not protected inside Repo."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from contextlib import contextmanager
from .inventory import read_stable_file, check_plain_chain

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
        raw = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")
        if len(raw) > 1024 * 1024:
            raise ContractError("Policy pack exceeds size limit")
        return raw

    def fingerprint(self) -> str:
        return hashlib.sha256(self.serialize()).hexdigest()

    @classmethod
    def parse(cls, raw: bytes) -> "PolicyPack":
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ContractError(f"Duplicate policy JSON key: {key}")
                result[key] = value
            return result
        obj = json.loads(raw, object_pairs_hook=unique)
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
    """Development store with exclusive edits; installed Windows ACL/secure handles remain unverified."""
    def __init__(self, root: Path):
        self.root = root

    def _path(self, pack_id: str) -> Path:
        if not PACK_ID.fullmatch(pack_id):
            raise ContractError("Invalid pack ID")
        return self.root / f"{pack_id}.json"

    @contextmanager
    def _edit_lock(self):
        ancestor = self.root
        while not ancestor.exists():
            ancestor = ancestor.parent
        check_plain_chain(ancestor)
        self.root.mkdir(parents=True, exist_ok=True)
        check_plain_chain(self.root)
        lock = self.root / ".policy-edit.lock"
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ContractError("Policy save locked by another editor or interrupted save") from exc
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink(missing_ok=True)

    def list_packs(self) -> tuple[PolicyPack, ...]:
        if not self.root.exists():
            return ()
        return tuple(self.load(p.stem) for p in sorted(self.root.glob("*.json")))

    def create(self, pack: PolicyPack) -> None:
        raw = pack.serialize()
        with self._edit_lock():
            path = self._path(pack.pack_id)
            created = False
            try:
                with path.open("xb") as file:
                    created = True
                    file.write(raw)
                    file.flush()
                    os.fsync(file.fileno())
            except BaseException:
                if created:
                    path.unlink(missing_ok=True)
                raise

    def load(self, pack_id: str) -> PolicyPack:
        path = self._path(pack_id)
        if path.stat().st_size > 1024 * 1024:
            raise ContractError("Policy pack exceeds size limit")
        value = PolicyPack.parse(read_stable_file(path))
        if value.pack_id != pack_id:
            raise ContractError("Pack identity mismatch")
        return value

    def update(self, pack: PolicyPack, expected_sha256: str) -> None:
        pack.validate()
        raw = pack.serialize()
        with self._edit_lock():
            old = self.load(pack.pack_id)
            if old.fingerprint() != expected_sha256:
                raise ContractError("Pack changed since edit started")
            temporary = self.root / f".update-{uuid.uuid4().hex}.tmp"
            try:
                with temporary.open("xb") as file:
                    file.write(raw)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary, self._path(pack.pack_id))
            finally:
                temporary.unlink(missing_ok=True)

    def delete(self, pack_id: str, expected_sha256: str) -> None:
        with self._edit_lock():
            if self.load(pack_id).fingerprint() != expected_sha256:
                raise ContractError("Pack changed since delete was requested")
            self._path(pack_id).unlink()

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
