"""No secrets printed; tests on temporary owner-private directories only."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from owner_enrollment import Enrollment

SID="rs_"+"a"*32
CID="abcdefgh-01234567"
SECRET_A="a"*64
SECRET_B="b"*64
FINGERPRINT_A=hashlib.sha256(bytes.fromhex(SECRET_A)).hexdigest()[:12]

class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.n=0
        def pair(sid):
            self.n+=1
            return {"version":1,"origin":"http://127.0.0.1:18755",
                    "conversation_id":CID,"reporting_session_id":SID,
                    "observer_key":"k"*48,"message_writer_key":"w"*48,
                    "dispatch_key":"d"*48}
        self.pair=pair
        self.clock=10
        self.valid=lambda sid,chat:sid==SID and chat==CID
        self.e=Enrollment(self.root,self.pair,clock=lambda:self.clock)

    def test_approval_one_time_and_reboot_reconnect_with_same_proof(self):
        pending=self.e.announce(SID,CID,SECRET_A,self.valid)
        self.assertEqual(pending,{"ok":True,"status":"awaiting_owner"})
        self.assertNotIn("pairing",pending)
        self.assertEqual(self.n,0)
        self.assertEqual(self.e.pending_for(SID)["pending"],
                         [{"fingerprint":FINGERPRINT_A,"chat":CID}])
        approved=self.e.approve(SID,CID,FINGERPRINT_A,self.valid)
        self.assertTrue(approved["approved"])
        self.assertNotIn(SECRET_A,(self.root/"approved-notifiers.json").read_text())
        self.assertEqual(self.n,0,"approval never returns a capability")
        self.assertEqual(self.e.announce(SID,CID,SECRET_A,self.valid)["status"],"approved")
        self.assertEqual(self.e.announce(SID,CID,SECRET_A,self.valid)["pairing"]["dispatch_key"],"d"*48)
        self.assertEqual(self.n,1,"pairing cached while Viewer runs")
        new=Enrollment(self.root,self.pair)
        self.assertTrue(new.pending_for(SID)["approved"])
        self.assertEqual(new.announce(SID,CID,SECRET_A,self.valid)["status"],"approved")
        self.assertEqual(new.announce(SID,CID,SECRET_A,self.valid)["pairing"]["observer_key"],"k"*48)
        self.assertEqual(self.n,2,"after reboot key is refreshed once")
        other=new.announce(SID,CID,SECRET_B,self.valid)
        self.assertEqual(other["status"],"already_approved_for_other_client")
        self.assertNotIn("pairing",other)

    def test_no_capability_for_url_only_or_wrong_proof_and_revocation(self):
        for sid,chat,proof in [(SID,"another-chat",SECRET_A),
                               ("invalid",CID,SECRET_A),(SID,CID,"short")]:
            with self.assertRaises(ValueError):
                self.e.announce(sid,chat,proof,self.valid)
        self.e.announce(SID,CID,SECRET_A,self.valid)
        with self.assertRaises(ValueError):
            self.e.approve(SID,CID,"000000000000",self.valid)
        self.e.approve(SID,CID,FINGERPRINT_A,self.valid)
        self.assertTrue(self.e.revoke(SID)["revoked"])
        self.assertFalse(Enrollment(self.root,self.pair).pending_for(SID)["approved"])
        self.assertEqual(self.e.announce(SID,CID,SECRET_A,self.valid)["status"],"awaiting_owner")
        self.assertFalse(self.e.revoke(SID)["revoked"])

    def test_race_multiple_claimants_never_auto_approve(self):
        self.e.announce(SID,CID,SECRET_A,self.valid)
        self.e.announce(SID,CID,SECRET_B,self.valid)
        info=self.e.pending_for(SID)
        self.assertEqual(len(info["pending"]),2)
        self.assertFalse(info["approved"])
        self.assertEqual(self.n,0)

    def test_pending_expiration_and_corrupt_storage_fail_closed(self):
        self.e.announce(SID,CID,SECRET_A,self.valid)
        self.clock+=181
        self.assertEqual(self.e.pending_for(SID)["pending"],[])
        with self.assertRaises(ValueError):
            self.e.approve(SID,CID,FINGERPRINT_A,self.valid)
        (self.root/"approved-notifiers.json").write_text('{"version":1,"grants":{"malicious":"x"}}')
        with self.assertRaises(ValueError):
            Enrollment(self.root,self.pair)



class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        EnrollmentTests.setUp(self)
        self.registered = False
        self.calls = []
        self.valid = lambda sid, chat: self.registered and sid == SID and chat == CID
        def register(url, title):
            self.calls.append((url, title))
            self.registered = True
            return {"ok": True, "created": True, "session": SID, "conversation_id": CID}
        self.register = register

    def test_presence_only_then_explicit_connect_and_durable_reconnect(self):
        self.assertEqual(self.e.discover(CID, SECRET_A)["status"], "not_registered")
        found = self.e.discovered_for_owner()
        self.assertEqual(found["chats"][0]["chat"], CID)
        self.assertEqual(found["chats"][0]["fingerprints"], [FINGERPRINT_A])
        self.assertNotIn(SECRET_A, json.dumps(found))
        self.assertFalse((self.root / "approved-notifiers.json").exists())
        self.assertEqual(self.n, 0)
        result = self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.assertTrue(result["approved"])
        self.assertFalse(result["task_intents"])
        self.assertEqual(self.calls, [("https://chatgpt.com/c/" + CID, "ChatGPT " + CID[:12])])
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])
        self.assertEqual(self.n, 0, "owner click does not return or fetch capability")
        self.assertNotIn(SECRET_A, (self.root / "approved-notifiers.json").read_text())
        self.assertEqual(Enrollment(self.root, self.pair).announce(SID, CID, SECRET_A, self.valid)["status"], "approved")

    def test_repeat_connect_is_idempotent_and_keeps_granted_scopes(self):
        self.e.discover(CID, SECRET_A)
        self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.e.enable_task_intents(SID, CID, self.valid)
        result = self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.assertFalse(result["created"])
        self.assertTrue(result["task_intents"])
        self.assertEqual(len(self.calls), 1)

    def test_ambiguous_or_wrong_or_expired_claimant_never_registers(self):
        self.e.discover(CID, SECRET_A)
        with self.assertRaises(ValueError):
            self.e.connect_discovered(CID, "0" * 12, self.register, self.valid)
        self.e.discover(CID, SECRET_B)
        with self.assertRaises(ValueError):
            self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.clock += 181
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])
        with self.assertRaises(ValueError):
            self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.assertEqual(self.calls, [])

    def test_heartbeat_extends_presence_without_registration(self):
        self.e.discover(CID, SECRET_A)
        self.clock += 150
        self.e.discover(CID, SECRET_A)
        self.clock += 150
        self.assertEqual(len(self.e.discovered_for_owner()["chats"]), 1)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.e.approved)

    def test_unauthenticated_discovery_has_a_fixed_memory_bound(self):
        from owner_enrollment import MAX_DISCOVERED
        for i in range(MAX_DISCOVERED + 10):
            self.e.discover("synthetic-chat-" + str(i), SECRET_A)
        self.assertEqual(len(self.e.discovered_for_owner()["chats"]), MAX_DISCOVERED)
        self.assertFalse(self.e.approved)
        self.assertEqual(self.calls, [])
        self.clock += 181
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])

    def test_unknown_weak_proof_and_bad_chat_not_advertised(self):
        for chat, proof in ((CID, "weak"), ("../unsafe", SECRET_A), (CID, None)):
            with self.assertRaises(ValueError):
                self.e.discover(chat, proof)
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])

    def test_existing_registered_unapproved_chat_also_discovered(self):
        self.registered = True
        self.e.announce(SID, CID, SECRET_A, self.valid)
        self.assertEqual(self.e.discovered_for_owner()["chats"][0]["chat"], CID)
        self.e.approve(SID, CID, FINGERPRINT_A, self.valid)
        self.e.announce(SID, CID, SECRET_A, self.valid)
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])

    def test_existing_other_client_grant_is_never_replaced(self):
        self.registered = True
        self.e.announce(SID, CID, SECRET_A, self.valid)
        self.e.approve(SID, CID, FINGERPRINT_A, self.valid)
        self.e.announce(SID, CID, SECRET_B, self.valid)
        self.assertTrue(self.e.discovered_for_owner()["chats"][0]["blocked"])
        fp = hashlib.sha256(bytes.fromhex(SECRET_B)).hexdigest()[:12]
        with self.assertRaises(ValueError):
            self.e.connect_discovered(CID, fp, self.register, self.valid)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.e.approved[SID]["sha256"][:12], FINGERPRINT_A)

    def test_registration_failure_keeps_candidate_for_explicit_retry(self):
        self.e.discover(CID, SECRET_A)
        def fail(url, title):
            raise OSError("synthetic temporary unavailable")
        with self.assertRaises(OSError):
            self.e.connect_discovered(CID, FINGERPRINT_A, fail, self.valid)
        self.assertEqual(len(self.e.discovered_for_owner()["chats"]), 1)
        self.assertFalse(self.e.approved)
        self.assertTrue(self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)["approved"])

    def test_mismatched_registration_never_grants(self):
        self.e.discover(CID, SECRET_A)
        def wrong(url, title):
            return {"ok": True, "created": True, "session": SID, "conversation_id": "another-chat"}
        with self.assertRaises(ValueError):
            self.e.connect_discovered(CID, FINGERPRINT_A, wrong, self.valid)
        self.assertFalse(self.e.approved)
        self.assertEqual(self.n, 0)


class TabTitleTests(unittest.TestCase):
    setUp = DiscoveryTests.setUp

    def test_titles_are_display_only_and_never_replace_the_registered_identity(self):
        name = "Проект 🧪 <b>Альфа</b>"
        self.e.discover(CID, SECRET_A, name)
        self.assertEqual(self.e.discovered_for_owner()["chats"][0]["title"], name)
        result = self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.assertEqual(result["session"], SID)
        self.assertEqual(self.e.discovered_for_owner()["session_titles"], {SID: name})
        self.assertEqual(self.calls[0][1], "ChatGPT " + CID[:12])
        self.assertNotIn(name, (self.root / "approved-notifiers.json").read_text())

    def test_only_approved_exact_proof_can_change_a_connected_session_caption(self):
        self.e.discover(CID, SECRET_A, "Первое имя")
        self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.e.announce(SID, CID, SECRET_A, self.valid, "Новое имя")
        self.assertEqual(self.e.discovered_for_owner()["session_titles"][SID], "Новое имя")
        self.e.discover(CID, SECRET_B, "Чужая подпись")
        self.assertEqual(self.e.discovered_for_owner()["session_titles"][SID], "Новое имя")
        self.assertTrue(self.e.discovered_for_owner()["chats"][0]["blocked"])

    def test_title_expires_on_restart_or_silence_without_revoking_pairing(self):
        self.e.discover(CID, SECRET_A, "Временное имя")
        self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.clock += 181
        self.assertEqual(self.e.discovered_for_owner()["session_titles"], {})
        self.assertTrue(self.e.pending_for(SID)["approved"])
        restarted = Enrollment(self.root, self.pair)
        self.assertEqual(restarted.discovered_for_owner()["session_titles"], {})
        self.assertTrue(restarted.pending_for(SID)["approved"])

    def test_invalid_title_never_enters_the_discovery_registry(self):
        for title in (123, "x" * 129, "bad\nname", "\u202ename", "\ud800"):
            with self.assertRaises((ValueError, UnicodeError)):
                self.e.discover(CID, SECRET_A, title)
        self.assertEqual(self.e.discovered_for_owner()["chats"], [])

    def test_ambiguous_titles_are_not_chosen_randomly_and_revoke_clears_caption(self):
        self.e.discover(CID, SECRET_A, "Имя А")
        self.e.discover(CID, SECRET_B, "Имя Б")
        self.assertEqual(self.e.discovered_for_owner()["chats"][0]["title"], "")
        self.e.discovered.pop((CID, hashlib.sha256(bytes.fromhex(SECRET_B)).hexdigest()))
        self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.e.revoke(SID)
        self.assertEqual(self.e.discovered_for_owner()["session_titles"], {})

    def test_legacy_client_without_title_still_connects(self):
        self.e.discover(CID, SECRET_A)
        self.assertEqual(self.e.discovered_for_owner()["chats"][0]["title"], "")
        self.e.connect_discovered(CID, FINGERPRINT_A, self.register, self.valid)
        self.assertEqual(self.e.discovered_for_owner()["session_titles"], {})

if __name__=="__main__":
    unittest.main()
