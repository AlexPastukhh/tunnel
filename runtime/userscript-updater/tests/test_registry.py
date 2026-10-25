import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from checker.model import ContractError, Registration, Selection
from checker.registry import RegistryDocument, RegistrySession, RegistryStore, RegistrationDraft
from checker.ui_model import ReviewPresenter


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="checker-registry-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "state" / "проекты.json"
        self.presenter = ReviewPresenter()
        self.store = RegistryStore(self.path)
        self.session = RegistrySession(self.presenter, self.store)
        self.project = Registration("one", "Кириллица 日本語", (
            Selection("file", str(self.root / "файл.js"), "код/файл.js"),
            Selection("directory", str(self.root / "папка"), "проект"),
        ), ("shared", "extra"), str(self.root / "approved"))

    def test_save_restart_restore_mixed_mappings_and_last_selection(self):
        self.session.put(self.project)
        other = Registration("two", "Только проверка", (
            Selection("file", str(self.root / "другой.py")),), ("shared",))
        self.session.put(other)
        self.session.select("one")
        restored = ReviewPresenter()
        session = RegistrySession(restored, RegistryStore(self.path))
        self.assertEqual(restored.registrations, {"one": self.project, "two": other})
        self.assertEqual(session.document.last_selected, "one")
        self.assertIn("Кириллица 日本語", self.path.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(self.path.read_text())["schema_version"], 1)
        self.assertFalse(restored.can_apply("one"))

    def test_corrupt_or_unknown_schema_never_becomes_empty_registry(self):
        self.session.put(self.project)
        original = self.path.read_bytes()
        for raw in (b"{broken", b'{"schema_version":2,"registrations":[],"last_selected":null}',
                    b'{"schema_version":1,"schema_version":1,"registrations":[],"last_selected":null}'):
            self.path.write_bytes(raw)
            with self.subTest(raw=raw):
                with self.assertRaises(ContractError):
                    RegistrySession(ReviewPresenter(), self.store)
                with self.assertRaises(ContractError):
                    self.session.put(replace(self.project, name="Changed"))
                self.assertEqual(self.path.read_bytes(), raw)
                self.assertEqual(self.presenter.registrations["one"], self.project)
        self.path.write_bytes(original)

    def test_failed_replace_preserves_file_and_ui_and_cleans_owned_temp(self):
        self.session.put(self.project)
        original = self.path.read_bytes()
        with patch("checker.registry.os.replace", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                self.session.put(replace(self.project, name="Unsaved"))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.presenter.registrations["one"], self.project)
        self.assertEqual(set(p.name for p in self.path.parent.iterdir()), {self.path.name})

    def test_concurrent_editor_and_existing_lock_cannot_clobber_saved_state(self):
        self.session.put(self.project)
        second_view = ReviewPresenter()
        second = RegistrySession(second_view, self.store)
        self.session.put(replace(self.project, name="Saved first"))
        with self.assertRaisesRegex(ContractError, "another session"):
            second.put(replace(self.project, name="Stale second"))
        self.assertEqual(second_view.registrations["one"], self.project)
        self.assertEqual(self.store.load()[0].registrations[0].name, "Saved first")
        lock = self.path.with_name(self.path.name + ".lock")
        lock.write_text("synthetic other editor")
        with self.assertRaisesRegex(ContractError, "locked"):
            self.session.put(replace(self.project, name="Blocked"))
        self.assertEqual(lock.read_text(), "synthetic other editor")

    def test_invalid_edit_does_not_change_memory_or_disk(self):
        self.session.put(self.project)
        before = self.path.read_bytes()
        with self.assertRaises(ContractError):
            self.session.put(replace(self.project, name=" "))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.presenter.registrations["one"], self.project)

    def test_delete_clears_last_selection_and_does_not_reappear_after_restart(self):
        self.session.put(self.project)
        self.session.remove("one")
        restarted = RegistrySession(ReviewPresenter(), self.store)
        self.assertIsNone(restarted.document.last_selected)
        self.assertEqual(restarted.document.registrations, ())
        self.assertEqual(self.presenter.registrations, {})

    def test_duplicate_ids_and_unknown_selection_are_refused(self):
        for doc in (RegistryDocument((self.project, self.project), "one"),
                    RegistryDocument((self.project,), "unknown")):
            with self.subTest(doc=doc), self.assertRaises(ContractError):
                doc.serialize()
        with self.assertRaises(ContractError):
            self.session.select("unknown")
        self.assertFalse(self.path.exists())

    def test_picker_cancel_and_invalid_duplicate_are_atomic_draft_operations(self):
        draft = RegistrationDraft()
        draft.add("file", ())
        self.assertEqual(draft.selections, [])
        draft.add("file", (str(self.root / "один.js"), str(self.root / "два.py")))
        draft.add("directory", (str(self.root / "папка"),))
        saved = tuple(draft.selections)
        with self.assertRaises(ContractError):
            draft.add("file", (str(self.root / "ещё.js"), str(self.root / "один.js")))
        self.assertEqual(tuple(draft.selections), saved)
        check = draft.build("Смешанный", ("shared",), None)
        self.assertTrue(all(s.target is None for s in check.selections))
        promotion = draft.build("Смешанный", ("shared",), str(self.root / "approved"))
        self.assertEqual([s.target for s in promotion.selections], ["один.js", "два.py", "папка"])
        self.assertFalse(self.path.exists())
