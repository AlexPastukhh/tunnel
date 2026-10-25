"""Review/confirmation/transaction core, independent of any target-write backend.

The GUI supplies NO mutation backend before V1-4. A backend must implement and
verify its OS boundary; JSON, scanner exit0 and confirmation fingerprints grant
no OS authority. Tests supply a strictly temporary synthetic backend.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .coverage import build_coverage_matrix
from .inventory import digest, read_stable_file, unchanged_since_snapshot, under
from .model import ContractError, relative_target
from .policies import PolicyStore
from .preview import TargetPreview, _read_tree, build_target_preview
from .promotion_state import ManagedStore, atomic_bytes, encoded, load_json, token
from .reports import summarize
from .review import ReviewBinding

TERMINAL = {"COMPLETED", "ABORTED", "ROLLED_BACK", "ROLLED_BACK_WITH_EXTERNAL_DRIFT"}


def _entry(document, project, target):
    return next((copy.deepcopy(e) for e in document["entries"]
                 if e["project_id"] == project and e["target_root"] == target), None)


def _with_entry(document, project, target, entry):
    result = copy.deepcopy(document)
    result["entries"] = [e for e in result["entries"]
                         if (e["project_id"], e["target_root"]) != (project, target)]
    if entry is not None:
        result["entries"].append(copy.deepcopy(entry))
    result["entries"].sort(key=lambda e: (e["project_id"], e["target_root"]))
    ManagedStore.validate(result)
    return result


def _claims(document, project, target, paths):
    wanted = [str(Path(target) / relative_target(p)).casefold() for p in paths]
    for e in document["entries"]:
        if (e["project_id"], e["target_root"]) == (project, target):
            continue
        for rel in e["files"]:
            other = str(Path(e["target_root"]) / relative_target(rel)).casefold()
            if any(p == other or p.startswith(other + "/") or other.startswith(p + "/") for p in wanted):
                raise ContractError("Destination is managed by another project")


def _tree(root):
    files, dirs = _read_tree(root)
    return {p: digest(raw) for p, raw in files.items()}, list(dirs)


@dataclass(frozen=True)
class PromotionReview:
    review_id: str
    check: object
    preview: TargetPreview
    managed_document: dict
    managed_token: str | None
    fingerprint: str


@dataclass(frozen=True)
class Confirmation:
    confirmation_id: str
    review_id: str
    fingerprint: str


@dataclass(frozen=True)
class TransactionOutcome:
    operation_id: str
    state: str
    scope: str
    detail: str


class PromotionService:
    def __init__(self, settings, backend=None):
        self.settings = settings
        self.backend = backend
        self.store = ManagedStore(settings.state_root / "promotion")
        self.reviews = {}
        self.confirmations = {}
        self.rollback_reviews = {}

    @property
    def native_update_available(self):
        # No installer/OS-boundary issuer exists in V1-3; a flag/profile cannot enable Windows Update.
        return False

    def invalidate(self, project_id=None):
        if project_id is None:
            self.reviews.clear()
        else:
            self.reviews = {k: r for k, r in self.reviews.items()
                            if r.check.project.registration_id != project_id}
        self.confirmations = {k: c for k, c in self.confirmations.items() if c.review_id in self.reviews}

    def _valid_check(self, check, current):
        self.settings.check_storage_paths()
        if current is None or current.fingerprint() != check.project.fingerprint():
            raise ContractError("Registration changed; run Check again")
        if not current.target_root:
            raise ContractError("Check-only registration has no target")
        self.settings.check_target_isolation(current.target_root)
        if any(under(Path(current.target_root), r) or under(r, Path(current.target_root))
               for r in self.settings.source_roots):
            raise ContractError("Promotion source and target roots must be separate")
        if not Path(current.target_root).exists() and not Path(current.target_root).parent.is_dir():
            raise ContractError("Target parent must exist; no hidden ancestor creation")
        if (check.scan.status != "NOT_AUTHORIZED" or check.coverage.status != "NOT_AUTHORIZED"
                or not check.scan.reports or any(r.status != "STRUCTURAL_CLEAR" for r in check.scan.reports)
                or summarize(check.snapshot, check.captured.combined_sha256, check.scan.reports).status != "NOT_AUTHORIZED"
                or build_coverage_matrix(check.snapshot, check.scan.reports, self.settings.required_for_suffix).status != "NOT_AUTHORIZED"):
            raise ContractError("Check has findings/errors/unsupported/incomplete coverage")
        if (check.snapshot.registration_sha256 != current.fingerprint()
                or check.captured.registration_sha256 != current.fingerprint()
                or not unchanged_since_snapshot(current, self.settings.source_roots, check.snapshot)
                or not PolicyStore(self.settings.policy_root).still_current(current, check.captured)):
            raise ContractError("Source/snapshot/policy changed; run Check again")
        if self.settings.tool_identities() != check.original_tools:
            raise ContractError("Tools changed; run Check again")
        if (not check.effective.configs or len(check.effective.configs) != len(check.effective.validations)
                or check.effective.policy_sha256 != check.captured.combined_sha256
                or check.scan.policy_sha256 != check.captured.combined_sha256
                or check.scan.snapshot_id != check.snapshot.snapshot_id
                or check.scan.registration_sha256 != current.fingerprint()):
            raise ContractError("Check/effective-policy identities are inconsistent")
        for config, validation in zip(check.effective.configs, check.effective.validations):
            if validation.status != "VALIDATED_DEVELOPMENT" or config.fingerprint() != validation.tool_fingerprint:
                raise ContractError("Effective tool/config changed")

    def review(self, check, current, *, adopted_existing=()):
        self._valid_check(check, current)
        document, state_token = self.store.read()
        previous = _entry(document, current.registration_id, current.target_root)
        managed = tuple(previous["files"]) if previous else ()
        desired = tuple(r.target_relative for r in check.snapshot.records)
        _claims(document, current.registration_id, current.target_root, (*managed, *desired))
        binding = ReviewBinding.capture(current, check.snapshot, check.captured.combined_sha256,
                                        check.effective.tool_fingerprints, managed)
        preview = build_target_preview(check.snapshot, Path(current.target_root), managed,
                                       binding=binding, adopted_existing=tuple(p for p in adopted_existing
                                           if p.casefold() not in {q.casefold() for q in managed}))
        identity = uuid.uuid4().hex
        fingerprint = token([identity, preview.fingerprint, state_token,
                             asdict(check.scan), asdict(check.coverage), check.original_tools])
        result = PromotionReview(identity, check, preview, document, state_token, fingerprint)
        self.invalidate(current.registration_id)
        self.reviews[identity] = result
        return result

    def _fresh(self, review, current):
        self._valid_check(review.check, current)
        document, state_token = self.store.read()
        if state_token != review.managed_token or document != review.managed_document:
            raise ContractError("Managed scope changed; review again")
        fresh = build_target_preview(review.check.snapshot, Path(current.target_root),
            review.preview.binding.previously_managed, binding=review.preview.binding,
            adopted_existing=review.preview.adopted_existing)
        if fresh != review.preview:
            raise ContractError("Target or exact preview changed; review again")

    def confirm(self, review_id, fingerprint, current):
        review = self.reviews.get(review_id)
        if review is None or review.fingerprint != fingerprint:
            raise ContractError("Missing/stale exact review")
        self._fresh(review, current)
        confirmation = Confirmation(uuid.uuid4().hex, review_id, fingerprint)
        # Re-confirming replaces earlier acknowledgements, never creates parallel apply permits.
        self.confirmations = {k: c for k, c in self.confirmations.items() if c.review_id != review_id}
        self.confirmations[confirmation.confirmation_id] = confirmation
        return confirmation

    def _authority(self, target):
        if self.backend is None:
            raise ContractError("No verified native mutation backend; Windows Update is disabled")
        self.settings.check_target_isolation(str(target))
        if any(under(Path(target), r) or under(r, Path(target)) for r in self.settings.source_roots):
            raise ContractError("Mutation target overlaps a source root")
        self.backend.authorize(Path(target), self.settings)
        return self.backend

    def _operations(self):
        root = self.store.root / "transactions"
        if not root.exists():
            return ()
        result = []
        for p in root.iterdir():
            if p.is_dir():
                if not (p / "journal.json").exists():
                    raise ContractError("Unjournaled transaction directory requires inspection")
                result.append((p.name, load_json(p / "journal.json")))
        return tuple(result)

    def pending(self):
        return tuple((key, doc["state"]) for key, doc in self._operations() if doc["state"] not in TERMINAL)

    def _save(self, op, document):
        atomic_bytes(op / "journal.json", encoded(document))

    def _op(self, operation_id):
        if not isinstance(operation_id, str) or len(operation_id) != 32 or any(c not in "0123456789abcdef" for c in operation_id):
            raise ContractError("Invalid transaction ID")
        return self.store.root / "transactions" / operation_id

    def apply(self, confirmation, current, *, control=None):
        stored = self.confirmations.pop(confirmation.confirmation_id, None)
        if stored != confirmation:
            raise ContractError("Confirmation missing/consumed; review again")
        review = self.reviews.get(confirmation.review_id)
        if review is None or review.fingerprint != confirmation.fingerprint:
            raise ContractError("Review invalidated")
        backend = self._authority(review.preview.target_root)
        with self.store.lock():
            if self.pending():
                raise ContractError("Incomplete transaction requires recovery first")
            self._fresh(review, current)
            if control:
                control.check()
            operation_id = uuid.uuid4().hex
            op = self._op(operation_id)
            op.mkdir(parents=True, exist_ok=False)
            before_files, before_dirs = _tree(Path(current.target_root))
            previous = _entry(review.managed_document, current.registration_id, current.target_root)
            new_entry = dict(project_id=current.registration_id, target_root=current.target_root,
                             files=sorted(r.target_relative for r in review.check.snapshot.records))
            records = []
            doc = dict(schema_version=1, operation_id=operation_id, state="PREPARING",
                scope=backend.scope, project_id=current.registration_id, target_root=current.target_root,
                review_fingerprint=review.fingerprint, snapshot_id=review.check.snapshot.snapshot_id,
                policy_sha256=review.check.captured.combined_sha256,
                previous_entry=previous, new_entry=new_entry, before_files=before_files,
                before_dirs=before_dirs, root_existed=review.preview.target_root_exists,
                created_dirs={}, directory_intent=[], operations=records)
            self._save(op, doc)
            for index, change in enumerate(review.preview.changes):
                rel = relative_target(change.relative_path)
                raw = backend.read(Path(current.target_root), rel)
                if (digest(raw) if raw is not None else None) != change.before_sha256:
                    raise ContractError("Preimage changed during preparation")
                metadata = backend.metadata(Path(current.target_root), rel) if raw is not None else None
                if change.kind in ("modify", "delete"):
                    atomic_bytes(op / f"before-{index}.bin", raw)
                if change.kind in ("create", "modify"):
                    record = next(r for r in review.check.snapshot.records if r.target_relative == rel)
                    data = read_stable_file(review.check.snapshot.root / record.snapshot_relative)
                    if digest(data) != change.after_sha256 or len(data) != change.after_size:
                        raise ContractError("Snapshot tampered before staging")
                    atomic_bytes(op / f"after-{index}.bin", data)
                records.append(dict(kind=change.kind, path=rel, before=change.before_sha256,
                    after=change.after_sha256, before_size=change.before_size, after_size=change.after_size,
                    metadata=metadata, intent=False, done=False))
            doc["state"] = "PREPARED"
            self._save(op, doc)
            try:
                # Revalidate after staging as well as immediately before the first target operation.
                self._fresh(review, current)
                self._verify_blobs(op, doc)
                if control:
                    control.check()
                doc["state"] = "APPLYING"
                self._save(op, doc)
                parents = {""} if not doc["root_existed"] else set()
                for item in records:
                    if item["kind"] in ("create", "modify"):
                        parent = Path(item["path"]).parent
                        while str(parent) != ".":
                            if parent.as_posix() not in before_dirs:
                                parents.add(parent.as_posix())
                            parent = parent.parent
                for rel in sorted(parents, key=lambda p: (p.count("/"), len(p))):
                    # An unrecorded mkdir crash leaves a preserved directory, never a blind recursive delete.
                    doc["directory_intent"].append(rel)
                    self._save(op, doc)
                    identity = backend.mkdir(Path(current.target_root), rel)
                    doc["created_dirs"][rel] = identity
                    self._save(op, doc)
                expected = dict(before_files)
                for index, item in enumerate(records):
                    if control:
                        control.check()
                    if item["kind"] == "unchanged":
                        continue
                    actual, _ = _tree(Path(current.target_root))
                    if actual != expected:
                        raise ContractError("Concurrent target edit during apply")
                    item["intent"] = True
                    self._save(op, doc)  # write-ahead intent survives replace -> journal crash gap
                    if item["kind"] == "delete":
                        backend.remove(Path(current.target_root), item["path"], expected_sha256=item["before"])
                        expected.pop(item["path"], None)
                    else:
                        backend.replace(Path(current.target_root), item["path"],
                                        self._blob(op, "after", index, item), item["metadata"], expected_sha256=item["before"])
                        expected[item["path"]] = item["after"]
                    raw = backend.read(Path(current.target_root), item["path"])
                    if (digest(raw) if raw is not None else None) != item["after"]:
                        raise ContractError("Target readback mismatch")
                    item["done"] = True
                    self._save(op, doc)
                actual, dirs = _tree(Path(current.target_root))
                expected_dirs = sorted(set(before_dirs) | {p for p in doc["created_dirs"] if p})
                if actual != expected or sorted(dirs) != expected_dirs:
                    raise ContractError("Final target inventory differs from exact plan")
                self._valid_check(review.check, current)  # drift cannot be declared completed
                if control:
                    control.check()
                value, current_token = self.store.read()
                if current_token != review.managed_token:
                    raise ContractError("Managed state changed during apply")
                self.store.write(_with_entry(value, current.registration_id, current.target_root, new_entry))
                doc["state"] = "COMPLETED"
                self._save(op, doc)
                self.invalidate(current.registration_id)
                return TransactionOutcome(operation_id, doc["state"], backend.scope, "All reviewed bytes read back")
            except Exception as exc:
                if not any(item["intent"] for item in records) and not doc["directory_intent"]:
                    doc["state"] = "ABORTED"
                    self._save(op, doc)
                    return TransactionOutcome(operation_id, "ABORTED", backend.scope, str(exc))
                return self._restore(op, doc, reason=str(exc))

    @staticmethod
    def _blob(op, side, index, item):
        raw = read_stable_file(op / f"{side}-{index}.bin")
        if digest(raw) != item[side] or len(raw) != item[side + "_size"]:
            raise ContractError("Tampered backup/staged bytes; recovery blocked")
        return raw

    def _verify_blobs(self, op, doc):
        seen = set()
        for index, item in enumerate(doc["operations"]):
            if not isinstance(item, dict) or set(item) != {
                "kind", "path", "before", "after", "before_size", "after_size", "metadata", "intent", "done"
            }:
                raise ContractError("Invalid journal operation schema")
            path = relative_target(item["path"])
            if path.casefold() in seen or type(item["intent"]) is not bool or type(item["done"]) is not bool:
                raise ContractError("Duplicate journal path or malformed write intent")
            seen.add(path.casefold())
            if item["kind"] not in ("create", "modify", "delete", "unchanged"):
                raise ContractError("Invalid journal operation")
            for side in ("before", "after"):
                value, size = item[side], item[side + "_size"]
                if value is None:
                    if size is not None:
                        raise ContractError("Absent journal pre/post-image has size")
                elif (not isinstance(value, str) or len(value) != 64
                      or any(c not in "0123456789abcdef" for c in value)
                      or type(size) is not int or size < 0):
                    raise ContractError("Invalid journal image hash/size")
            kind = item["kind"]
            if ((kind == "create" and (item["before"] is not None or item["after"] is None))
                    or (kind == "delete" and (item["before"] is None or item["after"] is not None))
                    or (kind == "modify" and (item["before"] is None or item["after"] is None))
                    or (kind == "unchanged" and (item["intent"] or item["before"] != item["after"] or item["before"] is None))):
                raise ContractError("Contradictory journal operation")
            for side, needed in (("before", item["kind"] in ("modify", "delete")),
                                 ("after", item["kind"] in ("modify", "create"))):
                if needed:
                    data = read_stable_file(op / f"{side}-{index}.bin")
                    if digest(data) != item[side] or len(data) != item[side + "_size"]:
                        raise ContractError("Tampered backup/staged bytes; recovery blocked")

    def _load(self, operation_id):
        op = self._op(operation_id)
        doc = load_json(op / "journal.json")
        if (doc.get("schema_version") != 1 or doc.get("operation_id") != operation_id
                or doc.get("state") not in TERMINAL | {"PREPARING", "APPLYING", "PREPARED", "ROLLING_BACK", "RECOVERY_BLOCKED"}
                or not isinstance(doc.get("operations"), list)):
            raise ContractError("Invalid transaction journal")
        if (not isinstance(doc.get("target_root"), str) or not Path(doc["target_root"]).is_absolute()
                or ".." in Path(doc["target_root"]).parts or not isinstance(doc.get("project_id"), str)):
            raise ContractError("Invalid journal destination/identity")
        self.settings.check_target_isolation(doc["target_root"])
        self._verify_blobs(op, doc)
        return op, doc

    def _restore(self, op, doc, reason):
        backend = self._authority(doc["target_root"])
        root = Path(doc["target_root"])
        try:
            self._verify_blobs(op, doc)
            value, state_token = self.store.read()
            own = _entry(value, doc["project_id"], doc["target_root"])
            if own not in (doc["previous_entry"], doc["new_entry"]):
                raise ContractError("Managed ownership changed; do not overwrite it")
            _claims(value, doc["project_id"], doc["target_root"],
                    tuple(doc["previous_entry"]["files"] if doc["previous_entry"] else ()) +
                    tuple(item["path"] for item in doc["operations"] if item["intent"]))
            for item in doc["operations"]:
                if item["intent"]:
                    raw = backend.read(root, item["path"])
                    if (digest(raw) if raw is not None else None) not in (item["before"], item["after"]):
                        raise ContractError("Third-party edit of touched target; recovery blocked")
            doc["state"] = "ROLLING_BACK"
            self._save(op, doc)
            for index in reversed(range(len(doc["operations"]))):
                item = doc["operations"][index]
                if not item["intent"]:
                    continue
                raw = backend.read(root, item["path"])
                if (digest(raw) if raw is not None else None) == item["before"]:
                    continue
                if item["before"] is None:
                    backend.remove(root, item["path"], expected_sha256=digest(raw) if raw is not None else None)
                else:
                    backend.replace(root, item["path"], self._blob(op, "before", index, item), item["metadata"],
                                    expected_sha256=digest(raw) if raw is not None else None)
                raw = backend.read(root, item["path"])
                if (digest(raw) if raw is not None else None) != item["before"]:
                    raise ContractError("Rollback readback mismatch")
            for rel, identity in sorted(doc["created_dirs"].items(), key=lambda p: len(p[0]), reverse=True):
                backend.rmdir_if_owned_empty(root, rel, identity)
            latest, latest_token = self.store.read()
            if latest_token != state_token:
                raise ContractError("Managed state changed during recovery")
            # Merge only this project/target entry; unrelated projects are preserved.
            self.store.write(_with_entry(latest, doc["project_id"], doc["target_root"], doc["previous_entry"]))
            actual, dirs = _tree(root)
            exact = (actual == doc["before_files"] and sorted(dirs) == sorted(doc["before_dirs"])
                     and root.exists() == doc["root_existed"])
            doc["state"] = "ROLLED_BACK" if exact else "ROLLED_BACK_WITH_EXTERNAL_DRIFT"
            self._save(op, doc)
            return TransactionOutcome(doc["operation_id"], doc["state"], backend.scope, reason)
        except Exception as exc:
            doc["state"] = "RECOVERY_BLOCKED"
            self._save(op, doc)
            return TransactionOutcome(doc["operation_id"], doc["state"], backend.scope, str(exc))

    def recover(self, operation_id):
        with self.store.lock():
            op, doc = self._load(operation_id)
            self._authority(doc["target_root"])
            if doc["state"] in TERMINAL:
                return TransactionOutcome(operation_id, doc["state"], doc["scope"], "No automatic rollback of terminal transaction")
            if doc["state"] in ("PREPARING", "PREPARED"):
                doc["state"] = "ABORTED"
                self._save(op, doc)
                return TransactionOutcome(operation_id, "ABORTED", doc["scope"], "Prepared-only transaction has no target intent")
            return self._restore(op, doc, "Interrupted transaction recovery")

    def review_rollback(self, operation_id):
        op, doc = self._load(operation_id)
        if doc["state"] != "COMPLETED":
            raise ContractError("Explicit rollback requires a completed transaction")
        current, state_token = self.store.read()
        fingerprint = token([doc, _tree(Path(doc["target_root"])), state_token])
        self.rollback_reviews[operation_id] = fingerprint
        return fingerprint

    def rollback(self, operation_id, fingerprint):
        if self.rollback_reviews.pop(operation_id, None) != fingerprint:
            raise ContractError("Exact rollback review not acknowledged")
        with self.store.lock():
            op, doc = self._load(operation_id)
            _, state_token = self.store.read()
            if token([doc, _tree(Path(doc["target_root"])), state_token]) != fingerprint:
                raise ContractError("Rollback target/state changed; review again")
            return self._restore(op, doc, "Explicit reviewed rollback")
