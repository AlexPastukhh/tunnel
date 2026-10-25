"""Tk registration editor; no filesystem changes until explicit Save."""
from dataclasses import replace

from .registry import RegistrationDraft


class RegistrationEditor:
    def __init__(self, app, project=None):
        self.app = app
        self.draft = RegistrationDraft(project)
        self.tk, t = app.tk, app.ttk
        self.window = self.tk.Toplevel(app.root)
        self.window.title("Регистрация проекта")
        self.window.geometry("900x550")
        self.window.transient(app.root)
        self.window.grab_set()
        self.name = self.tk.StringVar(value=project.name if project else "")
        from .policies import PolicyStore
        catalog = ()
        if getattr(app, "policy_root", None) is not None:
            try:
                catalog = PolicyStore(app.policy_root).list_packs()
            except (OSError, ValueError):
                pass
        available = tuple(p.pack_id for p in catalog)
        initial = ", ".join(project.policy_pack_ids) if project else ("starter" if "starter" in available else "")
        self.packs = self.tk.StringVar(value=initial)
        self.target = self.tk.StringVar(value=(project.target_root or "") if project else "")
        fields = t.Frame(self.window, padding=10)
        fields.pack(fill="x")
        for row, (label, variable) in enumerate((("Название", self.name),
                ("Пакеты (ID через запятую)", self.packs),
                ("Корень назначения (пусто = только проверка)", self.target))):
            t.Label(fields, text=label).grid(row=row, column=0, sticky="w", pady=3)
            widget = (t.Combobox(fields, textvariable=variable, values=available, width=65)
                      if variable is self.packs else t.Entry(fields, textvariable=variable, width=65))
            widget.grid(row=row, column=1, sticky="ew")
        fields.columnconfigure(1, weight=1)
        t.Button(fields, text="Выбрать назначение", command=self.choose_target).grid(row=3, column=1, sticky="e")
        t.Label(fields, text="Для каждого source задаётся путь внутри корня назначения. "
                "При пустом корне перенос не настраивается.", wraplength=800).grid(row=4, column=0, columnspan=2, sticky="w")
        t.Label(fields, text="Доступные пакеты: " + ("; ".join(p.pack_id + " — " + p.name for p in catalog)
                or "каталог пока пуст"), wraplength=800).grid(row=5, column=0, columnspan=2, sticky="w")
        self.tree = t.Treeview(self.window, columns=("kind", "source", "target", "content"), show="headings")
        for column, title in (("kind", "Тип"), ("source", "Источник"), ("target", "Относительное назначение"), ("content", "Состав")):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=110 if column == "kind" else 330)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        controls = t.Frame(self.window, padding=10)
        controls.pack(fill="x")
        t.Button(controls, text="Добавить файлы", command=self.choose_files).pack(side="left")
        t.Button(controls, text="Добавить папку", command=self.choose_folder).pack(side="left", padx=4)
        t.Button(controls, text="Убрать выбор", command=self.remove).pack(side="left")
        self.mapping = self.tk.StringVar()
        t.Entry(controls, textvariable=self.mapping, width=24).pack(side="left", padx=4)
        t.Button(controls, text="Задать mapping", command=self.set_mapping).pack(side="left")
        t.Button(controls, text="Отмена", command=self.window.destroy).pack(side="right")
        t.Button(controls, text="Сохранить", command=self.save).pack(side="right", padx=4)
        scope = t.Frame(self.window, padding=10)
        scope.pack(fill="x")
        self.content = self.tk.StringVar(value="code")
        t.Combobox(scope, textvariable=self.content, state="readonly",
                   values=("code", "dependency", "resource", "data"), width=13).pack(side="left")
        self.exclusions = self.tk.StringVar()
        t.Label(scope, text="Исключения папки (пути через ;)").pack(side="left", padx=5)
        t.Entry(scope, textvariable=self.exclusions, width=42).pack(side="left")
        t.Button(scope, text="Задать состав", command=self.set_scope).pack(side="left", padx=5)
        t.Label(self.window, text="code/dependency: обязателен анализ. resource: только профиль ресурсов; "
                "data: сохранять, не переносить. Исключения явные, без масок.",
                wraplength=850).pack(fill="x", padx=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_selected)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for index, entry in enumerate(self.draft.selections):
            self.tree.insert("", "end", iid=str(index), values=(entry.kind, entry.source, entry.target or "", entry.content))

    def choose_target(self):
        path = self.app.filedialog.askdirectory(parent=self.window, title="Корень внешнего назначения")
        if path:
            self.target.set(path)

    def choose_files(self):
        paths = self.app.filedialog.askopenfilenames(parent=self.window, title="Файлы для проверки")
        self.add("file", tuple(paths))

    def choose_folder(self):
        path = self.app.filedialog.askdirectory(parent=self.window, title="Папка для проверки")
        self.add("directory", (path,) if path else ())

    def add(self, kind, paths):
        try:
            self.draft.add(kind, paths)
            self.refresh()
        except (ValueError, TypeError) as exc:
            self.app.messagebox.showerror("Неверный выбор", str(exc), parent=self.window)

    def remove(self):
        selected = self.tree.selection()
        if selected:
            del self.draft.selections[int(selected[0])]
            self.refresh()

    def on_selected(self, _event=None):
        selected = self.tree.selection()
        if selected:
            entry = self.draft.selections[int(selected[0])]
            self.mapping.set(entry.target or "")
            self.content.set(entry.content)
            self.exclusions.set("; ".join(entry.excluded_paths))

    def set_scope(self):
        selected = self.tree.selection()
        if selected:
            index = int(selected[0])
            candidate = replace(self.draft.selections[index], content=self.content.get(),
                excluded_paths=tuple(p.strip() for p in self.exclusions.get().split(";") if p.strip()))
            try:
                candidate.validate()
                self.draft.selections[index] = candidate
                self.refresh()
            except ValueError as exc:
                self.app.messagebox.showerror("Неверный состав", str(exc), parent=self.window)

    def set_mapping(self):
        selected = self.tree.selection()
        if selected:
            index = int(selected[0])
            candidate = replace(self.draft.selections[index], target=self.mapping.get())
            try:
                candidate.validate()
                self.draft.selections[index] = candidate
                self.refresh()
            except ValueError as exc:
                self.app.messagebox.showerror("Неверное назначение", str(exc), parent=self.window)

    def save(self):
        try:
            project = self.draft.build(self.name.get(),
                tuple(p.strip() for p in self.packs.get().split(",") if p.strip()),
                self.target.get().strip() or None)
        except (ValueError, TypeError) as exc:
            self.app.messagebox.showerror("Неверная регистрация", str(exc), parent=self.window)
            return
        if self.app._save_project(project):
            self.window.destroy()
