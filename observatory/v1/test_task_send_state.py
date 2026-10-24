"""Step B regression: isolated storage, HTTP, scope grant and narrow relay."""
import json
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.request import Request, build_opener

import test_task_intents as fixtures
from task_intents import TaskIntents
from owner_enrollment import Enrollment
from owner_notifier_bridge import scoped_request, owner_pair, validate_task_metadata
from browser_relay_dispatch import forward


class SendStateTests(unittest.TestCase):
    setUp = fixtures.IntentStoreTests.setUp
    body_for = fixtures.IntentStoreTests.body_for
    accept = fixtures.IntentStoreTests.accept
    card = fixtures.IntentStoreTests.card

    def send(self, revision=1, phase="send_unconfirmed"):
        return {k: self.body[k] for k in ("version", "reporting_session_id", "conversation_id", "task_id")} | {
            "revision": revision, "phase": phase, "observed_at_client_ms": int(time.time()*1000)}

    def test_register_required_and_metadata_is_not_activity_or_archive_authority(self):
        with self.assertRaises(ValueError):
            self.api.send_state(self.send(), self.key)
        self.api.register(self.body, self.key)
        self.api.send_state(self.send(), self.key)
        self.assertEqual(self.card()["state"], "waiting_ai")
        self.assertIsNone(self.card()["first_work_at"])
        self.assertFalse(self.store.task_activity(self.sid,self.store.observer_key(self.sid),self.body["task_id"])["found"])
        with self.assertRaisesRegex(ValueError,"first_activity_not_accepted"):
            self.store.write_user_message(self.sid,self.store.message_writer_key(self.sid),self.body["task_id"],self.meta["conversation_id"],"synthetic")

    def test_revisions_idempotent_out_of_order_and_conflicting_updates(self):
        self.api.register(self.body,self.key)
        first=self.send(1,"send_requested"); latest=self.send(2,"send_observed")
        self.api.send_state(first,self.key);self.api.send_state(latest,self.key)
        self.assertEqual(self.api.send_state(first,self.key)["status"],"stale")
        self.assertEqual(self.api.send_state(latest,self.key)["status"],"existing")
        with self.assertRaises(ValueError):self.api.send_state({**latest,"phase":"send_requested"},self.key)
        with self.assertRaises(ValueError):self.api.send_state(self.send(3,"send_not_attempted"),self.key)
        self.assertEqual(self.card()["send_phase"],"send_observed")

    def test_terminal_and_multiple_tasks_not_hidden_by_send_updates(self):
        self.accept(self.body["task_id"],0,"completed")
        self.api.register(self.body,self.key);self.api.send_state(self.send(),self.key)
        self.assertEqual(self.card()["state"],"completed")
        other=self.body_for();self.api.register(other,self.key)
        counts=self.api.snapshot(self.sid)["counts"]
        self.assertEqual(counts["prepared"],1);self.assertEqual(counts["completed"],1)

    def test_not_attempted_and_long_wait_never_become_ai_failure(self):
        self.api.register(self.body,self.key)
        self.api.send_state(self.send(1,"send_not_attempted"),self.key)
        self.assertEqual(self.card()["state"],"prepared")
        self.api.send_state(self.send(2,"send_requested"),self.key)
        with patch("task_intents.time.time",return_value=time.time()+86400):
            card=self.card();self.assertEqual(card["state"],"waiting_ai");self.assertTrue(card["waiting_overdue"])

    def test_bad_keys_schema_types_and_future_time_are_refused(self):
        self.api.register(self.body,self.key)
        for key in (self.store.observer_key(self.sid),self.store.message_writer_key(self.sid)):
            with self.assertRaises(PermissionError):self.api.send_state(self.send(),key)
        for extra in ({"original_text":"secret"},{"revision":True},{"phase":"send_confirmed"},
                      {"observed_at_client_ms":int(time.time()*1000)+60000}):
            with self.assertRaises(ValueError):self.api.send_state({**self.send(),**extra},self.key)

    def test_send_record_survives_reload_and_refuses_symlink(self):
        self.api.register(self.body,self.key);self.api.send_state(self.send(),self.key)
        self.assertEqual(TaskIntents(self.store).snapshot(self.sid)["tasks"],self.api.snapshot(self.sid)["tasks"])
        p=self.api._send_path(self.sid,self.body["task_id"]);p.unlink();p.symlink_to(self.root/'missing')
        with self.assertRaises(ValueError):self.api.send_state(self.send(),self.key)
        with self.assertRaises(ValueError):self.api.snapshot(self.sid)


class SendHttpTests(unittest.TestCase):
    setUp = fixtures.IntentHttpTests.setUp
    request = fixtures.IntentHttpTests.request

    def test_narrow_owner_bridge_and_relay_to_isolated_http_service(self):
        port=self.server.server_port
        class Client:
            def open(self, req, timeout):
                return build_opener().open(Request('http://127.0.0.1:'+str(port)+req.selector,
                    data=req.data,headers=dict(req.header_items()),method=req.method),timeout=timeout)
        def execute(argv, **kwargs):
            envelope=json.loads(kwargs['input'])
            self.assertNotIn(self.key,' '.join(argv))
            return SimpleNamespace(returncode=0,stdout=json.dumps(forward(envelope,opener=Client())).encode())
        code,data=scoped_request('synthetic-container','POST','/api/task-intents',self.key,self.body,executor=execute)
        self.assertEqual(code,201);self.assertTrue(data['registered'])
        send={k:self.body[k] for k in ('version','reporting_session_id','conversation_id','task_id')} | {
            'revision':1,'phase':'send_unconfirmed','observed_at_client_ms':int(time.time()*1000)}
        code,data=scoped_request('synthetic-container','POST','/api/task-send-state',self.key,send,executor=execute)
        self.assertEqual(code,201);self.assertTrue(data['recorded'])
        send['original_text']='not allowed'
        with self.assertRaises(ValueError):scoped_request('synthetic-container','POST','/api/task-send-state',self.key,send,executor=execute)
        with self.assertRaises(ValueError):validate_task_metadata('/api/task-intent-pair',{})


