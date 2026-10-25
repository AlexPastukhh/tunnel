"""One background Check job, progress events and immutable captured policy.

No UI thread mutation, no candidate execution, no promotion/owner PASS.
"""
from __future__ import annotations

import json
import queue
import threading
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .coverage import CoverageMatrix, build_coverage_matrix
from .engines import run_dev_engine
from .inventory import Snapshot, make_snapshot, unchanged_since_snapshot, under
from .model import ContractError, Registration
from .policies import CapturedPolicies, PolicyStore
from .policy_validation import EffectivePolicy, prepare_effective_policy
from .processes import RunControl, Cancelled, DeadlineExceeded
from .reports import ScanReport, summarize
from .settings import DevelopmentSettings
from .policy_service import PolicyService, PolicySaved
from .promotion import PromotionReview


@dataclass(frozen=True)
class CheckResult:
    project: Registration
    captured: CapturedPolicies
    snapshot: Snapshot
    effective: EffectivePolicy
    scan: ScanReport
    coverage: CoverageMatrix
    evidence_dir: Path
    original_tools: tuple[tuple[str, str], ...]
    presentation_stamps: tuple[tuple, ...]


def _presentation_stamps(settings, effective):
    # Cheap late UI invalidation only. Full byte verification stays in the worker;
    # promotion must independently rehash, never authorize from these timestamps.
    paths = {p for config in (*settings.tools, *effective.configs)
             for p in (config.executable, config.config, *([config.node] if config.node else []))}
    rows = []
    for path in sorted(paths):
        info = path.stat()
        rows.append((str(path), info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return tuple(rows)


@dataclass(frozen=True)
class JobEvent:
    job_id: str
    project_id: str
    phase: str
    detail: str = ""
    result: CheckResult | PolicySaved | PromotionReview | None = None
    terminal: bool = False


class CheckJobs:
    def __init__(self, settings: DevelopmentSettings):
        settings.validate()
        self.settings = settings
        self.events = queue.Queue()
        self.thread = None
        self.control = None
        self.job_id = None

    @property
    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def cancel(self):
        if self.control:
            self.control.cancel()

    def start(self, project: Registration) -> str:
        if self.busy:
            raise ContractError("A Check job is already running")
        project.validate()
        self.settings.check_target_isolation(project.target_root)
        for selection in project.selections:
            if selection.kind == "directory" and any(under(root, Path(selection.source)) for root in
                    (self.settings.state_root, self.settings.policy_root)):
                raise ContractError("Job state/policies cannot be inside a selected source directory")
        self.job_id = str(uuid.uuid4())
        self.control = RunControl(self.settings.timeout_seconds)
        ticket, control = self.job_id, self.control
        # The worker captures packs off the UI thread. Registration itself is frozen.
        self.thread = threading.Thread(target=self._worker, args=(ticket, project, control), daemon=True)
        self.thread.start()
        return ticket

    def start_review(self, service, check, current, *, first_import=False):
        if self.busy:
            raise ContractError("Another operation is running")
        self.job_id = str(uuid.uuid4())
        self.control = RunControl(self.settings.timeout_seconds)
        self.thread = threading.Thread(target=self._review_worker,
            args=(self.job_id, service, check, current, first_import, self.control), daemon=True)
        self.thread.start()
        return self.job_id

    def _review_worker(self, ticket, service, check, current, first_import, control):
        try:
            control.check()
            self.events.put(JobEvent(ticket, current.registration_id, "preview",
                                     "Сверка Check, управляемого состава и фактического target"))
            adopted = tuple(r.target_relative for r in check.snapshot.records
                            if first_import and r.target_relative is not None
                            and (Path(current.target_root) / r.target_relative).is_file())
            review = service.review(check, current, adopted_existing=adopted)
            control.check()
            self.events.put(JobEvent(ticket, current.registration_id, "REVIEW_READY",
                                     "Полный просмотр готов; native Update ещё заблокирован", review, True))
        except (Cancelled, DeadlineExceeded) as exc:
            service.invalidate(current.registration_id)
            self.events.put(JobEvent(ticket, current.registration_id,
                "CANCELLED" if isinstance(exc, Cancelled) else "TIMEOUT", str(exc), terminal=True))
        except Exception as exc:
            self.events.put(JobEvent(ticket, current.registration_id, "ERROR", str(exc), terminal=True))

    def start_transaction(self, service, action, *args):
        if self.busy:
            raise ContractError("Another operation is running")
        if action not in ("apply", "history", "restoration_review", "restore"):
            raise ContractError("Unknown transaction action")
        self.job_id = str(uuid.uuid4())
        self.control = RunControl(self.settings.timeout_seconds)
        self.thread = threading.Thread(target=self._transaction_worker,
            args=(self.job_id, service, action, args, self.control), daemon=True)
        self.thread.start()
        return self.job_id

    def _transaction_worker(self, ticket, service, action, args, control):
        try:
            control.check()
            self.events.put(JobEvent(ticket, "", "transaction", action))
            if action == "apply":
                review, project = args
                confirmation = service.confirm(review.review_id, review.fingerprint, project)
                result = service.apply(confirmation, project, control=control)
                phase = "TRANSACTION_RESULT"
            elif action == "history":
                result, phase = service.history(), "TRANSACTIONS"
            elif action == "restoration_review":
                result = service.restoration_review(args[0], recovery=args[1], include_conflicts=args[2] if len(args) > 2 else False)
                phase = "RESTORATION_READY"
            else:
                review, = args
                result = (service.recover_reviewed(review) if review.recovery else
                          service.rollback(review.operation_id, review.fingerprint))
                phase = "TRANSACTION_RESULT"
            # A cancellation cannot hide a completed mutation or rollback outcome.
            self.events.put(JobEvent(ticket, "", phase, "Операция завершена", result, True))
        except Exception as exc:
            self.events.put(JobEvent(ticket, "", "ERROR", str(exc), terminal=True))

    def start_policy_save(self, pack, expected_sha256, projects):
        if self.busy:
            raise ContractError("A job is already running")
        self.job_id = str(uuid.uuid4())
        self.control = RunControl(self.settings.timeout_seconds)
        ticket, control = self.job_id, self.control
        self.thread = threading.Thread(target=self._policy_worker,
            args=(ticket, pack, expected_sha256, projects, control), daemon=True)
        self.thread.start()
        return ticket

    def _policy_worker(self, ticket, pack, expected_sha256, projects, control):
        try:
            def progress(phase, detail):
                self.events.put(JobEvent(ticket, "", phase, detail))
            saved = PolicyService(self.settings).save(pack, expected_sha256, projects, control, progress)
            self.events.put(JobEvent(ticket, "", "POLICY_SAVED", "Пакет сохранён для всех потребителей", saved, True))
        except Cancelled as exc:
            self.events.put(JobEvent(ticket, "", "CANCELLED", str(exc), terminal=True))
        except DeadlineExceeded as exc:
            self.events.put(JobEvent(ticket, "", "TIMEOUT", str(exc), terminal=True))
        except Exception as exc:
            self.events.put(JobEvent(ticket, "", "ERROR", f"{type(exc).__name__}: {exc}", terminal=True))

    def _worker(self, ticket, project, control):
        def progress(phase, detail=""):
            control.check()
            self.events.put(JobEvent(ticket, project.registration_id, phase, detail))

        try:
            progress("capture", "Фиксация общих пакетов и инструментов")
            settings = self.settings
            settings.check_storage_paths()
            store = PolicyStore(settings.policy_root)
            captured = store.capture(project)
            original_tools = settings.tool_identities()
            root = settings.state_root / "jobs" / ticket
            root.mkdir(parents=True, exist_ok=False)
            progress("snapshot", "Инвентаризация и снимок выбранных байтов")
            snapshot = make_snapshot(project, settings.source_roots, root / "snapshots")
            progress("policy", "Компиляция действующих конфигураций")
            effective = prepare_effective_policy(captured, settings.tools, root / "policy", control=control)
            requirements = dict(effective.required_rules)
            validations = {v.engine: v for v in effective.validations}
            reports = []
            evidence_dir = root / "evidence"
            for config in effective.configs:
                applicable = {".js", ".cjs", ".mjs"} if config.kind == "eslint" else {".js", ".cjs", ".mjs", ".py"}
                if not any(r.content in ("code", "dependency") and Path(r.source_path).suffix.lower() in applicable for r in snapshot.records):
                    continue
                progress(config.kind, "Статический анализ снимка")
                reports.append(run_dev_engine(snapshot, config, required_rules=requirements[config.kind],
                    control=control, validation=validations[config.kind], evidence_dir=evidence_dir))
            progress("freshness", "Сверка source, правил и инструментов")
            scan = summarize(snapshot, captured.combined_sha256, tuple(reports))
            coverage = build_coverage_matrix(snapshot, tuple(reports), settings.required_for_suffix)
            # Scanner aggregate alone must not hide unsupported/missing required per-file coverage.
            for status in ("ERROR", "INCOMPLETE", "UNSUPPORTED", "FINDINGS", "NOT_AUTHORIZED"):
                if status in (scan.status, coverage.status):
                    scan = replace(scan, status=status)
                    break
            result = CheckResult(project, captured, snapshot, effective, scan, coverage,
                                 evidence_dir, original_tools, _presentation_stamps(settings, effective))
            stale = (not unchanged_since_snapshot(project, settings.source_roots, snapshot)
                     or not store.still_current(project, captured)
                     or settings.tool_identities() != original_tools
                     or any(c.fingerprint() != validations[c.kind].tool_fingerprint for c in effective.configs))
            control.check()
            # Saved development evidence is historical data, not a reusable installed authorization.
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / "report.json").write_text(json.dumps({
                "schema_version": 1, "job_id": ticket, "stale": stale,
                "registration": json.loads(project.to_json()), "snapshot_id": snapshot.snapshot_id,
                "manifest": snapshot.manifest(), "policy_sha256": captured.combined_sha256,
                "original_tools": original_tools,
                "rules": [asdict(v) for v in effective.validations],
                "scan": asdict(scan), "coverage": asdict(coverage),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            control.check()
            self.events.put(JobEvent(ticket, project.registration_id,
                "STALE" if stale else "COMPLETE_DEVELOPMENT",
                "Исходники/правила/инструменты изменились" if stale else "Проверка завершена; НЕ ДОПУСК",
                result, True))
        except Cancelled as exc:
            self.events.put(JobEvent(ticket, project.registration_id, "CANCELLED", str(exc), terminal=True))
        except DeadlineExceeded as exc:
            self.events.put(JobEvent(ticket, project.registration_id, "TIMEOUT", str(exc), terminal=True))
        except Exception as exc:
            self.events.put(JobEvent(ticket, project.registration_id, "ERROR",
                                     f"{type(exc).__name__}: {exc}", terminal=True))

    def drain(self) -> tuple[JobEvent, ...]:
        result = []
        while True:
            try:
                event = self.events.get_nowait()
                # A late prior job cannot become the selected/current result.
                if event.job_id == self.job_id:
                    if event.phase in ("COMPLETE_DEVELOPMENT", "REVIEW_READY") and self.control.cancelled.is_set():
                        event = JobEvent(event.job_id, event.project_id, "CANCELLED", "Cancelled before presentation", terminal=True)
                    result.append(event)
            except queue.Empty:
                return tuple(result)

    def is_current(self, result: CheckResult, current: Registration | None) -> bool:
        if current is None or current.fingerprint() != result.project.fingerprint():
            return False
        try:
            return (PolicyStore(self.settings.policy_root).still_current(current, result.captured)
                    and _presentation_stamps(self.settings, result.effective) == result.presentation_stamps)
        except (OSError, ValueError):
            return False
