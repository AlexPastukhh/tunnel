"""Validate a direct shared-pack edit and every affected composition before save."""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .inventory import digest
from .model import ContractError, Registration
from .policies import CapturedPolicies, PolicyPack, PolicyStore
from .policy_validation import prepare_effective_policy
from .processes import RunControl
from .settings import DevelopmentSettings


def capture_pack_values(packs: tuple[PolicyPack, ...], registration_sha256="policy-edit"):
    entries = tuple((p.pack_id, p.fingerprint(), p.serialize()) for p in packs)
    combined = digest(json.dumps([(i, token) for i, token, _ in entries], sort_keys=True).encode())
    return CapturedPolicies(registration_sha256, entries, combined)


@dataclass(frozen=True)
class PolicySaved:
    pack_id: str
    affected_projects: tuple[str, ...]


class PolicyService:
    def __init__(self, settings: DevelopmentSettings):
        self.settings = settings
        self.store = PolicyStore(settings.policy_root)

    def remove(self, pack_id: str, expected_sha256: str, projects: tuple[Registration, ...]):
        used = [p.name for p in projects if pack_id in p.policy_pack_ids]
        if used:
            raise ContractError("Pack is in use; rebind these projects first: " + ", ".join(used))
        self.store.delete(pack_id, expected_sha256)

    def save(self, pack: PolicyPack, expected_sha256: str | None,
             projects: tuple[Registration, ...], control: RunControl,
             progress=lambda _phase, _detail: None) -> PolicySaved:
        pack.validate()
        for project in projects:
            self.settings.check_target_isolation(project.target_root)
        control.check()
        if expected_sha256 is not None and self.store.load(pack.pack_id).fingerprint() != expected_sha256:
            raise ContractError("Pack changed since edit started")
        affected = tuple(p for p in projects if pack.pack_id in p.policy_pack_ids)
        compositions = [(pack,)]
        references = []
        for project in affected:
            packs = tuple(pack if key == pack.pack_id else self.store.load(key) for key in project.policy_pack_ids)
            compositions.append(packs)
            references.extend(p for p in packs if p.pack_id != pack.pack_id)
        self.settings.check_storage_paths()
        self.settings.state_root.mkdir(parents=True, exist_ok=True)
        original_tools = self.settings.tool_identities()
        with tempfile.TemporaryDirectory(prefix="policy-edit-", dir=self.settings.state_root) as tmp:
            for index, packs in enumerate(compositions):
                progress("policy", f"Валидация пакета и привязок: {index + 1}/{len(compositions)}")
                prepare_effective_policy(capture_pack_values(packs), self.settings.tools,
                    Path(tmp) / str(index), control=control)
            if self.settings.tool_identities() != original_tools:
                raise ContractError("Tools changed during policy edit")
            if any(self.store.load(p.pack_id).fingerprint() != p.fingerprint() for p in references):
                raise ContractError("Another shared pack changed during validation")
            control.check()
            if expected_sha256 is None:
                self.store.create(pack)
            else:
                self.store.update(pack, expected_sha256)
        return PolicySaved(pack.pack_id, tuple(sorted(p.registration_id for p in affected)))