class ExplicitIntentGrantTests(unittest.TestCase):
    def test_old_approval_never_silently_gains_new_scope_and_enable_is_durable(self):
        sid='rs_'+'a'*32;chat='12345678-abcd';proof='b'*64
        with tempfile.TemporaryDirectory() as root:
            calls=[]
            e=Enrollment(root,lambda sid:calls.append(sid) or {'scope':'synthetic'})
            valid=lambda s,c:s==sid and c==chat
            with self.assertRaises(ValueError):e.enable_task_intents(sid,chat,valid)
            e.announce(sid,chat,proof,valid)
            fp=e.pending_for(sid)['pending'][0]['fingerprint'];e.approve(sid,chat,fp,valid)
            e.announce(sid,chat,proof,valid);self.assertEqual(len(calls),1)
            self.assertFalse(e.pending_for(sid)['task_intents'])
            e.enable_task_intents(sid,chat,valid)
            e.announce(sid,chat,proof,valid);self.assertEqual(len(calls),2)
            self.assertTrue(Enrollment(root,lambda _:{}).pending_for(sid)['task_intents'])
            self.assertNotEqual(e.announce(sid,chat,'c'*64,valid).get('status'),'approved')

    def test_pair_helper_requests_metadata_key_only_when_explicit(self):
        sid='rs_'+'a'*32;calls=[]
        base={'version':1,'origin':'http://127.0.0.1:18754','reporting_session_id':sid,
              'conversation_id':'12345678-abcd','observer_key':'o'*48,'message_writer_key':'w'*48}
        def execute(argv,**kwargs):
            calls.append(argv)
            return SimpleNamespace(returncode=0,stdout=json.dumps(base | (
                {'task_intent_key':'i'*48} if '--task-intents' in argv else {})).encode())
        self.assertNotIn('task_intent_key',owner_pair('synthetic-container',sid,executor=execute))
        self.assertIn('task_intent_key',owner_pair('synthetic-container',sid,executor=execute,task_intents=True))
        self.assertNotIn('--task-intents',calls[0]);self.assertIn('--task-intents',calls[1])


class OwnerMetadataBoundaryTests(unittest.TestCase):
    setUp = fixtures.IntentHttpTests.setUp
    request = fixtures.IntentHttpTests.request

    def test_explicit_grant_and_metadata_transport_through_owner_http(self):
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        from owner_viewer import handler_for, WIN_PORT
        root=self.app.store.archive.parent
        enrollment=Enrollment(root,lambda sid:{"synthetic":True})
        chat=self.body['conversation_id'];proof='b'*64
        valid=lambda sid,c:sid==self.sid and c==chat
        enrollment.announce(self.sid,chat,proof,valid)
        enrollment.approve(self.sid,chat,enrollment.pending_for(self.sid)['pending'][0]['fingerprint'],valid)
        calls=[]
        def read(kind,sid,task):
            return {'ok':True,'sessions':[dict(self.meta)]}
        def relay(method,path,key,body):
            calls.append(path)
            return self.request(method,path,body,headers={'X-Fortis-Task-Intent-Key':key})
        srv=ThreadingHTTPServer(('127.0.0.1',0),handler_for('synthetic-viewer',read,'nonce',
            notifier_forward=relay,enrollment=enrollment))
        self.addCleanup(srv.server_close)
        threading.Thread(target=srv.serve_forever,daemon=True).start();self.addCleanup(srv.shutdown)
        def owner_request(path,body,auth=False,origin=None,raw=None):
            conn=http.client.HTTPConnection('127.0.0.1',srv.server_port,timeout=5)
            self.addCleanup(conn.close)
            headers={'Host':f'127.0.0.1:{WIN_PORT}','Content-Type':'application/json',
                     'X-Fortis-Task-Intent-Key':self.key}
            if auth:headers['Authorization']='Bearer synthetic-viewer'
            if origin:headers['Origin']=origin
            conn.request('POST',path,body=raw if raw is not None else json.dumps(body).encode(),headers=headers)
            response=conn.getresponse();return response.status,json.loads(response.read())
        grant={'session':self.sid,'chat':chat};url='/api/notifier/task-intents';local=f'http://127.0.0.1:{WIN_PORT}'
        self.assertEqual(owner_request(url,grant,origin=local)[0],401)
        self.assertEqual(owner_request(url,grant,auth=True,origin='https://chatgpt.com')[0],403)
        self.assertFalse(enrollment.pending_for(self.sid)['task_intents'])
        self.assertEqual(owner_request(url,grant,auth=True,origin=local)[0],200)
        self.assertTrue(enrollment.pending_for(self.sid)['task_intents'])
        self.assertEqual(owner_request('/api/task-intents',self.body,origin='https://chatgpt.com')[0],201)
        bad={**self.body,'original_text':'synthetic private text'}
        self.assertEqual(owner_request('/api/task-intents',bad,origin='https://chatgpt.com')[0],403)
        duplicate=(json.dumps(self.body)[:-1]+',"version":1}').encode()
        self.assertEqual(owner_request('/api/task-intents',self.body,raw=duplicate)[0],403)
        self.assertEqual(calls,['/api/task-intents'])


if __name__=='__main__':unittest.main()
