"""Direct shared-pack edit/copy UI; actual validation/save runs in background."""
import json

from .policies import PolicyPack
from .registry import unique_object


class PolicyEditor:
    def __init__(self, app, pack=None, copy=False):
        self.app = app
        tk, t = app.tk, app.ttk
        self.window = tk.Toplevel(app.root)
        self.window.title("Общий пакет правил")
        self.window.geometry("820x660")
        self.window.transient(app.root)
        self.window.grab_set()
        self.expected = pack.fingerprint() if pack and not copy else None
        self.pack_id = tk.StringVar(value=pack.pack_id if pack and not copy else "")
        self.name = tk.StringVar(value=(pack.name + (" (копия)" if copy else "")) if pack else "")
        fields = t.Frame(self.window, padding=10)
        fields.pack(fill="x")
        for row, (label, variable) in enumerate((("ID пакета", self.pack_id), ("Название", self.name))):
            t.Label(fields, text=label).grid(row=row, column=0, sticky="w")
            entry = t.Entry(fields, textvariable=variable, width=65)
            entry.grid(row=row, column=1, sticky="ew")
            if row == 0 and self.expected:
                entry.configure(state="readonly")
        fields.columnconfigure(1, weight=1)
        t.Label(fields, text="Сохранение действует сразу для всех привязанных проектов. "
                "Для отдельного набора создайте копию и смените привязку.", wraplength=770).grid(row=2, column=0, columnspan=2)
        t.Label(self.window, text="Встроенные правила ESLint: JSON {rule-id: off/warn/error}").pack(anchor="w", padx=10)
        self.eslint = tk.Text(self.window, height=6, wrap="none")
        self.eslint.pack(fill="x", padx=10)
        self.eslint.insert("1.0", json.dumps(pack.eslint_core_rules if pack else {"no-eval": "error"}, indent=2))
        t.Label(self.window, text="Локальные правила Semgrep: YAML/JSON (можно оставить пустым)").pack(anchor="w", padx=10)
        self.semgrep = tk.Text(self.window, height=12, wrap="none")
        self.semgrep.pack(fill="both", expand=True, padx=10, pady=5)
        self.semgrep.insert("1.0", pack.semgrep_rules_text if pack else "")
        self.notice = tk.StringVar(value="До успешной проверки анализаторами старый пакет сохраняется.")
        t.Label(self.window, textvariable=self.notice, wraplength=770).pack(fill="x", padx=10)
        controls = t.Frame(self.window, padding=10)
        controls.pack(fill="x")
        self.save_button = t.Button(controls, text="Проверить и сохранить пакет", command=self.save)
        self.save_button.pack(side="right")
        t.Button(controls, text="Отмена", command=self.cancel).pack(side="right", padx=6)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

    def save(self):
        try:
            rules = json.loads(self.eslint.get("1.0", "end-1c"), object_pairs_hook=unique_object)
            pack = PolicyPack(self.pack_id.get().strip(), self.name.get(), rules,
                              self.semgrep.get("1.0", "end-1c"))
            pack.validate()
            self.app._save_policy(pack, self.expected, self)
            self.save_button.configure(state="disabled")
            self.notice.set("Валидация пакета и всех затронутых привязок…")
        except (ValueError, TypeError, OSError) as exc:
            self.app.messagebox.showerror("Пакет не сохранён", str(exc), parent=self.window)

    def cancel(self):
        if self.app.jobs and self.app.jobs.busy:
            self.app.jobs.cancel()
        self.app.policy_editor = None
        self.window.destroy()
