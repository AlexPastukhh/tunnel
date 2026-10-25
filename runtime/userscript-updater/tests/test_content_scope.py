"""Complete folder/scope regressions; safe private Docker fixtures only."""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from checker.coverage import build_coverage_matrix
from checker.inventory import make_snapshot, unchanged_since_snapshot
from checker.model import ContractError, Registration, Selection
from checker.preview import build_target_preview
from checker.reports import summarize


class ContentScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.target = self.root / "target"
        self.target.mkdir()
        self.reg = Registration("scope", "Scope", (Selection("directory", str(self.source), "app"),),
                                ("rules",), str(self.target))

    def snap(self, reg=None):
        return make_snapshot(reg or self.reg, (self.source,), self.root / "snapshots")

    def test_empty_directory_create_and_inventory_drift(self):
        (self.source / "a" / "empty").mkdir(parents=True)
        snapshot = self.snap()
        self.assertEqual(len(snapshot.records), 0)
        preview = build_target_preview(snapshot, self.target, ())
        self.assertEqual(preview.created_directories, ("app", "app/a", "app/a/empty"))
        self.assertEqual(summarize(snapshot, "rules", ()).status, "NOT_AUTHORIZED")
        self.assertEqual(build_coverage_matrix(snapshot, (), {}).status, "NOT_AUTHORIZED")
        (self.source / "a" / "another").mkdir()
        self.assertFalse(unchanged_since_snapshot(self.reg, (self.source,), snapshot))

    def test_delete_only_preserves_owner_files_and_empty_directories(self):
        (self.target / "app").mkdir()
        (self.target / "app" / "removed.js").write_text("old")
        (self.target / "owner.bin").write_bytes(b"owner")
        (self.target / "owner-empty").mkdir()
        preview = build_target_preview(self.snap(), self.target, ("app/removed.js",))
        self.assertEqual([(c.kind, c.relative_path) for c in preview.changes],
                         [("delete", "app/removed.js")])
        self.assertIn("owner.bin", preview.preserved)
        self.assertIn("owner-empty", preview.preserved_directories)

    def test_excluded_previous_path_is_preserved_and_visible(self):
        (self.source / "main.js").write_text("const x = 1;")
        (self.source / "cache").mkdir()
        (self.source / "cache" / "untrusted.js").write_text("eval(x)")
        (self.target / "app" / "cache").mkdir(parents=True)
        (self.target / "app" / "cache" / "untrusted.js").write_text("owner")
        reg = replace(self.reg, selections=(replace(self.reg.selections[0], excluded_paths=("cache",)),))
        snapshot = self.snap(reg)
        self.assertEqual(len(snapshot.records), 1)
        preview = build_target_preview(snapshot, self.target, ("app/cache/untrusted.js",))
        self.assertIn("app/cache/untrusted.js", preview.preserved)
        self.assertEqual(preview.excluded_scope[0][0], "app/cache")

    def test_resource_is_explicit_unscanned_and_code_cannot_be_resource(self):
        (self.source / "photo.png").write_bytes(b"fixture image bytes")
        reg = replace(self.reg, selections=(Selection("file", str(self.source / "photo.png"),
                                                     "photo.png", "resource"),))
        snapshot = self.snap(reg)
        matrix = build_coverage_matrix(snapshot, (), {})
        self.assertEqual(matrix.status, "NOT_AUTHORIZED")
        self.assertIn("no code analysis", matrix.files[0].reason)
        self.assertEqual(summarize(snapshot, "rules", ()).status, "NOT_AUTHORIZED")
        (self.source / "code.js").write_text("eval(x)")
        bad = replace(reg, selections=(Selection("file", str(self.source / "code.js"), "code.js", "resource"),))
        with self.assertRaises(ContractError):
            self.snap(bad)

    def test_declared_data_is_never_copied_or_deleted(self):
        (self.source / "data").mkdir()
        (self.source / "data" / "private.bin").write_bytes(b"source")
        (self.target / "data").mkdir()
        (self.target / "data" / "private.bin").write_bytes(b"owner")
        reg = replace(self.reg, selections=(Selection("directory", str(self.source / "data"), "data", "data"),))
        snapshot = self.snap(reg)
        preview = build_target_preview(snapshot, self.target, ("data/private.bin",))
        self.assertFalse(preview.changes)
        self.assertIn("data/private.bin", preview.preserved)
        self.assertIn("never copied", preview.excluded_scope[0][1])

    def test_legacy_registration_and_scope_roundtrip(self):
        reg = replace(self.reg, selections=(replace(self.reg.selections[0], content="dependency",
                                                   excluded_paths=("node_modules", ".git")),))
        self.assertEqual(Registration.from_json(reg.to_json()), reg)
        import json
        legacy = json.loads(self.reg.to_json())
        for selection in legacy["selections"]:
            selection.pop("content")
            selection.pop("excluded_paths")
        self.assertEqual(Registration.from_json(json.dumps(legacy)), self.reg)


    def test_json_exclusion_string_is_not_coerced_to_characters(self):
        import json
        raw = json.loads(self.reg.to_json())
        raw["selections"][0]["excluded_paths"] = "cache"
        with self.assertRaises(ContractError):
            Registration.from_json(json.dumps(raw))

    def test_data_destination_cannot_be_overwritten_by_another_mapping(self):
        code = self.source / "main.js"
        code.write_text("const answer = 42;")
        data = self.source / "data"
        data.mkdir()
        reg = replace(self.reg, selections=(Selection("file", str(code), "data/main.js"),
                    Selection("directory", str(data), "data", "data")))
        with self.assertRaisesRegex(ContractError, "data destination"):
            build_target_preview(self.snap(reg), self.target, ())


    def test_single_missing_source_is_visible_deletion_candidate_only(self):
        absent = self.source / "removed.js"
        reg = replace(self.reg, selections=(Selection("file", str(absent), "removed.js"),))
        (self.target / "removed.js").write_text("previous")
        snapshot = self.snap(reg)
        self.assertEqual(len(snapshot.missing), 1)
        self.assertEqual(build_coverage_matrix(snapshot, (), {}).status, "NOT_AUTHORIZED")
        unmanaged = build_target_preview(snapshot, self.target, ())
        self.assertFalse(unmanaged.changes)
        self.assertIn("removed.js", unmanaged.preserved)
        managed = build_target_preview(snapshot, self.target, ("removed.js",))
        self.assertEqual([(c.kind, c.relative_path) for c in managed.changes], [("delete", "removed.js")])
        self.assertEqual(managed.missing_sources, ((str(absent), "removed.js"),))
        absent.write_text("new version appeared")
        self.assertFalse(unchanged_since_snapshot(reg, (self.source,), snapshot))

    def test_missing_selected_folder_is_distinct_from_unavailable_source_root(self):
        absent = self.source / "removed-folder"
        reg = replace(self.reg, selections=(Selection("directory", str(absent), "app"),))
        snapshot = self.snap(reg)
        self.assertEqual(snapshot.missing[0].kind, "directory")
        self.source.rmdir()
        with self.assertRaises(ContractError):
            self.snap(reg)
