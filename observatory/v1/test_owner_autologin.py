"""Synthetic owner auto-unlock checks. Never reads Windows secrets or starts Edge."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import re
import unittest
from unittest.mock import patch

import owner_viewer as viewer


class OwnerAutoLoginTest(unittest.TestCase):
    def test_owner_acl_powershell_fail_closed_and_file_can_inherit_private_acl(self):
        with TemporaryDirectory() as td, patch.object(viewer.sys, "platform", "win32"):
            captured = []
            def runner(args, **kwargs):
                captured.append((args, kwargs))
                return SimpleNamespace(returncode=0, stdout=b"PRIVATE_ACL_OK\r\n")
            sid = "S-1-5-21-111-222-333-1001"
            viewer.assert_owner_only_launcher_dir(Path(td), sid, runner=runner)
            self.assertEqual(captured[-1][1]["env"]["FORTIS_LAUNCH_REQUIRE_PROTECTED"], "1")
            viewer.assert_owner_only_launcher_dir(Path(td), sid, runner=runner,
                                                   require_protected=False)
            self.assertEqual(captured[-1][1]["env"]["FORTIS_LAUNCH_REQUIRE_PROTECTED"], "0")
            import base64
            script = base64.b64decode(captured[-1][0][-1]).decode("utf-16le")
            self.assertIn("Get-Acl", script)
            self.assertIn("Foreign ACL principal", script)
            self.assertIn("Reparse point", script)

    def test_acl_denial_refuses_auto_mode(self):
        with TemporaryDirectory() as td, patch.object(viewer.sys, "platform", "win32"):
            bad = lambda *a, **kw: SimpleNamespace(returncode=1, stdout=b"")
            with self.assertRaisesRegex(ValueError, "private_launcher_acl_denied"):
                viewer.assert_owner_only_launcher_dir(Path(td), "owner", runner=bad)

    def test_private_launcher_file_has_no_token_in_url(self):
        secret = "s" * 43  # synthetic, no real token
        with TemporaryDirectory() as td:
            with patch.object(viewer, "assert_owner_only_launcher_dir"):
                path = viewer.write_owner_only_launcher(Path(td), secret, "owner")
                try:
                    html = path.read_text(encoding="utf-8")
                    self.assertIn(json.dumps(secret), html)
                    self.assertNotIn(secret, path.as_uri())
                    self.assertIn("window.open(destination", html)
                    self.assertIn("postMessage", html)
                    self.assertIn('destination.slice(0,-1)', html)
                    self.assertNotIn("location.hash", html)
                    self.assertIn("viewer-private-launch-", path.name)
                finally:
                    path.unlink()

    def test_manual_login_code_and_api_bearer_remain(self):
        page = viewer.PAGE
        self.assertIn('id="form"', page)
        self.assertIn('id="secret"', page)
        self.assertIn('async function unlockViewer(value)', page)
        self.assertIn('event.source!==window.opener', page)
        self.assertIn('event.origin!=="null"', page)
        import inspect
        code = inspect.getsource(viewer.handler_for)
        self.assertEqual(code.count('"viewer_key_required"'), 2)
        self.assertIn('compare_digest', code)


if __name__ == "__main__":
    unittest.main()
