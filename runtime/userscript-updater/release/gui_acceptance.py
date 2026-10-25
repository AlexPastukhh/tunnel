"""Owner-operated native GUI acceptance, restricted to newly created fixtures."""
import argparse
import importlib.util
import json
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
handles = []
if os.name != "nt":
    raise SystemExit("Native Windows is required; this is not a Docker GUI result")
for directory in (ROOT / "python/DLLs", ROOT / "pydeps/pywin32_system32"):
    if directory.is_dir():
        handles.append(os.add_dll_directory(str(directory)))

from checker.environment import configure_gui_environment
configure_gui_environment(ROOT)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from checker.gui import DesktopApp
from checker.installed import current_sid
from checker.inventory import digest
from checker.model import Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.promotion import PromotionService
from checker.settings import DevelopmentSettings

spec = importlib.util.spec_from_file_location("native_acceptance_fixture", ROOT / "qa/native_acceptance.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class NativeWidgetFixtureService(PromotionService):
    @property
    def native_update_available(self):
        # This private QA service is outside app's import path and writes only the new fixture.
        return True


def main(profile, report):
    settings = DevelopmentSettings.load(profile)
    observed = {}
    with tempfile.TemporaryDirectory(prefix="native-acceptance-gui-", dir=settings.state_root.parent) as temporary:
        root = Path(temporary)
        source, target = root / "source", root / "target"
        source.mkdir(); target.mkdir()
        (source / "пример.js").write_text("const answer = 42;\n", encoding="utf-8")
        (source / "пример.py").write_text("answer = 42\n", encoding="utf-8")
        (source / "empty").mkdir()
        (target / "owner.bin").write_bytes(b"owner data, preserve")
        local = DevelopmentSettings(root / "state", root / "policies", (source,), settings.tools,
                                    settings.required_for_suffix, 180)
        pack = PolicyPack.parse((ROOT / "profiles/starter-pack.json").read_bytes())
        PolicyStore(local.policy_root).create(pack)
        data = asdict(local)
        data["schema_version"] = 1
        local_profile = root / "profile.json"
        local_profile.write_text(json.dumps(data, default=str), encoding="utf-8")
        app = DesktopApp(tk, ttk, filedialog, messagebox, root / "state/projects.json", local_profile)
        app.promotion = NativeWidgetFixtureService(local, fixtures.NativeFixtureTarget(root))
        app.root.title("Project Checker — NATIVE GUI ACCEPTANCE: TEMPORARY FIXTURES ONLY")
        project = Registration("native-gui", "Нативная приёмка — безопасный пример", (
            Selection("directory", str(source), "app"),), ("starter",), str(target))
        app._save_project(project)
        original_drain = app.jobs.drain
        def drain():
            events = original_drain()
            for event in events:
                if event.phase in ("COMPLETE_DEVELOPMENT", "REVIEW_READY", "POLICY_SAVED", "CANCELLED"):
                    observed[event.phase] = observed.get(event.phase, 0) + 1
                if event.phase == "TRANSACTION_RESULT":
                    state = event.result.state
                    observed[state] = observed.get(state, 0) + 1
            return events
        app.jobs.drain = drain
        messagebox.showinfo("Нативная приёмка", "Работа ограничена новой временной папкой:\n" + str(root) +
            "\n\n1. Проверьте реальные file/folder chooser и читаемость Unicode/размеров/diff."
            "\n2. Измените имя общего пакета, сохраните; дождитесь действительной проверки правил."
            "\n3. Запустите Проверить, отмените во время CLI, затем выполните новую проверку."
            "\n4. Полный просмотр → Обновить → подтверждение. owner.bin должен сохраниться."
            "\n5. Восстановление → журнал → просмотр отката → подтвердить."
            "\n6. Закройте окно для сохранения отчёта.", parent=app.root)
        app.root.mainloop()
        picker_visual = messagebox.askyesno("Подтверждение наблюдения владельца",
            "Вы лично проверили нативные file/folder chooser, Unicode, размеры и diff, "
            "понятность подтверждения и результата?\n"
            "Отчёт также требует фактически зарегистрированных Check/cancel/edit/apply/rollback событий.")
        result = dict(schema_version=1, platform="Windows", fixture_only=True, owner_sid=current_sid(),
                      installation_profile_sha256=digest(profile.read_bytes()),
                      observed=observed, manual_picker_visual=picker_visual)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        required = ("COMPLETE_DEVELOPMENT", "REVIEW_READY", "COMPLETED", "ROLLED_BACK", "POLICY_SAVED", "CANCELLED")
        success = picker_visual and all(observed.get(key, 0) > 0 for key in required)
        print("GUI acceptance observations:", observed, "PASS" if success else "INCOMPLETE")
        return 0 if success else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.profile, args.report))
