import json
import subprocess
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

from store import Store, chat_id, stage
from server import Application, handler_for


def event(meta, sequence=0, event_name="started", summary="Начата работа"):
    return {"version": 1, "event_id": uuid.uuid4().hex,
            "reporting_session_id": meta["reporting_session_id"],
            "task_id": meta["task_id"], "route": meta["route"],
            "sequence": sequence, "event": event_name,
            "stage": "planning", "summary": summary}


def v2_event(meta, task_id, sequence, name, summary="Изучаю задачу"):
    item = event(meta, sequence, "progress", summary)
    item.update(version=2, task_id=task_id, session_task_id=meta["task_id"], event=name)
    if name in ("user_message", "assistant_message"):
        item["stage"] = "other"
        item["summary"] = ("Получено сообщение пользователя" if name == "user_message"
                           else "Ответ ChatGPT заявлен отправителем")
    return item


class FileFirstTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        self.archive = self.root / "archive"
        self.store = Store(self.archive, {"repo": self.inbox})
        self.meta = self.store.register("https://chatgpt.com/c/12345678-abcd?x=1", "repo", "Тест задачи")

    def test_manual_enrollment_and_two_sessions_same_chat(self):
        self.assertEqual(chat_id("https://chatgpt.com/c/12345678-abcd"), "12345678-abcd")
        self.assertEqual(len(self.store.sessions()), 1)
        new = self.store.register("https://chatgpt.com/c/12345678-abcd", "repo", "Другая задача")
        self.assertNotEqual(new["reporting_session_id"], self.meta["reporting_session_id"])
        self.assertEqual(len(self.store.sessions()), 2)
        for url in ("http://chatgpt.com/c/12345678-abcd", "https://evil.com/c/12345678-abcd",
                    "https://chatgpt.com/share/12345678-abcd", "https://chatgpt.com/c/../../a"):
            with self.assertRaises(ValueError):
                chat_id(url)

    def test_cli_sender_to_markdown_end_to_end(self):
        command = [sys.executable, str(Path(__file__).with_name("emit.py")),
                   "--inbox", str(self.inbox),
                   "--session", self.meta["reporting_session_id"],
                   "--task", self.meta["task_id"], "--route", "repo",
                   "--sequence", "0", "--event", "started",
                   "--stage", "planning", "--summary", "Начата работа"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STAGED_ONLY", result.stdout)
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events"][0]["summary"], "Начата работа")

    def test_detailed_event_utf8_stdin_archive_and_legacy_fallback(self):
        # repo_task's security boundary intentionally allows only /workspace/repo.
        with tempfile.TemporaryDirectory(dir="/workspace/repo") as d:
            root = Path(d)
            inbox = root / "inbox" / "repo"
            inbox.mkdir(parents=True)
            receiver = Store(root / "archive", {"repo": inbox})
            meta = receiver.register("https://chatgpt.com/c/12345678-abcd", "repo", "Тест")
            task = "task_" + uuid.uuid4().hex
            explanation = ("Проверил содержимое схемы.\n"
                           "Обнаружил короткий summary; отдельное пояснение 🌍.\n"
                           "Следующий шаг — проверить отображение.\n") * 10
            command = [sys.executable, str(Path(__file__).with_name("repo_task.py")),
                       "--state-dir", str(root), "event",
                       "--session", meta["reporting_session_id"],
                       "--chat-id", meta["conversation_id"],
                       "--task", task, "--event", "progress", "--stage", "reviewing",
                       "--summary", "Проверяю структуру", "--detail-stdin"]
            result = subprocess.run(command, input=explanation, capture_output=True,
                                    text=True, timeout=7)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("STAGED_ONLY", result.stdout)
            self.assertEqual(list(inbox.glob("*.json")), [],
                             "old importer must not see compound detail events")
            self.assertEqual(len(list((inbox / ".event_bundle").glob("*.json"))), 1)
            stats = receiver.poll()
            self.assertEqual(stats["accepted"], 1, stats)
            item = next(x for x in receiver.sessions()[0]["events"] if x["task_id"] == task)
            self.assertEqual(item["summary"], "Проверяю структуру")
            self.assertTrue(item["has_detail"])
            from repo_messages import RepoMessages
            archive = root / "archive"
            rm = RepoMessages(receiver, root / "inbox" / "messages", root / "quarantine")
            events = rm.history(meta["reporting_session_id"], task)["events"]
            self.assertEqual(events[0]["detail"], explanation)
            self.assertEqual(receiver.poll()["accepted"], 0)
            stage(inbox, v2_event(meta, task, 1, "progress", "Старое событие"))
            self.assertEqual(receiver.poll()["accepted"], 1)
            old = next(x for x in receiver.sessions()[0]["events"]
                       if x["summary"] == "Старое событие")
            self.assertNotIn("detail", old)
            self.assertEqual(list((inbox / ".event_details").glob("*.txt")), [])

    def test_missing_bundle_detail_cannot_accept_event_or_receipt(self):
        with tempfile.TemporaryDirectory(dir="/workspace/repo") as d:
            root=Path(d)
            inbox=root/"inbox"/"repo"
            (inbox/".event_bundle").mkdir(parents=True)
            receiver=Store(root/"archive",{"repo":inbox})
            meta=receiver.register("https://chatgpt.com/c/12345678-abcd","repo","Тест")
            task="task_"+uuid.uuid4().hex
            item=v2_event(meta,task,0,"progress","Подробное событие")
            bundle=stage(inbox/".event_bundle",item)
            first=receiver.poll()
            self.assertEqual(first["accepted"],0,first)
            self.assertEqual(first["retryable"],1,first)
            self.assertTrue(bundle.exists())
            self.assertEqual(receiver.sessions()[0]["events_count"],0)
            from store import _dir, _atomic
            details=_dir(inbox/".event_details")
            details.mkdir(exist_ok=True)
            original="Проверил корректность → продолжу анализ 🌍"
            _atomic(details/(item["event_id"]+".txt"),original.encode("utf-8"))
            recovered=receiver.poll()
            self.assertEqual(recovered["accepted"],1,recovered)
            self.assertFalse(bundle.exists())
            self.assertTrue(receiver.sessions()[0]["events"][0]["has_detail"])
            from repo_messages import RepoMessages
            repo=RepoMessages(receiver,root/"inbox"/"messages",root/"quarantine")
            self.assertEqual(repo.history(meta["reporting_session_id"],task)["events"][0]["detail"],original)
            legacy=v2_event(meta,task,1,"progress","Старый формат")
            stage(inbox,legacy)
            self.assertEqual(receiver.poll()["accepted"],1)
            self.assertEqual(receiver.sessions()[0]["events_count"],2)

    def test_detailed_event_rejects_oversize_and_marker(self):
        with tempfile.TemporaryDirectory(dir="/workspace/repo") as d:
            root = Path(d)
            inbox = root / "inbox" / "repo"
            inbox.mkdir(parents=True)
            meta = Store(root / "archive", {"repo": inbox}).register(
                "https://chatgpt.com/c/12345678-abcd", "repo", "Тест")
            task = "task_" + uuid.uuid4().hex
            cmd = [sys.executable, str(Path(__file__).with_name("repo_task.py")),
                   "--state-dir", str(root), "event",
                   "--session", meta["reporting_session_id"],
                   "--chat-id", meta["conversation_id"], "--task", task,
                   "--event", "progress", "--stage", "reviewing",
                   "--summary", "Проверяю тесты", "--detail-stdin"]
            for body in ("A"*8193, "secret in event text"):
                result = subprocess.run(cmd, input=body, capture_output=True,
                                        text=True, timeout=7)
                self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(inbox.glob("*.json")), [])
            self.assertEqual(list((inbox / ".event_details").glob("*.txt")), [])

    def test_staged_accepted_and_markdown_readback(self):
        item = event(self.meta)
        filename = stage(self.inbox, item)
        self.assertEqual(len(list(self.archive.rglob("*.md"))), 1)
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertFalse(filename.exists())
        session = self.store.sessions()[0]
        self.assertEqual(session["state"], "WORKING")
        self.assertEqual(session["events"][0]["summary"], "Начата работа")
        paths = list((self.archive / "sessions" / self.meta["reporting_session_id"] / "events").glob("*.md"))
        self.assertEqual(len(paths), 1)
        text = paths[0].read_text(encoding="utf-8")
        self.assertIn("# STARTED", text)
        self.assertIn("Начата работа", text)

    def test_delete_file_no_resurrection_and_external_edit(self):
        item = event(self.meta)
        stage(self.inbox, item)
        self.store.poll()
        event_file = next((self.store._session_dir(self.meta["reporting_session_id"]) / "events").glob("*.md"))
        event_file.write_text(event_file.read_text(encoding="utf-8").replace("Начата работа", "Исправлена заметка"),
                              encoding="utf-8")
        self.assertEqual(self.store.sessions()[0]["events"][0]["summary"], "Исправлена заметка")
        event_file.unlink()
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)
        self.store = Store(self.archive, {"repo": self.inbox})  # restart
        stage(self.inbox, item)  # duplicate arriving after deleted file
        self.assertEqual(self.store.poll()["duplicate"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)
        (self.store._session_dir(self.meta["reporting_session_id"]) / "session.md").unlink()
        self.assertEqual(self.store.sessions(), [])

    def test_accepted_not_result_saved_and_late_sequences(self):
        for n, kind in ((0, "started"), (1, "progress"), (2, "completed")):
            stage(self.inbox, event(self.meta, n, kind))
        self.assertEqual(self.store.poll()["accepted"], 3)
        session = self.store.sessions()[0]
        self.assertEqual(session["state"], "REPORTED_COMPLETED")
        self.assertNotIn("SAVED", session["state"])
        self.assertEqual([e["sequence"] for e in session["events"]], [0, 1, 2])

    def test_stepwise_progress_visible_before_completion(self):
        steps = (
            ("started", "planning", "Планирую работу"),
            ("progress", "reviewing", "Изучаю структуру проекта"),
            ("progress", "editing", "Вношу исправления"),
            ("checkpoint", "testing", "Тесты прошли"),
            ("progress", "reviewing", "Проверяю результат"),
            ("completed", "other", "Работа завершена"),
        )
        for sequence, (kind, stage_name, description) in enumerate(steps):
            payload = event(self.meta, sequence, kind, description)
            payload["stage"] = stage_name
            stage(self.inbox, payload)
            self.assertEqual(self.store.poll()["accepted"], 1)
            snapshot = self.store.sessions()[0]
            self.assertEqual(snapshot["events_count"], sequence + 1)
            self.assertEqual([x["sequence"] for x in snapshot["events"]],
                             list(range(sequence + 1)))
            self.assertEqual(snapshot["events"][-1]["summary"], description)
            self.assertEqual(snapshot["events"][-1]["stage"], stage_name)
            self.assertEqual(snapshot["state"],
                             "REPORTED_COMPLETED" if kind == "completed" else "WORKING")
        restored = Store(self.archive, {"repo": self.inbox}).sessions()[0]
        self.assertEqual(restored["events_count"], len(steps))
        self.assertEqual(restored["missing_sequences"], 0)

    def test_reject_wrong_session_route_task_and_payload(self):
        wrong = event(self.meta)
        wrong["task_id"] = "task_wrong"
        stage(self.inbox, wrong)
        self.assertEqual(self.store.poll()["unknown_session"], 1)
        for value in ("<script>", "http://private.example", "C:\\users\\owner"):
            broken = event(self.meta, summary=value)
            with self.assertRaises(ValueError):
                stage(self.inbox, broken)
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)

    def test_v2_unique_task_per_user_message_and_legacy_compatibility(self):
        task_one = "task_" + uuid.uuid4().hex
        task_two = "task_" + uuid.uuid4().hex
        self.assertNotEqual(task_one, task_two)
        self.assertNotEqual(task_one, self.meta["task_id"])
        records = (
            v2_event(self.meta, task_one, 0, "user_message"),
            v2_event(self.meta, task_one, 1, "started"),
            v2_event(self.meta, task_one, 2, "progress"),
            v2_event(self.meta, task_one, 3, "assistant_message"),
            v2_event(self.meta, task_one, 4, "completed", "Завершена работа"),
            v2_event(self.meta, task_two, 5, "user_message"),
            v2_event(self.meta, task_two, 6, "started"),
            v2_event(self.meta, task_two, 7, "completed", "Завершена работа"),
        )
        for item in records:
            stage(self.inbox, item)
            self.assertEqual(self.store.poll()["accepted"], 1)
        view = self.store.sessions()[0]
        self.assertEqual(view["events_count"], 8)
        self.assertEqual(view["missing_sequences"], 0)
        self.assertEqual(view["state"], "REPORTED_COMPLETED")
        self.assertEqual(view["last_task_id"], task_two)
        self.assertEqual([x["task_id"] for x in view["events"]],
                         [task_one] * 5 + [task_two] * 3)
        restored = Store(self.archive, {"repo": self.inbox})
        self.assertEqual(restored.sessions()[0]["events_count"], 8)
        self.assertEqual(restored.sessions()[0]["last_task_id"], task_two)
        # A legacy event still requires the enrollment task ID.
        stage(self.inbox, event(self.meta, 8, "checkpoint", "Проверка пройдена"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 9)

    def test_offline_v2_collision_resequenced_without_losing_any_event(self):
        # Sender cannot see a running server; all events reused cached seq=0.
        task = "task_" + uuid.uuid4().hex
        pending = [stage(self.inbox, v2_event(self.meta, task, 0, kind))
                   for kind in ("user_message", "progress", "assistant_message", "completed")]
        self.assertTrue(all(p.exists() for p in pending))
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)
        result = self.store.poll()
        self.assertEqual((result["accepted"], result["rejected"]), (4, 0))
        self.assertTrue(all(not p.exists() for p in pending))
        session = self.store.sessions()[0]
        self.assertEqual([e["sequence"] for e in session["events"]], [0, 1, 2, 3])
        self.assertEqual([e["sender_sequence"] for e in session["events"]], [0] * 4)
        self.assertEqual([e["event"] for e in session["events"]],
                         ["user_message", "progress", "assistant_message", "completed"])
        self.assertEqual(session["state"], "REPORTED_COMPLETED")
        first = self.store.task_activity(self.meta["reporting_session_id"],
                                         self.store.observer_key(self.meta["reporting_session_id"]), task)
        self.assertEqual((first["found"], first["event"], first["sequence"]),
                         (True, "user_message", 0))
        reopened = Store(self.archive, {"repo": self.inbox})
        self.assertEqual(reopened.sessions()[0]["events_count"], 4)
        # A fifth late sender file with another cached 0 must still be accepted.
        stage(self.inbox, v2_event(self.meta, task, 0, "checkpoint"))
        self.assertEqual(reopened.poll()["accepted"], 1)
        self.assertEqual([x["sequence"] for x in reopened.sessions()[0]["events"]],
                         [0, 1, 2, 3, 4])

    def test_unknown_session_is_deferred_and_accepted_after_restoring_session(self):
        task = "task_" + uuid.uuid4().hex
        archive_folder = self.store._session_dir(self.meta["reporting_session_id"])
        enrollment_file = archive_folder / "session.md"
        missing = self.root / "temp-session.md"
        enrollment_file.rename(missing)
        item = stage(self.inbox, v2_event(self.meta, task, 0, "progress"))
        first = self.store.poll()
        self.assertEqual(first["deferred_session"], 1)
        self.assertEqual(first["unknown_session"], 0)
        self.assertEqual(first["state"], "pending_sessions")
        self.assertTrue(item.exists())
        self.assertEqual(self.store.poll()["deferred_session"], 1)
        enrollment_file.write_bytes(missing.read_bytes())
        missing.unlink()
        successful = self.store.poll()
        self.assertEqual(successful["accepted"], 1)
        self.assertFalse(item.exists())
        self.assertTrue(self.store.task_activity(self.meta["reporting_session_id"],
                                               self.store.observer_key(self.meta["reporting_session_id"]),
                                               task)["found"])

    def test_invalid_enrollment_remains_permanently_refused(self):
        item = v2_event(self.meta, "task_" + uuid.uuid4().hex, 0, "progress")
        item["session_task_id"] = "task_" + uuid.uuid4().hex
        file = stage(self.inbox, item)
        report = self.store.poll()
        self.assertEqual(report["unknown_session"], 1)
        self.assertEqual(report["deferred_session"], 0)
        self.assertFalse(file.exists())
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)

    def test_v1_collision_remains_strict(self):
        first = stage(self.inbox, event(self.meta, 0, "started"))
        second = stage(self.inbox, event(self.meta, 0, "completed"))
        result = self.store.poll()
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(result["rejected"], 1)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertEqual(self.store.sessions()[0]["events_count"], 1)

    def test_stage_names_sort_by_time_and_accept_old_file_names(self):
        from unittest.mock import patch
        task = "task_" + uuid.uuid4().hex
        with patch("store.time.time_ns", side_effect=[222, 111, 333]):
            later = stage(self.inbox, v2_event(self.meta, task, 0, "completed"))
            earlier = stage(self.inbox, v2_event(self.meta, task, 0, "progress"))
            last = stage(self.inbox, v2_event(self.meta, task, 0, "checkpoint"))
        self.assertRegex(earlier.name, r"^[0-9]{20}-[0-9a-f]{32}\.json$")
        # Legacy UUID-only files remain importable during transition.
        legacy = self.inbox / (uuid.uuid4().hex + ".json")
        legacy.write_bytes(stage(self.inbox, v2_event(self.meta, task, 0, "blocked")).read_bytes())
        # Ignore the extra staging source for this one test of legacy compatibility.
        for f in self.inbox.iterdir():
            if f.name not in (later.name, earlier.name, last.name, legacy.name):
                f.unlink()
        result = self.store.poll()
        self.assertEqual(result["accepted"], 4)
        self.assertEqual(self.store.sessions()[0]["events_count"], 4)
        self.assertTrue(all(e["sender_sequence"] == 0 for e in self.store.sessions()[0]["events"]))
        # Timestamp-prefixed files are ordered by the local sender clock;
        # legacy files were historically unordered and do not have this claim.

    def test_first_accepted_per_task_signal_persists_and_is_not_last_event(self):
        sid = self.meta["reporting_session_id"]
        key = self.store.observer_key(sid)
        a = "task_" + uuid.uuid4().hex
        b = "task_" + uuid.uuid4().hex
        self.assertFalse(self.store.task_activity(sid, key, a)["found"])
        events = [v2_event(self.meta, b, 0, "assistant_message"),
                  v2_event(self.meta, a, 1, "progress"),
                  v2_event(self.meta, b, 2, "completed"),
                  v2_event(self.meta, a, 3, "user_message")]
        for item in events:
            stage(self.inbox, item)
            self.assertEqual(self.store.poll()["accepted"], 1)
        activity_a = self.store.task_activity(sid, key, a)
        activity_b = self.store.task_activity(sid, key, b)
        self.assertEqual((activity_a["event"], activity_a["sequence"]), ("progress", 1))
        self.assertEqual((activity_b["event"], activity_b["sequence"]), ("assistant_message", 0))
        self.assertEqual(activity_a["provenance"], "sender_claim")
        self.assertNotIn("summary", activity_a)
        self.assertNotIn("body", activity_b)
        self.assertEqual(Store(self.archive, {"repo": self.inbox}).task_activity(sid, key, b)["sequence"], 0)
        with self.assertRaises(PermissionError):
            self.store.task_activity(sid, "wrong", a)
        # The legacy enrollment ID has the same syntax, but is not an activity signal.
        self.assertFalse(self.store.task_activity(sid, key, self.meta["task_id"])["found"])
        with self.assertRaises(ValueError):
            self.store.task_activity(sid, key, "task_foobar")
        # External removal follows file-first owner archive source of truth.
        first = next((self.store._session_dir(sid) / "events").glob("000000-*.md"))
        first.unlink()
        self.assertEqual(self.store.task_activity(sid, key, b)["sequence"], 2)

    def test_v2_message_markers_never_serialize_chat_text(self):
        task_id = "task_" + uuid.uuid4().hex
        wrong = v2_event(self.meta, task_id, 0, "user_message")
        wrong["summary"] = "Часть текста сообщения"
        with self.assertRaisesRegex(ValueError, "unsafe_message_marker"):
            stage(self.inbox, wrong)
        wrong = v2_event(self.meta, task_id, 0, "user_message")
        wrong["full_text"] = "secret should never be stored"
        with self.assertRaisesRegex(ValueError, "invalid_schema"):
            stage(self.inbox, wrong)
        wrong = v2_event(self.meta, task_id, 0, "user_message")
        wrong["session_task_id"] = "task_" + uuid.uuid4().hex
        stage(self.inbox, wrong)
        self.assertEqual(self.store.poll()["unknown_session"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)
        # Message marker alone is not a work-start/completion status.
        stage(self.inbox, v2_event(self.meta, task_id, 0, "user_message"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        key = self.store.observer_key(self.meta["reporting_session_id"])
        status = self.store.observer_status(self.meta["reporting_session_id"], key)
        self.assertEqual((status["event"], status["sequence"]), ("none", -1))
        stage(self.inbox, v2_event(self.meta, task_id, 1, "completed"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        stage(self.inbox, v2_event(self.meta, task_id, 2, "assistant_message"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        status = self.store.observer_status(self.meta["reporting_session_id"], key)
        self.assertEqual((status["event"], status["sequence"], status["task_id"]),
                         ("completed", 1, task_id))
        self.assertNotIn("summary", status)

    def test_user_message_writer_requires_accepted_signal_and_idempotence(self):
        sid = self.meta["reporting_session_id"]
        task = "task_" + uuid.uuid4().hex
        writer = self.store.message_writer_key(sid)
        observer = self.store.observer_key(sid)
        original = "  Привет\n~~~json\n</script>  "
        self.assertNotEqual(writer, observer)
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], original)
        stage(self.inbox, v2_event(self.meta, task, 0, "progress"))
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], original)
        self.assertEqual(self.store.poll()["accepted"], 1)
        with self.assertRaises(PermissionError):
            self.store.write_user_message(sid, observer, task, self.meta["conversation_id"], original)
        receipt = self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], original)
        self.assertEqual(receipt["status"], "created")
        path = self.store._user_message_path(sid, task)
        meta, text = self.store._read_user_message(path)
        self.assertEqual(text, original)
        self.assertNotIn("</script>", path.read_text(encoding="utf-8"))
        self.assertEqual(meta["sha256"], receipt["sha256"])
        self.assertEqual(self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], original)["status"], "existing")
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], "other")
        restored = Store(self.archive, {"repo": self.inbox})
        self.assertEqual(restored.write_user_message(sid, writer, task, self.meta["conversation_id"], original)["status"], "existing")
        path.unlink()
        with self.assertRaises(ValueError):
            restored.write_user_message(sid, writer, task, self.meta["conversation_id"], original)

    def test_user_original_above_old_limit_keeps_exact_unicode_and_deduplicates(self):
        sid = self.meta["reporting_session_id"]
        task = "task_" + uuid.uuid4().hex
        writer = self.store.message_writer_key(sid)
        original = ("Длинный оригинал 🌍\\n" * 6000).rstrip() + "\\n<private>\\n"
        assert 65536 < len(original.encode("utf-8")) < 512 * 1024
        stage(self.inbox, v2_event(self.meta, task, 0, "progress"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        receipt = self.store.write_user_message(
            sid, writer, task, self.meta["conversation_id"], original)
        self.assertEqual(receipt["status"], "created")
        path = self.store._user_message_path(sid, task)
        self.assertEqual(self.store._read_user_message(path)[1], original)
        self.assertEqual(self.store.write_user_message(
            sid, writer, task, self.meta["conversation_id"], original)["status"], "existing")

    def test_user_archive_oversize_and_symlink_receipt_refused(self):
        sid = self.meta["reporting_session_id"]
        task = "task_" + uuid.uuid4().hex
        writer = self.store.message_writer_key(sid)
        stage(self.inbox, v2_event(self.meta, task, 0, "completed"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], "X" * (512 * 1024 + 1))
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, self.meta["conversation_id"], "")
        with self.assertRaises(ValueError):
            self.store.write_user_message(sid, writer, task, "wrong-12345678", "text")
        self.assertFalse(self.store._user_message_path(sid, task).exists())
        # Even a dangling receipt symlink must never be followed.
        receipt = self.store.user_message_ids
        try:
            receipt.symlink_to(self.root / "does-not-exist")
        except (OSError, NotImplementedError):
            return  # Platform restrictions; Windows reparse acceptance separately.
        with self.assertRaises(ValueError):
            Store(self.archive, {"repo": self.inbox})

    def test_cli_v2_requires_enrollment_and_preserves_message_id(self):
        task_id = "task_" + uuid.uuid4().hex
        base = [sys.executable, str(Path(__file__).with_name("emit.py")),
                "--inbox", str(self.inbox), "--session", self.meta["reporting_session_id"],
                "--task", task_id, "--version", "2", "--route", "repo",
                "--sequence", "0", "--event", "user_message", "--stage", "other",
                "--summary", "Получено сообщение пользователя"]
        missing = subprocess.run(base, capture_output=True, text=True, timeout=5)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("NOT_STAGED", missing.stdout)
        sent = subprocess.run(base + ["--session-task", self.meta["task_id"]],
                              capture_output=True, text=True, timeout=5)
        self.assertEqual(sent.returncode, 0, sent.stdout + sent.stderr)
        self.assertIn("STAGED_ONLY", sent.stdout)
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events"][0]["task_id"], task_id)

    def test_collision_and_symlink(self):
        first = event(self.meta, 0)
        stage(self.inbox, first)
        self.store.poll()
        stage(self.inbox, event(self.meta, 0))
        self.assertEqual(self.store.poll()["rejected"], 1)
        file = self.inbox / (uuid.uuid4().hex + ".json")
        file.symlink_to(self.archive / "sessions" / self.meta["reporting_session_id"] / "session.md")
        self.assertGreaterEqual(self.store.poll()["rejected"], 1)

    def test_missing_sequence_and_bad_archive_file_visible(self):
        stage(self.inbox, event(self.meta, 2, "progress"))
        self.assertEqual(self.store.poll()["accepted"], 1)
        folder = self.store._session_dir(self.meta["reporting_session_id"]) / "events"
        bad = folder / ("000003-" + "a" * 32 + ".md")
        bad.write_text("<script>bad</script>", encoding="utf-8")
        result = self.store.sessions()[0]
        self.assertEqual(result["missing_sequences"], 2)
        self.assertEqual(result["invalid_files"], 1)

    def test_invalid_json_enum_types_do_not_stop_other_events(self):
        for i, (field, value) in enumerate((("route", []), ("event", {}), ("stage", []))):
            payload = event(self.meta, i)
            payload[field] = value
            (self.inbox / (f"{i:032x}.json")).write_text(json.dumps(payload), encoding="utf-8")
        stage(self.inbox, event(self.meta, 3))
        result = self.store.poll()
        self.assertEqual(result["rejected"], 3)
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 1)
        self.assertEqual(list(self.inbox.glob("*.json")), [])

    def test_conflicting_queued_event_does_not_restore_deleted_markdown(self):
        stage(self.inbox, event(self.meta, 0))
        stage(self.inbox, event(self.meta, 0))
        status = self.store.poll()
        self.assertEqual((status["accepted"], status["rejected"]), (1, 1))
        self.assertEqual(list(self.inbox.glob("*.json")), [])
        folder = self.store._session_dir(self.meta["reporting_session_id"]) / "events"
        next(folder.glob("*.md")).unlink()
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)
        self.store = Store(self.archive, {"repo": self.inbox})
        self.assertEqual(self.store.poll()["accepted"], 0)
        self.assertEqual(self.store.sessions()[0]["events_count"], 0)

    def test_backlog_above_limit_drains_over_two_passes(self):
        for n in range(513):
            payload = event(self.meta, n)
            (self.inbox / (f"{n:032x}.json")).write_text(json.dumps(payload), encoding="utf-8")
        first = self.store.poll()
        self.assertEqual(first["state"], "capacity_exceeded")
        self.assertEqual(first["accepted"], 512)
        self.assertEqual(len(list(self.inbox.glob("*.json"))), 1)
        second = self.store.poll()
        self.assertEqual(second["accepted"], 1)
        self.assertEqual(second["state"], "available")
        self.assertEqual(self.store.sessions()[0]["events_count"], 513)

    def test_backlog_fairness_with_retryable_items(self):
        from unittest.mock import patch
        for n in range(513):
            payload = event(self.meta, n)
            (self.inbox / (f"{n:032x}.json")).write_text(json.dumps(payload), encoding="utf-8")
        real_import = self.store._import_one

        def fail_first_batch(route, candidate):
            if int(candidate.stem, 16) < 512:
                raise OSError("temporary synthetic read failure")
            return real_import(route, candidate)

        with patch.object(self.store, "_import_one", side_effect=fail_first_batch):
            first = self.store.poll()
            self.assertEqual((first["retryable"], first["accepted"]), (512, 0))
            second = self.store.poll()
            self.assertEqual(second["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 1)
        self.assertEqual(len(list(self.inbox.glob("*.json"))), 512)

    def test_failed_archive_read_retries_after_manual_repair(self):
        stage(self.inbox, event(self.meta))
        path = self.store._session_dir(self.meta["reporting_session_id"]) / "session.md"
        original = path.read_text(encoding="utf-8")
        path.write_text("invalid session metadata", encoding="utf-8")
        self.assertEqual(self.store.poll()["retryable"], 1)
        self.assertEqual(len(list(self.inbox.glob("*.json"))), 1)
        path.write_text(original, encoding="utf-8")
        self.assertEqual(self.store.poll()["accepted"], 1)
        self.assertEqual(self.store.sessions()[0]["events_count"], 1)

    def test_corrupted_metadata_isolated_from_other_sessions(self):
        second = self.store.register("https://chatgpt.com/c/87654321-aaaa", "repo", "Other")
        stage(self.inbox, event(self.meta))
        stage(self.inbox, event(second))
        self.store.poll()
        path = next((self.store._session_dir(self.meta["reporting_session_id"]) / "events").glob("*.md"))
        original = path.read_text(encoding="utf-8")
        meta_line, rest = original.split("\n", 1)
        prefix, suffix = "<!-- fortis-v1 ", " -->"
        metadata = json.loads(meta_line[len(prefix):-len(suffix)])
        for field, bad_value in (("sequence", "invalid"), ("accepted_unix", "invalid"),
                                 ("event", {}), ("accepted_at", {})):
            with self.subTest(field=field):
                broken = dict(metadata)
                broken[field] = bad_value
                path.write_text(prefix + json.dumps(broken) + suffix + "\n" + rest, encoding="utf-8")
                sessions = self.store.sessions()
                self.assertEqual(len(sessions), 2)
                bad = next(s for s in sessions if s["reporting_session_id"] == self.meta["reporting_session_id"])
                good = next(s for s in sessions if s["reporting_session_id"] == second["reporting_session_id"])
                self.assertEqual((bad["events_count"], bad["invalid_files"]), (0, 1))
                self.assertEqual(good["events_count"], 1)
        path.write_text(original, encoding="utf-8")

    def test_last_received_time_independent_of_logical_sequence(self):
        from unittest.mock import patch
        with patch("store.time.time", return_value=1700000000):
            stage(self.inbox, event(self.meta, 2, "progress"))
            self.store.poll()
        with patch("store.time.time", return_value=1700000120):
            stage(self.inbox, event(self.meta, 0))
            self.store.poll()
            current = self.store.sessions()[0]
        arrival_by_sequence = {x["sequence"]: x["accepted_at"] for x in current["events"]}
        self.assertEqual(current["last_signal_at"], arrival_by_sequence[0])
        self.assertEqual([x["sequence"] for x in current["events"]], [0, 2])
        self.assertEqual(current["state"], "WORKING")

    def test_inbox_not_auto_created_and_missing_route(self):
        with self.assertRaises(ValueError):
            Store(self.root / "a", {}).register("https://chatgpt.com/c/12345678-abcd", "repo", "Test")
        with self.assertRaises(ValueError):
            stage(self.root / "missing", event(self.meta))
        with self.assertRaises(ValueError):
            Store(self.root / "other", {"repo": self.root / "missing"}).register(
                "https://chatgpt.com/c/12345678-abcd", "repo", "Test")


class HttpTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        inbox = base / "inbox"
        inbox.mkdir()
        self.app = Application(base / "archive", {"repo": inbox},
                               {"repo": "/workspace/files/approved-inbox"}, token="owner-synthetic-token")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.app))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def request(self, path, method="GET", token=None, body=None, headers=None):
        head = dict(headers or {})
        if token is not None:
            head["Authorization"] = "Bearer " + token
        if body is not None:
            head["Content-Type"] = "application/json"
        req = Request(self.base + path, data=json.dumps(body).encode() if body else None,
                      headers=head, method=method)
        try:
            with urlopen(req, timeout=5) as result:
                return result.status, result.read().decode("utf-8", "replace")
        except HTTPError as error:
            return error.code, error.read().decode("utf-8", "replace")

    def test_owner_positive_guest_negative(self):
        self.assertEqual(self.request("/api/state")[0], 401)
        self.assertEqual(self.request("/api/state", method="HEAD")[0], 401)
        self.assertEqual(self.request("/api/state", token="not-owner")[0], 401)
        self.assertEqual(self.request("/api/state", token="owner-synthetic-token")[0], 200)
        self.assertEqual(self.request("/api/state", token="owner-synthetic-token",
                                      headers={"Sec-Fetch-Site": "cross-site"})[0], 401)
        self.assertEqual(self.request("/api/state", token="owner-synthetic-token",
                                      headers={"Host": "remote.invalid"})[0], 401)
        self.assertEqual(self.request("/store.py")[0], 404)
        self.assertEqual(self.request("/../store.py")[0], 404)
        self.assertEqual(self.request("/")[0], 200)

    def test_http_state_survives_corrupt_event_metadata(self):
        request_body = {"url": "https://chatgpt.com/c/12345678-abcd",
                        "route": "repo", "title": "Synthetic"}
        code, body = self.request("/api/sessions", "POST", "owner-synthetic-token", request_body)
        self.assertEqual(code, 201)
        meta = json.loads(body)["session"]
        payload = event(meta)
        stage(self.app.store.inboxes["repo"], payload)
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        path = next((self.app.store._session_dir(meta["reporting_session_id"]) / "events").glob("*.md"))
        before = path.read_text(encoding="utf-8")
        record, contents = before.split("\n", 1)
        obj = json.loads(record[len("<!-- fortis-v1 "):-len(" -->")])
        obj["sequence"] = "bad_metadata"
        path.write_text("<!-- fortis-v1 " + json.dumps(obj) + " -->\n" + contents, encoding="utf-8")
        status, body = self.request("/api/state", token="owner-synthetic-token")
        self.assertEqual(status, 200)
        saved = json.loads(body)["sessions"][0]
        self.assertEqual((saved["events_count"], saved["invalid_files"]), (0, 1))

    def test_observer_completion_read_only_capability(self):
        body = {"url": "https://chatgpt.com/c/12345678-abcd",
                "route": "repo", "title": "Observer Test"}
        status, raw = self.request("/api/sessions", "POST", "owner-synthetic-token", body)
        self.assertEqual(status, 201)
        meta = json.loads(raw)["session"]
        sid = meta["reporting_session_id"]
        path = "/api/observer-status?session=" + sid
        self.assertEqual(self.request(path)[0], 403)
        self.assertEqual(self.request(path, headers={"X-Fortis-Observer-Key": "no"})[0], 403)
        self.assertEqual(self.request("/api/observer-pair?session=" + sid)[0], 401)
        status, raw = self.request("/api/observer-pair?session=" + sid, token="owner-synthetic-token")
        self.assertEqual(status, 200)
        pair = json.loads(raw)["pairing"]
        self.assertNotIn("owner-synthetic-token", raw)
        self.assertEqual(pair["conversation_id"], "12345678-abcd")
        status, raw = self.request(path, headers={"X-Fortis-Observer-Key": pair["observer_key"]})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["event"], "none")
        event0 = event(meta)
        event0["event"] = "started"
        stage(self.app.store.inboxes["repo"], event0)
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        event1 = event(meta, 1, "completed", "Завершена работа")
        stage(self.app.store.inboxes["repo"], event1)
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        status, raw = self.request(path, headers={"X-Fortis-Observer-Key": pair["observer_key"]})
        self.assertEqual(status, 200)
        response = json.loads(raw)
        self.assertEqual((response["sequence"], response["event"]), (1, "completed"))
        self.assertNotIn("summary", response)
        self.assertNotIn("events", response)
        self.assertNotIn("owner-synthetic-token", raw)
        next_event = event(meta, 2, "started", "Начата новая работа")
        stage(self.app.store.inboxes["repo"], next_event)
        self.app.store.poll()
        status, raw = self.request(path, headers={"X-Fortis-Observer-Key": pair["observer_key"]})
        self.assertEqual(json.loads(raw)["event"], "started")
        file_path = self.app.store._session_dir(sid) / "events"
        for file in file_path.glob("*.md"):
            if file.name.startswith("000002-"):
                file.unlink()
        status, raw = self.request(path, headers={"X-Fortis-Observer-Key": pair["observer_key"]})
        self.assertEqual(json.loads(raw)["event"], "completed")

    def test_task_activity_observer_only_metadata_and_negative_access(self):
        meta = self.app.store.register("https://chatgpt.com/c/12345678-abcd", "repo", "New Task")
        sid = meta["reporting_session_id"]
        task = "task_" + uuid.uuid4().hex
        url = "/api/task-activity?session=" + sid + "&task=" + task
        self.assertEqual(self.request(url)[0], 403)
        self.assertEqual(self.request(url, token="owner-synthetic-token")[0], 403)
        status, raw = self.request("/api/observer-pair?session=" + sid, token="owner-synthetic-token")
        self.assertEqual(status, 200)
        key = json.loads(raw)["pairing"]["observer_key"]
        headers = {"X-Fortis-Observer-Key": key}
        code, raw = self.request(url, headers=headers)
        self.assertEqual(code, 200)
        self.assertFalse(json.loads(raw)["found"])
        self.assertEqual(self.request(url, headers={"X-Fortis-Observer-Key": "invalid"})[0], 403)
        self.assertEqual(self.request(url + "-wrong", headers=headers)[0], 403)
        self.assertEqual(self.request(url, headers={**headers, "Host": "remote.invalid"})[0], 403)
        another = self.app.store.register("https://chatgpt.com/c/abcdefgh-1234", "repo", "Other Task")
        bad_session_url = "/api/task-activity?session=" + another["reporting_session_id"] + "&task=" + task
        self.assertEqual(self.request(bad_session_url, headers=headers)[0], 403)
        stage(self.app.store.inboxes["repo"], v2_event(meta, task, 0, "progress"))
        # Staged alone is not accepted.
        self.assertFalse(json.loads(self.request(url, headers=headers)[1])["found"])
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        status, raw = self.request(url, headers=headers)
        self.assertEqual(status, 200)
        response = json.loads(raw)
        self.assertEqual((response["event"], response["sequence"]), ("progress", 0))
        self.assertEqual(response["task_id"], task)
        self.assertNotIn("summary", response)
        self.assertNotIn("owner-synthetic-token", raw)
        self.assertNotIn("observer_key", raw)
        self.assertNotIn("text", raw)
        self.assertEqual(self.request(url, method="HEAD", headers=headers)[0], 401)

    def test_http_owner_writer_pair_and_private_message_post(self):
        meta = self.app.store.register("https://chatgpt.com/c/12345678-abcd", "repo", "Archive")
        sid = meta["reporting_session_id"]
        task = "task_" + uuid.uuid4().hex
        url = "/api/message-writer-pair?session=" + sid
        self.assertEqual(self.request(url)[0], 401)
        status, raw = self.request(url, token="owner-synthetic-token")
        self.assertEqual(status, 200)
        pair = json.loads(raw)["pairing"]
        ro = json.loads(self.request("/api/observer-pair?session=" + sid,
                                    token="owner-synthetic-token")[1])["pairing"]
        self.assertNotIn("message_writer_key", ro)
        self.assertNotEqual(pair["observer_key"], pair["message_writer_key"])
        body = {"reporting_session_id": sid, "conversation_id": meta["conversation_id"],
                "task_id": task, "original_text": "Секретный тест\nстрока 2"}
        path = "/api/user-messages"
        key = {"X-Fortis-Message-Writer-Key": pair["message_writer_key"]}
        self.assertEqual(self.request(path, "POST", body=body)[0], 403)
        self.assertEqual(self.request(path, "POST", token="owner-synthetic-token", body=body)[0], 403)
        self.assertEqual(self.request(path, "POST", body=body, headers={"X-Fortis-Message-Writer-Key": ro["observer_key"]})[0], 403)
        self.assertEqual(self.request(path, "POST", body=body, headers=key)[0], 409)
        stage(self.app.store.inboxes["repo"], v2_event(meta, task, 0, "assistant_message"))
        self.assertEqual(self.request(path, "POST", body=body, headers=key)[0], 409)
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        for special in ({"Origin": "https://evil.example"}, {"Sec-Fetch-Site": "cross-site"}, {"Host": "remote.invalid"}):
            self.assertEqual(self.request(path, "POST", body=body, headers={**key, **special})[0], 403)
        status, response = self.request(path, "POST", body=body, headers=key)
        self.assertEqual(status, 201)
        received = json.loads(response)
        self.assertTrue(received["archived"])
        self.assertEqual(received["status"], "created")
        self.assertNotIn("original_text", response)
        self.assertNotIn("Секретный", response)
        self.assertNotIn("message_writer_key", response)
        self.assertEqual(self.request(path, "POST", body=body, headers=key)[0], 200)
        self.assertEqual(self.request(path, "POST", body={**body, "original_text": "other"}, headers=key)[0], 409)

    def test_post_origin_and_instruction(self):
        content = {"url": "https://chatgpt.com/c/12345678-abcd", "route": "repo", "title": "Проект"}
        self.assertEqual(self.request("/api/sessions", "POST", body=content)[0], 401)
        self.assertEqual(self.request("/api/sessions", "POST", "owner-synthetic-token", content,
                                      {"Origin": "https://evil.example"})[0], 403)
        status, raw = self.request("/api/sessions", "POST", "owner-synthetic-token", content)
        self.assertEqual(status, 201)
        session = json.loads(raw)["session"]
        path = "/api/instructions?session=" + session["reporting_session_id"]
        status, body = self.request(path, token="owner-synthetic-token")
        self.assertEqual(status, 200)
        text = json.loads(body)["text"]
        self.assertIn("STAGED_ONLY", text)
        self.assertIn("BOOTSTRAP", text)
        self.assertIn("repo_task.py event", text)
        self.assertIn("repo_task.py message", text)
        self.assertNotIn(session["task_id"], text)
        self.assertNotIn(session["reporting_session_id"], text)
        for old in ("session_task_id", "session-task", "enrollment"):
            self.assertNotIn(old, text)
        self.assertLess(len(text), 3000)
        self.assertNotIn("owner-synthetic-token", text)
        self.assertEqual(self.request(path)[0], 401)


if __name__ == "__main__":
    unittest.main()
