"""Offline safety and source-visibility tests: never touch real histories."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from threading import Thread
import http.client

import activity_audit


class ActivityReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.history = Path(self.tmp.name) / "tool-history.jsonl"

    def write(self, items):
        self.history.write_text("\n".join(json.dumps(x) for x in items) + "\n")

    def test_never_expose_commands_arguments_outputs_tokens(self):
        secret = "github_pat_THIS_IS_A_SYNTHETIC_TEST_SECRET_DO_NOT_EXPOSE_1234"
        self.write([{
            "timestamp": "2026-10-16T01:00:00Z",
            "toolName": "start_process",
            "arguments": {"command": "echo " + secret, "timeout_ms": 3000},
            "output": {"text": "private output " + secret},
            "duration": 52,
        }])
        result = activity_audit.records(self.history, "repo")
        wire = json.dumps(result)
        self.assertNotIn(secret, wire)
        self.assertNotIn("echo", wire)
        self.assertNotIn("private output", wire)
        event = result["events"][0]
        self.assertTrue(event["command_present"])
        self.assertEqual(event["kind"], "terminal")
        self.assertEqual(event["outcome"], "unverified")
        self.assertIsNone(event["chat_id"])

    def test_error_only_if_explicit(self):
        self.write([
            {"toolName": "write_file", "timestamp": "2026-10-16T02:00:00Z", "arguments": {},
             "output": {"isError": True, "text": "synthetic file"}, "duration": 2},
            {"toolName": "read_file", "timestamp": "2026-10-16T02:00:01Z", "arguments": {},
             "output": {"text": "synthetic success"}, "duration": 3},
        ])
        out = activity_audit.records(self.history, "g2")
        self.assertEqual([e["outcome"] for e in out["events"]], ["error", "unverified"])
        self.assertEqual([e["route"] for e in out["events"]], ["g2", "g2"])

    def test_missing_and_symlink(self):
        self.assertEqual(activity_audit.records(self.history, "repo")["source_state"], "unavailable")
        source = Path(self.tmp.name) / "elsewhere"
        source.write_text("{}")
        self.history.symlink_to(source)
        with self.assertRaises(ValueError):
            activity_audit.records(self.history, "repo")

    def test_bounded_limit_and_malformed_json(self):
        values = [
            {"toolName": "list_directory", "timestamp": "2026-10-16T02:00:01Z",
             "arguments": {"path": "private"}, "duration": 1}
        ] * 4
        self.write(values)
        with self.history.open("a") as stream:
            stream.write("not valid JSON\n")
        result = activity_audit.records(self.history, "repo", limit=2)
        self.assertEqual(result["returned"], 2)
        self.assertEqual(result["invalid_records_in_window"], 1)
        self.assertEqual(result["events"][0]["kind"], "files")

    def test_exact_command_requires_interactive_tty(self):
        with patch.object(activity_audit.sys.stdout, "isatty", return_value=False):
            with self.assertRaises(PermissionError):
                activity_audit.unsafe_local_commands(self.history, "repo", 5)


class ActivityApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.history = Path(self.tmp.name) / "hist.jsonl"
        self.history.write_text(json.dumps({
            "timestamp": "2026-10-16T05:00:00Z",
            "toolName": "start_process",
            "arguments": {"command": "danger secret private echo"},
            "output": {"text": "secret private output"},
            "duration": 5,
        }) + "\n")

    def test_configured_and_missing_routes(self):
        import server
        with patch.dict(server.AUDIT_SOURCES, {"repo": self.history}, clear=True):
            data = server.activity_feed(5)
        self.assertEqual(data["feeds"]["repo"]["source_state"], "available")
        self.assertEqual(data["feeds"]["g2"]["source_state"], "unconfigured")
        self.assertEqual(len(data["events"]), 1)
        self.assertNotIn("secret private", json.dumps(data))

    def test_http_metadata_only(self):
        import server
        with patch.dict(server.AUDIT_SOURCES, {"repo": self.history}, clear=True), \
             patch.object(server, "OWNER_AUTH_TOKEN", "SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"):
            instance = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = Thread(target=instance.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=3)
                connection.request("GET", "/api/activity?limit=1", headers={
                    "Authorization":"Bearer SYNTHETIC_OWNER_TEST_TOKEN_ONLY_NOT_FOR_PRODUCTION"})
                result = connection.getresponse()
                body = result.read().decode()
                self.assertEqual(result.status, 200)
                self.assertNotIn("danger secret", body)
                self.assertNotIn("private output", body)
                self.assertEqual(json.loads(body)["events"][0]["tool"], "start_process")
                connection.close()
            finally:
                instance.shutdown()
                instance.server_close()
                thread.join(timeout=3)


class RetirementTests(unittest.TestCase):
    def test_retired_host_skips_old_port(self):
        import server
        with patch.object(server, "LEGACY_HOST_ENABLED", False):
            with patch.object(server, "fetch_json", side_effect=AssertionError("no polling")):
                result = server.build_snapshot()
        self.assertTrue(result["legacy_host_retired"])
        self.assertIsNone(result["error"])


if __name__ == "__main__":
    unittest.main()
