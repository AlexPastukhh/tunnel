"""View-only Windows Tkinter desktop GUI source (NOT a trusted release).

Pure presentation: JSON data import, project browsing, policy binding display,
scan/preview panes, planned installation-path diagnostics. There is deliberately
NO scanner execution, owner approval, or write-target/update action in this UI.
Tkinter is loaded lazily, allowing headless backend tests inside Fortis Repo.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .ui_model import BLOCK_REASON, DisplayTable, ReviewPresenter
from .windows_layout import RootSpec, review_windows_layout

MAX_REGISTRATION_JSON = 256 * 1024


class DesktopApp:
    def __init__(self, tk, ttk, filedialog, messagebox) -> None:
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.presenter = ReviewPresenter()
        self.selected = ""
        self.root = tk.Tk()
        self.root.title("Project Checker — UI prototype, NO APPROVAL")
        self.root.geometry("1130x720")
        self.root.minsize(850, 550)
        self.tables = {}
        self.row_details = {}
        self.detail_panes = {}
        self.status = tk.StringVar(value=BLOCK_REASON)
        self._build()
        self.refresh()

    def _build(self) -> None:
        t = self.ttk
        top = t.Frame(self.root, padding=12)
        top.pack(fill="x")
        t.Label(top, text="Project Checker — прототип интерфейса",
                font=("Segoe UI", 15, "bold")).pack(anchor="w")
        t.Label(top, text="Исходники в Fortis Repo НЕ доверенные. "
                "Windows-приложение не установлено; проверка и обновление отключены.",
                wraplength=1050).pack(anchor="w", pady=(4, 2))
        self.tabs = t.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
        names = ("Проекты", "Правила", "Проверка", "Просмотр обновления",
                 "Установка / доверие")
        for name in names:
            frame = t.Frame(self.tabs, padding=6)
            self.tabs.add(frame, text=name)
            self.tables[name] = self._new_table(frame)
        project_frame = self.tabs.nametowidget(self.tabs.tabs()[0])
        control = t.Frame(project_frame)
        control.pack(side="bottom", fill="x", pady=5)
        t.Button(control, text="Добавить JSON-регистрацию", command=self._import_registration).pack(side="left", padx=3)
        t.Button(control, text="Удалить из списка", command=self._remove).pack(side="left", padx=3)
        t.Button(control, text="Обновить вид", command=self.refresh).pack(side="left", padx=3)
        policies_frame = self.tabs.nametowidget(self.tabs.tabs()[1])
        t.Label(policies_frame,
                text="Пакеты правил отображаются из регистраций. "
                     "Доверенное редактирование будет доступно только после установки вне Repo.",
                wraplength=800).pack(side="bottom", fill="x", pady=3)
        install_frame = self.tabs.nametowidget(self.tabs.tabs()[4])
        self._layout_controls(install_frame)
        self.tabs.bind("<<NotebookTabChanged>>", lambda _: self.refresh())
        footer = t.Frame(self.root, padding=(12, 0, 12, 9))
        footer.pack(fill="x")
        t.Label(footer, textvariable=self.status, wraplength=900).pack(side="left", fill="x", expand=True)
        t.Button(footer, text="Проверить (недоступно)", state="disabled").pack(side="right", padx=5)
        t.Button(footer, text="Обновить (недоступно)", state="disabled").pack(side="right", padx=5)

    def _new_table(self, frame):
        t = self.ttk
        container = t.Frame(frame)
        container.pack(side="top", fill="both", expand=True)
        tree = t.Treeview(container, show="headings", selectmode="browse")
        y = t.Scrollbar(container, orient="vertical", command=tree.yview)
        x = t.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        y.pack(side="right", fill="y")
        x.pack(side="bottom", fill="x")
        tree.pack(side="top", fill="both", expand=True)
        summary = self.tk.StringVar()
        t.Label(frame, textvariable=summary, wraplength=1000).pack(side="bottom", fill="x", pady=(3, 4))
        if frame is not self.tabs.nametowidget(self.tabs.tabs()[0]):
            # A dedicated detail/diff pane is necessary: action rows alone
            # are not a full preview of intended changes.
            info = self.tk.Text(frame, height=8, wrap="none", state="disabled",
                                font=("Consolas", 9))
            info.pack(side="bottom", fill="x", pady=(2, 0))
            self.detail_panes[str(frame)] = info
            tree.bind("<<TreeviewSelect>>",
                      lambda event, ref=str(frame): self._show_selected_detail(ref, event))
        return tree, summary

    def _show_selected_detail(self, frame_key: str, _event=None) -> None:
        pane = self.detail_panes.get(frame_key)
        if pane is None:
            return
        tab = None
        for label, widgets in self.tables.items():
            if str(widgets[0].master.master) == frame_key:
                tab = label
                break
        if tab is None:
            return
        tree = self.tables[tab][0]
        selections = tree.selection()
        detail = self.row_details.get(tab, {}).get(selections[0], "") if selections else ""
        pane.configure(state="normal")
        pane.delete("1.0", "end")
        pane.insert("1.0", detail or "Детали отсутствуют.")
        pane.configure(state="disabled")

    def _layout_controls(self, frame):
        t = self.ttk
        inputs = t.Frame(frame)
        inputs.pack(side="bottom", fill="x")
        self.layout_inputs = {}
        for idx, (role, label) in enumerate((
            ("app", "Приложение"), ("tools", "Анализаторы"),
            ("policies", "Политики"), ("state", "Состояние"),
            ("approved", "Внешняя копия"), ("source", "Исходники"),
            ("agent_write", "Каталог, доступный ИИ (ещё пути через ;)"),
        )):
            t.Label(inputs, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            var = self.tk.StringVar()
            t.Entry(inputs, textvariable=var, width=76).grid(row=idx, column=1, sticky="ew", pady=2)
            self.layout_inputs[role] = var
        inputs.columnconfigure(1, weight=1)
        t.Button(inputs, text="Проверить схему путей (не ACL)",
                 command=self._inspect_layout).grid(row=8, column=0,
                                                     columnspan=2, sticky="ew", pady=(4, 0))
        self.layout_review = None

    def _show_table(self, tab: str, data: DisplayTable) -> None:
        tree, summary = self.tables[tab]
        previous = tree.selection()
        old_key = tree.item(previous[0], "values")[0] if previous else None
        tree.delete(*tree.get_children())
        self.row_details[tab] = {}
        keys = tuple(f"c{i}" for i in range(len(data.columns)))
        tree["columns"] = keys
        for key, title in zip(keys, data.columns):
            tree.heading(key, text=title)
            tree.column(key, width=135 if key == "c0" else 240, stretch=True)
        for idx, row in enumerate(data.rows):
            iid = f"item{idx}"
            tree.insert("", "end", iid=iid, values=row.columns)
            self.row_details[tab][iid] = row.detail
        summary.set(data.footer)
        if old_key is not None:
            for iid in tree.get_children():
                if tree.item(iid, "values")[0] == old_key:
                    tree.selection_set(iid)
                    break

    def refresh(self) -> None:
        self._show_table("Проекты", self.presenter.projects_table())
        self._show_table("Проверка", self.presenter.scan_table(self.selected))
        self._show_table("Просмотр обновления", self.presenter.preview_table(self.selected))
        reg = self.presenter.registrations.get(self.selected)
        table = self.presenter.bindings_table(self.selected)
        # Tab 2 describes selected project's rule links AND source selections.
        self._show_table("Правила", DisplayTable(
            "Привязанные политики", ("Тип", "Исходник", "Назначение"),
            table.rows, (", ".join(reg.policy_pack_ids) if reg else "Выберите регистрацию.")
        ))
        self._show_table("Установка / доверие",
                         self.presenter.layout_table(self.layout_review))
        self.status.set(BLOCK_REASON)
        self.tables["Проекты"][0].bind("<<TreeviewSelect>>", self._on_selected)

    def _on_selected(self, _event=None) -> None:
        tree = self.tables["Проекты"][0]
        selected = tree.selection()
        if not selected:
            return
        columns = tree.item(selected[0], "values")
        if columns:
            self.selected = str(columns[0])
            # Rebuild selected tabs only to avoid selection-change recursion.
            self._show_table("Проверка", self.presenter.scan_table(self.selected))
            self._show_table("Просмотр обновления", self.presenter.preview_table(self.selected))
            binding = self.presenter.bindings_table(self.selected)
            self._show_table("Правила", binding)

    def _import_registration(self) -> None:
        path = self.filedialog.askopenfilename(title="Регистрация JSON (только данные)",
                                              filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            candidate = Path(path)
            if candidate.stat().st_size > MAX_REGISTRATION_JSON:
                raise ValueError("Файл JSON превышает установленный предел размера")
            project = self.presenter.register_json(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.messagebox.showerror("Некорректная регистрация", str(exc))
            return
        self.selected = project.registration_id
        self.refresh()

    def _remove(self) -> None:
        if not self.selected:
            return
        self.presenter.remove(self.selected)
        self.selected = ""
        self.refresh()

    def _inspect_layout(self) -> None:
        paths = []
        for role, value in self.layout_inputs.items():
            # Agent-write roots may include multiple separately attested mounts.
            for item in value.get().split(";"):
                if item.strip():
                    paths.append(RootSpec(role, item.strip()))
        self.layout_review = review_windows_layout(tuple(paths))
        self._show_table("Установка / доверие",
                         self.presenter.layout_table(self.layout_review))

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Untrusted Project Checker UI prototype")
    parser.add_argument("--model-smoke", action="store_true",
                        help="run a pure presentation check without Tk or display")
    args = parser.parse_args(argv)
    if args.model_smoke:
        presenter = ReviewPresenter()
        if presenter.can_apply():
            raise RuntimeError("Unsafe presenter unexpectedly enabled")
        print("GUI model ready. PROMOTION DISABLED. Windows visual QA NOT RUN.")
        return 0
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError as exc:
        raise SystemExit(
            "Tkinter is not installed in this Docker runtime. "
            "Only run the graphical demo on an independent Windows test installation. "
            "This does not mean a trusted installer is ready."
        ) from exc
    DesktopApp(tk, ttk, filedialog, messagebox).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
