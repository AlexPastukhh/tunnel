"""Step A: synthetic archives and ephemeral HTTP ports only; never live state."""
import hashlib
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uuid

from server import Application, handler_for
from store import Store, stage
from task_intents import TaskIntents
from test_v1 import v2_event


class IntentStoreTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="fortis-intents-test-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        self.store = Store(self.root / "archive", {"repo": self.inbox})
        self.meta = self.store.register("https://chatgpt.com/c/12345678-abcd", "repo", "Synthetic")
        self.sid = self.meta["reporting_session_id"]
        self.api = TaskIntents(self.store)
        self.key = self.api.issue_key(self.sid, self.meta["conversation_id"])
        self.body = self.body_for()

    def body_for(self):
        return {"version": 1, "reporting_session_id": self.sid,
                "conversation_id": self.meta["conversation_id"],
                "task_id": "task_" + uuid.uuid4().hex,
                "prepared_at_client_ms": int(time.time() * 1000) - 1000}

    def accept(self, task, sequence, name, stage_name="planning"):
        item = v2_event(self.meta, task, sequence, name)
        if name not in ("user_message", "assistant_message"):
            item["stage"] = stage_name
        stage(self.inbox, item)
        self.assertEqual(self.store.poll()["accepted"], 1)

    def card(self, task=None):
        task = task or self.body["task_id"]
        return next(t for t in self.api.snapshot(self.sid)["tasks"] if t["task_id"] == task)

    def test_saved_draft_before_activity_is_persistent_and_idempotent(self):
        before = self.store.sessions()
        receipt = self.api.register(self.body, self.key)
        self.assertTrue(receipt["registered"])
        self.assertEqual(self.card()["state"], "prepared")
        self.assertIsNone(self.card()["first_work_at"])
        again = self.api.register(self.body, self.key)
        self.assertEqual(again, {**receipt, "status": "existing"})
        fresh = TaskIntents(Store(self.root / "archive", {"repo": self.inbox}))
        self.assertEqual(fresh.snapshot(self.sid)["tasks"], self.api.snapshot(self.sid)["tasks"])
        self.assertEqual(self.store.sessions(), before)
        signal = self.store.task_activity(self.sid, self.store.observer_key(self.sid), self.body["task_id"])
        self.assertFalse(signal["found"])

    def test_conflict_and_extra_text_do_not_overwrite_record(self):
        self.api.register(self.body, self.key)
        path = self.api._folder(self.sid) / (self.body["task_id"] + ".md")
        before = path.read_bytes()
        for body in ({**self.body, "prepared_at_client_ms": 1},
                     {**self.body, "original_text": "synthetic private text"},
                     {**self.body, "submitted_text": "synthetic"},
                     {**self.body, "send_state": "sent"}):
            with self.assertRaises(ValueError):
                self.api.register(body, self.key)
        self.assertEqual(path.read_bytes(), before)

    def test_bad_ids_types_future_time_and_enrollment_task_refused(self):
        invalid = [("version", True), ("version", []), ("prepared_at_client_ms", True),
                   ("prepared_at_client_ms", float("nan")), ("prepared_at_client_ms", -1),
                   ("prepared_at_client_ms", int(time.time() * 1000) + 60000),
                   ("task_id", "../other"), ("task_id", self.meta["task_id"]),
                   ("task_id", []), ("conversation_id", "foreign-chat"),
                   ("reporting_session_id", "rs_bad")]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                with self.assertRaises((ValueError, PermissionError)):
                    self.api.register({**self.body, field: value}, self.key)
        self.assertEqual(self.api.snapshot(self.sid)["tasks"], [])

    def test_old_offline_time_does_not_age_a_new_work_signal(self):
        self.body["prepared_at_client_ms"] = 1
        self.api.register(self.body, self.key)
        self.accept(self.body["task_id"], 0, "started")
        self.assertEqual(self.card()["state"], "working")

    def test_observer_writer_and_foreign_keys_cannot_register(self):
        foreign = self.store.register("https://chatgpt.com/c/foreign-12345678", "repo", "Other")
        foreign_key = self.api.issue_key(foreign["reporting_session_id"], foreign["conversation_id"])
        for key in (self.store.observer_key(self.sid), self.store.message_writer_key(self.sid),
                    foreign_key, "invalid"):
            with self.assertRaises(PermissionError):
                self.api.register(self.body, key)
        with self.assertRaises(ValueError):
            self.api.issue_key(self.sid, "foreign-chat")
        self.assertEqual(self.api.snapshot(self.sid)["tasks"], [])

    def test_registration_does_not_unlock_original_archive(self):
        self.api.register(self.body, self.key)
        writer = self.store.message_writer_key(self.sid)
        with self.assertRaisesRegex(ValueError, "first_activity_not_accepted"):
            self.store.write_user_message(self.sid, writer, self.body["task_id"],
                                          self.meta["conversation_id"], "synthetic original")
        self.accept(self.body["task_id"], 0, "user_message")
        self.assertEqual(self.card()["state"], "activity_observed")
        self.assertIsNone(self.card()["first_work_at"])
        receipt = self.store.write_user_message(self.sid, writer, self.body["task_id"],
                                                self.meta["conversation_id"], "synthetic original")
        self.assertEqual(receipt["sha256"], hashlib.sha256(b"synthetic original").hexdigest())
        with self.assertRaises(PermissionError):
            self.store.write_user_message(self.sid, self.key, self.body["task_id"],
                                          self.meta["conversation_id"], "synthetic original")

    def test_user_and_assistant_markers_never_start_work(self):
        self.api.register(self.body, self.key)
        for index, name in enumerate(("user_message", "assistant_message")):
            self.accept(self.body["task_id"], index, name)
            self.assertEqual(self.card()["state"], "activity_observed")
            self.assertIsNone(self.card()["first_work_at"])
        self.accept(self.body["task_id"], 2, "checkpoint")
        self.assertEqual(self.card()["state"], "working")

    def test_work_before_registration_merges_same_task(self):
        self.accept(self.body["task_id"], 0, "progress")
        self.assertFalse(self.card()["preparation_recorded"])
        self.api.register(self.body, self.key)
        self.assertTrue(self.card()["preparation_recorded"])
        self.assertEqual(self.card()["state"], "working")
        self.assertEqual(len(self.api.snapshot(self.sid)["tasks"]), 1)

    def test_terminal_without_started_and_late_registration_cannot_reopen(self):
        for index, terminal in enumerate(("completed", "failed")):
            body = self.body_for()
            self.accept(body["task_id"], index * 2, terminal)
            self.api.register(body, self.key)
            self.accept(body["task_id"], index * 2 + 1, "progress")
            card = self.card(body["task_id"])
            self.assertEqual(card["state"], terminal)
            self.assertEqual(card["terminal_event"], terminal)

    def test_silence_unknown_and_waiting_tool_never_become_failed(self):
        self.accept(self.body["task_id"], 0, "started")
        accepted = self.card()["last_work_at"]
        for seconds, expected in ((899, "working"), (900, "silent"), (3600, "unknown"),
                                  (86400, "unknown")):
            with patch("task_intents.time.time", return_value=accepted + seconds):
                self.assertEqual(self.card()["state"], expected)
        self.accept(self.body["task_id"], 1, "progress", "waiting_tool")
        accepted = self.card()["last_work_at"]
        for seconds, expected in ((1799, "working"), (1800, "silent"), (7200, "unknown")):
            with patch("task_intents.time.time", return_value=accepted + seconds):
                self.assertEqual(self.card()["state"], expected)

    def test_independent_tasks_blocked_and_draft_survive_other_completion(self):
        bodies = [self.body, self.body_for(), self.body_for()]
        for body in bodies:
            self.api.register(body, self.key)
        self.accept(bodies[0]["task_id"], 0, "completed")
        self.accept(bodies[1]["task_id"], 1, "blocked")
        counts = self.api.snapshot(self.sid)["counts"]
        self.assertEqual((counts["completed"], counts["blocked"], counts["prepared"]), (1, 1, 1))
        self.accept(bodies[1]["task_id"], 2, "progress")
        self.assertEqual(self.card(bodies[1]["task_id"])["state"], "working")

    def test_quota_rejects_new_but_accepts_exact_retry(self):
        with patch("task_intents.MAX_INTENTS", 2):
            self.api.register(self.body, self.key)
            self.api.register(self.body_for(), self.key)
            with self.assertRaisesRegex(ValueError, "intent_limit"):
                self.api.register(self.body_for(), self.key)
            self.assertEqual(self.api.register(self.body, self.key)["status"], "existing")

    def test_symlink_key_directory_record_and_corruption_refused(self):
        key_path = self.store._session_dir(self.sid) / ".task-intent-key"
        key_path.unlink()
        key_path.symlink_to(self.root / "missing")
        with self.assertRaises((ValueError, PermissionError)):
            self.api.register(self.body, self.key)
        key_path.unlink()
        self.key = self.api.issue_key(self.sid, self.meta["conversation_id"])
        folder = self.api._folder(self.sid)
        folder.symlink_to(self.root)
        with self.assertRaises(ValueError):
            self.api.register(self.body, self.key)
        folder.unlink()
        self.api.register(self.body, self.key)
        path = folder / (self.body["task_id"] + ".md")
        path.unlink()
        path.symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            self.api.register(self.body, self.key)
        with self.assertRaises(ValueError):
            self.api.snapshot(self.sid)
        path.unlink()
        path.write_text("corrupted", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.api.snapshot(self.sid)

    def test_failed_atomic_write_has_no_receipt_and_can_retry(self):
        with patch("task_intents._atomic", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                self.api.register(self.body, self.key)
        self.assertEqual(self.api.snapshot(self.sid)["tasks"], [])
        self.assertEqual(self.api.register(self.body, self.key)["status"], "created")


    def test_staged_event_is_not_work_and_no_activity_never_times_out_to_failed(self):
        self.api.register(self.body, self.key)
        stage(self.inbox, v2_event(self.meta, self.body["task_id"], 0, "started"))
        with patch("task_intents.time.time", return_value=time.time() + 864000):
            self.assertEqual(self.card()["state"], "prepared")
            self.assertIsNone(self.card()["first_work_at"])
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertEqual(self.card()["state"], "working")

    def test_exact_retry_after_clock_change_preserves_receipt(self):
        first = self.api.register(self.body, self.key)
        with patch("task_intents.time.time", return_value=time.time() - 86400):
            again = self.api.register(self.body, self.key)
        self.assertEqual(first["registered_at_unix"], again["registered_at_unix"])
        self.assertEqual(again["status"], "existing")

    def test_readback_failure_has_no_success_receipt_but_retry_recovers(self):
        read_record = self.api._read
        with patch.object(self.api, "_read", side_effect=lambda *args: {
                **read_record(*args), "registered_at_unix": 1}):
            with self.assertRaisesRegex(OSError, "intent_readback_failed"):
                self.api.register(self.body, self.key)
        self.assertEqual(self.api.register(self.body, self.key)["status"], "existing")

    def test_g2_session_and_missing_key_do_not_implicitly_enable_writes(self):
        g2 = Store(self.root / "g2-archive", {"g2": self.inbox})
        meta = g2.register("https://chatgpt.com/c/g2-chat-12345678", "g2", "G2")
        with self.assertRaises(ValueError):
            TaskIntents(g2).issue_key(meta["reporting_session_id"], meta["conversation_id"])
        path = self.store._session_dir(self.sid) / ".task-intent-key"
        path.unlink()
        with self.assertRaises(PermissionError):
            self.api.register(self.body, self.key)
        self.assertFalse(path.exists())

class IntentHttpTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="fortis-intent-http-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        inbox = root / "inbox"
        inbox.mkdir()
        self.app = Application(root / "archive", {"repo": inbox}, token="synthetic-owner")
        self.meta = self.app.store.register("https://chatgpt.com/c/12345678-abcd", "repo", "Synthetic")
        self.sid = self.meta["reporting_session_id"]
        self.body = {"version": 1, "reporting_session_id": self.sid,
                     "conversation_id": self.meta["conversation_id"],
                     "task_id": "task_" + uuid.uuid4().hex,
                     "prepared_at_client_ms": int(time.time() * 1000) - 1000}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.app))
        self.addCleanup(self.server.server_close)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.shutdown)
        self.key = TaskIntents(self.app.store).issue_key(self.sid, self.meta["conversation_id"])

    def request(self, method="POST", path="/api/task-intents", body=None, headers=None, raw=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        self.addCleanup(conn.close)
        head = {"Content-Type": "application/json", **(headers or {})}
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        conn.request(method, path, body=data, headers=head)
        response = conn.getresponse()
        return response.status, json.loads(response.read())

    def pair_body(self):
        return {k: self.body[k] for k in ("version", "reporting_session_id", "conversation_id")}

    def test_pairing_is_explicit_owner_post_only(self):
        path = "/api/task-intent-pair"
        for headers in ({}, {"X-Fortis-Task-Intent-Key": self.key},
                        {"X-Fortis-Observer-Key": self.app.store.observer_key(self.sid)}):
            self.assertEqual(self.request(path=path, body=self.pair_body(), headers=headers)[0], 401)
        code, data = self.request(path=path, body=self.pair_body(), headers={"Authorization": "Bearer synthetic-owner"})
        self.assertEqual(code, 200)
        self.assertEqual(data["pairing"]["task_intent_key"], self.key)
        self.assertEqual(self.request("GET", path, headers={"Authorization": "Bearer synthetic-owner"})[0], 404)

    def test_register_read_and_capabilities_are_separate(self):
        for headers in ({}, {"Authorization": "Bearer synthetic-owner"},
                        {"X-Fortis-Task-Intent-Key": self.app.store.observer_key(self.sid)},
                        {"X-Fortis-Task-Intent-Key": self.app.store.message_writer_key(self.sid)}):
            self.assertEqual(self.request(body=self.body, headers=headers)[0], 403)
        headers = {"X-Fortis-Task-Intent-Key": self.key}
        self.assertEqual(self.request(body=self.body, headers=headers)[0], 201)
        self.assertEqual(self.request(body=self.body, headers=headers)[0], 200)
        path = "/api/task-intents?session=" + self.sid
        for head in ({}, headers, {"X-Fortis-Observer-Key": self.app.store.observer_key(self.sid)}):
            self.assertEqual(self.request("GET", path, headers=head)[0], 401)
        code, data = self.request("GET", path, headers={"Authorization": "Bearer synthetic-owner"})
        self.assertEqual(code, 200)
        self.assertEqual(data["counts"]["prepared"], 1)
        encoded = json.dumps(data)
        for value in (self.key, "original_text", "submitted_text", "summary", "synthetic-owner", "_key"):
            self.assertNotIn(value, encoded)

    def test_foreign_session_and_chat_do_not_gain_records(self):
        foreign = self.app.store.register("https://chatgpt.com/c/other-12345678", "repo", "Other")
        for field, value, expected in (("reporting_session_id", foreign["reporting_session_id"], 403),
                                       ("conversation_id", foreign["conversation_id"], 409)):
            code, _ = self.request(body={**self.body, field: value}, headers={"X-Fortis-Task-Intent-Key": self.key})
            self.assertEqual(code, expected)
        self.assertEqual(TaskIntents(self.app.store).snapshot(self.sid)["tasks"], [])

    def test_origin_host_and_cross_site_refused_for_both_posts(self):
        for path, body in (("/api/task-intents", self.body), ("/api/task-intent-pair", self.pair_body())):
            for extra in ({"Host": "evil.invalid"}, {"Origin": "https://chatgpt.com"},
                          {"Sec-Fetch-Site": "cross-site"}):
                headers = {"X-Fortis-Task-Intent-Key": self.key, "Authorization": "Bearer synthetic-owner", **extra}
                self.assertEqual(self.request(path=path, body=body, headers=headers)[0], 403)

    def test_schema_duplicates_content_type_oversize_and_query_refused(self):
        head = {"X-Fortis-Task-Intent-Key": self.key}
        duplicate = (json.dumps(self.body)[:-1] + ", \"version\": 1}").encode()
        for raw in (duplicate, b'[]', b'{', b' ' * 1025):
            self.assertEqual(self.request(raw=raw, headers=head)[0], 409)
        for extra in ({"original_text": "synthetic"}, {"task_intent_key": self.key}, {"send_state": "sent"}):
            self.assertEqual(self.request(body={**self.body, **extra}, headers=head)[0], 409)
        self.assertEqual(self.request(body=self.body, headers={**head, "Content-Type": "text/plain"})[0], 409)
        self.assertEqual(self.request(path="/api/task-intents?extra=1", body=self.body, headers=head)[0], 403)
        for suffix in ("", "?session=", "?session=" + self.sid + "&session=" + self.sid,
                       "?session=" + self.sid + "&extra=1"):
            self.assertEqual(self.request("GET", "/api/task-intents" + suffix,
                                         headers={"Authorization": "Bearer synthetic-owner"})[0], 409)

    def test_storage_failure_returns_retryable_without_leaking_exception(self):
        with patch("task_intents._atomic", side_effect=OSError("private synthetic diagnostic")):
            code, data = self.request(body=self.body, headers={"X-Fortis-Task-Intent-Key": self.key})
        self.assertEqual(code, 503)
        self.assertNotIn("private", json.dumps(data))
        self.assertEqual(self.request(body=self.body, headers={"X-Fortis-Task-Intent-Key": self.key})[0], 201)


    def test_concurrent_retries_create_one_record(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.request(
                body=self.body, headers={"X-Fortis-Task-Intent-Key": self.key}), range(8)))
        self.assertEqual(sorted(code for code, _ in results), [200] * 7 + [201])
        self.assertEqual(len({body["registered_at_unix"] for _, body in results}), 1)
        self.assertEqual(len(TaskIntents(self.app.store).snapshot(self.sid)["tasks"]), 1)
        path = "/api/task-activity?session=" + self.sid + "&task=" + self.body["task_id"]
        self.assertEqual(self.request("GET", path, headers={"X-Fortis-Observer-Key": self.key})[0], 403)

if __name__ == "__main__":
    unittest.main()
