import json
from pathlib import Path
import tempfile
import unittest
import uuid

import task_progress as t


def event(task="task-a", sequence=0, kind="started", stage="planning"):
    return {"schema_version": 1, "event_id": str(uuid.uuid4()),
            "task_id": task, "sequence": sequence, "event": kind,
            "stage": stage, "route": "repo", "title": "Fortis task",
            "summary": "Checking source"}


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "safe.sqlite3"
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()

    def test_started_progress_completed_and_duplicate(self):
        for i, name in enumerate(("started", "progress", "completed")):
            obj = event(sequence=i, kind=name)
            self.assertTrue(t.accept(self.db, obj, 100 + i))
            self.assertFalse(t.accept(self.db, obj, 100 + i))
        result = t.tasks(self.db, 120)["tasks"][0]
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["events_count"], 3)

    def test_out_of_order_and_missing_start(self):
        t.accept(self.db, event(sequence=2, kind="completed"), 100)
        t.accept(self.db, event(sequence=0), 101)
        t.accept(self.db, event(sequence=1, kind="progress"), 102)
        self.assertEqual(t.tasks(self.db, 130)["tasks"][0]["state"], "COMPLETED")
        t.accept(self.db, event("orphan", 4, "progress"), 200)
        self.assertEqual(t.tasks(self.db, 230)["tasks"][0]["state"], "UNKNOWN")

    def test_silence_and_recovery(self):
        t.accept(self.db, event(), 100)
        self.assertEqual(t.tasks(self.db, 101)["tasks"][0]["state"], "WORKING")
        self.assertEqual(t.tasks(self.db, 1000)["tasks"][0]["state"], "SILENT")
        self.assertEqual(t.tasks(self.db, 4000)["tasks"][0]["state"], "UNKNOWN")
        t.accept(self.db, event(sequence=1, kind="progress"), 4001)
        self.assertEqual(t.tasks(self.db, 4002)["tasks"][0]["state"], "WORKING")

    def test_blocked_and_failed(self):
        t.accept(self.db, event("a", 0, "blocked"), 100)
        t.accept(self.db, event("b", 0, "failed"), 100)
        self.assertEqual({row["state"] for row in t.tasks(self.db, 100)["tasks"]},
                         {"BLOCKED", "FAILED"})

    def test_parallel_tasks_and_idempotent_spool(self):
        for name in ("a", "b"):
            obj = event(name)
            t.queue(self.inbox, obj)
            t.queue(self.inbox, obj)
        batch = t.ingest(self.db, self.inbox)
        self.assertEqual((batch["added"], batch["duplicate"]), (2, 2))
        self.assertEqual(len(t.tasks(self.db)["tasks"]), 2)

    def test_reject_sensitive_fields_and_symlink(self):
        for summary in ("Bearer abc", "C:\\Users\\owner", "https://site", "/home/owner"):
            item = event()
            item["summary"] = summary
            with self.assertRaises(ValueError):
                t.validate(item)
        item = event()
        item["content"] = "private"
        with self.assertRaises(ValueError):
            t.validate(item)
        invalid = self.inbox / (uuid.uuid4().hex + ".json")
        invalid.symlink_to(self.db)
        self.assertEqual(t.ingest(self.db, self.inbox)["rejected"], 1)

    def test_oversize_and_capacity(self):
        name = self.inbox / (uuid.uuid4().hex + ".json")
        name.write_bytes(b"x" * (t.MAX_BYTES + 1))
        self.assertEqual(t.ingest(self.db, self.inbox)["rejected"], 1)
        with self.assertRaises(ValueError):
            t.validate({"schema_version": 1})

    def test_restart_and_retention(self):
        t.accept(self.db, event(), 100)
        self.assertEqual(t.tasks(self.db, 101)["tasks"][0]["state"], "WORKING")
        t.prune(self.db, 100 + 31 * 86400)
        self.assertEqual(t.tasks(self.db)["tasks"], [])


if __name__ == "__main__":
    unittest.main()
