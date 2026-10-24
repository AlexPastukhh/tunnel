import tempfile
import unittest
from pathlib import Path

from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyPack, PolicyStore


class PackTests(unittest.TestCase):
    def test_mutable_shared_pack_and_clone(self):
        with tempfile.TemporaryDirectory() as temp:
            store = PolicyStore(Path(temp) / "policies")
            original = PolicyPack("js-common", "Common rules", {"no-eval": "error"})
            store.create(original)
            reg_a = Registration("A", "A", (Selection("file", "/demo/a.js"),), ("js-common",))
            reg_b = Registration("B", "B", (Selection("file", "/demo/b.js"),), ("js-common",))
            a = store.capture(reg_a)
            b = store.capture(reg_b)
            self.assertTrue(store.still_current(reg_a, a))
            store.clone("js-common", "js-legacy", "Legacy")
            reg_c = Registration("C", "C", (Selection("file", "/demo/c.js"),), ("js-legacy",))
            c = store.capture(reg_c)
            changed = PolicyPack("js-common", "Common rules", {"no-eval": "error", "no-implied-eval": "error"})
            store.update(changed, original.fingerprint())
            self.assertFalse(store.still_current(reg_a, a))
            self.assertFalse(store.still_current(reg_b, b))
            self.assertTrue(store.still_current(reg_c, c))
            self.assertNotEqual(a.combined_sha256, store.capture(reg_a).combined_sha256)
            self.assertIn(b"no-eval", a.packs[0][2])

    def test_conflicting_editor_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            store = PolicyStore(Path(temp))
            original = PolicyPack("policy", "Demo", {"no-eval": "error"})
            store.create(original)
            changed = PolicyPack("policy", "Changed", {"no-eval": "warn"})
            store.update(changed, original.fingerprint())
            with self.assertRaisesRegex(ContractError, "Pack changed"):
                store.update(original, original.fingerprint())

    def test_pack_id_cannot_escape_store(self):
        with tempfile.TemporaryDirectory() as temp:
            store = PolicyStore(Path(temp))
            with self.assertRaises(ContractError):
                store.create(PolicyPack("../bad", "Bad", {"no-eval": "error"}))
            with self.assertRaises(ContractError):
                store.load("../bad")

    def test_empty_pack_invalid(self):
        with self.assertRaises(ContractError):
            PolicyPack("empty", "Empty", {}).serialize()


if __name__ == "__main__":
    unittest.main()
