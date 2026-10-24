"""Synthetic owner-local dispatch, no browser access and no actual send."""
import unittest
from concurrent.futures import ThreadPoolExecutor

from owner_dispatch import DispatchBoard, MAX_TEXT_BYTES

SID = "rs_" + "a"*32
CHAT = "abcdefgh-01234567"
TASK = "task_" + "b"*32


class DispatchBoardTests(unittest.TestCase):
    def setUp(self):
        self.clock = 100.0
        self.board = DispatchBoard(clock=lambda: self.clock)
        self.key = self.board.pair(SID, CHAT)

    def test_pairing_status_distinguishes_code_from_verified_heartbeat(self):
        board = DispatchBoard(clock=lambda: self.clock)
        missing = board.status(SID)
        self.assertFalse(missing["paired"])
        self.assertFalse(missing["available"])
        self.assertFalse(missing["ever_seen"])
        self.assertIsNone(missing["last_seen_seconds_ago"])
        key = board.pair(SID, CHAT)
        issued = board.status(SID)
        self.assertTrue(issued["paired"])
        self.assertFalse(issued["available"])
        self.assertFalse(issued["ever_seen"])
        self.assertIsNone(issued["last_seen_seconds_ago"])
        with self.assertRaises(PermissionError):
            board.poll(SID, CHAT, "invalid-key")
        self.assertFalse(board.status(SID)["ever_seen"])
        board.poll(SID, CHAT, key)
        self.assertTrue(board.status(SID)["available"])
        self.assertEqual(board.status(SID)["last_seen_seconds_ago"], 0)
        self.clock += 16
        stale = board.status(SID)
        self.assertTrue(stale["paired"])
        self.assertTrue(stale["ever_seen"])
        self.assertFalse(stale["available"])
        self.assertEqual(stale["last_seen_seconds_ago"], 16)

    def test_requires_heartbeat_and_separate_capability(self):
        with self.assertRaisesRegex(ValueError, "tab_not_connected"):
            self.board.enqueue(SID, CHAT, "send", "Hello")
        with self.assertRaises(PermissionError):
            self.board.poll(SID, CHAT, "observer_key_not_authorized")
        with self.assertRaises(PermissionError):
            self.board.poll(SID, "wrong-chat", self.key)
        self.assertIsNone(self.board.poll(SID, CHAT, self.key)["command"])
        self.assertTrue(self.board.status(SID)["available"])

    def test_claim_only_once_even_with_two_tabs(self):
        self.board.poll(SID, CHAT, self.key)
        command = self.board.enqueue(SID, CHAT, "send", "Проверка 🪐")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.board.poll(SID, CHAT, self.key), range(2)))
        claimed = [item["command"] for item in results if item["command"]]
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0]["text"], "Проверка 🪐")
        self.assertEqual(claimed[0]["dispatch_id"], command["dispatch_id"])
        self.assertEqual(self.board.status(SID)["dispatch"]["status"], "claimed")
        with self.assertRaises(ValueError):
            self.board.enqueue(SID, CHAT, "send", "Another")
        self.board.ack(SID, CHAT, self.key, command["dispatch_id"], "send_initiated", TASK)
        self.assertEqual(self.board.status(SID)["dispatch"]["task_id"], TASK)
        self.assertIsNone(self.board.poll(SID, CHAT, self.key)["command"])
        with self.assertRaises(ValueError):
            self.board.ack(SID, CHAT, self.key, command["dispatch_id"], "send_initiated", TASK)
        self.assertNotIn("text", self.board._sessions[SID]["command"])

    def test_insertion_does_not_allow_faked_task_id(self):
        self.board.poll(SID, CHAT, self.key)
        dispatch = self.board.enqueue(SID, CHAT, "insert", "Редактируемый черновик")
        self.board.poll(SID, CHAT, self.key)
        with self.assertRaises(ValueError):
            self.board.ack(SID, CHAT, self.key, dispatch["dispatch_id"], "send_initiated", TASK)
        with self.assertRaises(ValueError):
            self.board.ack(SID, CHAT, self.key, dispatch["dispatch_id"], "inserted", TASK)
        self.board.ack(SID, CHAT, self.key, dispatch["dispatch_id"], "inserted")
        self.assertEqual(self.board.status(SID)["dispatch"]["status"], "inserted")
        self.assertNotIn("task_id", self.board.status(SID)["dispatch"])

    def test_heartbeat_closed_tab_no_queue_and_claim_expiry_no_replay(self):
        self.board.poll(SID, CHAT, self.key)
        self.clock += 16.0
        with self.assertRaisesRegex(ValueError, "tab_not_connected"):
            self.board.enqueue(SID, CHAT, "send", "No background queue")
        self.board.poll(SID, CHAT, self.key)
        d = self.board.enqueue(SID, CHAT, "send", "Unconfirmed once")
        self.board.poll(SID, CHAT, self.key)
        self.clock += 41.0
        self.assertEqual(self.board.status(SID)["dispatch"]["status"], "unconfirmed")
        self.assertIsNone(self.board.poll(SID, CHAT, self.key)["command"])
        self.assertNotIn("text", self.board._sessions[SID]["command"])
        self.assertNotEqual(self.board.enqueue(SID, CHAT, "send", "Explicit new action")["dispatch_id"],
                            d["dispatch_id"])

    def test_owner_revocation_disables_old_pairing_without_replay(self):
        self.board.poll(SID, CHAT, self.key)
        self.board.enqueue(SID, CHAT, "send", "Данные для текущего чата")
        self.assertTrue(self.board.revoke(SID)["revoked"])
        self.assertFalse(self.board.status(SID)["available"])
        self.assertIsNone(self.board.status(SID)["dispatch"])
        with self.assertRaises(PermissionError):
            self.board.poll(SID, CHAT, self.key)
        self.assertFalse(self.board.revoke(SID)["revoked"])
        new_key=self.board.pair(SID, CHAT)
        self.assertNotEqual(new_key,self.key)
        self.assertIsNone(self.board.poll(SID, CHAT, new_key)["command"])

    def test_heartbeat_polls_expire_claim_and_remove_sensitive_text(self):
        self.board.poll(SID, CHAT, self.key)
        item=self.board.enqueue(SID,CHAT,"send","Sensitive draft to clean")
        self.assertIsNotNone(self.board.poll(SID,CHAT,self.key)["command"])
        self.clock += 41.0
        self.assertIsNone(self.board.poll(SID,CHAT,self.key)["command"])
        state=self.board._sessions[SID]["command"]
        self.assertEqual(state["status"],"unconfirmed")
        self.assertNotIn("text",state)
        self.assertEqual(self.board.status(SID)["dispatch"]["status"],"unconfirmed")
        self.assertEqual(self.board.ack(SID,CHAT,self.key,item["dispatch_id"],
                         "send_initiated",TASK)["status"],"send_initiated")
        self.assertNotIn("text",state)
        with self.assertRaises(ValueError):
            self.board.ack(SID,CHAT,self.key,item["dispatch_id"],"send_initiated",TASK)

    def test_pending_expiry_does_not_claim_old_command(self):
        self.board.poll(SID,CHAT,self.key)
        self.board.enqueue(SID,CHAT,"insert","Sensitive pending draft")
        self.clock += 21.0
        self.assertIsNone(self.board.poll(SID,CHAT,self.key)["command"])
        self.assertEqual(self.board.status(SID)["dispatch"]["status"],"expired")
        self.assertNotIn("text",self.board._sessions[SID]["command"])

    def test_existing_notifier_profiles_mirrored_by_id_without_body_or_secrets(self):
        self.board.poll(SID,CHAT,self.key)
        catalog=[{"id":"policy.verification","title":"Проверка"},
                 {"id":"review.summary","title":"Обзор"}]
        profiles=[
            {"id":"default","name":"Обычный","module_ids":[]},
            {"id":"repo","name":"Работа в Repo","module_ids":["policy.verification"]}]
        with self.assertRaises(PermissionError):
            self.board.update_modules(SID,CHAT,"wrong-key",catalog,[],profiles,"repo")
        with self.assertRaisesRegex(ValueError,"invalid_profiles"):
            self.board.update_modules(SID,CHAT,self.key,catalog,[],
                                      profiles+[profiles[0]],"repo")
        with self.assertRaisesRegex(ValueError,"invalid_profiles"):
            self.board.update_modules(SID,CHAT,self.key,catalog,[],profiles,"unknown")
        with self.assertRaisesRegex(ValueError,"invalid_profiles"):
            self.board.update_modules(SID,CHAT,self.key,catalog,[],
                                      [{"id":"bad","name":"X",
                                        "module_ids":[],"text":"secret"}],"bad")
        result=self.board.update_modules(SID,CHAT,self.key,catalog,
                                         ["policy.verification"],profiles,"repo")
        self.assertTrue(result["ok"])
        status=self.board.status(SID)
        self.assertTrue(status["profiles_synced"])
        self.assertEqual(status["profiles"],profiles)
        self.assertEqual(status["active_profile_id"],"repo")
        self.assertNotIn("text",str(status))
        with self.assertRaisesRegex(ValueError,"unknown_dispatch_profile"):
            self.board.enqueue(SID,CHAT,"insert","точный оригинал",None,"missing")
        item=self.board.enqueue(SID,CHAT,"insert","точный оригинал",None,"default")
        polled=self.board.poll(SID,CHAT,self.key)["command"]
        self.assertEqual(polled["module_ids"],None,
                         "local Notifier must resolve selected saved profile")
        self.assertEqual(polled["profile_id"],"default")
        self.board.ack(SID,CHAT,self.key,item["dispatch_id"],"inserted",TASK)
        self.assertEqual(self.board.status(SID)["dispatch"]["task_id"],TASK)
        self.assertNotIn("profile_id",self.board._sessions[SID]["command"])
        self.assertFalse(self.board.status(SID)["dispatch"].get("profile_id"))
        # Legacy Notifier sends catalog without profile metadata; do not
        # leave the prior profile list active for a client that can't use it.
        self.board.update_modules(SID,CHAT,self.key,catalog,["policy.verification"])
        self.assertFalse(self.board.status(SID)["profiles_synced"])
        self.assertEqual(self.board.status(SID)["profiles"],[])

    def test_module_catalog_is_owner_metadata_only_and_never_accepts_external_code(self):
        self.board.poll(SID,CHAT,self.key)
        self.assertFalse(self.board.status(SID)["modules_synced"])
        with self.assertRaises(PermissionError):
            self.board.update_modules(SID,CHAT,"wrong-key",[])
        with self.assertRaises(ValueError):
            self.board.update_modules(SID,CHAT,self.key,[{"id":"bad id","title":"bad"}])
        with self.assertRaises(ValueError):
            self.board.update_modules(SID,CHAT,self.key,
                                      [{"id":"review","title":"Один"},
                                       {"id":"review","title":"Дубль"}])
        self.assertEqual(self.board.update_modules(SID,CHAT,self.key,
            [{"id":"review.summary","title":"Обзор"}],["review.summary"])["count"],1)
        meta=self.board.status(SID)
        self.assertTrue(meta["modules_synced"])
        self.assertEqual(meta["default_module_ids"],["review.summary"])
        self.assertEqual(meta["modules"],[{"id":"review.summary","title":"Обзор"}])
        with self.assertRaisesRegex(ValueError,"unknown_dispatch_modules"):
            self.board.enqueue(SID,CHAT,"file","Текст",["unknown.module"])
        command=self.board.enqueue(SID,CHAT,"file","Точный UTF-8 оригинал",["review.summary"])
        claimed=self.board.poll(SID,CHAT,self.key)["command"]
        self.assertEqual(claimed["mode"],"file")
        self.assertEqual(claimed["module_ids"],["review.summary"])
        self.assertEqual(claimed["text"],"Точный UTF-8 оригинал")
        self.board.ack(SID,CHAT,self.key,command["dispatch_id"],"file_attached")
        self.assertEqual(self.board.status(SID)["dispatch"]["status"],"file_attached")
        self.assertNotIn("text",self.board._sessions[SID]["command"])
        self.assertNotIn("module_ids",self.board._sessions[SID]["command"])

    def test_legacy_dispatch_uses_active_local_profile_null_and_no_file_task_id(self):
        self.board.poll(SID,CHAT,self.key)
        command=self.board.enqueue(SID,CHAT,"insert","старый запрос")
        claimed=self.board.poll(SID,CHAT,self.key)["command"]
        self.assertIsNone(claimed["module_ids"])
        self.board.ack(SID,CHAT,self.key,command["dispatch_id"],"inserted")
        with self.assertRaisesRegex(ValueError,"already_acknowledged"):
            self.board.ack(SID,CHAT,self.key,command["dispatch_id"],"file_attached",TASK)

    def test_rejected_payload_never_queued(self):
        self.board.poll(SID, CHAT, self.key)
        for text in ("", " ", "a" * (MAX_TEXT_BYTES + 1)):
            with self.assertRaises(ValueError):
                self.board.enqueue(SID, CHAT, "send", text)
        with self.assertRaises(ValueError):
            self.board.enqueue(SID, CHAT, "execute", "test")
        with self.assertRaises(ValueError):
            self.board.enqueue(SID, "other_chat", "send", "test")
        self.assertIsNone(self.board.status(SID)["dispatch"])

