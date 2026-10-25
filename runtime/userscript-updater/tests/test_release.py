"""Release boundary and archive regressions; no native acceptance is inferred."""
import base64
import csv
import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from checker.engines import EngineConfig, build_argv, command_batches
from checker.installed import InstalledAuthority, WindowsTarget
from checker.model import ContractError
from checker.promotion import PromotionService
from release.build_bundle import inspect_wheel


class ReleaseTests(unittest.TestCase):
    def test_development_cannot_construct_installed_writer(self):
        with self.assertRaises(ContractError):
            WindowsTarget(object())
        if os.name != "nt":
            with self.assertRaisesRegex(ContractError, "Windows"):
                InstalledAuthority(Path("/untrusted"))

    def test_native_semgrep_uses_actual_console_entry_not_deprecated_module(self):
        config = EngineConfig("semgrep", Path("/trusted/python.exe"), "pin", Path("/trusted/rules.json"), "pin")
        argv = build_argv(config, (Path("/snapshot/a.js"),))
        self.assertIn("-I", argv)
        self.assertIn("-S", argv)
        self.assertNotIn("-m", argv)
        self.assertIn("--legacy", argv)
        self.assertIn("--jobs=1", argv)
        self.assertIn("semgrep.console_scripts.entrypoint", argv[argv.index("-c") + 1])
        self.assertEqual(argv[-2:], ["--", "/snapshot/a.js"])

    def wheel(self, root, *, corrupt=False, traversal=False):
        path = root / "fixture-1.0-py3-none-any.whl"
        members = {"fixture/__init__.py": b"answer = 42\n",
                   "fixture-1.0.dist-info/METADATA": b"Name: fixture\nVersion: 1.0\n"}
        if traversal:
            members["../escape.py"] = b"escape"
        rows = []
        for name, raw in members.items():
            sha = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode()
            rows.append((name, "sha256=" + ("A" * len(sha) if corrupt else sha), str(len(raw))))
        rows.append(("fixture-1.0.dist-info/RECORD", "", ""))
        record = io.StringIO()
        csv.writer(record).writerows(rows)
        members[rows[-1][0]] = record.getvalue().encode()
        with zipfile.ZipFile(path, "w") as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_wheel_pin_record_and_platform_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            path, pin = self.wheel(Path(temporary))
            result = inspect_wheel(path, {pin})
            self.assertEqual((result["name"], result["version"]), ("fixture", "1.0"))
            with self.assertRaisesRegex(ValueError, "not pinned"):
                inspect_wheel(path, {"wrong"})
            path, pin = self.wheel(Path(temporary), corrupt=True)
            with self.assertRaisesRegex(ValueError, "RECORD"):
                inspect_wheel(path, {pin})

    def test_wheel_traversal_is_never_extracted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path, pin = self.wheel(Path(temporary), traversal=True)
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                inspect_wheel(path, {pin})


    def test_folder_commands_fit_utf16_windows_limit_without_dropping_files(self):
        from unittest.mock import patch
        config = EngineConfig("semgrep", Path("/trusted/semgrep"), "pin", Path("/trusted/rules.json"), "pin")
        files = tuple(Path("/snapshot/") / ("日本語😀" * 20 + str(i) + ".js") for i in range(500))
        with patch("checker.engines.MAX_ARG_CHARS", 1000):
            batches = command_batches(config, files)
        self.assertGreater(len(batches), 1)
        self.assertEqual(tuple(p for batch in batches for p in batch), files)
        import subprocess
        for batch in batches:
            units = len(subprocess.list2cmdline(build_argv(config, batch)).encode("utf-16-le")) // 2
            self.assertLessEqual(units, 1000)

    @unittest.skipUnless(os.environ.get("UPDATER_DEV_SEMGREP"), "Real Semgrep required")
    def test_actual_console_entry_point_on_safe_fixtures(self):
        import subprocess
        from checker.environment import analyzer_environment
        from checker.reports import parse_semgrep
        cli = Path(os.environ["UPDATER_DEV_SEMGREP"])
        python = cli.parent / "python"
        rules = Path(__file__).resolve().parent.parent / "release/base-semgrep.json"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            js, py = root / "a.js", root / "b.py"
            js.write_text("const answer = 42;\n")
            py.write_text("answer = 42\n")
            config = EngineConfig("semgrep", Path("/trusted/python.exe"), "pin", rules, "pin")
            argv = build_argv(config, (js, py))
            argv[0] = str(python)
            argv.remove("-S")  # Linux dev venv uses site; installed Windows ._pth supplies the pinned closure.
            for expected in ("STRUCTURAL_CLEAR", "FINDINGS"):
                if expected == "FINDINGS":
                    js.write_text("eval('1');\n")
                process = subprocess.run(argv, cwd=root, env=analyzer_environment(root),
                                         capture_output=True, text=True, encoding="utf-8", timeout=30)
                report = parse_semgrep(process.stdout, process.returncode, (js, py), root)
                self.assertEqual(report.status, expected, report)
