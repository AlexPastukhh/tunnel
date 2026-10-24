import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import repo_monitor


class RepoMonitorTests(unittest.TestCase):
    def test_url_validation(self):
        for value in ("https://127.0.0.1:9000", "http://localhost:9000", "http://127.0.0.1:9000/path"):
            with patch.dict("os.environ", {"OBS_REPO_URL": value}):
                urls, error = repo_monitor.candidates()
            self.assertEqual(urls, [])
            self.assertTrue(error)

    def test_loopback_configuration(self):
        with patch.dict("os.environ", {"OBS_REPO_URL": "http://127.0.0.1:19000"}):
            self.assertEqual(repo_monitor.candidates()[0], ["http://127.0.0.1:19000"])

    def test_identity_mismatch_must_not_claim_up(self):
        with patch.object(repo_monitor, "candidates", return_value=(["http://127.0.0.1:19000"], None)):
            with patch.object(repo_monitor, "_request", return_value="unrelated metrics"):
                self.assertEqual(repo_monitor.collect_repo()["state"], "UNKNOWN")

    def test_verified_live(self):
        def fake_request(base, path):
            if path == "/metrics":
                return 'tunnel_identity{tunnel_id="' + repo_monitor.REPO_ID + '"} 1'
            return json.dumps({"live": True, "ready": True, "runtime": {"uptime_seconds": 22}})
        with patch.object(repo_monitor, "candidates", return_value=(["http://127.0.0.1:19000"], None)):
            with patch.object(repo_monitor, "_request", side_effect=fake_request):
                sample = repo_monitor.collect_repo()
        self.assertEqual(sample["state"], "UP")
        self.assertTrue(sample["verified"])

    def test_unknown_without_discovery(self):
        with patch.object(repo_monitor, "candidates", return_value=([], "unavailable")):
            self.assertEqual(repo_monitor.collect_repo()["state"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()


class ApiTests(unittest.TestCase):
    def test_repo_routes(self):
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        import server
        with patch.object(server, "latest_repo", return_value={"state": "UNKNOWN", "verified": False}):
            with patch.object(server, "repo_history", return_value={"ok": True, "samples": 0, "history": []}), \
                 patch.object(server, "OWNER_AUTH_TOKEN", "SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"):
                srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                thread = threading.Thread(target=srv.serve_forever, daemon=True)
                thread.start()
                try:
                    for route, key in (("/api/repo-status", "state"), ("/api/repo-history", "history")):
                        conn = http.client.HTTPConnection("127.0.0.1", srv.server_port, timeout=3)
                        conn.request("GET", route, headers={"Authorization":"Bearer SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"})
                        response = conn.getresponse()
                        self.assertEqual(response.status, 200)
                        self.assertIn(key, json.loads(response.read()))
                        conn.close()
                finally:
                    srv.shutdown()
                    srv.server_close()
                    thread.join(timeout=2)

class WindowsDiscoveryTests(unittest.TestCase):
    def discover(self, effect):
        behavior = {"return_value": effect} if isinstance(effect, subprocess.CompletedProcess) else {"side_effect": effect}
        with patch.dict("os.environ", {"OBS_REPO_URL": ""}):
            with patch.object(repo_monitor.sys, "platform", "win32"):
                with patch.object(repo_monitor.subprocess, "run", **behavior):
                    return repo_monitor.candidates()

    def test_provider_slower_than_old_deadline_can_be_discovered(self):
        def delayed_provider(args, **kwargs):
            # Native baseline required 6.516s; model it without sleeping.
            if kwargs["timeout"] <= 6.516:
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            return subprocess.CompletedProcess(args, 0, stdout="[50385, 50386]", stderr="")
        self.assertEqual(self.discover(delayed_provider),
                         (["http://127.0.0.1:50385", "http://127.0.0.1:50386"], None))

    def test_timeout_reason_does_not_disclose_partial_output(self):
        secret = "SYNTHETIC_PRIVATE_DIAGNOSTIC"
        result = self.discover(subprocess.TimeoutExpired("powershell", 15, output=secret, stderr=secret))
        self.assertEqual(result, ([], "Native Repo listener discovery timed out"))
        self.assertNotIn(secret, str(result))

    def test_failed_command_reason_does_not_disclose_stderr(self):
        result = self.discover(subprocess.CalledProcessError(1, "powershell",
                               stderr="SYNTHETIC_PRIVATE_DIAGNOSTIC"))
        self.assertEqual(result, ([], "Native Repo listener discovery command failed"))

    def test_invalid_output_and_invalid_port_do_not_become_candidates(self):
        for stdout in ("SYNTHETIC_PRIVATE_DIAGNOSTIC", "[70000]"):
            with self.subTest(stdout=stdout):
                self.assertEqual(self.discover(subprocess.CompletedProcess(
                    "powershell", 0, stdout=stdout, stderr="")),
                    ([], "Native Repo listener discovery returned invalid output"))

    def test_unavailable_powershell_has_distinct_reason(self):
        self.assertEqual(self.discover(FileNotFoundError("SYNTHETIC_PRIVATE_DIAGNOSTIC")),
                         ([], "Native Repo listener discovery could not start"))
