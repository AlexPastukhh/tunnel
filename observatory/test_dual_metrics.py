"""Synthetic regression tests; native Windows acceptance is separate."""
import json
import http.client
from http.server import ThreadingHTTPServer
from threading import Thread
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import dual_metrics
import server


class MetricTests(unittest.TestCase):
    def test_minimized_allowlist(self):
        raw = (
            '# HELP not exposed\n'
            'commands_polled_total{token="should_not_leak"} 12\n'
            'commands_queue_length{scope="cp"} 0\n'
            'dispatcher_worker_pool_occupancy{scope="internal"} 1\n'
            'command_end_to_end_latency_milliseconds_count{status="200"} 2\n'
            'command_end_to_end_latency_milliseconds_count{status="500"} 2\n'
            'command_end_to_end_latency_milliseconds_sum{status="200"} 400\n'
            'command_end_to_end_latency_milliseconds_sum{status="500"} 1200\n'
            'not_allowlisted{secret="HIDDEN"} 123\n'
        )
        data = dual_metrics.summarize(raw)
        self.assertEqual(data["polled_total"], 12)
        self.assertEqual(data["queue_length"], 0)
        self.assertEqual(data["command_latency_count"], 4)
        self.assertEqual(data["command_latency_avg_ms"], 400)
        self.assertNotIn("should_not_leak", json.dumps(data))
        self.assertNotIn("HIDDEN", json.dumps(data))
        self.assertNotIn("not_allowlisted", json.dumps(data))

    def test_invalid_and_missing(self):
        data = dual_metrics.summarize(
            "commands_polled_total -1\ncommands_queue_length NaN\n"
            "commands_queue_capacity +Inf\ncommands_enqueued_total 4\n"
        )
        self.assertIsNone(data["polled_total"])
        self.assertIsNone(data["queue_capacity"])
        self.assertEqual(data["enqueued_total"], 4)
        with self.assertRaises(ValueError):
            dual_metrics.summarize("a" * 500_001)

    def test_identity_discovery_and_invalid_ports(self):
        result = type("Result", (), {"stdout": "52218\n"})()
        with patch.object(dual_metrics.sys, "platform", "win32"), \
             patch.object(dual_metrics.subprocess, "run", return_value=result) as run:
            endpoints, error = dual_metrics.discover_g2()
        self.assertEqual(endpoints, ["http://127.0.0.1:52218"])
        self.assertIsNone(error)
        self.assertIn("GetOwnerSid", run.call_args.args[0][-1])
        self.assertIn("fortis-host-g2-test", run.call_args.args[0][-1])
        self.assertIn(dual_metrics.G2_USER_SID, run.call_args.args[0][-1])
        result.stdout = '["http://evil.example"]'
        with patch.object(dual_metrics.sys, "platform", "win32"), \
             patch.object(dual_metrics.subprocess, "run", return_value=result):
            endpoints, error = dual_metrics.discover_g2()
        self.assertEqual(endpoints, [])
        self.assertIsNotNone(error)

    def test_g2_safe_probe(self):
        health = {"live": True, "ready": True, "components": {"mcp": {"state": "initialized"}},
                  "runtime": {"uptime_seconds": 30}, "untrusted_secret": "NEVER_EXPORT"}
        def local_get(base, path):
            if path.startswith("/health"):
                return json.dumps(health)
            return 'commands_polled_total{credential="SECRET"} 7\ncommands_queue_length 0\n'
        with patch.object(dual_metrics, "discover_g2", return_value=(["http://127.0.0.1:52218"], None)), \
             patch.object(dual_metrics, "_local_get", side_effect=local_get):
            value = dual_metrics.collect_g2()
        self.assertEqual(value["state"], "UP")
        self.assertTrue(value["verified"])
        self.assertEqual(value["metrics"]["polled_total"], 7)
        self.assertNotIn("SECRET", json.dumps(value))
        self.assertNotIn("NEVER_EXPORT", json.dumps(value))

    def test_no_unsupported_g2_positive(self):
        with patch.object(dual_metrics, "discover_g2", return_value=([], "Identity unavailable")):
            self.assertEqual(dual_metrics.collect_g2()["state"], "UNKNOWN")
        with patch.object(dual_metrics, "discover_g2", return_value=(["http://127.0.0.1:12345"], None)), \
             patch.object(dual_metrics, "_local_get", return_value='{}'):
            self.assertEqual(dual_metrics.collect_g2()["state"], "UNKNOWN")

    def test_native_tunnels_report_two_independent_sources(self):
        with patch.object(server, "latest_repo", return_value={"state": "UP", "verified": True}), \
             patch.object(server, "latest_g2", return_value={"state": "UNKNOWN", "verified": False}):
            data = server.native_tunnels()
        self.assertEqual(data["repo"]["state"], "UP")
        self.assertEqual(data["g2"]["state"], "UNKNOWN")
        self.assertEqual(data["legacy_host"], "RETIRED")

    def test_malformed_browser_local_link_redirects_only_exact_path(self):
        instance = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = Thread(target=instance.serve_forever, daemon=True)
        thread.start()
        try:
            client = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=3)
            client.request("GET", "/**?utm_source=chatgpt.com")
            resp = client.getresponse()
            resp.read()
            self.assertEqual(resp.status, 302)
            self.assertEqual(resp.getheader("Location"), "/index.html")
            client.request("GET", "/index.html")
            ok = client.getresponse()
            doc = ok.read().decode("utf-8")
            self.assertEqual(ok.status, 200)
            self.assertIn("Fortis Observatory", doc)
            client.request("GET", "/favicon.ico")
            icon = client.getresponse()
            icon.read()
            self.assertEqual(icon.status, 204)
            client.close()
        finally:
            instance.shutdown()
            instance.server_close()
            thread.join(timeout=3)

    def test_http_routes_live_metadata_only(self):
        with patch.object(server, "latest_repo", return_value={
                "state": "UP", "verified": True,
                "metrics": {"queue_length": 0, "polled_total": 10}}), \
             patch.object(server, "latest_g2", return_value={
                "state": "UNKNOWN", "verified": False, "reason": "source_unavailable"}), \
             patch.object(server, "OWNER_AUTH_TOKEN", "SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"):
            instance = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = Thread(target=instance.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=3)
                connection.request("GET", "/api/tunnels", headers={
                    "Authorization":"Bearer SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"})
                reply = connection.getresponse()
                body = reply.read().decode()
                self.assertEqual(reply.status, 200)
                self.assertEqual(json.loads(body)["g2"]["state"], "UNKNOWN")
                self.assertEqual(json.loads(body)["repo"]["metrics"]["queue_length"], 0)
                self.assertNotIn("CONTROL_PLANE_API_KEY", body)
                connection.close()
            finally:
                instance.shutdown()
                instance.server_close()
                thread.join(timeout=3)

    def test_g2_sanitized_hour_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g2-history.jsonl"
            sample={"state": "UP", "verified": True, "sampled_at": time.time(),
                    "mcp_state": "initialized",
                    "metrics": {"polled_total": 7},
                    "private": "DO_NOT_PERSIST"}
            with patch.object(server, "G2_HISTORY_FILE", path), \
                 patch.object(server, "DATA_DIR", Path(tmp)), \
                 patch.object(server, "ARCHIVE_DB", Path(tmp) / "archive.sqlite3"), \
                 patch.object(server, "collect_g2", return_value=sample):
                with server.G2_LOCK:
                    server.G2_HISTORY.clear()
                server.capture_g2()
                saved = json.loads(path.read_text())
                self.assertEqual(saved["metrics"]["polled_total"], 7)
                self.assertNotIn("private", saved)
                self.assertEqual(server.g2_history()["samples"], 1)
                with server.G2_LOCK:
                    server.G2_HISTORY.clear()


if __name__ == "__main__":
    unittest.main()
