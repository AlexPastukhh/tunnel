"""Synthetic local HTTP bridge integration; never exposes Windows listener."""
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from browser_relay_dispatch import forward, validate
from owner_browser_relay import request_guard, docker_exec, owner_pairing_code, handler_for, WIN_PORT
from server import Application, handler_for as observatory_handler
from store import stage


class BrowserRelayContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fortis-relay-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        inbox = root / "inbox"
        inbox.mkdir()
        self.app = Application(root / "archive", {"repo": inbox},
                               token="synthetic_owner_token_never_output")
        self.meta = self.app.store.register(
            "https://chatgpt.com/c/12345678-abcd", "repo", "synthetic")
        self.task = "task_" + uuid.uuid4().hex
        self.key = self.app.store.observer_key(self.meta["reporting_session_id"])
        self.writer = self.app.store.message_writer_key(self.meta["reporting_session_id"])
        stage(inbox, {
            "version": 2, "event_id": uuid.uuid4().hex,
            "reporting_session_id": self.meta["reporting_session_id"],
            "session_task_id": self.meta["task_id"], "task_id": self.task,
            "sequence": 0, "route": "repo", "event": "progress",
            "stage": "other", "summary": "Синтетический сигнал"})
        self.assertEqual(self.app.store.poll()["accepted"], 1)
        self.backend = ThreadingHTTPServer(
            ("127.0.0.1", 0), observatory_handler(self.app))
        self.backend_thread = threading.Thread(target=self.backend.serve_forever, daemon=True)
        self.backend_thread.start()
        self.addCleanup(self.backend.server_close)
        self.addCleanup(self.backend.shutdown)
        self.addCleanup(lambda: self.backend_thread.join(timeout=2))
        upstream = f"http://127.0.0.1:{self.backend.server_port}"
        self.bridge = ThreadingHTTPServer(
            ("127.0.0.1", 0), handler_for(lambda envelope: forward(envelope, upstream=upstream)))
        self.bridge_thread = threading.Thread(target=self.bridge.serve_forever, daemon=True)
        self.bridge_thread.start()
        self.addCleanup(self.bridge.server_close)
        self.addCleanup(self.bridge.shutdown)
        self.addCleanup(lambda: self.bridge_thread.join(timeout=2))

    def call(self, path, key=None, post=None, headers=None, host=None):
        head = {"Host": host or f"127.0.0.1:{WIN_PORT}",
                "Origin": "https://chatgpt.com"}
        if key:
            head["X-Fortis-Message-Writer-Key" if post is not None
                 else "X-Fortis-Observer-Key"] = key
        data = json.dumps(post).encode() if post is not None else None
        if post is not None:
            head["Content-Type"] = "application/json"
        head.update(headers or {})
        req = Request(f"http://127.0.0.1:{self.bridge.server_port}" + path,
                      headers=head, data=data, method="POST" if post is not None else "GET")
        try:
            response = urlopen(req, timeout=3)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def test_valid_per_task_poll_and_original_write_roundtrip(self):
        sid = self.meta["reporting_session_id"]
        url = f"/api/task-activity?session={sid}&task={self.task}"
        status, response = self.call(url, key=self.key)
        self.assertEqual(status, 200)
        self.assertTrue(response["found"])
        self.assertEqual(response["task_id"], self.task)
        original = "  Синтетический точный оригинал 👋 <script>  "
        status, receipt = self.call("/api/user-messages", post={
            "reporting_session_id": sid,
            "conversation_id": self.meta["conversation_id"],
            "task_id": self.task, "original_text": original
        }, key=self.writer)
        self.assertEqual(status, 201)
        self.assertTrue(receipt["archived"])
        path = self.app.store._user_message_path(sid, self.task)
        self.assertEqual(self.app.store._read_user_message(path)[1], original)
        status, second = self.call("/api/user-messages", post={
            "reporting_session_id": sid, "conversation_id": self.meta["conversation_id"],
            "task_id": self.task, "original_text": original
        }, key=self.writer)
        self.assertEqual((status, second["status"]), (200, "existing"))
        self.assertEqual(self.call("/api/observer-status?session="+sid, key=self.key)[0], 200)

    def test_large_exact_original_via_owner_bridge(self):
        sid = self.meta["reporting_session_id"]
        original = ("Большой оригинал 🌍\\n" * 6700).rstrip()
        self.assertGreater(len(original.encode("utf-8")), 65536)
        self.assertLess(len(original.encode("utf-8")), 512 * 1024)
        status, receipt = self.call("/api/user-messages", post={
            "reporting_session_id": sid,
            "conversation_id": self.meta["conversation_id"],
            "task_id": self.task,
            "original_text": original,
        }, key=self.writer)
        self.assertEqual(status, 201)
        self.assertTrue(receipt["archived"])
        path = self.app.store._user_message_path(sid, self.task)
        self.assertEqual(self.app.store._read_user_message(path)[1], original)

    def test_refuse_owner_bearer_unpaired_wrong_origin_host_and_sensitive_routes(self):
        sid = self.meta["reporting_session_id"]
        task = self.task
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}")[0], 403)
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}",
                                   key=self.key, headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}",
                                   key=self.key, host="127.0.0.1:9999")[0], 403)
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}",
                                   key=self.key,
                                   headers={"Authorization": "Bearer synthetic_owner_token_never_output"})[0], 403)
        for path in ("/api/repo-history?session="+sid+"&task="+task,
                     "/api/state", "/api/observer-pair?session="+sid,
                     "/api/message-writer-pair?session="+sid,
                     "/api/sessions", "/"):
            self.assertEqual(self.call(path, key=self.key)[0], 403, path)
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}&extra=1",
                                   key=self.key)[0], 403)
        self.assertEqual(self.call(f"/api/task-activity?session={sid}&task={task}&task={task}",
                                   key=self.key)[0], 403)
        self.assertIsNone(request_guard("GET", "http://evil.example/api/task-activity",
                                        {"Host": f"127.0.0.1:{WIN_PORT}",
                                         "X-Fortis-Observer-Key": self.key}, None))

    def test_no_injected_shell_and_no_body_in_argv(self):
        sid = self.meta["reporting_session_id"]
        original = "unprinted synthetic source body"
        sent = {}
        def fake_runner(command, input, **kwargs):
            sent["argv"] = command
            sent["payload"] = json.loads(input.decode("ascii"))
            return subprocess.CompletedProcess(command, 0, stdout=b'{"status":403,"body":{"ok":false}}')
        payload = request_guard("POST", "/api/user-messages", {
            "Host":f"127.0.0.1:{WIN_PORT}",
            "X-Fortis-Message-Writer-Key":self.writer,
            "Content-Type":"application/json"}, json.dumps({
                "reporting_session_id":sid, "conversation_id":self.meta["conversation_id"],
                "task_id":self.task,"original_text":original
            }).encode())
        self.assertIsNotNone(payload)
        outcome = docker_exec("approved-test-container", payload, "docker.exe", fake_runner)
        self.assertEqual(outcome["status"],403)
        self.assertEqual(sent["argv"][:4],["docker.exe","exec","-i","approved-test-container"])
        self.assertNotIn(original, " ".join(sent["argv"]))
        self.assertNotIn(self.writer, " ".join(sent["argv"]))
        self.assertIn(original, sent["payload"]["body"]["original_text"])

    def test_pairing_code_is_owner_console_only_and_never_an_http_route(self):
        sid = self.meta["reporting_session_id"]
        key = self.key
        writer = self.writer
        captured = []
        def fake_runner(argv, **kwargs):
            captured.append((argv, kwargs))
            full = "--writer" in argv
            obj = {"version": 1, "origin": "http://127.0.0.1:18754",
                   "conversation_id": self.meta["conversation_id"],
                   "reporting_session_id": sid, "observer_key": key}
            if full:
                obj["message_writer_key"] = writer
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(obj).encode("ascii"))
        minimal = owner_pairing_code("reviewed-container", sid, False, runner=fake_runner)
        self.assertNotIn("message_writer_key", minimal)
        full = owner_pairing_code("reviewed-container", sid, True, runner=fake_runner)
        self.assertEqual(full["message_writer_key"], writer)
        for args, kwargs in captured:
            self.assertEqual(args[0:3], ["docker.exe", "exec", "reviewed-container"])
            self.assertNotIn(key, " ".join(args))
            self.assertNotIn(writer, " ".join(args))
            self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(self.call("/api/message-writer-pair?session=" + sid, key=key)[0], 403)
        self.assertEqual(self.call("/api/observer-pair?session=" + sid, key=key)[0], 403)
        with self.assertRaises(ValueError):
            owner_pairing_code("--evil", sid, True, runner=fake_runner)
        with self.assertRaises(ValueError):
            owner_pairing_code("reviewed-container", "rs_invalid", True, runner=fake_runner)

    def test_guest_headers_and_http_preflight_never_gain_access(self):
        sid = self.meta["reporting_session_id"]
        path = f"/api/task-activity?session={sid}&task={self.task}"
        self.assertEqual(self.call(path, key=self.key, headers={"Origin": "https://evil.example"})[0], 403)
        # Without Origin, valid holder of a scoped key may be an authorized GM_XHR.
        # Keyless guests remain denied; this is not an ACL test.
        self.assertEqual(self.call(path, headers={"Origin": ""})[0], 403)
        req = Request(f"http://127.0.0.1:{self.bridge.server_port}/api/task-activity",
                      method="OPTIONS",
                      headers={"Host": f"127.0.0.1:{WIN_PORT}",
                               "Origin": "https://evil.example"})
        try:
            with urlopen(req, timeout=3) as response:
                self.fail("OPTIONS unexpectedly allowed")
        except HTTPError as error:
            self.assertEqual(error.code, 405)
            self.assertIsNone(error.headers.get("Access-Control-Allow-Origin"))
        # Read-only API cannot enumerate full history, even with a valid observer.
        status, payload = self.call("/api/repo-history?session=" + sid + "&task=" + self.task,
                                    key=self.key)
        self.assertEqual(status, 403)
        self.assertNotIn("original_text", payload)

    def test_oversize_and_invalid_envelope_denied(self):
        sid=self.meta["reporting_session_id"]
        uri=f"/api/task-activity?session={sid}&task={self.task}"
        self.assertIsNone(request_guard("GET",uri,{"Host":f"127.0.0.1:{WIN_PORT}"},None))
        self.assertIsNone(request_guard("POST","/api/user-messages",{
            "Host":f"127.0.0.1:{WIN_PORT}", "X-Fortis-Message-Writer-Key":self.writer,
            "Content-Type":"application/json"},b"{" + b"A"*131073 + b"}"))
        with self.assertRaises(ValueError):
            validate({"method":"GET","path":"/api/state","key":self.key,"body":None})
        self.assertEqual(forward({"method":"GET","path":"/api/state","key":self.key,"body":None})["status"],403)


if __name__ == "__main__":
    unittest.main()
