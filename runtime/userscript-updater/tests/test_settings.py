import tempfile
import json
import unittest
from pathlib import Path

from checker.model import ContractError
from checker.settings import DevelopmentSettings
from checker.engines import EngineConfig
from checker.policies import PolicyPack, PolicyStore
from checker.policy_service import PolicyService
from checker.model import Registration, Selection


class SettingsAndPolicyStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.settings = DevelopmentSettings(self.root / "state", self.root / "policies",
            (self.root / "source",), (EngineConfig("eslint", self.root / "tool", "pin",
                self.root / "config", "pin", self.root / "node"),), {".js": ("eslint",)}, 30)

    def test_state_or_tool_inside_source_is_rejected(self):
        from dataclasses import replace
        self.settings.validate()
        with self.assertRaises(ContractError):
            replace(self.settings, state_root=self.root / "source" / "state").validate()
        with self.assertRaises(ContractError):
            replace(self.settings, tools=(replace(self.settings.tools[0], config=self.root / "source" / "config"),)).validate()

    def test_policy_delete_refuses_consumers_then_allows_unbound_pack(self):
        pack = PolicyPack("pack", "Rules", {"no-eval": "error"})
        store = PolicyStore(self.settings.policy_root)
        store.create(pack)
        reg = Registration("one", "One", (Selection("file", str(self.root / "source" / "script.js")),), ("pack",))
        service = PolicyService(self.settings)
        with self.assertRaisesRegex(ContractError, "in use"):
            service.remove("pack", pack.fingerprint(), (reg,))
        self.assertEqual(store.load("pack"), pack)
        service.remove("pack", pack.fingerprint(), ())
        self.assertEqual(store.list_packs(), ())

    def test_duplicate_policy_keys_and_linked_storage_fail_closed(self):
        with self.assertRaises(ContractError):
            PolicyPack.parse(b'{"pack_id":"x","pack_id":"y"}')
        target = self.root / "other"
        target.mkdir()
        link = self.root / "alias"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ContractError):
            PolicyStore(link).create(PolicyPack("pack", "Rules", {"no-eval": "error"}))
        self.assertEqual(list(target.iterdir()), [])

    def test_malformed_profile_is_contract_error_instead_of_gui_crash(self):
        profile = self.root / "development.json"
        data = dict(schema_version=1, state_root=str(self.settings.state_root),
            policy_root=str(self.settings.policy_root), source_roots=[str(self.root / "source")],
            tools=[], required_for_suffix=None, timeout_seconds=30)
        profile.write_text(json.dumps(data))
        with self.assertRaises(ContractError):
            DevelopmentSettings.load(profile)

    def test_check_refuses_target_overlapping_job_state_before_start(self):
        from checker.jobs import CheckJobs
        jobs = CheckJobs(self.settings)
        project = Registration("one", "Overlap", (Selection("file", str(self.root / "source/script.js"), "script.js"),),
                               ("pack",), str(self.settings.state_root))
        try:
            with self.assertRaisesRegex(ContractError, "Target.*overlap"):
                jobs.start(project)
        finally:
            jobs.cancel()
            if jobs.thread:
                jobs.thread.join(2)
        self.assertFalse(self.settings.state_root.exists())
