"""Synthetic localhost discovery/one-click connection; no live owner grants."""
import hashlib
from http.server import ThreadingHTTPServer
import tempfile
import threading
import unittest

from owner_enrollment import Enrollment
from owner_viewer import handler_for, WIN_PORT
import test_owner_auto_pair_http as enrollment_http_tests

CID = "unregistered-chat-12345678"
SID = "rs_" + "d" * 32
PROOF = "e" * 64
FP = hashlib.sha256(bytes.fromhex(PROOF)).hexdigest()[:12]
OWNER_ORIGIN = f"http://127.0.0.1:{WIN_PORT}"


class DiscoveryHTTPTests(unittest.TestCase):
    req = enrollment_http_tests.HTTPEnrollmentTests.req

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = 1
        self.sessions = []
        self.register_calls = []
        self.pair_calls = 0
        self.offline = False
        def pair(sid):
            self.pair_calls += 1
            return {"version": 1, "origin": OWNER_ORIGIN, "conversation_id": CID,
                    "reporting_session_id": sid, "observer_key": "o" * 48}
        self.enrollment = Enrollment(self.tmp.name, pair, clock=lambda: self.clock)
        def read(kind, sid, task):
            if self.offline:
                raise OSError("synthetic offline Repo")
            return {"ok": True, "sessions": list(self.sessions)}
        def register(url, title):
            self.register_calls.append((url, title))
            created = not self.sessions
            if created:
                self.sessions.append({"conversation_id": CID, "reporting_session_id": SID,
                                      "route": "repo", "title": title})
            return {"ok": True, "created": created, "session": SID, "conversation_id": CID}
        self.bearer = "synthetic_owner_bearer"
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0),
            handler_for(self.bearer, read, "nonce", register, enrollment=self.enrollment))
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(lambda: self.thread.join(timeout=2))
        self.addCleanup(self.srv.shutdown)

    def announce(self, proof=PROOF):
        return self.req("/api/notifier/enroll", {"chat": CID, "proof": proof},
                        origin="https://chatgpt.com")

    def connect(self, **kwargs):
        return self.req("/api/notifier/connect", {"chat": CID, "fingerprint": FP},
                        **kwargs)

    def test_unknown_chat_discovered_without_registration_then_owner_click(self):
        self.assertEqual(self.announce()[1]["status"], "not_registered")
        self.assertFalse(self.sessions)
        self.assertFalse(self.register_calls)
        self.assertEqual(self.req("/api/notifier/discovered")[0], 401)
        code, discovered = self.req("/api/notifier/discovered", auth=True)
        self.assertEqual(code, 200)
        self.assertEqual(discovered["chats"][0]["chat"], CID)
        self.assertNotIn(PROOF, str(discovered))
        self.assertEqual(self.pair_calls, 0)
        code, result = self.connect(auth=True, origin=OWNER_ORIGIN)
        self.assertEqual(code, 201)
        self.assertTrue(result["approved"])
        self.assertFalse(result["task_intents"])
        self.assertEqual(self.register_calls[0][0], "https://chatgpt.com/c/" + CID)
        self.assertEqual(self.pair_calls, 0, "no capability in connect response")
        self.assertEqual(self.req("/api/notifier/discovered", auth=True)[1]["chats"], [])
        code, repeated = self.connect(auth=True, origin=OWNER_ORIGIN)
        self.assertEqual(code, 200)
        self.assertFalse(repeated["created"])
        self.assertEqual(len(self.register_calls), 1)
        self.assertEqual(self.announce()[1]["status"], "approved")
        self.assertEqual(self.pair_calls, 1)

    def test_owner_token_origin_and_exact_fields_required(self):
        self.announce()
        self.assertEqual(self.connect(origin=OWNER_ORIGIN)[0], 401)
        self.assertEqual(self.connect(auth=True, origin="https://chatgpt.com")[0], 403)
        self.assertEqual(self.connect(auth=True, origin="https://evil.example")[0], 403)
        self.assertEqual(self.req("/api/notifier/connect",
            {"chat": CID, "fingerprint": FP, "session": SID},
            auth=True, origin=OWNER_ORIGIN)[0], 403)
        self.assertEqual(self.req("/api/notifier/discovered", auth=True,
            origin="https://evil.example")[0], 403)
        self.assertFalse(self.register_calls)
        self.assertEqual(self.pair_calls, 0)

    def test_expired_wrong_and_ambiguous_claims_do_not_register(self):
        self.announce()
        self.assertEqual(self.req("/api/notifier/connect",
            {"chat": CID, "fingerprint": "0" * 12}, auth=True, origin=OWNER_ORIGIN)[0], 403)
        self.announce("f" * 64)
        self.assertEqual(self.connect(auth=True, origin=OWNER_ORIGIN)[0], 403)
        self.clock += 181
        self.assertEqual(self.connect(auth=True, origin=OWNER_ORIGIN)[0], 403)
        self.assertFalse(self.register_calls)
        self.assertFalse(self.enrollment.approved)

    def test_invalid_unknown_proof_not_retained_and_no_capability(self):
        self.assertEqual(self.announce("weak")[0], 403)
        self.assertEqual(self.req("/api/notifier/discovered", auth=True)[1]["chats"], [])
        self.assertEqual(self.pair_calls, 0)

    def test_offline_repo_does_not_prevent_local_discovery(self):
        self.offline = True
        code, result = self.announce()
        self.assertEqual(code, 200)
        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(self.req("/api/notifier/discovered", auth=True)[1]["chats"][0]["chat"], CID)
        self.assertEqual(self.connect(auth=True, origin=OWNER_ORIGIN)[0], 503)
        self.assertFalse(self.enrollment.approved)
        self.offline = False
        # Registration may have succeeded before validation became unavailable.
        # Retry reuses the registered session and completes only the approval.
        self.assertEqual(self.connect(auth=True, origin=OWNER_ORIGIN)[0], 200)
        self.assertEqual(len(self.sessions), 1)


    def test_title_feature_is_optional_and_display_stays_owner_only(self):
        name = "Проект 🧪 — Альфа"
        code, info = self.req("/api/notifier/enroll", {"chat": CID, "proof": PROOF, "title": name},
                              origin="https://chatgpt.com")
        self.assertEqual(code, 200)
        self.assertTrue(info["supports_tab_titles"])
        self.assertNotIn(name, str(info))
        self.assertEqual(self.req("/api/notifier/discovered")[0], 401)
        self.assertEqual(self.req("/api/notifier/discovered", auth=True)[1]["chats"][0]["title"], name)
        self.connect(auth=True, origin=OWNER_ORIGIN)
        self.assertEqual(self.req("/api/notifier/discovered", auth=True)[1]["session_titles"][SID], name)
        self.assertNotEqual(self.sessions[0]["title"], name)
        self.assertEqual(self.pair_calls, 0)

    def test_invalid_title_or_extra_field_never_grants_and_legacy_probe_advertises(self):
        code, info = self.announce()
        self.assertEqual(code, 200)
        self.assertTrue(info["supports_tab_titles"])
        for title in ({"body": "not a title"}, "x" * 129, "bad\nname"):
            self.assertEqual(self.req("/api/notifier/enroll",
                {"chat": CID, "proof": PROOF, "title": title}, origin="https://chatgpt.com")[0], 403)
        self.assertFalse(self.enrollment.approved)
        self.assertEqual(self.pair_calls, 0)


if __name__ == "__main__":
    unittest.main()
