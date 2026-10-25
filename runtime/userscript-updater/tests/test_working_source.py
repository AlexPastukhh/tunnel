"""Working-copy startup/authority regression tests. No Windows acceptance implied."""
import hashlib
import json
import os
import tempfile
import time
import unittest
import zipfile
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock, patch

from checker.engines import EngineConfig
from checker.gui import DesktopApp
from checker.inventory import digest
from checker.jobs import CheckJobs
from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyStore
from checker.promotion import PromotionService
from checker.registry import RegistryDocument, RegistryStore
from checker.settings import DevelopmentSettings
from checker.source_bootstrap import (BUNDLE_PREFIX, SOURCE_ROOT, extract_bundle, file_hash,
                                      prepare_runtime, runtime_for, seed_policies)
from checker.working import WorkingContext, WorkingSettings, WorkingWindowsTarget
from promotion_support import SyntheticTarget


class BootstrapTests(unittest.TestCase):
    def test_starter_created_once_and_owner_edits_or_invalid_file_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "policies"
            seed_policies(root)
            original = PolicyStore(root).load("starter")
            edited = replace(original, name="Owner edited")
            PolicyStore(root).update(edited, original.fingerprint())
            seed_policies(root)
            self.assertEqual(PolicyStore(root).load("starter").name, "Owner edited")
            (root / "starter.json").write_bytes(b"owner unfinished edit")
            seed_policies(root)
            self.assertEqual((root / "starter.json").read_bytes(), b"owner unfinished edit")

    def archive(self, root, *, unsafe=False, corrupt=False, extra=False):
        archive = root / "bundle.zip"
        name = "../escape" if unsafe else "profiles/base.json"
        content = b"safe fixture"
        files = [dict(path=name, size=len(content), sha256=digest(b"changed" if corrupt else content))]
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(BUNDLE_PREFIX + "bundle-manifest.json",
                            json.dumps(dict(schema_version=1, files=files)))
            output.writestr(BUNDLE_PREFIX + name, content)
            if extra:
                output.writestr(BUNDLE_PREFIX + "extra", b"unexpected")
        return archive

    def test_archive_pins_members_and_exact_closure_before_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.archive(root)
            extract_bundle(archive, root / "valid", file_hash(archive))
            self.assertEqual((root / "valid/profiles/base.json").read_bytes(), b"safe fixture")
            with self.assertRaisesRegex(ContractError, "archive SHA"):
                extract_bundle(archive, root / "bad-outer", "wrong")
            for options in (dict(unsafe=True), dict(corrupt=True), dict(extra=True)):
                archive = self.archive(root, **options)
                with self.subTest(options=options), self.assertRaises(ContractError):
                    extract_bundle(archive, root / "refused", file_hash(archive))
            self.assertFalse((root / "escape").exists())

    def test_missing_runtime_is_not_silently_installed_and_other_source_pointer_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "projects.json"
            self.assertIsNone(runtime_for(registry))
            (root / "source-runtime.json").write_text(json.dumps(dict(
                schema_version=1, source_root="/other/source", runtime_root=str(root / "runtimes/one"))))
            with self.assertRaisesRegex(ContractError, "different working folder"):
                runtime_for(registry)

    def test_preparation_cannot_execute_installers_outside_windows(self):
        with tempfile.TemporaryDirectory() as temporary, patch("checker.working.platform.system", return_value="Linux"), \
                patch("checker.source_bootstrap.subprocess.run") as execute:
            with self.assertRaisesRegex(ContractError, "Windows"):
                prepare_runtime(Path(temporary) / "projects.json")
            execute.assert_not_called()
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_owner_bootstrap_offline_commands_profile_and_failure_keep_existing_state(self):
        import subprocess
        from checker.source_bootstrap import launch_runtime, resume_runtime
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "projects.json"
            registry.write_bytes(b"existing owner registry")
            calls = []
            def payload(_archive, destination):
                (destination / "python-3.13.17-amd64.exe").write_bytes(b"fixture installer")
                (destination / "wheelhouse").mkdir()
                for name in ("requirements-windows.lock", "npm-package.json", "npm-package-lock.json"):
                    (destination / name).write_text("{}")
                (destination / "npm-cache").mkdir()
                (destination / "profiles").mkdir()
                for name in ("base-eslint.cjs", "base-semgrep.json"):
                    (destination / "profiles" / name).write_bytes((SOURCE_ROOT / "release" / name).read_bytes())
                with zipfile.ZipFile(destination / "node-v22.23.3-win-x64.zip", "w") as node:
                    node.writestr("node-v22.23.3-win-x64/node.exe", b"fixture node")
                    node.writestr("node-v22.23.3-win-x64/node_modules/npm/bin/npm-cli.js", b"npm")
            def execute(args, **_kwargs):
                calls.append(args)
                if Path(args[0]).name == "python-3.13.17-amd64.exe":
                    target = Path(next(a for a in args if a.startswith("TargetDir=")).split("=", 1)[1])
                    target.mkdir()
                    (target / "python.exe").write_bytes(b"fixture python")
                if "ci" in args:
                    eslint = Path(args[args.index("--prefix") + 1]) / "node_modules/eslint/bin"
                    eslint.mkdir(parents=True)
                    (eslint / "eslint.js").write_bytes(b"fixture eslint")
                return subprocess.CompletedProcess(args, 0)
            with patch("checker.working.require_windows_owner"), \
                    patch("checker.source_bootstrap.extract_bundle", side_effect=payload), \
                    patch("checker.source_bootstrap.subprocess.run", side_effect=execute), \
                    patch.dict(os.environ, {"SystemRoot": str(root / "windows")}):
                runtime = prepare_runtime(registry, root / "offline.zip")
                self.assertEqual(runtime_for(registry), runtime)
                settings = DevelopmentSettings.load(runtime / "source-profile.json")
                self.assertEqual(settings.policy_root, root / "policies")
                self.assertEqual({t.kind for t in settings.tools}, {"eslint", "semgrep"})
                pth = (runtime / "python/python313._pth").read_text()
                self.assertIn(str(SOURCE_ROOT), pth)
                self.assertNotIn("import site", pth)
                npm = next(args for args in calls if "ci" in args)
                self.assertIn("--offline", npm)
                self.assertIn("--ignore-scripts", npm)
                self.assertNotEqual(npm[npm.index("--userconfig") + 1], npm[npm.index("--globalconfig") + 1])
                pip = next(args for args in calls if "pip" in args)
                self.assertIn("--no-index", pip)
                self.assertIn("--require-hashes", pip)
                self.assertTrue(any("validate_runtime" in " ".join(args) for args in calls))
                with patch("checker.source_bootstrap.subprocess.call", return_value=0) as launch:
                    self.assertEqual(launch_runtime(runtime, registry), 0)
                    argv = launch.call_args.args[0]
                    self.assertEqual(argv[:5], [str(runtime / "python/python.exe"), "-I", "-S", "-B", "-m"])
                    self.assertIn("--source-profile", argv)
                previous = (root / "source-runtime.json").read_bytes()
                # Installation has finished but validation/ready publication may need retry.
                (root / "source-runtime.json").unlink()
                before = len(calls)
                profile_bytes = (runtime / "source-profile.json").read_bytes()
                self.assertEqual(resume_runtime(registry, runtime), runtime)
                self.assertEqual(len(calls) - before, 1)
                self.assertIn("validate_runtime", " ".join(calls[-1]))
                self.assertEqual((runtime / "source-profile.json").read_bytes(), profile_bytes)
                self.assertEqual((root / "source-runtime.json").read_bytes(), previous)
                with patch("checker.source_bootstrap.subprocess.run",
                           side_effect=subprocess.CalledProcessError(1, "validation failed")):
                    with self.assertRaises(subprocess.CalledProcessError):
                        resume_runtime(registry, runtime)
                self.assertEqual((root / "source-runtime.json").read_bytes(), previous)
                with patch("checker.source_bootstrap.subprocess.run") as child:
                    with self.assertRaises(ContractError):
                        resume_runtime(registry, root / "other-runtime")
                    config = runtime / "profiles/base-semgrep.json"
                    original = config.read_bytes()
                    config.write_bytes(b"changed without a pin update")
                    try:
                        with self.assertRaisesRegex(ValueError, "pin"):
                            resume_runtime(registry, runtime)
                    finally:
                        config.write_bytes(original)
                    pth = runtime / "python/python313._pth"
                    original = pth.read_bytes()
                    pth.write_text("import site")
                    try:
                        with self.assertRaisesRegex(ContractError, "Python/source paths"):
                            resume_runtime(registry, runtime)
                    finally:
                        pth.write_bytes(original)
                    changed = json.loads(profile_bytes)
                    changed["state_root"] = str(root / "unrelated-state")
                    (runtime / "source-profile.json").write_text(json.dumps(changed))
                    try:
                        with self.assertRaisesRegex(ContractError, "different data paths"):
                            resume_runtime(registry, runtime)
                    finally:
                        (runtime / "source-profile.json").write_bytes(profile_bytes)
                    child.assert_not_called()
                self.assertEqual((root / "source-runtime.json").read_bytes(), previous)
                with patch("checker.source_bootstrap.subprocess.run",
                           side_effect=subprocess.CalledProcessError(1, "fixture failed")):
                    with self.assertRaises(subprocess.CalledProcessError):
                        prepare_runtime(registry, root / "offline.zip")
                self.assertEqual((root / "source-runtime.json").read_bytes(), previous)
                self.assertEqual(registry.read_bytes(), b"existing owner registry")
                self.assertFalse((root / ".source-runtime-setup.lock").exists())

    def test_resume_cli_routes_without_tk_or_installers_and_requires_windows(self):
        from checker.gui import main
        from checker.source_bootstrap import resume_runtime
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "projects.json"
            runtime = root / "runtimes/existing"
            with patch("checker.source_bootstrap.resume_runtime") as resume, \
                    patch("checker.source_bootstrap.prepare_runtime") as install:
                self.assertEqual(main(["--registry", str(registry),
                                       "--resume-source-runtime", str(runtime)]), 0)
                resume.assert_called_once_with(registry, runtime)
                install.assert_not_called()
            with patch("checker.working.platform.system", return_value="Linux"), \
                    patch("checker.source_bootstrap.subprocess.run") as execute:
                with self.assertRaisesRegex(ContractError, "Windows"):
                    resume_runtime(registry, runtime)
                execute.assert_not_called()
            self.assertFalse((root / ".source-runtime-setup.lock").exists())

    def test_unknown_policy_id_cannot_be_saved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            seed_policies(root / "policies")
            app = DesktopApp.__new__(DesktopApp)
            app.registry_error, app.jobs, app.promotion = "", None, None
            app.policy_root = root / "policies"
            app.registry = Mock()
            app.messagebox = Mock()
            project = Registration("one", "One", (Selection("file", str(root / "a.js"), "a.js"),),
                                   ("absent",), str(root / "target"))
            self.assertFalse(app._save_project(project))
            app.registry.put.assert_not_called()
            self.assertIn("absent", str(app.messagebox.showerror.call_args))


class WorkingScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="checker-promotion-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "project"
        self.source.mkdir()
        self.registry = self.root / "projects.json"
        self.project = Registration("one", "One", (Selection("directory", str(self.source), "app"),),
                                    ("starter",), str(self.root / "target"))
        RegistryStore(self.registry).save(RegistryDocument((self.project,), "one"), None)
        tool = self.root / "tools"
        (tool / "bin").mkdir(parents=True)
        self.settings = DevelopmentSettings(self.root / "state", self.root / "policies",
            (self.root / "placeholder",), (EngineConfig("semgrep", tool / "bin/semgrep", "pin",
                 tool / "rules.json", "pin"),), {".py": ("semgrep",)})
        self.working = WorkingSettings(self.settings, self.registry)

    def test_exact_selected_directory_allows_sibling_target_and_storage(self):
        self.working.prepare_project(self.project)
        self.assertEqual(self.working.source_roots, (self.root,))
        self.assertEqual(self.working.source_overlap_roots, (self.source,))
        self.working.check_target_isolation(self.project.target_root)
        # Replacing selection by a directory containing runtime/state must fail.
        broad = replace(self.project, selections=(Selection("directory", str(self.root), "app"),))
        _, token = RegistryStore(self.registry).load()
        RegistryStore(self.registry).save(RegistryDocument((broad,), "one"), token)
        with self.assertRaisesRegex(ContractError, "separate"):
            self.working.prepare_project(broad)

    def test_registry_drift_blocks_check_before_any_worker(self):
        changed = replace(self.project, name="unsaved changes")
        jobs = CheckJobs(self.working)
        with self.assertRaisesRegex(ContractError, "Регистрация"):
            jobs.start(changed)
        self.assertIsNone(jobs.thread)

    def test_registered_targets_only_no_overlap_with_any_registered_source(self):
        with patch("checker.working.require_windows_owner"), patch("checker.working.native_io") as native:
            context = WorkingContext(self.settings, self.registry, self.root / "runtime")
            target = WorkingWindowsTarget(context)
            target.authorize(self.root / "target", context.settings)
            native.return_value.validate.assert_called()
            with self.assertRaisesRegex(ContractError, "регистрациях"):
                target.authorize(self.root / "unknown", context.settings)
            other = replace(self.project, registration_id="two",
                            selections=(Selection("directory", str(self.root / "target")),),
                            target_root=None)
            _, token = RegistryStore(self.registry).load()
            RegistryStore(self.registry).save(RegistryDocument((self.project, other), "one"), token)
            with self.assertRaisesRegex(ContractError, "пересекается"):
                target.authorize(self.root / "target", context.settings)

    def test_working_context_cannot_be_constructed_from_raw_development_profile(self):
        with self.assertRaises(ContractError):
            WorkingWindowsTarget(self.settings)
        self.assertFalse(PromotionService(self.settings).update_available)
        self.assertFalse(PromotionService(self.settings).native_update_available)


