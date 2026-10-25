"""Actual config compilers and safe local fixtures; no candidate code is executed."""
import os
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from checker.engines import EngineConfig, run_dev_engine
from checker.inventory import digest, make_snapshot
from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.policy_validation import prepare_effective_policy, validate_engine_config

RULES = """rules:
  - id: js-no-eval
    languages: [javascript]
    severity: ERROR
    message: eval prohibited in fixture
    pattern: eval(...)
  - id: py-no-eval
    languages: [python]
    severity: ERROR
    message: eval prohibited in fixture
    pattern: eval(...)
"""


@unittest.skipUnless(os.environ.get("UPDATER_DEV_ESLINT") and os.environ.get("UPDATER_DEV_SEMGREP"),
                     "Both Docker fixture tools required")
class EffectivePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="policy-validation-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tools = []
        for kind in ("eslint", "semgrep"):
            cli = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
            cfg = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
            self.tools.append(EngineConfig(kind, cli, digest(cli.read_bytes()), cfg,
                digest(cfg.read_bytes()), Path("/usr/local/bin/node") if kind == "eslint" else None))
        self.tools = tuple(self.tools)
        self.store = PolicyStore(self.root / "packs")
        self.pack = PolicyPack("shared", "Общий", {"no-eval": "error"}, RULES)
        self.store.create(self.pack)
        self.source = self.root / "пример.js"
        self.source.write_text("const answer = 42;\n", encoding="utf-8")
        self.reg = Registration("one", "Первый", (Selection("file", str(self.source)),), ("shared",))

    def config(self, kind, text):
        suffix = "cjs" if kind == "eslint" else "yaml"
        file = self.root / f"custom-{kind}.{suffix}"
        file.write_text(text, encoding="utf-8")
        original = next(c for c in self.tools if c.kind == kind)
        return replace(original, config=file, config_sha256=digest(file.read_bytes()))

    def test_schema_accepts_unknown_rule_but_real_engine_and_scan_refuse(self):
        PolicyPack("bad", "Bad", {"not-a-real-rule": "error"}).validate()
        cfg = self.config("eslint", 'module.exports = [{rules: {"not-a-real-rule": "error"}}];')
        result = validate_engine_config(cfg)
        self.assertEqual(result.status, "ERROR", result.detail)
        snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        report = run_dev_engine(snap, cfg)
        self.assertEqual(report.status, "ERROR", report.detail)
        self.assertEqual(report.scanned, ())

    def test_unknown_disabled_rule_is_also_invalid(self):
        cfg = self.config("eslint", 'module.exports = [{rules: {"not-a-real-rule": "off", "no-eval": "error"}}];')
        self.assertEqual(validate_engine_config(cfg).status, "ERROR")

    def test_required_eslint_rule_cannot_be_disabled_or_scoped_away(self):
        for text in (
            'module.exports = [{rules: {"no-eval": "off", "no-undef": "error"}}];',
            'module.exports = [{files: ["**/*.py"], rules: {"no-eval": "error"}}];',
            'module.exports = [{rules: {"no-undef": "error"}}];',
        ):
            with self.subTest(text=text):
                result = validate_engine_config(self.config("eslint", text), required_rules=("no-eval",))
                self.assertEqual(result.status, "ERROR", result.detail)

    def test_bad_yaml_empty_config_and_duplicate_keys_fail(self):
        for text in ("rules: [", "hello: world", "rules: []", RULES + RULES,
                     RULES.replace("pattern: eval(...)", "pattern: eval(...)\n    pattern: print(...)")):
            with self.subTest(text=text):
                result = validate_engine_config(self.config("semgrep", text))
                self.assertEqual(result.status, "ERROR", result.detail)

    def test_semgrep_pattern_is_compiled_by_real_engine(self):
        cfg = self.config("semgrep", RULES.replace("eval(...)", "def (("))
        result = validate_engine_config(cfg)
        self.assertEqual(result.status, "ERROR", result.detail)
        self.assertIn("compile/fixture", result.detail)

    def test_semgrep_missing_duplicate_or_version_disabled_required_rule(self):
        for text, required in (
            (RULES, ("missing-rule",)),
            (RULES.replace("py-no-eval", "js-no-eval"), ()),
            (RULES.replace("    pattern:", '    min-version: "999.0.0"\n    pattern:'), ("js-no-eval",)),
        ):
            with self.subTest(text=text):
                result = validate_engine_config(self.config("semgrep", text), required_rules=required)
                self.assertEqual(result.status, "ERROR", result.detail)

    def test_missing_tool_is_error_without_execution(self):
        config = replace(self.tools[0], executable=self.root / "missing-eslint")
        with patch("checker.policy_validation.subprocess.run") as run:
            self.assertEqual(validate_engine_config(config).status, "ERROR")
            run.assert_not_called()

    def test_timeout_is_error(self):
        with patch("checker.policy_validation.subprocess.run", side_effect=subprocess.TimeoutExpired("fixture", 1)):
            result = validate_engine_config(self.tools[0], timeout=1)
        self.assertEqual(result.status, "ERROR")
        self.assertIn("TimeoutExpired", result.detail)

    def test_missing_required_engine_and_conflicting_shared_packs_refuse(self):
        captured = self.store.capture(self.reg)
        with self.assertRaisesRegex(ContractError, "Missing required engine"):
            prepare_effective_policy(captured, (self.tools[0],), self.root / "missing-engine")
        self.store.create(PolicyPack("other", "Other", {"no-eval": "off"}))
        reg = replace(self.reg, policy_pack_ids=("shared", "other"))
        with self.assertRaisesRegex(ContractError, "Conflicting ESLint"):
            prepare_effective_policy(self.store.capture(reg), self.tools, self.root / "conflict")
        self.assertFalse((self.root / "conflict").exists())

    def test_disabled_required_rule_in_pack_blocks_effective_policy(self):
        self.store.update(replace(self.pack, eslint_core_rules={"no-eval": "off", "no-undef": "error"}),
                          self.pack.fingerprint())
        with self.assertRaisesRegex(ContractError, "Disabled/missing"):
            prepare_effective_policy(self.store.capture(self.reg), self.tools, self.root / "disabled",
                                     required_rules=(("eslint", ("no-eval",)),))

    def test_valid_shared_policy_real_clean_and_violation_in_both_engines(self):
        captured = self.store.capture(self.reg)
        effective = prepare_effective_policy(captured, self.tools,
            self.root / "effective", required_rules=(("eslint", ("no-eval",)),
                                                     ("semgrep", ("js-no-eval", "py-no-eval"))))
        self.assertTrue(all(v.status == "VALIDATED_DEVELOPMENT" for v in effective.validations))
        self.assertEqual(len(effective.tool_fingerprints), 2)
        py = self.root / "пример.py"
        py.write_text("answer = 42\n", encoding="utf-8")
        reg = replace(self.reg, selections=(*self.reg.selections, Selection("file", str(py))))
        required = dict(effective.required_rules)
        for code, status in (("const answer = 42;", "STRUCTURAL_CLEAR"),
                             ('/* eslint-disable */ eval("2+2");', "FINDINGS")):
            self.source.write_text(code, encoding="utf-8")
            py.write_text("answer = 42\n" if status == "STRUCTURAL_CLEAR" else 'eval("2+2")\n')
            snapshot = make_snapshot(reg, (self.root,), self.root / "reviews")
            for config in effective.configs:
                with self.subTest(engine=config.kind, status=status):
                    report = run_dev_engine(snapshot, config, required_rules=required[config.kind])
                    self.assertEqual(report.status, status, report.detail)
        # Saving a shared pack changes both consumers' captured effective policy.
        second = replace(self.reg, registration_id="two", name="Второй")
        old = self.store.capture(second).combined_sha256
        self.store.update(replace(self.pack, eslint_core_rules={"no-eval": "warn"}), self.pack.fingerprint())
        self.assertFalse(self.store.still_current(self.reg, captured))
        self.assertNotEqual(self.store.capture(second).combined_sha256, old)
