"""Real Tk widget/worker smoke for a Docker virtual display, synthetic files only.

File-picker results and message boxes are injected. This is NOT native Windows QA.
"""
import json
import os
import tempfile
import time
from pathlib import Path

import tkinter as tk
from tkinter import ttk

from checker.gui import DesktopApp
from checker.inventory import digest
from checker.policies import PolicyStore
from checker.registration_editor import RegistrationEditor


class Dialogs:
    files = ()
    directory = ""
    errors = []

    def askopenfilenames(self, **_kwargs):
        return self.files

    def askdirectory(self, **_kwargs):
        return self.directory

    def askopenfilename(self, **_kwargs):
        return ""

    def showerror(self, title, message, **_kwargs):
        self.errors.append((title, message))

    def askyesno(self, *_args, **_kwargs):
        return True


def pump(app, condition, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.root.update()
        if condition():
            app.root.update_idletasks()
            return
        time.sleep(0.01)
    raise AssertionError("GUI operation did not finish: " + app.status.get())


def main():
    with tempfile.TemporaryDirectory(prefix="checker-tk-synthetic-") as tmp:
        root = Path(tmp)
        source = root / "source"
        source.mkdir()
        js, py = source / "пример.js", source / "пример.py"
        js.write_text("const answer = 42;\n", encoding="utf-8")
        py.write_text("answer = 42\n", encoding="utf-8")
        folder = source / "папка"
        folder.mkdir()
        (folder / "extra.cjs").write_text("const value = 1;\n")
        tools = []
        for kind in ("eslint", "semgrep"):
            cli = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
            config = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
            tools.append(dict(kind=kind, executable=str(cli), executable_sha256=digest(cli.read_bytes()),
                config=str(config), config_sha256=digest(config.read_bytes()),
                node="/usr/local/bin/node" if kind == "eslint" else None))
        profile = root / "development.json"
        profile.write_text(json.dumps(dict(schema_version=1, state_root=str(root / "state"),
            policy_root=str(root / "policies"), source_roots=[str(source)], tools=tools,
            required_for_suffix={s: ["eslint", "semgrep"] for s in (".js", ".cjs", ".mjs")} | {".py": ["semgrep"]},
            timeout_seconds=90)))
        registry = root / "projects.json"
        dialogs = Dialogs()
        app = DesktopApp(tk, ttk, dialogs, dialogs, registry, profile)
        app.root.update()
        assert len(app.tabs.tabs()) == 7
        assert str(app.check_button["state"]) == "disabled"
        app._edit_policy(new=True)
        editor = app.policy_editor
        editor.pack_id.set("common")
        editor.name.set("Общие правила")
        rules = (Path(__file__).resolve().parents[1] / "policies/demo/semgrep-rules.yaml").read_text()
        editor.semgrep.insert("1.0", rules)
        editor.save_button.invoke()
        pump(app, lambda: app.policy_editor is None and not app.jobs.busy)
        assert PolicyStore(root / "policies").load("common").name == "Общие правила"
        print("TK-01 PASS: actual editor, real policy compilation and save", flush=True)

        project_editor = RegistrationEditor(app)
        project_editor.name.set("Смешанный 日本語")
        project_editor.packs.set("common")
        dialogs.files = (str(js), str(py))
        project_editor.choose_files()
        dialogs.directory = str(folder)
        project_editor.choose_folder()
        assert len(project_editor.draft.selections) == 3
        project_editor.save()
        app.root.update()
        project_id = app.selected
        assert len(app.presenter.registrations[project_id].selections) == 3
        before = registry.read_bytes()
        cancelled = RegistrationEditor(app)
        dialogs.files = ()
        cancelled.choose_files()
        assert not cancelled.draft.selections
        cancelled.window.destroy()
        assert registry.read_bytes() == before
        print("TK-02 PASS: file/files/folder editor and cancelled picker preserve persisted state", flush=True)

        heartbeat = [0]
        def beat():
            heartbeat[0] += 1
            app.root.after(20, beat)
        app.root.after(20, beat)
        app.check_button.invoke()
        pump(app, lambda: project_id in app.presenter.scan_reports and not app.jobs.busy)
        assert heartbeat[0] > 20
        assert app.presenter.scan_reports[project_id].status == "NOT_AUTHORIZED"
        assert len(app.tables["Покрытие файлов"][0].get_children()) == 3
        assert len(app.tables["Действующие правила"][0].get_children()) == 3
        print("TK-03 PASS: real async Check, responsive event loop and detailed tables", flush=True)

        app.pack_choice.set("common")
        old = PolicyStore(root / "policies").load("common").serialize()
        app._edit_policy()
        editor = app.policy_editor
        editor.eslint.delete("1.0", "end")
        editor.eslint.insert("1.0", '{"not-real-rule": "error"}')
        editor.save_button.invoke()
        pump(app, lambda: not app.jobs.busy and "ERROR" in editor.notice.get())
        assert PolicyStore(root / "policies").load("common").serialize() == old
        editor.eslint.delete("1.0", "end")
        editor.eslint.insert("1.0", '{"no-eval": "warn"}')
        editor.save_button.invoke()
        pump(app, lambda: app.policy_editor is None and not app.jobs.busy)
        assert project_id not in app.presenter.scan_reports
        print("TK-04 PASS: invalid rule rejected; direct valid edit invalidates consumer reports", flush=True)

        app._edit_policy(copy=True)
        editor = app.policy_editor
        editor.pack_id.set("copy")
        editor.name.set("Independent")
        editor.save_button.invoke()
        pump(app, lambda: app.policy_editor is None and not app.jobs.busy)
        app.pack_choice.set("copy")
        app._bind_policy("replace")
        assert app.presenter.registrations[project_id].policy_pack_ids == ("copy",)
        app.pack_choice.set("common")
        app._delete_policy()
        assert not (root / "policies/common.json").exists()
        print("TK-05 PASS: validated copy, rebind and delete unused package", flush=True)
        # Stop the smoke-only heartbeat before restarting Tk in this process.
        for timer in app.root.tk.call("after", "info"):
            app.root.after_cancel(timer)
        app._close()

        app = DesktopApp(tk, ttk, dialogs, dialogs, registry, profile)
        app.root.update()
        assert app.selected == project_id
        assert app.presenter.registrations[project_id].policy_pack_ids == ("copy",)
        app.check_button.invoke()
        pump(app, lambda: project_id in app.presenter.scan_reports and not app.jobs.busy)
        print("TK-06 PASS: save -> restart -> restore selection -> real Check -> report", flush=True)

        py.write_text('eval("2+2")\n')
        app.check_button.invoke()
        pump(app, lambda: project_id in app.presenter.scan_reports and not app.jobs.busy)
        assert app.presenter.scan_reports[project_id].status == "FINDINGS"
        assert any("пример.py" in " ".join(row.columns) for row in app.presenter.scan_table(project_id).rows)
        print("TK-07 PASS: actual finding locations visible in GUI table", flush=True)

        app.check_button.invoke()
        pump(app, lambda: app.job_status.startswith("semgrep"))
        app.cancel_button.invoke()
        pump(app, lambda: not app.jobs.busy and "CANCELLED" in app.job_status)
        assert project_id not in app.presenter.scan_reports
        print("TK-08 PASS: GUI cancellation stops job without restoring stale report", flush=True)
        assert not app.presenter.can_apply(project_id)
        assert not dialogs.errors, dialogs.errors
        app._close()
        print("Tk widget smoke: 8/8 PASS. SYNTHETIC DOCKER ONLY; WINDOWS NOT TESTED.", flush=True)


if __name__ == "__main__":
    main()
