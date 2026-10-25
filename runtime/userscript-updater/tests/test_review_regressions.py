import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checker.inventory import (make_snapshot, selected_files, unchanged_since_snapshot,
                               digest)
from checker.model import ContractError, Registration, Selection, relative_target
from checker.reports import parse_eslint, parse_semgrep, summarize, EngineReport


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / "a.js").write_text("let a = 1;")
        self.reg = Registration("r1", "source", (Selection("directory", str(self.src), "managed"),),
                                ("p",), str(self.root / "external"))

    def snapshot(self):
        return make_snapshot(self.reg, (self.root,), self.root / "review")

    def test_snapshot_keeps_source_extension(self):
        snap = self.snapshot()
        self.assertEqual(snap.records[0].snapshot_relative, "000000.js")
        self.assertEqual(digest((snap.root / "000000.js").read_bytes()), snap.records[0].sha256)

    def test_policy_or_mapping_binding_stales(self):
        snap = self.snapshot()
        modified = Registration("r1", "source", self.reg.selections, ("other-policy",), self.reg.target_root)
        self.assertFalse(unchanged_since_snapshot(modified, (self.root,), snap))

    def test_mutation_during_snapshot_is_rejected_and_cleaned(self):
        from checker import inventory
        original = inventory.read_stable_file
        mutated = []
        def changing(path):
            result = original(path)
            if not mutated:
                (self.src / "added.py").write_text("print('new')")
                mutated.append(True)
            return result
        with patch.object(inventory, "read_stable_file", side_effect=changing):
            with self.assertRaisesRegex(ContractError, "changed during snapshot"):
                self.snapshot()
        self.assertEqual(list((self.root / "review").iterdir()), [])

    def test_walk_error_not_ignored(self):
        def broken(_root, *, topdown, followlinks, onerror):
            onerror(PermissionError("denied"))
            return iter(())
        with patch("checker.inventory.os.walk", side_effect=broken):
            with self.assertRaisesRegex(ContractError, "Cannot enumerate"):
                list(selected_files(self.reg, (self.root,)))

    def test_empty_nested_directory_is_captured_and_binds_freshness(self):
        (self.src / "empty").mkdir()
        snapshot = self.snapshot()
        self.assertTrue(any(d.source_relative == "empty" for d in snapshot.directories))
        (self.src / "empty" / "nested").mkdir()
        self.assertFalse(unchanged_since_snapshot(self.reg, (self.root,), snapshot))

    def test_hardlink_rejected(self):
        other = self.src / "b.js"
        os.link(self.src / "a.js", other)
        with self.assertRaisesRegex(ContractError, "hardlink"):
            self.snapshot()

    def test_review_storage_under_source_rejected(self):
        with self.assertRaisesRegex(ContractError, "Review directory"):
            make_snapshot(self.reg, (self.root,), self.src / "review")

    def test_target_parent_conflict(self):
        (self.src / "b.js").write_text("let b = 2;")
        reg = Registration("x", "conflict", (
            Selection("file", str(self.src / "a.js"), "foo"),
            Selection("file", str(self.src / "b.js"), "foo/bar.js"),
        ), ("p",), str(self.root / "external"))
        with self.assertRaisesRegex(ContractError, "ancestor conflict"):
            list(selected_files(reg, (self.root,)))

    def test_windows_name_and_structure_rejections(self):
        for path in ("CON.js", "foo/NUL", "name.", "name ", "part//file.js",
                     "foo/../bar", "AUX", "foo/."):
            with self.subTest(path=path):
                with self.assertRaises(ContractError):
                    relative_target(path)

    def test_semgrep_missing_coverage_blocks(self):
        snap = self.snapshot()
        expected = (snap.root / snap.records[0].snapshot_relative,)
        payload = {"results": [], "errors": [], "paths": {"scanned": [], "skipped": []}}
        report = parse_semgrep(json.dumps(payload), 0, expected, snap.root)
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertEqual(summarize(snap, "pack-hash", (report,)).status, "INCOMPLETE")

    def test_semgrep_errors_skipped_rules_and_findings(self):
        snap = self.snapshot()
        expected = (snap.root / snap.records[0].snapshot_relative,)
        base = {"results": [], "errors": [], "paths": {"scanned": ["000000.js"], "skipped": []}}
        self.assertEqual(parse_semgrep(json.dumps(base), 0, expected, snap.root).status, "STRUCTURAL_CLEAR")
        for field, value, expected_status in (
            ("errors", [{"message": "parse error"}], "ERROR"),
            ("skipped_rules", ["bad-rule"], "INCOMPLETE"),
            ("results", [{"check_id": "x"}], "FINDINGS")
        ):
            with self.subTest(field=field):
                payload = {**base, field: value}
                self.assertEqual(parse_semgrep(json.dumps(payload), 0, expected, snap.root).status, expected_status)

    def test_eslint_fatal_ignored_and_output_error(self):
        snap = self.snapshot()
        expected = (snap.root / snap.records[0].snapshot_relative,)
        clear = [{"filePath": "000000.js", "messages": []}]
        self.assertEqual(parse_eslint(json.dumps(clear), 0, expected, snap.root).status, "STRUCTURAL_CLEAR")
        self.assertEqual(parse_eslint(json.dumps([]), 0, expected, snap.root).status, "ERROR")
        self.assertEqual(parse_eslint(json.dumps(clear), 2, expected, snap.root).status, "ERROR")
        bad = [{"filePath": "000000.js", "messages": [{"fatal": True, "message": "parser"}]}]
        self.assertEqual(parse_eslint(json.dumps(bad), 1, expected, snap.root).status, "ERROR")
        ignored = [{"filePath": "000000.js", "messages": [{"severity": 1, "message": "ignored"}]}]
        self.assertEqual(parse_eslint(json.dumps(ignored), 1, expected, snap.root).status, "FINDINGS")

    def test_fake_report_never_approves(self):
        snap = self.snapshot()
        path = str(snap.root / snap.records[0].snapshot_relative)
        fake = EngineReport("eslint", "STRUCTURAL_CLEAR", (path,), (path,), 0, "fake")
        self.assertEqual(summarize(snap, "packhash", (fake,)).status, "NOT_AUTHORIZED")

    def test_snapshot_tamper_denied(self):
        snap = self.snapshot()
        path = snap.root / snap.records[0].snapshot_relative
        path.write_text("malicious")
        self.assertEqual(summarize(snap, "packhash", ()).status, "ERROR")


    def test_bogus_engine_pin_is_error_and_never_executes(self):
        from checker.engines import EngineConfig, run_dev_engine
        snap = self.snapshot()
        bogus = EngineConfig("eslint", Path("/not-installed/eslint.js"), "bad",
                             Path("/not-installed/policy.js"), "bad", Path("/usr/local/bin/node"))
        outcome = run_dev_engine(snap, bogus)
        self.assertEqual(outcome.status, "ERROR")

    def test_semgrep_command_disables_gaps_by_explicit_flags(self):
        from checker.engines import EngineConfig, build_argv
        cfg = EngineConfig("semgrep", Path("/dummy/semgrep"), "", Path("/dummy/rules.yaml"), "")
        args = build_argv(cfg, (Path("/synthetic/000000.py"),))
        for flag in ("--no-git-ignore", "--disable-nosem", "--metrics=off", "--strict",
                     "--error", "--no-autofix", "--oss-only", "--disable-version-check"):
            self.assertIn(flag, args)
        self.assertNotIn("--allow-local-builds", args)
        self.assertNotIn("--allow-untrusted-validators", args)

    def test_file_limit_is_a_refusal_not_a_skip(self):
        from checker import inventory
        with patch.object(inventory, "MAX_FILE_BYTES", 2):
            with self.assertRaisesRegex(ContractError, "exceeds limit"):
                self.snapshot()



if __name__ == "__main__":
    unittest.main()
