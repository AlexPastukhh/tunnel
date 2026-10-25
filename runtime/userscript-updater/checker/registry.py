"""Versioned local registrations, atomic save and optimistic edit conflict checks.

Development storage only; independent Windows state ACL/handles remain required.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from .inventory import check_plain_chain, digest, read_stable_file
from .model import ContractError, Registration, Selection
from .ui_model import ReviewPresenter

MAX_REGISTRY_BYTES = 2 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True)
class RegistryDocument:
    registrations: tuple[Registration, ...] = ()
    last_selected: str | None = None

    def serialize(self) -> bytes:
        ids = []
        for project in self.registrations:
            project.validate()
            ids.append(project.registration_id)
        if len(ids) != len(set(ids)) or (self.last_selected is not None and self.last_selected not in ids):
            raise ContractError("Duplicate registration ID or unknown last selection")
        data = {"schema_version": 1, "last_selected": self.last_selected,
                "registrations": [json.loads(p.to_json()) for p in self.registrations]}
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")
        if len(raw) > MAX_REGISTRY_BYTES:
            raise ContractError("Registry exceeds explicit size limit")
        return raw

    @classmethod
    def parse(cls, raw: bytes) -> "RegistryDocument":
        if len(raw) > MAX_REGISTRY_BYTES:
            raise ContractError("Registry exceeds explicit size limit")
        try:
            data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
            if (not isinstance(data, dict) or set(data) != {"schema_version", "last_selected", "registrations"}
                    or type(data["schema_version"]) is not int or data["schema_version"] != 1
                    or not isinstance(data["registrations"], list)):
                raise ContractError("Unsupported registry schema/version")
            result = cls(tuple(Registration.from_json(json.dumps(item)) for item in data["registrations"]),
                         data["last_selected"])
            result.serialize()
            return result
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise ContractError(f"Cannot load registry; original file preserved: {exc}") from exc


class RegistryStore:
    def __init__(self, path: Path):
        if not path.is_absolute():
            raise ContractError("Registry path must be absolute")
        self.path = path

    def _bytes(self) -> bytes | None:
        if not self.path.exists() and not self.path.is_symlink():
            return None
        if self.path.stat().st_size > MAX_REGISTRY_BYTES:
            raise ContractError("Registry exceeds explicit size limit")
        return read_stable_file(self.path)

    def load(self) -> tuple[RegistryDocument, str | None]:
        raw = self._bytes()
        return (RegistryDocument(), None) if raw is None else (RegistryDocument.parse(raw), digest(raw))

    def save(self, document: RegistryDocument, expected_sha256: str | None) -> str:
        raw = document.serialize()
        parent = self.path.parent
        ancestor = parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        check_plain_chain(ancestor)
        parent.mkdir(parents=True, exist_ok=True)
        check_plain_chain(parent)
        lock = parent / (self.path.name + ".lock")
        temporary = parent / (".registry-" + uuid.uuid4().hex + ".tmp")
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ContractError("Registry save is locked; another editor or interrupted save needs review") from exc
        try:
            os.close(fd)
            current = self._bytes()
            if (digest(current) if current is not None else None) != expected_sha256:
                raise ContractError("Registry changed in another session; reload before saving")
            # Parse again so corrupt state is never replaced as if it were an empty registry.
            if current is not None:
                RegistryDocument.parse(current)
            with temporary.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
            lock.unlink(missing_ok=True)
        return digest(raw)


class RegistrySession:
    """Commit storage before changing the UI; failed saves preserve both old states."""
    def __init__(self, presenter: ReviewPresenter, store: RegistryStore | None = None):
        self.presenter = presenter
        self.store = store
        self.document, self.token = store.load() if store else (RegistryDocument(), None)
        for project in self.document.registrations:
            presenter.register(project)

    def _commit(self, document: RegistryDocument) -> None:
        document.serialize()
        token = self.store.save(document, self.token) if self.store else None
        self.document, self.token = document, token

    def put(self, project: Registration) -> None:
        project.validate()
        projects = tuple(p for p in self.document.registrations if p.registration_id != project.registration_id)
        self._commit(RegistryDocument((*projects, project), project.registration_id))
        self.presenter.register(project)

    def remove(self, project_id: str) -> None:
        projects = tuple(p for p in self.document.registrations if p.registration_id != project_id)
        selected = self.document.last_selected if self.document.last_selected != project_id else None
        self._commit(RegistryDocument(projects, selected))
        self.presenter.remove(project_id)

    def select(self, project_id: str) -> None:
        if self.document.last_selected != project_id:
            self._commit(RegistryDocument(self.document.registrations, project_id))


class RegistrationDraft:
    """Picker/editor data: cancellation never creates or saves a partial registration."""
    def __init__(self, project: Registration | None = None):
        self.project_id = project.registration_id if project else str(uuid.uuid4())
        self.selections = list(project.selections) if project else []

    def add(self, kind: str, paths: tuple[str, ...]) -> None:
        entries = [Selection(kind, path, Path(path).name) for path in paths if path]
        for entry in entries:
            entry.validate()
        keys = [e.source.casefold() for e in [*self.selections, *entries]]
        if len(keys) != len(set(keys)):
            raise ContractError("Duplicate source selection")
        self.selections.extend(entries)

    def build(self, name: str, pack_ids: tuple[str, ...], target_root: str | None) -> Registration:
        project = Registration(self.project_id, name,
            tuple(Selection(e.kind, e.source, (e.target or Path(e.source).name) if target_root else None)
                  for e in self.selections), pack_ids, target_root)
        project.validate()
        return project
