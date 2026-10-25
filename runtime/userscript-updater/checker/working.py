"""Functional Windows run from the working directory; never independent acceptance."""
from __future__ import annotations

import ctypes
import platform
from dataclasses import fields
from pathlib import Path

from .inventory import under
from .model import ContractError, relative_target
from .registry import RegistryStore
from .settings import DevelopmentSettings
from .windows_io import native_io
from .windows_target import WindowsFileOperations


def require_windows_owner():
    if platform.system() != "Windows":
        raise ContractError("Рабочий запуск предназначен для обычного процесса Windows")
    if ctypes.windll.shell32.IsUserAnAdmin():
        raise ContractError("Запустите Checker из обычного PowerShell, без прав администратора")


class WorkingSettings(DevelopmentSettings):
    def __init__(self, settings, registry_path):
        super().__init__(**{f.name: getattr(settings, f.name) for f in fields(DevelopmentSettings)})
        object.__setattr__(self, "_registry_path", registry_path)

    def validate(self):
        roots = getattr(self, "_selected_roots", self.source_roots)
        basic = DevelopmentSettings(**{f.name: (roots if f.name == "source_roots" else getattr(self, f.name))
                                     for f in fields(DevelopmentSettings)})
        basic.validate()

    def prepare_project(self, project):
        self.check_registration(project)
        actual = tuple(Path(s.source) for s in project.selections)
        object.__setattr__(self, "_selected_roots", actual)
        # Root allowance is for reading, while recursion/overlap uses the exact selection.
        object.__setattr__(self, "source_roots", tuple(dict.fromkeys(p.parent for p in actual)))
        self.validate()

    @property
    def source_overlap_roots(self):
        return getattr(self, "_selected_roots", ())

    def check_registration(self, project):
        document, _ = RegistryStore(self._registry_path).load()
        actual = next((p for p in document.registrations if p.registration_id == project.registration_id), None)
        if actual is None or actual.fingerprint() != project.fingerprint():
            raise ContractError("Регистрация на диске изменилась; перезагрузите список проектов")


class WorkingContext:
    def __init__(self, settings, registry_path, runtime_root):
        require_windows_owner()
        settings.validate()
        if not registry_path.is_absolute():
            raise ContractError("Absolute registry path required")
        self.registry_path = registry_path
        self.runtime_root = runtime_root
        self.settings = WorkingSettings(settings, registry_path)


class WorkingWindowsTarget(WindowsFileOperations):
    scope = "WINDOWS_WORKING_COPY_TEST"

    def __init__(self, context):
        if type(context) is not WorkingContext:
            raise ContractError("Explicit Windows working context required")
        require_windows_owner()
        self.context, self.io = context, native_io()

    @property
    def available(self):
        return platform.system() == "Windows"

    def authorize(self, target, settings):
        if settings is not self.context.settings:
            raise ContractError("Working settings identity changed")
        settings.check_storage_paths()
        settings.check_target_isolation(str(target))
        self._registered(target)
        document, _ = RegistryStore(self.context.registry_path).load()
        for project in document.registrations:
            for selection in project.selections:
                source = Path(selection.source)
                if under(source, target) or under(target, source):
                    raise ContractError("Назначение пересекается с зарегистрированным источником")

    def _registered(self, target):
        document, _ = RegistryStore(self.context.registry_path).load()
        if not any(p.target_root and Path(p.target_root) == target for p in document.registrations):
            raise ContractError("Назначение отсутствует в сохранённых регистрациях")
        ancestor = target
        while not ancestor.exists():
            ancestor = ancestor.parent
        self.io.validate(ancestor)

    def path(self, root, relative):
        self._registered(root)
        return root / relative_target(relative) if relative else root
