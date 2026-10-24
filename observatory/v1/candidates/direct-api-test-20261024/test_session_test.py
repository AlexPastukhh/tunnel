import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("session_test", Path(__file__).with_name("Run-ObservatorySessionTest.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SID = "rs_" + "a" * 32
CHAT = "6ad00000-1111-2222-3333-444444444444"
DID = "dispatch_" + "b" * 32


class FakeApi:
    def __init__(self, connected=False):
        self.connected = connected
        self.posts = []
        self.dispatch = None
        self.lost_send_reply = False
        self.archived = False
        self.ambiguous_title = False
        self.ambiguous_client = False

    def __call__(self, method, path, body=None):
        if method == "POST":
            self.posts.append((path, body))
            if path == "/api/notifier/connect":
                self.connected = True
                return {"ok": True, "session": SID, "approved": True, "conversation_id": CHAT}
            if path == "/api/dispatch":
                self.dispatch = {"dispatch_id": DID, "status": "send_initiated", "task_id": "task_" + "c" * 32}
                if self.lost_send_reply:
                    raise module.ApiError("connection")
                return {"ok": True, "dispatch_id": DID, "status": "pending"}
        if path == "/api/state":
            rows = [{"reporting_session_id": SID, "conversation_id": CHAT,
                     "title": "technical name", "route": "repo"}] if self.connected else []
            return {"ok": True, "sessions": rows}
        if path == "/api/notifier/discovered":
            rows = [] if self.connected else [{"title": module.TARGET, "chat": CHAT,
                    "fingerprints": ["1" * 12, "2" * 12] if self.ambiguous_client else ["1" * 12],
                    "blocked": False}]
            if self.ambiguous_title:
                rows.append({"title": module.TARGET, "chat": "another-chat-id",
                             "fingerprints": ["2" * 12], "blocked": False})
            return {"ok": True, "chats": rows,
                    "session_titles": {SID: module.TARGET} if self.connected else {}}
        if path == "/api/session-visibility":
            return {"ok": True, "archived": {SID: CHAT} if self.archived else {}}
        if path.startswith("/api/dispatch/status"):
            return {"ok": True, "available": True, "dispatch": self.dispatch}
        raise AssertionError((method, path))

    def send_count(self):
        return len([p for p, body in self.posts if p == "/api/dispatch"])


class FlowTests(unittest.TestCase):
    def invoke(self, api, directory):
        with contextlib.redirect_stdout(io.StringIO()):
            return module.run(api, Path(directory), lambda p: None, sleep=lambda n: None)


    def test_check_cli_never_connects_sends_or_creates_a_journal(self):
        from unittest.mock import patch
        api = FakeApi()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(module, "authenticate", return_value=(api, Path(directory), lambda p: None)):
                with patch.object(module.sys, "argv", ["helper.py", "--check"]):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(module.main(), 0)
            self.assertEqual(api.posts, [])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_unknown_cli_argument_never_authenticates_or_sends(self):
        from unittest.mock import patch
        with patch.object(module, "authenticate") as authenticate:
            with patch.object(module.sys, "argv", ["helper.py", "--typo"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(), 1)
            authenticate.assert_not_called()


    def test_check_prints_whitelisted_candidate_metadata_before_a_name_mismatch(self):
        api = FakeApi()
        def unusual_title_api(method, path, body=None):
            data = api(method, path, body)
            if path == "/api/notifier/discovered":
                data["chats"][0]["title"] = "Тест связи\u200b"
                data["chats"][0]["private_key"] = "SHOULD_NOT_BE_PRINTED"
            return data
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(module.StopTest):
                module.check_only(unusual_title_api)
        text = output.getvalue()
        self.assertIn("DISCOVERED_COUNT=1", text)
        self.assertIn(CHAT, text)
        self.assertIn("u200b", text)
        self.assertNotIn("SHOULD_NOT_BE_PRINTED", text)
        self.assertEqual(api.posts, [])

    def test_connect_then_one_send_and_resume_without_resending(self):
        api = FakeApi()
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.invoke(api, directory), 0)
            self.assertEqual(self.invoke(api, directory), 0)
            self.assertEqual(api.send_count(), 1)
            self.assertEqual(api.posts[0][0], "/api/notifier/connect")
            sent = [b for p, b in api.posts if p == "/api/dispatch"][0]
            self.assertEqual(sent, {"session": SID, "chat": CHAT, "mode": "send", "text": "Тест"})

    def test_connected_session_does_not_get_reconnected(self):
        api = FakeApi(connected=True)
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.invoke(api, directory), 0)
            self.assertEqual([p for p, b in api.posts], ["/api/dispatch"])

    def test_ambiguous_titles_never_mutate(self):
        api = FakeApi()
        api.ambiguous_title = True
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(module.StopTest):
                self.invoke(api, directory)
            self.assertEqual(api.posts, [])

    def test_ambiguous_clients_never_mutate(self):
        api = FakeApi()
        api.ambiguous_client = True
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(module.StopTest):
                self.invoke(api, directory)
            self.assertEqual(api.posts, [])

    def test_archived_session_never_mutates(self):
        api = FakeApi(connected=True)
        api.archived = True
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(module.StopTest):
                self.invoke(api, directory)
            self.assertEqual(api.posts, [])

    def test_lost_post_reply_never_resends(self):
        api = FakeApi(connected=True)
        api.lost_send_reply = True
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(module.ApiError):
                self.invoke(api, directory)
            with self.assertRaises(module.StopTest):
                self.invoke(api, directory)
            self.assertEqual(api.send_count(), 1)
            record = json.loads(next(Path(directory).glob("direct-api-test-*.json")).read_text())
            self.assertEqual(record["status"], "request_may_start")

    def test_other_inflight_command_blocks_send(self):
        api = FakeApi(connected=True)
        api.dispatch = {"dispatch_id": "dispatch_" + "d" * 32, "status": "claimed"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(module.StopTest):
                self.invoke(api, directory)
            self.assertEqual(api.posts, [])


if __name__ == "__main__":
    unittest.main()
