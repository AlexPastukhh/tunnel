"""Presentation-only data, independent from optional Tk GUI.

All reports and previews are display data. They never grant promotion.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import ContractError, Registration
from .preview import TargetPreview
from .reports import ScanReport
from .windows_layout import BoundaryReview

BLOCK_REASON = (
    "Обновление заблокировано: нет независимого Windows-допуска, "
    "защищённых анализаторов/политик и проверенного механизма применения."
)


@dataclass(frozen=True)
class DisplayRow:
    columns: tuple[str, ...]
    detail: str = ""


@dataclass(frozen=True)
class DisplayTable:
    title: str
    columns: tuple[str, ...]
    rows: tuple[DisplayRow, ...]
    footer: str


class ReviewPresenter:
    """Read-only UI model plus in-memory registration collection."""

    def __init__(self) -> None:
        self.registrations: dict[str, Registration] = {}
        self.scan_reports: dict[str, ScanReport] = {}
        self.previews: dict[str, TargetPreview] = {}

    def register(self, project: Registration) -> None:
        project.validate()
        self.registrations[project.registration_id] = project
        self.scan_reports.pop(project.registration_id, None)
        self.previews.pop(project.registration_id, None)

    def register_json(self, raw: str) -> Registration:
        project = Registration.from_json(raw)
        self.register(project)
        return project

    def remove(self, project_id: str) -> None:
        self.registrations.pop(project_id, None)
        self.scan_reports.pop(project_id, None)
        self.previews.pop(project_id, None)

    def invalidate_shared_pack(self, policy_pack_id: str) -> tuple[str, ...]:
        """Presentation invalidation for every registration referencing a changed pack."""
        affected = []
        for project_id, project in self.registrations.items():
            if policy_pack_id in project.policy_pack_ids:
                self.scan_reports.pop(project_id, None)
                self.previews.pop(project_id, None)
                affected.append(project_id)
        return tuple(sorted(affected))

    def set_reports(self, project_id: str, scan: ScanReport | None = None,
                    preview: TargetPreview | None = None) -> None:
        if project_id not in self.registrations:
            raise ContractError("Unknown project")
        project = self.registrations[project_id]
        if scan is not None:
            if scan.registration_sha256 != project.fingerprint():
                raise ContractError("Report refers to different registration")
            self.scan_reports[project_id] = scan
        if preview is not None:
            if preview.target_root != project.target_root:
                raise ContractError("Preview destination differs from registration")
            self.previews[project_id] = preview

    def projects_table(self) -> DisplayTable:
        rows = []
        for project in sorted(self.registrations.values(), key=lambda p: p.name.casefold()):
            rows.append(DisplayRow((project.registration_id, project.name,
                                    str(len(project.selections)),
                                    ", ".join(project.policy_pack_ids),
                                    project.target_root or "Только проверка")))
        return DisplayTable("Проекты", ("ID", "Название", "Выборы", "Пакеты", "Назначение"),
                            tuple(rows), f"Регистраций: {len(rows)}. Исходный код не исполняется.")

    def bindings_table(self, project_id: str) -> DisplayTable:
        project = self.registrations.get(project_id)
        if project is None:
            return DisplayTable("Выборы", ("Тип", "Источник", "Назначение"), (), "Выберите проект.")
        rows = tuple(DisplayRow((s.kind, s.source, s.target or "Без назначения"))
                     for s in project.selections)
        return DisplayTable("Выборы", ("Тип", "Источник", "Назначение"),
                            rows, f"Правила: {', '.join(project.policy_pack_ids)}")

    def scan_table(self, project_id: str) -> DisplayTable:
        report = self.scan_reports.get(project_id)
        if report is None:
            return DisplayTable("Проверка", ("Анализатор", "Статус", "Находки", "Детали"), (),
                                "Нет доверенного Windows-сканирования; проверка не выполнялась.")
        rows = tuple(DisplayRow((r.engine, r.status, str(r.findings), r.detail))
                     for r in report.reports)
        return DisplayTable("Результат (НЕ ДОПУСК)",
                            ("Анализатор", "Статус", "Находки", "Детали"), rows,
                            f"Итог: {report.status}. Нет полномочий на перенос.")

    def preview_table(self, project_id: str) -> DisplayTable:
        preview = self.previews.get(project_id)
        if preview is None:
            return DisplayTable("Просмотр", ("Эффект", "Путь", "До SHA-256", "После SHA-256"), (),
                                "Предварительный просмотр не сформирован.")
        rows = tuple(DisplayRow((c.kind, c.relative_path,
                                 c.before_sha256 or "—", c.after_sha256 or "—"),
                                c.text_diff if c.text_diff is not None else (c.diff_note or ""))
                     for c in preview.changes)
        rows += tuple(DisplayRow(("preserve", path, "—", "—"),
                                 "Вне управляемого состава: не изменять и не удалять.")
                      for path in preview.preserved)
        rows += tuple(DisplayRow(("preserve-dir", path, "—", "—"),
                                 "Существующий каталог сохраняется.")
                      for path in preview.preserved_directories)
        return DisplayTable("Просмотр (НЕ РАЗРЕШЕНИЕ)",
                            ("Эффект", "Путь", "До SHA-256", "После SHA-256"), rows,
                            f"План: {preview.fingerprint}. Вне состава: "
                            f"{len(preview.preserved)} файлов и "
                            f"{len(preview.preserved_directories)} каталогов.")

    @staticmethod
    def layout_table(review: BoundaryReview | None) -> DisplayTable:
        if review is None:
            return DisplayTable("Установка", ("Уровень", "Код", "Сведения"), (),
                                "Нужна проверка Windows final paths, ACL и agent-write routes.")
        rows = tuple(DisplayRow((f.severity, f.code, f.details)) for f in review.findings)
        return DisplayTable("Схема размещения", ("Уровень", "Код", "Сведения"), rows,
                            f"{review.status}. Это НЕ проверка свойств ОС.")

    @staticmethod
    def can_apply(_project_id: str | None = None) -> bool:
        return False
