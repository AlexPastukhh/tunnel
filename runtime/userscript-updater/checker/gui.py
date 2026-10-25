"""Development Tkinter desktop GUI source (NOT a trusted Windows release).

Registration editor/pickers and atomic versioned JSON persistence, policy binding display,
scan/preview panes, planned installation-path diagnostics. An explicit development profile enables background static Check and shared-pack editing.
Development profiles cannot update. A Windows working context enables functional
tests; an independently accepted Windows context enables exact confirmation, transaction results and reviewed recovery.
Tkinter is loaded lazily, allowing headless backend tests inside Fortis Repo.
"""
from __future__ import annotations

import argparse
from dataclasses import replace

from .jobs import CheckJobs, CheckResult
from .settings import DevelopmentSettings
from .policies import PolicyStore
from .policy_editor import PolicyEditor
from .policy_service import PolicyService
from .promotion import PromotionService
from pathlib import Path

from .model import Registration
from .registry import RegistrySession, RegistryStore
from .registration_editor import RegistrationEditor
from .ui_model import BLOCK_REASON, DisplayRow, DisplayTable, ReviewPresenter
from .windows_layout import RootSpec, review_windows_layout

MAX_REGISTRATION_JSON = 256 * 1024


class DesktopApp:
    def __init__(self, tk, ttk, filedialog, messagebox, registry_path: Path | None = None, settings_path: Path | None = None, *, installed_context=None, working_context=None, policy_root=None, startup_status="") -> None:
        self.installed_context = installed_context
        self.working_context = working_context
        self.policy_root = policy_root
        if installed_context is not None and working_context is not None:
            raise ValueError("Choose one runtime context")
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.presenter = ReviewPresenter()
        self.selected = ""
        self.root = tk.Tk()
        self.root.title("Project Checker — тестовая проверка, без допуска к обновлению")
        self.root.geometry("1130x720")
        self.root.minsize(850, 550)
        self.registry_error = ""
        try:
            self.registry = RegistrySession(self.presenter, RegistryStore(registry_path) if registry_path else None)
        except (OSError, ValueError, TypeError) as exc:
            self.registry = RegistrySession(self.presenter)
            self.registry_error = str(exc)
            messagebox.showerror("Реестр не загружен; исходный файл сохранён", self.registry_error)
        self.selected = self.registry.document.last_selected or ""
        self.jobs = None
        self.job_status = startup_status
        self.policy_editor = None
        self.active_check_project = None
        self.active_ticket = None
        if settings_path:
            try:
                self.jobs = CheckJobs(DevelopmentSettings.load(settings_path))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                messagebox.showerror("Тестовый профиль не загружен", str(exc))
                self.job_status = "Check отключён: неверный тестовый профиль."
        if installed_context is not None:
            from .installed import InstalledAuthority, InstalledSettings, WindowsTarget
            if type(installed_context) is not InstalledAuthority:
                raise ValueError("Invalid installed context")
            self.jobs = CheckJobs(InstalledSettings(installed_context))
            self.promotion = PromotionService(self.jobs.settings, WindowsTarget(installed_context))
            self.root.title("Project Checker — личная Windows V1")
        elif working_context is not None:
            from .working import WorkingContext, WorkingWindowsTarget
            if type(working_context) is not WorkingContext:
                raise ValueError("Invalid working context")
            self.jobs = CheckJobs(working_context.settings)
            self.promotion = PromotionService(self.jobs.settings, WorkingWindowsTarget(working_context))
            self.root.title("Project Checker — проверка рабочей копии Windows")
        else:
            self.promotion = PromotionService(self.jobs.settings) if self.jobs else None
        if self.jobs:
            self.policy_root = self.jobs.settings.policy_root
        self.check_results = {}
        self.active_review = None
        self.restoration = None
        self.history_rows = ()
        self.tables = {}
        self.row_details = {}
        self.detail_panes = {}
        self.status = tk.StringVar(value=BLOCK_REASON)
        self._build()
        self.refresh()
        self.poll_timer = self.root.after(100, self._poll_jobs)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        t = self.ttk
        top = t.Frame(self.root, padding=12)
        top.pack(fill="x")
        t.Label(top, text="Project Checker",
                font=("Segoe UI", 15, "bold")).pack(anchor="w")
        intro = ("Проверьте проект, просмотрите полный план и отдельно подтвердите обновление."
                 if self.installed_context else
                 "Рабочая копия Windows: выберите источники, пакеты правил и назначение. "
                 "После проверки просмотрите план и отдельно подтвердите запись. Защищённая установка ещё не принята."
                 if self.working_context else
                 "Выберите источники, пакеты правил и назначение. Для проверки подготовьте анализаторы.")
        t.Label(top, text=intro,
                wraplength=1050).pack(anchor="w", pady=(4, 2))
        self.tabs = t.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
        names = ("Проекты", "Правила", "Проверка", "Просмотр обновления",
                 "Установка / доверие", "Покрытие файлов", "Действующие правила", "Восстановление")
        for name in names:
            frame = t.Frame(self.tabs, padding=6)
            self.tabs.add(frame, text=name)
            self.tables[name] = self._new_table(frame)
        project_frame = self.tabs.nametowidget(self.tabs.tabs()[0])
        control = t.Frame(project_frame)
        control.pack(side="bottom", fill="x", pady=5)
        t.Button(control, text="Новый проект", command=lambda: RegistrationEditor(self)).pack(side="left", padx=3)
        t.Button(control, text="Изменить", command=self._edit_project).pack(side="left", padx=3)
        t.Button(control, text="Импорт JSON", command=self._import_registration).pack(side="left", padx=3)
        t.Button(control, text="Удалить из списка", command=self._remove).pack(side="left", padx=3)
        t.Button(control, text="Обновить вид", command=self.refresh).pack(side="left", padx=3)
        policies_frame = self.tabs.nametowidget(self.tabs.tabs()[1])
        self._policy_controls(policies_frame)
        preview_frame = self.tabs.nametowidget(self.tabs.tabs()[3])
        controls = t.Frame(preview_frame)
        controls.pack(side="bottom", fill="x", pady=4)
        self.preview_button = t.Button(controls, text="Сформировать полный просмотр", command=self._review, state="disabled")
        self.preview_button.pack(side="left")
        self.import_button = t.Button(controls, text="Просмотр первого импорта", command=lambda: self._review(first_import=True), state="disabled")
        self.import_button.pack(side="left", padx=5)
        t.Label(controls, text="Обновление требует подтверждения точного плана." if (self.installed_context or self.working_context) else "Для рабочего Windows-запуска сначала подготовьте анализаторы.").pack(side="left", padx=5)
        install_frame = self.tabs.nametowidget(self.tabs.tabs()[4])
        self.layout_review = None
        if self.installed_context is None:
            self._layout_controls(install_frame)
        restore_frame = self.tabs.nametowidget(self.tabs.tabs()[7])
        restore_controls = t.Frame(restore_frame)
        restore_controls.pack(side="bottom", fill="x", pady=4)
        self.history_button = t.Button(restore_controls, text="Обновить журнал", command=self._history)
        self.history_button.pack(side="left")
        self.rollback_preview_button = t.Button(restore_controls, text="Просмотр отката",
                                                command=lambda: self._restoration_review(False))
        self.rollback_preview_button.pack(side="left", padx=4)
        self.recovery_preview_button = t.Button(restore_controls, text="Просмотр восстановления",
                                                command=lambda: self._restoration_review(True))
        self.recovery_preview_button.pack(side="left", padx=4)
        self.conflict_preview_button = t.Button(restore_controls, text="Просмотр конфликтов",
                command=lambda: self._restoration_review(True, True))
        self.conflict_preview_button.pack(side="left", padx=4)
        self.restore_button = t.Button(restore_controls, text="Подтвердить восстановление",
                                      command=self._restore, state="disabled")
        self.restore_button.pack(side="right")
        self.tabs.bind("<<NotebookTabChanged>>", lambda _: self.refresh())
        footer = t.Frame(self.root, padding=(12, 0, 12, 9))
        footer.pack(fill="x")
        t.Label(footer, textvariable=self.status, wraplength=900).pack(side="left", fill="x", expand=True)
        self.check_button = t.Button(footer, text="Проверить" if (self.installed_context or self.working_context) else "Проверить (тестовая среда)", command=self._check, state="disabled")
        self.check_button.pack(side="right", padx=5)
        self.cancel_button = t.Button(footer, text="Отмена проверки", command=self._cancel_job, state="disabled")
        self.cancel_button.pack(side="right", padx=5)
        self.update_button = t.Button(footer, text="Обновить", command=self._update, state="disabled")
        self.update_button.pack(side="right", padx=5)

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
            width = 100 if "байт" in title else (135 if key == "c0" else 240)
            tree.column(key, width=width, minwidth=80, stretch=True)
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
        layout = self.presenter.layout_table(self.layout_review)
        if self.installed_context is not None:
            authority = self.installed_context
            cert = authority.certificate
            rows = (DisplayRow(("Установка", str(authority.root))),
                    DisplayRow(("Владелец SID", authority.owner_sid)),
                    DisplayRow(("Manifest SHA-256", cert["manifest_sha256"])),
                    DisplayRow(("Profile SHA-256", cert["profile_sha256"])),
                    DisplayRow(("Native QA SHA-256", cert["native_qa_sha256"])),
                    DisplayRow(("GUI QA SHA-256", cert["manual_gui_receipt"])))
            rows += tuple(DisplayRow(("Разрешённое назначение", str(p))) for p in authority.approved_roots)
            layout = DisplayTable("Защищённая установка", ("Свойство", "Значение"), rows,
                "Owner receipt загружен. Состав, ACL и заявленные маршруты повторно проверяются перед операцией.")
        if self.working_context is not None:
            layout = DisplayTable("Рабочий запуск Windows", ("Свойство", "Значение"), (
                DisplayRow(("Режим", "Проверка и обновление тестовых копий")),
                DisplayRow(("Исходники приложения", str(Path(__file__).resolve().parent.parent))),
                DisplayRow(("Анализаторы", str(self.working_context.runtime_root))),
                DisplayRow(("Реестр", str(self.working_context.registry_path))),
                DisplayRow(("Пакеты", str(self.policy_root))),
            ), "Функциональная проверка. Для независимого допуска позже нужна отдельная защищённая установка.")
        self._show_table("Установка / доверие", layout)
        storage = self.registry_error or ("Реестр сохраняется в JSON." if self.registry.store else "Реестр в памяти; для сохранения укажите --registry.")
        self.status.set((self.job_status or BLOCK_REASON) + " " + storage)
        self._show_table("Покрытие файлов", self.presenter.coverage_table(self.selected))
        self._show_table("Действующие правила", self.presenter.rules_table(self.selected))
        self._refresh_job_buttons()
        self._refresh_pack_selector()
        tree = self.tables["Проекты"][0]
        tree.bind("<<TreeviewSelect>>", self._on_selected)
        for iid in tree.get_children():
            if tree.item(iid, "values")[0] == self.selected:
                tree.selection_set(iid)
                break

    def _on_selected(self, _event=None) -> None:
        tree = self.tables["Проекты"][0]
        selected = tree.selection()
        if not selected:
            return
        columns = tree.item(selected[0], "values")
        if columns:
            try:
                if self.registry_error:
                    return
                self.registry.select(str(columns[0]))
            except (OSError, ValueError) as exc:
                self.messagebox.showerror("Не удалось сохранить выбор", str(exc))
                return
            if self.selected != str(columns[0]) and self.active_check_project is not None:
                self._cancel_job()
            self.selected = str(columns[0])
            # Rebuild selected tabs only to avoid selection-change recursion.
            self._show_table("Проверка", self.presenter.scan_table(self.selected))
            self._show_table("Просмотр обновления", self.presenter.preview_table(self.selected))
            binding = self.presenter.bindings_table(self.selected)
            self._show_table("Правила", binding)
            self._show_table("Покрытие файлов", self.presenter.coverage_table(self.selected))
            self._show_table("Действующие правила", self.presenter.rules_table(self.selected))
            self._refresh_job_buttons()

    def _import_registration(self) -> None:
        path = self.filedialog.askopenfilename(title="Регистрация JSON (только данные)",
                                              filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            candidate = Path(path)
            if candidate.stat().st_size > MAX_REGISTRATION_JSON:
                raise ValueError("Файл JSON превышает установленный предел размера")
            project = Registration.from_json(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.messagebox.showerror("Некорректная регистрация", str(exc))
            return
        self._save_project(project)

    def _edit_project(self) -> None:
        project = self.presenter.registrations.get(self.selected)
        if project:
            RegistrationEditor(self, project)

    def _save_project(self, project: Registration) -> bool:
        try:
            if self.registry_error:
                raise ValueError("Сохранение заблокировано: реестр не был корректно загружен. " + self.registry_error)
            if self.jobs and self.jobs.busy:
                raise ValueError("Дождитесь завершения или отмены текущей операции")
            if self.policy_root is not None:
                for pack_id in project.policy_pack_ids:
                    try:
                        PolicyStore(self.policy_root).load(pack_id)
                    except FileNotFoundError as exc:
                        raise ValueError(f"Пакет {pack_id!r} отсутствует. Выберите ID из каталога на вкладке «Правила».") from exc
            self.registry.put(project)
            self.check_results.pop(project.registration_id, None)
            if self.promotion:
                self.promotion.invalidate(project.registration_id)
        except (OSError, ValueError, TypeError) as exc:
            self.messagebox.showerror("Не удалось сохранить регистрацию", str(exc))
            return False
        self.selected = project.registration_id
        self.refresh()
        return True

    def _remove(self) -> None:
        if not self.selected:
            return
        try:
            if self.registry_error:
                raise ValueError(self.registry_error)
            if self.jobs and self.jobs.busy:
                raise ValueError("Дождитесь завершения или отмены текущей операции")
            self.registry.remove(self.selected)
            self.check_results.pop(self.selected, None)
            if self.promotion:
                self.promotion.invalidate(self.selected)
        except (OSError, ValueError) as exc:
            self.messagebox.showerror("Не удалось удалить регистрацию", str(exc))
            return
        self.selected = self.registry.document.last_selected or ""
        self.refresh()

    def _policy_controls(self, frame):
        t = self.ttk
        controls = t.Frame(frame)
        controls.pack(side="bottom", fill="x", pady=5)
        self.pack_choice = self.tk.StringVar()
        self.pack_selector = t.Combobox(controls, textvariable=self.pack_choice, state="readonly", width=20)
        self.pack_selector.pack(side="left")
        self.policy_buttons = []
        for text, command in (("Новый пакет", lambda: self._edit_policy(new=True)),
                ("Изменить", self._edit_policy), ("Копия", lambda: self._edit_policy(copy=True)), ("Удалить пакет", self._delete_policy),
                ("Привязать", lambda: self._bind_policy("add")),
                ("Отвязать", lambda: self._bind_policy("remove")),
                ("Только этот пакет", lambda: self._bind_policy("replace"))):
            button = t.Button(controls, text=text, command=command)
            button.pack(side="left", padx=2)
            self.policy_buttons.append(button)
        self.binding_buttons = self.policy_buttons[-3:]
        t.Label(frame, text="Общие пакеты: сохранение влияет на всех потребителей. "
                "Выберите пакет из каталога и привяжите его к проекту. Сохранение правил проверяется анализаторами.",
                wraplength=1000).pack(side="bottom", fill="x")

    def _refresh_pack_selector(self):
        if self.policy_root is None:
            return
        try:
            packs = PolicyStore(self.policy_root).list_packs()
            values = tuple(p.pack_id for p in packs)
            self.pack_selector.configure(values=values)
            if self.pack_choice.get() not in values:
                self.pack_choice.set(values[0] if values else "")
        except (ValueError, OSError, TypeError) as exc:
            self.pack_selector.configure(values=())
            self.job_status = "Ошибка пакетов: " + str(exc)
            self.status.set(self.job_status)

    def _refresh_job_buttons(self):
        busy = self.jobs is not None and self.jobs.busy
        enabled = self.jobs is not None and not busy and not self.registry_error
        self.check_button.configure(state="normal" if enabled and self.selected else "disabled")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        selected_project = self.presenter.registrations.get(self.selected)
        review_enabled = (enabled and self.selected in self.check_results
                          and selected_project is not None and selected_project.target_root is not None)
        self.preview_button.configure(state="normal" if review_enabled else "disabled")
        self.import_button.configure(state="normal" if review_enabled else "disabled")
        native = bool(enabled and self.promotion and self.promotion.update_available)
        current_review = (self.active_review is not None and selected_project is not None
                          and self.active_review.check.project == selected_project)
        self.update_button.configure(state="normal" if native and current_review else "disabled")
        self.restore_button.configure(state="normal" if native and self.restoration else "disabled")
        for button in (self.history_button, self.rollback_preview_button, self.recovery_preview_button, self.conflict_preview_button):
            button.configure(state="normal" if enabled else "disabled")
        for button in self.policy_buttons:
            binding = button in getattr(self, "binding_buttons", ())
            catalog_enabled = self.policy_root is not None and not busy and not self.registry_error
            button.configure(state="normal" if enabled or (binding and catalog_enabled) else "disabled")

    def _edit_policy(self, new=False, copy=False):
        if not self.jobs or self.jobs.busy:
            return
        try:
            pack = None if new else PolicyStore(self.jobs.settings.policy_root).load(self.pack_choice.get())
            self.policy_editor = PolicyEditor(self, pack, copy)
        except (ValueError, OSError, TypeError) as exc:
            self.messagebox.showerror("Пакет не открыт", str(exc))

    def _delete_policy(self):
        if not self.jobs or self.jobs.busy:
            return
        try:
            key = self.pack_choice.get()
            pack = PolicyStore(self.jobs.settings.policy_root).load(key)
            if any(key in p.policy_pack_ids for p in self.presenter.registrations.values()):
                raise ValueError("Пакет используется. Сначала замените или уберите его привязки.")
            if self.messagebox.askyesno("Удаление пакета", f"Удалить неиспользуемый пакет {pack.name}?"):
                PolicyService(self.jobs.settings).remove(key, pack.fingerprint(), tuple(self.presenter.registrations.values()))
                self.refresh()
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("Пакет не удалён", str(exc))

    def _save_policy(self, pack, expected, editor):
        self.active_check_project = None
        self.active_ticket = self.jobs.start_policy_save(pack, expected,
                                                        tuple(self.presenter.registrations.values()))
        self.policy_editor = editor
        self.job_status = "Проверяется пакет; прежние правила пока действуют."
        self._refresh_job_buttons()

    def _bind_policy(self, mode):
        project = self.presenter.registrations.get(self.selected)
        if not project or self.policy_root is None or (self.jobs and self.jobs.busy):
            return
        try:
            key = self.pack_choice.get()
            PolicyStore(self.policy_root).load(key)
            if mode == "replace":
                keys = (key,)
            elif mode == "remove":
                keys = tuple(p for p in project.policy_pack_ids if p != key)
            else:
                keys = tuple(dict.fromkeys((*project.policy_pack_ids, key)))
            self._save_project(replace(project, policy_pack_ids=keys))
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("Привязка не изменена", str(exc))

    def _check(self):
        if not self.jobs or self.registry_error:
            return
        project = self.presenter.registrations.get(self.selected)
        if project is None:
            return
        try:
            self.check_results.pop(project.registration_id, None)
            if self.promotion:
                self.promotion.invalidate(project.registration_id)
            self.active_review = None
            self.active_ticket = self.jobs.start(project)
            self.active_check_project = project.registration_id
            self.presenter.cancel_review(project.registration_id)
            self.job_status = "Проверка выполняется; файлы назначения не меняются."
            self.refresh()
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("Проверка не начата", str(exc))

    def _review(self, first_import=False):
        project = self.presenter.registrations.get(self.selected)
        check = self.check_results.get(self.selected)
        if not project or check is None or not self.jobs or self.jobs.busy:
            return
        try:
            self.active_review = None
            self.presenter.previews.pop(project.registration_id, None)
            self.promotion.invalidate(project.registration_id)
            self.active_ticket = self.jobs.start_review(self.promotion, check, project, first_import=first_import)
            self.active_check_project = project.registration_id
            self.job_status = "Формируется полный просмотр. Назначение не изменяется."
            self.refresh()
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("Просмотр не сформирован", str(exc))

    def _update(self):
        review = self.active_review
        project = self.presenter.registrations.get(self.selected)
        if (not self.jobs or self.jobs.busy or review is None or project is None
                or review.check.project != project or not self.promotion.update_available):
            return
        counts = {kind: sum(c.kind == kind for c in review.preview.changes)
                  for kind in ("create", "modify", "delete", "unchanged")}
        text = (f"Назначение: {review.preview.target_root}\n"
                f"Файлы: {counts}\nСоздать каталогов: {len(review.preview.created_directories)}\n"
                f"План: {review.fingerprint}\n\n"
                "Применить этот просмотр? Изменения source, правил или назначения отменят подтверждение.")
        if not self.messagebox.askyesno("Подтвердить точное обновление", text, parent=self.root):
            return
        try:
            self.active_ticket = self.jobs.start_transaction(self.promotion, "apply", review, project)
            self.active_review = None
            self.active_check_project = project.registration_id
            self._refresh_job_buttons()
        except (ValueError, OSError) as exc:
            self.messagebox.showerror("Обновление не начато", str(exc))

    def _history(self):
        if self.jobs and not self.jobs.busy:
            self.restoration = None
            self.active_ticket = self.jobs.start_transaction(self.promotion, "history")
            self._refresh_job_buttons()

    def _selected_operation(self):
        tree = self.tables["Восстановление"][0]
        selected = tree.selection()
        return str(tree.item(selected[0], "values")[0]) if selected else None

    def _restoration_review(self, recovery, include_conflicts=False):
        key = self._selected_operation()
        if key and self.jobs and not self.jobs.busy:
            self.restoration = None
            self.active_ticket = self.jobs.start_transaction(self.promotion, "restoration_review", key, recovery, include_conflicts)
            self._refresh_job_buttons()

    def _restore(self):
        review = self.restoration
        if (not review or not self.jobs or self.jobs.busy or not self.promotion.update_available):
            return
        if self.messagebox.askyesno("Подтвердить просмотр восстановления",
                f"{review.target_root}\nОперация: {review.operation_id}\nПлан: {review.fingerprint}\n"
                f"Конфликтных файлов: {len(review.observed_conflicts)}. Их текущие bytes будут сохранены отдельно.\n"
                "Восстановить показанные файлы из проверенных backup?", parent=self.root):
            self.active_ticket = self.jobs.start_transaction(self.promotion, "restore", review)
            self.restoration = None
            self._refresh_job_buttons()

    def _cancel_job(self):
        if self.jobs:
            self.jobs.cancel()
        if self.active_check_project:
            self.presenter.cancel_review(self.active_check_project)
            self.check_results.pop(self.active_check_project, None)
            if self.promotion:
                self.promotion.invalidate(self.active_check_project)
        self.job_status = "Отмена: ожидание остановки процессов анализаторов."
        self.status.set(self.job_status)

    def _poll_jobs(self):
        if self.jobs:
            for event in self.jobs.drain():
                if event.job_id != self.active_ticket:
                    continue
                self.job_status = event.phase + ": " + event.detail
                if event.terminal:
                    if event.phase == "POLICY_SAVED":
                        affected = self.presenter.invalidate_shared_pack(event.result.pack_id)
                        for key in affected:
                            self.check_results.pop(key, None)
                            if self.promotion:
                                self.promotion.invalidate(key)
                        self.pack_choice.set(event.result.pack_id)
                        if self.policy_editor is not None:
                            self.policy_editor.window.destroy()
                            self.policy_editor = None
                    elif event.phase == "COMPLETE_DEVELOPMENT":
                        result = event.result
                        current = self.presenter.registrations.get(event.project_id)
                        if self.jobs.is_current(result, current):
                            self.check_results[event.project_id] = result
                            binding = self.presenter.begin_review(event.project_id, result.snapshot,
                                result.captured.combined_sha256, result.effective.tool_fingerprints)
                            self.presenter.set_reports(event.project_id, scan=replace(result.scan, binding=binding))
                            self.presenter.set_check_details(event.project_id, result.snapshot, result.coverage,
                                                            result.effective.validations, result.evidence_dir)
                            self.job_status = ("Обязательные проверки выполнены. Сформируйте просмотр обновления."
                                if self.installed_context and result.scan.status == "NOT_AUTHORIZED" and
                                any(r.content in ("code", "dependency") for r in result.snapshot.records) else
                                "Проверка: " + result.scan.status + ". Это НЕ ДОПУСК.")
                        else:
                            self.job_status = "STALE: регистрация, правила или инструменты изменились. Повторите Проверить."
                    elif event.phase == "REVIEW_READY":
                        review = event.result
                        if self.jobs.is_current(review.check, self.presenter.registrations.get(event.project_id)):
                            self.presenter.attach_promotion_preview(review.preview)
                            self.active_review = review
                            self.tabs.select(self.tabs.tabs()[3])
                            self.job_status = ("Просмотр готов: " + review.fingerprint +
                                (". Для применения нажмите Обновить." if self.promotion.update_available
                                 else ". Запись заблокирована до Windows-приёмки."))
                        else:
                            self.promotion.invalidate(event.project_id)
                            self.job_status = "STALE: выполните новую проверку."
                    elif event.phase == "TRANSACTIONS":
                        self.history_rows = event.result
                        self._show_table("Восстановление", DisplayTable("Журнал",
                            ("Операция", "Состояние", "Проект", "Назначение", "Контур"),
                            tuple(DisplayRow((r.operation_id, r.state, r.project_id, r.target_root, r.scope))
                                  for r in self.history_rows),
                            "Выберите операцию и сформируйте отдельный просмотр."))
                        self.tabs.select(self.tabs.tabs()[7])
                    elif event.phase == "RESTORATION_READY":
                        self.restoration = event.result
                        plan = self.restoration
                        rows = tuple(DisplayRow((c.kind, c.relative_path,
                            c.before_sha256 or "—", c.after_sha256 or "—",
                            str(c.before_size) if c.before_size is not None else "—",
                            str(c.after_size) if c.after_size is not None else "—"),
                            c.text_diff or c.diff_note or "") for c in plan.changes)
                        rows += tuple(DisplayRow(("remove-if-empty", d, "—", "—", "—", "—"),
                            "Убрать только если каталог создан этой операцией и до сих пор пуст.")
                                      for d in plan.created_directories)
                        self._show_table("Восстановление", DisplayTable("Просмотр восстановления",
                            ("Эффект", "Путь", "До SHA-256", "После SHA-256", "До, байт", "После, байт"), rows,
                            f"{plan.target_root}. Конфликтов: {len(plan.observed_conflicts)}. План: {plan.fingerprint}"))
                    elif event.phase == "TRANSACTION_RESULT":
                        outcome = event.result
                        self.active_review = None
                        self.restoration = None
                        self.check_results.clear()
                        for key in tuple(self.presenter.registrations):
                            self.presenter.cancel_review(key)
                        self.job_status = f"{outcome.state}: {outcome.detail}. Операция: {outcome.operation_id}"
                        self._show_table("Восстановление", DisplayTable("Результат",
                            ("Операция", "Состояние", "Контур"),
                            (DisplayRow((outcome.operation_id, outcome.state, outcome.scope), outcome.detail),),
                            outcome.detail))
                        self.tabs.select(self.tabs.tabs()[7])
                    elif self.policy_editor is not None:
                        self.policy_editor.notice.set(self.job_status)
                        self.policy_editor.save_button.configure(state="normal")
                    self.active_check_project = None
                    self.refresh()
                self.status.set(self.job_status)
            self._refresh_job_buttons()
        self.poll_timer = self.root.after(100, self._poll_jobs)

    def _close(self):
        if self.jobs and self.jobs.busy:
            self.jobs.cancel()
            self.status.set("Ожидание безопасного завершения операции…")
            self.root.after(100, self._close)
        else:
            self.root.after_cancel(self.poll_timer)
            self.root.destroy()

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
    import platform
    import subprocess
    parser = argparse.ArgumentParser(description="Project Checker")
    parser.add_argument("--model-smoke", action="store_true")
    parser.add_argument("--registry", type=Path, help="absolute registry JSON path")
    parser.add_argument("--development-settings", type=Path, help="explicit check-only development profile")
    setup = parser.add_mutually_exclusive_group()
    setup.add_argument("--prepare-source-runtime", action="store_true", help="owner: prepare offline Windows analyzers once")
    setup.add_argument("--resume-source-runtime", type=Path, help="owner: validate an already prepared runtime without reinstalling")
    setup.add_argument("--source-profile", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.model_smoke:
        presenter = ReviewPresenter()
        if presenter.can_apply():
            raise RuntimeError("Unsafe presenter unexpectedly enabled")
        print("GUI model ready. PROMOTION DISABLED. Windows visual QA NOT RUN.")
        return 0
    working = None
    policy_root = None
    startup_status = ""
    try:
        if args.prepare_source_runtime or args.resume_source_runtime or args.source_profile or (platform.system() == "Windows" and not args.development_settings):
            from .source_bootstrap import (default_registry, seed_policies, runtime_for, prepare_runtime,
                                           launch_runtime, load_context, resume_runtime, SETUP_HINT)
            args.registry = args.registry or default_registry()
            if not args.registry.is_absolute():
                raise ValueError("Use an absolute --registry path")
            if args.development_settings:
                raise ValueError("Source runtime and development profile are separate modes")
            policy_root = seed_policies(args.registry.parent / "policies")
            if args.prepare_source_runtime:
                prepare_runtime(args.registry)
                return 0
            if args.resume_source_runtime:
                resume_runtime(args.registry, args.resume_source_runtime)
                return 0
            if args.source_profile:
                working = load_context(args.source_profile, args.registry)
                from .environment import configure_gui_environment
                configure_gui_environment(working.runtime_root)
                startup_status = "Рабочая копия Windows. Назначение меняется только после отдельного подтверждения."
            else:
                runtime = runtime_for(args.registry)
                if runtime is not None:
                    return launch_runtime(runtime, args.registry)
                startup_status = SETUP_HINT + ' --registry "' + str(args.registry) + '"'
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        raise SystemExit("Project Checker: " + str(exc)) from exc
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError as exc:
        raise SystemExit("Tkinter is unavailable. Prepare the Windows runtime with --prepare-source-runtime.") from exc
    DesktopApp(tk, ttk, filedialog, messagebox, args.registry, args.development_settings,
               working_context=working, policy_root=policy_root, startup_status=startup_status).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
