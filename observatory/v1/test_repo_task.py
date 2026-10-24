"""One-shot per-message sender tests: Docker archive owns enrollment, not chat memory."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
import json

from server import Application
from store import Store, MESSAGE_SUMMARIES
from repo_messages import _check_message


class RepoTaskLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fortis-current-context-", dir="/workspace/repo")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.events = self.root / "inbox" / "repo"
        self.messages = self.root / "inbox" / "messages"
        self.events.mkdir(parents=True)
        self.messages.mkdir(parents=True)
        self.store = Store(self.root / "archive", {"repo": self.events})
        self.chat = "synthetic-12345678"
        self.session = self.store.register(
            "https://chatgpt.com/c/" + self.chat, "repo", "Synthetic Context")["reporting_session_id"]
        self.enrollment = self.store._session(self.session)["task_id"]
        self.task = "task_" + uuid.uuid4().hex

    def send(self, kind, *extra, body=None, chat=None, sid=None, task=None):
        cmd = [sys.executable, "repo_task.py", "--state-dir", str(self.root), kind,
               "--session", self.session if sid is None else sid,
               "--chat-id", self.chat if chat is None else chat,
               "--task", self.task if task is None else task, *extra]
        return subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=7)

    def test_sender_recovers_registered_enrollment_without_browser_memory_offline(self):
        event = self.send("event", "--event", "user_message",
                          "--stage", "other", "--summary", MESSAGE_SUMMARIES["user_message"])
        self.assertEqual(event.returncode, 0, event.stdout + event.stderr)
        self.assertIn("STAGED_ONLY", event.stdout)
        staged = list(self.events.glob("*.json"))
        self.assertEqual(len(staged),1)
        payload = json.loads(staged[0].read_text())
        self.assertEqual(payload["session_task_id"],self.enrollment)
        self.assertEqual(payload["task_id"],self.task)
        self.assertEqual(payload["version"],2)

        full_text="Отвечаю через Fortis Repo.\nПриватное сообщение 🧪"
        message=self.send("message","--kind","final",body=full_text)
        self.assertEqual(message.returncode,0,message.stdout+message.stderr)
        file=list(self.messages.glob("*.json"))
        self.assertEqual(len(file),1)
        obj = _check_message(json.loads(file[0].read_text()))
        self.assertEqual(obj["session_task_id"],self.enrollment)
        self.assertEqual(obj["task_id"],self.task)
        self.assertEqual(obj["body"],full_text)
        self.assertNotIn(full_text,message.stdout)
        self.assertNotIn(self.enrollment,message.stdout)
        self.assertIn("COMPLETION_STAGED_ONLY", message.stdout)
        completed = [json.loads(p.read_text()) for p in self.events.glob("*.json")
                     if json.loads(p.read_text()).get("event") == "completed"]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["task_id"], self.task)
        self.assertEqual(completed[0]["reporting_session_id"], self.session)
        self.assertEqual(completed[0]["session_task_id"], self.enrollment)
        self.assertEqual(completed[0]["event_id"],
                         json.loads(file[0].read_text())["message_id"][4:])
        # Identical final retries produce the same completion-event identity.
        replay = self.send("message", "--kind", "final", "--message-id",
                           obj["message_id"], body=full_text)
        self.assertEqual(replay.returncode, 0)
        duplicates = [json.loads(p.read_text()) for p in self.events.glob("*.json")
                      if json.loads(p.read_text()).get("event") == "completed"]
        self.assertEqual(len(duplicates), 2)
        self.assertEqual(duplicates[0]["event_id"], duplicates[1]["event_id"])

    def test_interim_never_auto_marks_completed(self):
        result = self.send("message", "--kind", "interim", body="Промежуточный ответ")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("COMPLETION_STAGED_ONLY", result.stdout)
        self.assertEqual(list(self.events.glob("*.json")), [])

    def test_wrong_session_chat_or_task_refuses_staging(self):
        for args in (
            {"chat":"different-chat-000"},
            {"sid":"rs_"+"a"*32},
            {"task":"task_invalid"},
        ):
            self.assertNotEqual(self.send("event","--event","progress",
                "--stage","testing","--summary","Проверяю контекст",**args).returncode,0)
            self.assertNotEqual(self.send("message","--kind","final",body="Hello",**args).returncode,0)
        self.assertEqual(list(self.events.glob("*.json")),[])
        self.assertEqual(list(self.messages.glob("*.json")),[])

    def test_bootstrap_cli_without_session_or_running_http(self):
        result=subprocess.run([sys.executable,"repo_service.py","bootstrap"],
                              capture_output=True,text=True,timeout=7)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("repo_task.py",result.stdout)
        self.assertNotIn(self.session,result.stdout)
        self.assertNotIn(self.enrollment,result.stdout)
        self.assertNotIn(self.chat,result.stdout)
        for forbidden in ("session_task_id", "session-task", "enrollment", "Session enrollment"):
            self.assertNotIn(forbidden,result.stdout)

    def test_repo_bootstrap_is_static_no_persistent_session_ids(self):
        app=Application(self.root / "archive", {"repo":self.events},
                        {"repo":str(self.events)})
        app.repo_messages=object()
        prompt=app.instructions(self.session)
        self.assertIn("BOOTSTRAP",prompt)
        self.assertIn("repo_task.py event",prompt)
        self.assertIn("repo_task.py message",prompt)
        self.assertIn("Fortis Repo",prompt)
        self.assertNotIn(self.session,prompt)
        self.assertNotIn(self.enrollment,prompt)
        self.assertNotIn(self.chat,prompt)
        for forbidden in ("session_task_id", "session-task", "enrollment", "Session enrollment"):
            self.assertNotIn(forbidden,prompt)
        self.assertNotIn("Ранее принятый архив предлагает номер",prompt)
        self.assertLess(len(prompt),3000)
        self.assertIn("Не проверяй HTTP", prompt)
        self.assertIn("опусти --session", prompt)
