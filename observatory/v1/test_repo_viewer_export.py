"""No live user text. Source-level viewer task listing from synthetic archive."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repo_viewer_export import session_tasks, read_only


class TasksFromArchive(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.sid="rs_"+"a"*32
        self.from_event="task_"+"b"*32
        self.from_message="task_"+"c"*32
        self.from_original="task_"+"d"*32
        self.folder=self.root/"archive"/"sessions"/self.sid
        (self.folder/"assistant_messages").mkdir(parents=True)
        (self.folder/"user_messages").mkdir()
        self.state={"ok":True,"sessions":[{
            "reporting_session_id":self.sid,"route":"repo",
            "events":[{"task_id":self.from_event,"event":"progress"}]}]}

    def test_list_ai_only_task_original_only_task_and_event(self):
        ai=self.folder/"assistant_messages"/("msg_"+"e"*32+".md")
        meta={"version":1,"task_id":self.from_message,
              "reporting_session_id":self.sid}
        ai.write_text("<!-- fortis-repo-message "+
                      json.dumps(meta,ensure_ascii=True,separators=(",",":"))+
                      " -->\n# ASSISTANT MESSAGE\n",encoding="ascii")
        from store import META_PREFIX
        original = "  Настоящий оригинал\n\n  🧪\n"
        meta = {"type":"user_message","version":1,
                "reporting_session_id":self.sid,"task_id":self.from_original,
                "conversation_id":"chat-12345678",
                "sha256":hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "first_activity_at":1735000000,"archived_at":"2024-12-24T00:10:00+00:00",
                "provenance":"notifier_original"}
        blob = (META_PREFIX + json.dumps(meta,ensure_ascii=True,separators=(",",":")) +
                " -->\n# USER MESSAGE\n\n~~~json\n" +
                json.dumps({"original_text":original},ensure_ascii=True,separators=(",",":")) +
                "\n~~~\n")
        (self.folder/"user_messages"/(self.from_original+".md")).write_text(
            blob,encoding="utf-8")
        result=session_tasks(self.sid,self.state,self.root)
        self.assertEqual(result["task_ids"][0],self.from_original)
        self.assertEqual(set(result["task_ids"]),{
            self.from_event,self.from_message,self.from_original})
        self.assertTrue(result["ok"])
        cards={task["task_id"]:task for task in result["tasks"]}
        self.assertEqual(cards[self.from_original]["original_preview"],"Настоящий оригинал 🧪")
        self.assertTrue(cards[self.from_original]["original_received"])
        self.assertEqual(cards[self.from_event]["original_preview"],None)
        self.assertFalse(cards[self.from_event]["original_received"])
        self.assertEqual(cards[self.from_original]["first_seen_at"],"2024-12-24T00:26:40+00:00")

    def test_foreign_and_missing_session_rejected(self):
        with self.assertRaises(ValueError):
            session_tasks("rs_"+"f"*32,self.state,self.root)
        with self.assertRaises(ValueError):
            session_tasks("bad",self.state,self.root)

    def test_symlink_unsafe_archive_rejected(self):
        alias=self.folder/"assistant_messages"/("msg_"+"e"*32+".md")
        alias.symlink_to(self.root/"external")
        result=session_tasks(self.sid,self.state,self.root)
        self.assertNotIn(self.from_message,result["task_ids"])
        (self.folder/"user_messages").rmdir()
        (self.folder/"user_messages").symlink_to(self.root)
        with self.assertRaises(ValueError):
            session_tasks(self.sid,self.state,self.root)

    def test_no_state_sensitive_content_exposed(self):
        with patch("repo_viewer_export.api_call",return_value=self.state):
            with patch("repo_viewer_export.session_tasks",return_value={
                "ok":True,"session":self.sid,
                "task_ids":[self.from_event],"truncated":False
            }) as task_list:
                result=read_only("tasks",self.sid)
                self.assertEqual(result["task_ids"],[self.from_event])
                task_list.assert_called_once_with(self.sid,self.state)
        with self.assertRaises(ValueError):
            read_only("tasks","bad")
        with self.assertRaises(ValueError):
            read_only("history","bad","bad")


if __name__=="__main__":
    unittest.main()
