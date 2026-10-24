"""Offline/current-chat outbox: durable data and strict later attribution."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

import repo_pending as pending
from repo_messages import RepoMessages
from store import Store, MESSAGE_SUMMARIES


class PendingContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fortis-pending-test-", dir="/workspace/repo")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.events = self.root / "inbox" / "repo"
        self.messages = self.root / "inbox" / "messages"
        self.events.mkdir(parents=True)
        self.messages.mkdir()
        self.quarantine = self.root / "quarantine"
        self.quarantine.mkdir()
        self.store = Store(self.root / "archive", {"repo": self.events})
        self.reader = RepoMessages(self.store, self.messages, self.quarantine)
        self.chat = "pending-chat-12345678"
        self.task = "task_" + uuid.uuid4().hex

    def register(self, chat=None):
        return self.store.register("https://chatgpt.com/c/" + (chat or self.chat), "repo", "Synthetic pending")

    def send(self, action, *args, body=None, chat=None):
        return subprocess.run([sys.executable, "repo_task.py", "--state-dir", str(self.root),
            action, "--chat-id", chat or self.chat, "--task", self.task, *args],
            input=body, capture_output=True, text=True, timeout=7)

    def files(self, action):
        return list(pending.folder(self.root, action).glob("*.json"))

    def test_cli_without_pairing_or_http_retains_then_imports_exact_text(self):
        full = "Полный ответ 🧪\\n  пробелы и строки  \\n"
        detail = "Проверено действие.\\nСледующий этап — проверка."
        for name, stage, summary, body in (
            ("user_message", "other", MESSAGE_SUMMARIES["user_message"], None),
            ("progress", "reviewing", "Проверяю запрос", detail)):
            result = self.send("event", "--event", name, "--stage", stage, "--summary", summary,
                               *(["--detail-stdin"] if body else []), body=body)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("STAGED_ONLY", result.stdout)
        result = self.send("message", "--kind", "final", body=full)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(full, result.stdout)
        self.assertEqual(len(self.files("event")), 3)
        self.assertEqual(len(self.files("message")), 1)
        completion=[json.loads(f.read_text()) for f in self.files("event")
                    if json.loads(f.read_text())["data"]["event"]=="completed"]
        self.assertEqual(len(completion),1)
        self.assertEqual(completion[0]["task_id"],self.task)
        # Collector running before registration cannot consume or guess.
        self.assertEqual(pending.poll_pending(self.root, self.store)["waiting_context"], 4)
        self.assertEqual(list(self.events.glob("*.json")), [])
        self.register("another-chat-12345678")
        self.assertEqual(pending.poll_pending(self.root, self.store)["waiting_context"], 4)
        meta = self.register()
        self.assertEqual(pending.poll_pending(self.root, self.store)["staged"], 4)
        self.assertEqual(self.files("event") + self.files("message"), [])
        self.store.poll()
        self.assertEqual(self.reader.poll()["accepted"], 1)
        history = self.reader.history(meta["reporting_session_id"], self.task)
        self.assertEqual(history["assistant_messages"][0]["body"], full)
        events = self.store.sessions()
        session = next(s for s in events if s["reporting_session_id"] == meta["reporting_session_id"])
        self.assertEqual(len(session["events"]), 3)
        progress = next(e for e in history["events"] if e["event"] == "progress")
        self.assertEqual(progress["detail"], detail)

    def test_service_collector_automatically_processes_pending_after_registration(self):
        import os
        import socket
        import time
        from urllib.request import Request, urlopen
        self.send("event", "--event", "user_message", "--stage", "other",
                  "--summary", MESSAGE_SUMMARIES["user_message"])
        self.send("message", "--kind", "final", body="Automatic offline replay 🧪")
        # Existing synthetic setup predates secure_folder's mode checks.
        for path in [self.root, *self.root.rglob("*")]:
            if path.is_dir():
                path.chmod(0o700)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        child = subprocess.Popen([sys.executable, "-B", "repo_service.py", "run",
            "--state-dir", str(self.root), "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def cleanup():
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=5)
        self.addCleanup(cleanup)
        token_path = self.root / ".repo-http-token"
        def call(path, payload=None):
            token = token_path.read_text().strip()
            data = json.dumps(payload).encode() if payload is not None else None
            req = Request(f"http://127.0.0.1:{port}" + path, data=data,
                          headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
            with urlopen(req, timeout=1) as response:
                return json.load(response)
        deadline = time.monotonic() + 7
        while True:
            try:
                call("/api/state")
                break
            except (OSError, ValueError):
                if time.monotonic() > deadline:
                    self.fail("synthetic service did not start")
                time.sleep(0.05)
        self.assertEqual(len(self.files("message")), 1)
        meta = call("/api/sessions", {"url": "https://chatgpt.com/c/" + self.chat,
                                     "route": "repo", "title": "Synthetic automatic"})["session"]
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline:
            obj = call("/api/repo-history?session=" + meta["reporting_session_id"] + "&task=" + self.task)
            history = obj.get("history", obj)
            if history.get("assistant_messages") and history.get("events"):
                break
            time.sleep(0.05)
        self.assertEqual(history["assistant_messages"][0]["body"], "Automatic offline replay 🧪")
        self.assertEqual(history["events"][0]["event"], "user_message")
        self.assertEqual(self.files("event") + self.files("message"), [])

    def test_multiple_sessions_same_chat_never_guessed(self):
        self.register()
        self.register()
        self.send("message", "--kind", "interim", body="Synthetic")
        self.assertEqual(pending.poll_pending(self.root, self.store)["waiting_context"], 1)
        self.assertIsNone(json.loads(self.files("message")[0].read_text())["binding"])
        self.assertEqual(list(self.messages.glob("*.json")), [])

    def test_retry_pins_binding_before_forward_and_never_rebinds(self):
        first = self.register()
        self.send("message", "--kind", "final", body="Synthetic")
        with patch.object(pending, "stage_assistant", side_effect=OSError("synthetic full disk")):
            self.assertEqual(pending.poll_pending(self.root, self.store)["retryable"], 1)
        path = self.files("message")[0]
        binding = json.loads(path.read_text())["binding"]
        self.assertEqual(binding["session"], first["reporting_session_id"])
        self.register()
        self.assertEqual(pending.poll_pending(self.root, self.store)["staged"], 1)
        self.reader.poll()
        self.assertEqual(len(self.reader.history(first["reporting_session_id"], self.task)["assistant_messages"]), 1)

    def test_removed_pinned_session_does_not_retarget_new_registration(self):
        first = self.register()
        self.send("message", "--kind", "final", body="Synthetic")
        with patch.object(pending, "stage_assistant", side_effect=OSError("synthetic")):
            pending.poll_pending(self.root, self.store)
        (self.store.sessions_path / first["reporting_session_id"] / "session.md").unlink()
        self.register()
        self.assertEqual(pending.poll_pending(self.root, self.store)["waiting_context"], 1)
        self.assertEqual(len(self.files("message")), 1)

    def test_stable_message_id_replay_is_duplicate_not_second_message(self):
        self.register()
        mid = "msg_" + uuid.uuid4().hex
        for _ in range(2):
            self.assertEqual(self.send("message", "--kind", "final", "--message-id", mid, body="Synthetic").returncode, 0)
        self.assertEqual(pending.poll_pending(self.root, self.store)["staged"], 4)
        self.store.poll()
        report = self.reader.poll()
        self.assertEqual(report["accepted"], 1)
        self.assertEqual(report["duplicate"], 1)
        data=self.reader.history(self.store.sessions()[0]["reporting_session_id"],self.task)
        completions=[item for item in data["events"] if item["event"]=="completed"]
        self.assertEqual(len(completions),1, "same message_id must not complete twice")

    def test_bad_metadata_and_detail_are_not_staged(self):
        for args, body in (
            (["--event", "progress", "--stage", "testing", "--summary", "secret value"], None),
            (["--event", "user_message", "--stage", "other", "--summary",
              MESSAGE_SUMMARIES["user_message"], "--detail-stdin"], "Extra text"),
            (["--event", "progress", "--stage", "testing", "--summary", "Проверка",
              "--detail-stdin"], "x" * 8193)):
            self.assertNotEqual(self.send("event", *args, body=body).returncode, 0)
        self.assertEqual(self.files("event"), [])
        self.assertNotEqual(self.send("message", "--kind", "final", body="x", chat="../unsafe").returncode, 0)
        self.assertEqual(self.files("message"), [])

    def test_explicit_wrong_session_is_not_downgraded_to_pending(self):
        self.assertNotEqual(self.send("message", "--session", "rs_" + "a" * 32,
                                     "--kind", "final", body="Synthetic").returncode, 0)
        self.assertEqual(self.files("message"), [])

    def test_capacity_retains_existing_and_symlink_is_not_followed(self):
        with patch.object(pending, "LIMIT", 1):
            path = pending.stage_pending(self.root, "message", self.chat, self.task,
                                         {"kind": "final", "body": "first"})
            with self.assertRaises(ValueError):
                pending.stage_pending(self.root, "message", self.chat, self.task,
                                      {"kind": "final", "body": "second"})
        self.assertEqual(json.loads(path.read_text())["data"]["body"], "first")
        original = path.read_bytes()
        path.unlink()
        outside = self.root / "synthetic-target"
        outside.write_bytes(original)
        path.symlink_to(outside)
        self.assertEqual(pending.poll_pending(self.root, self.store)["refused"], 1)
        self.assertEqual(outside.read_bytes(), original)

    def test_corrupt_pending_record_is_retained_without_output_or_import(self):
        self.send("message", "--kind", "final", body="Synthetic")
        path = self.files("message")[0]
        raw = json.loads(path.read_text())
        raw["unexpected"] = "private"
        path.write_text(json.dumps(raw))
        self.register()
        self.assertEqual(pending.poll_pending(self.root, self.store)["refused"], 1)
        self.assertTrue(path.exists())
        self.assertEqual(list(self.messages.glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