class PreparedOwnerSendAuditTests(unittest.TestCase):
    def setUp(self):
        self.now=100.0
        self.board=DispatchBoard(clock=lambda:self.now)
        self.sid=SID
        self.chat=CHAT
        self.key=self.board.pair(SID,CHAT)
        self.board.poll(SID,CHAT,self.key)

    def test_prepared_send_is_one_shot_with_task_id_and_bounded_history(self):
        item=self.board.enqueue(SID,CHAT,'send_prepared','',None,None)
        first=self.board.poll(SID,CHAT,self.key)['command']
        self.assertEqual(first['mode'],'send_prepared')
        self.assertEqual(first['text'],'')
        self.assertIsNone(self.board.poll(SID,CHAT,self.key)['command'])
        self.board.ack(SID,CHAT,self.key,item['dispatch_id'],'send_initiated',TASK)
        status=self.board.status(SID)
        self.assertEqual(status['dispatch']['task_id'],TASK)
        self.assertEqual([x['event'] for x in status['history']],
                         ['queued','claimed','send_initiated'])
        self.assertEqual(status['history'][-1]['task_id'],TASK)
        with self.assertRaisesRegex(ValueError,'already_acknowledged'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],'send_initiated',TASK)

    def test_refusal_reasons_are_allowlisted_and_no_secret_details(self):
        item=self.board.enqueue(SID,CHAT,'send_prepared','',None,None)
        self.board.poll(SID,CHAT,self.key)
        with self.assertRaisesRegex(ValueError,'invalid_ack'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],'refused',None,
                           'user private secret in error')
        self.board.ack(SID,CHAT,self.key,item['dispatch_id'],'refused',None,
                       'prepared_missing')
        self.assertEqual(self.board.status(SID)['history'][-1]['reason'],
                         'prepared_missing')
        self.assertNotIn('user private secret',str(self.board.status(SID)))

    def test_never_accept_prepared_send_with_new_text_or_profile(self):
        with self.assertRaisesRegex(ValueError,'invalid_dispatch'):
            self.board.enqueue(SID,CHAT,'send_prepared','new text')
        with self.assertRaisesRegex(ValueError,'invalid_dispatch'):
            self.board.enqueue(SID,CHAT,'send_prepared','',[],None)
        with self.assertRaisesRegex(ValueError,'invalid_dispatch'):
            self.board.enqueue(SID,CHAT,'send_prepared','',None,'default')