@unittest.skipUnless(os.environ.get("UPDATER_DEV_ESLINT") and os.environ.get("UPDATER_DEV_SEMGREP"),
                     "Both actual Docker CLIs required")
class WorkingActualIntegration(unittest.TestCase):
    def test_bootstrap_validation_uses_new_effective_directory_with_real_compilers(self):
        import sys
        from checker.source_bootstrap import validate_runtime
        with tempfile.TemporaryDirectory(prefix="checker-setup-validation-test-") as temporary:
            root = Path(temporary)
            seed_policies(root / "policies")
            tools = []
            for kind in ("eslint", "semgrep"):
                exe = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
                cfg = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
                tools.append(EngineConfig(kind, exe, file_hash(exe), cfg, file_hash(cfg),
                             Path("/usr/local/bin/node") if kind == "eslint" else None))
            settings = DevelopmentSettings(root / "state", root / "policies", (root / "source",),
                tuple(tools), {".js": ("eslint", "semgrep"), ".py": ("semgrep",)}, 90)
            profile = root / "source-profile.json"
            profile.write_text(json.dumps(dict(schema_version=1, **asdict(settings)), default=str))
            starter = (root / "policies/starter.json").read_bytes()
            # Headless Docker has no Tk. The import alone is replaced; real config
            # loading, tempfile lifecycle, compilers and safe analyzer fixtures run.
            with patch.dict(sys.modules, {"tkinter": Mock()}):
                validate_runtime(profile)
            self.assertEqual(list(settings.state_root.iterdir()), [])
            self.assertEqual((root / "policies/starter.json").read_bytes(), starter)

    def test_saved_project_real_analyzers_working_settings_and_native_adapter_contract(self):
        # Only the Win32 syscall layer is replaced by an existing named-temp test adapter.
        with tempfile.TemporaryDirectory(prefix="checker-promotion-test-") as temporary:
            root = Path(temporary)
            source = root / "project"
            source.mkdir()
            js, py = source / "a.js", source / "b.py"
            js.write_text("const answer = 42;\n")
            py.write_text("answer = 42\n")
            registry = root / "projects.json"
            project = Registration("one", "Mixed", (Selection("directory", str(source), "app"),),
                                   ("starter",), str(root / "target"))
            RegistryStore(registry).save(RegistryDocument((project,), "one"), None)
            seed_policies(root / "policies")
            tools = []
            for kind in ("eslint", "semgrep"):
                exe = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
                cfg = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
                tools.append(EngineConfig(kind, exe, file_hash(exe), cfg, file_hash(cfg),
                             Path("/usr/local/bin/node") if kind == "eslint" else None))
            settings = DevelopmentSettings(root / "state", root / "policies", (root / "placeholder",),
                tuple(tools), {".js": ("eslint", "semgrep"), ".py": ("semgrep",)}, 90)
            adapter = SyntheticTarget(root)
            target = root / "target"
            target.mkdir()
            (target / "owner.bin").write_bytes(b"owner data")
            class IO:
                def validate(self, path):
                    self_outer.assertTrue(path.is_relative_to(root))
                def split(self, path):
                    return target, path.relative_to(target).as_posix() if path != target else ""
                def read(self, path):
                    raw = adapter.read(*self.split(path))
                    if raw is None:
                        raise FileNotFoundError(2, "fixture missing")
                    return raw
                def metadata(self, path):
                    return adapter.metadata(*self.split(path))
                def write(self, path, data, metadata, expected):
                    adapter.replace(*self.split(path), data, metadata, expected_sha256=expected)
                def remove(self, path, expected, metadata):
                    adapter.remove(*self.split(path), expected_sha256=expected, expected_metadata=metadata)
                def mkdir(self, path):
                    return adapter.mkdir(*self.split(path))
                def rmdir_if_owned_empty(self, path, identity):
                    adapter.rmdir_if_owned_empty(*self.split(path), identity)
            self_outer = self
            with patch("checker.working.require_windows_owner"), patch("checker.working.native_io", return_value=IO()), \
                    patch("checker.working.platform.system", return_value="Windows"):
                context = WorkingContext(settings, registry, root / "runtime")
                service = PromotionService(context.settings, WorkingWindowsTarget(context))
                self.assertTrue(service.update_available)
                self.assertFalse(service.native_update_available)
                jobs = CheckJobs(context.settings)
                def check():
                    jobs.start(project)
                    deadline = time.monotonic() + 100
                    while time.monotonic() < deadline:
                        for event in jobs.drain():
                            if event.terminal:
                                jobs.thread.join(2)
                                self.assertEqual(event.phase, "COMPLETE_DEVELOPMENT", event.detail)
                                return event.result
                        time.sleep(0.02)
                    jobs.cancel()
                    jobs.thread.join(5)
                    self.fail("Actual analyzer job timed out")
                checked = check()
                review = service.review(checked, project)
                self.assertFalse(adapter.writes)
                result = service.apply(service.confirm(review.review_id, review.fingerprint, project), project)
                self.assertEqual((result.state, result.scope), ("COMPLETED", "WINDOWS_WORKING_COPY_TEST"))
                self.assertEqual((target / "app/a.js").read_bytes(), js.read_bytes())
                self.assertEqual((target / "owner.bin").read_bytes(), b"owner data")
                inverse = service.review_rollback(result.operation_id)
                self.assertEqual(service.rollback(result.operation_id, inverse).state, "ROLLED_BACK")
                self.assertFalse((target / "app/a.js").exists())
                # Findings still block update in the functional working mode.
                js.write_text("eval('1');\n")
                with self.assertRaisesRegex(ContractError, "findings"):
                    service.review(check(), project)