class PartialFileHistoryTests(unittest.TestCase):
    def setUp(self):
        self.board=DispatchBoard()
        self.sid=SID
        self.chat=CHAT
        self.key=self.board.pair(SID,CHAT)
        self.board.poll(SID,CHAT,self.key)

    def test_no_card_outcome_does_not_claim_file_was_not_attached(self):
        item=self.board.enqueue(SID,CHAT,'file','unique UTF-8 text')
        self.board.poll(SID,CHAT,self.key)
        result=self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                              'attachment_unconfirmed',None,'upload_unconfirmed')
        self.assertEqual(result['status'],'attachment_unconfirmed')
        self.assertEqual(self.board.status(SID)['history'][-1]['event'],
                         'attachment_unconfirmed')
        self.assertEqual(self.board.status(SID)['history'][-1]['reason'],
                         'upload_unconfirmed')
        self.assertNotIn('text',str(self.board.status(SID)['history']))
        with self.assertRaises(ValueError):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],'file_attached',TASK)

    def test_recognized_file_without_fortis_context_is_partial_not_complete(self):
        item=self.board.enqueue(SID,CHAT,'file','unique UTF-8 text')
        self.board.poll(SID,CHAT,self.key)
        result=self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                              'attachment_only',None,'context_mismatch')
        self.assertEqual(result['status'],'attachment_only')
        self.assertEqual(self.board.status(SID)['history'][-1]['event'],'attachment_only')

    def test_ambiguity_cannot_be_spoofed_for_insert_or_supply_unverified_task_id(self):
        item=self.board.enqueue(SID,CHAT,'insert','unique')
        self.board.poll(SID,CHAT,self.key)
        with self.assertRaisesRegex(ValueError,'ack_mode_mismatch'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                           'attachment_unconfirmed',None,'upload_unconfirmed')
        with self.assertRaisesRegex(ValueError,'invalid_partial_ack'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                           'attachment_only',TASK,'context_mismatch')
        with self.assertRaisesRegex(ValueError,'invalid_partial_ack'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                           'attachment_unconfirmed',None)

class NotifierFullDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.board=DispatchBoard()
        self.key=self.board.pair(SID,CHAT)
        self.board.poll(SID,CHAT,self.key)
        self.item=self.board.enqueue(SID,CHAT,'file','SECRET ORIGINAL NOT FOR EVENT')
        self.board.poll(SID,CHAT,self.key)
        self.detail=("Файл прикреплён, но контекст не добавлен: "
                     "Вставка не совпала с исходником посимвольно. "
                     "Исходник сохранён; Send не нажимался. "
                     "Не отправляй до ручной проверки.")

    def test_full_local_notifier_warning_is_visible_in_owner_history(self):
        self.board.ack(SID,CHAT,self.key,self.item['dispatch_id'],
                       'attachment_only',None,'context_mismatch',self.detail)
        history=self.board.status(SID)['history']
        self.assertEqual(history[-1]['detail'],self.detail)
        self.assertEqual(history[-1]['reason'],'context_mismatch')
        self.assertNotIn('SECRET ORIGINAL NOT FOR EVENT',str(history))
        self.assertNotIn('detail',str(history[0]))
        self.assertNotIn('detail',str(history[1]))

    def test_injected_source_or_secret_is_not_accepted_as_log_message(self):
        for detail in ('SECRET ORIGINAL NOT FOR EVENT',
                       self.detail+'\nPRIVATE KEY',
                       self.detail+'\x00',
                       '<script>alert(1)</script>',
                       'A'*513, '', 28):
            with self.subTest(detail=str(detail)[:30]):
                with self.assertRaisesRegex(ValueError,'invalid_ack'):
                    self.board.ack(SID,CHAT,self.key,self.item['dispatch_id'],
                                   'attachment_only',None,'context_mismatch',detail)
        self.assertEqual([e['event'] for e in self.board.status(SID)['history']],
                         ['queued','claimed'])

    def test_detailed_file_warning_disallowed_on_unrelated_insert_command(self):
        self.board.ack(SID,CHAT,self.key,self.item['dispatch_id'],
                       'attachment_only',None,'context_mismatch',self.detail)
        item=self.board.enqueue(SID,CHAT,'insert','another')
        self.board.poll(SID,CHAT,self.key)
        with self.assertRaisesRegex(ValueError,'invalid_detail_mode'):
            self.board.ack(SID,CHAT,self.key,item['dispatch_id'],
                           'refused',None,'context_mismatch',self.detail)
