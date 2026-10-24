"""Synthetic tests for manual Alexa Edge viewer, without Windows owner or Docker changes."""
from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import subprocess
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from owner_dispatch import DispatchBoard
from owner_viewer import (
    handler_for, repo_read, repo_register, valid_registration,
    ensure_repo_running, docker_command, read_owner_config,
    PAGE, WIN_PORT, DOCKER_READER, DOCKER_SERVICE, open_owner_edge,
)


class OwnerViewerTest(unittest.TestCase):
    def setUp(self):
        self.recorded=[]
        def fetch(action,sid,task):
            self.recorded.append((action,sid,task))
            if action=="tasks":
                return {"ok":True,"session":sid,"task_ids":["task_"+"b"*32],
                        "tasks":[{"task_id":"task_"+"b"*32,
                                  "first_seen_at":"2026-10-19T09:17:41+00:00",
                                  "original_preview":None,"original_received":False}]}
            if action=="state":
                return {"ok":True,"sessions":[{
                    "reporting_session_id":"rs_"+"a"*32,
                    "title":"Synthetic Session",
                     "conversation_id":"abcdefgh-01234567",
                    "route":"repo",
                    "events":[{"task_id":"task_"+"b"*32,"event":"progress","sequence":0}]
                }], "messages_ingest":{}}
            return {"ok":True,"session":sid,"task_id":task,
                    "original_text":"<img src=x onerror=alert(1)>",
                    "events":[{"event":"progress","sequence":0}],
                    "assistant_messages":[{"role":"assistant","body":"Привет ✨\n<script>alert('x')</script>",
                                           "kind":"final","provenance":"sender_claim"}]}
        self.registrations=[]
        def registrar(url,title):
            self.registrations.append((url,title))
            return {"ok":True,"created":True,"session":"rs_"+"e"*32,
                    "session_task_id":"task_"+"f"*32,"conversation_id":"abcdefgh-01234567"}
        self.token="viewer_local_only_example_"+"a"*32
        self.pair_calls=[]
        self.browser_calls=[]
        def pair(sid):
            self.pair_calls.append(sid)
            return {"version":1,"origin":f"http://127.0.0.1:{WIN_PORT}",
                    "conversation_id":"abcdefgh-01234567",
                    "reporting_session_id":sid,
                    "observer_key":"k"*48,"message_writer_key":"w"*48}
        def forward(method,path,key,body):
            self.browser_calls.append((method,path,key,body))
            if ((method=="GET" and key!="k"*48) or
                (method=="POST" and key!="w"*48)):
                return 403,{"ok":False,"error":"wrong_key"}
            if method=="POST":
                return 201,{"ok":True,"task_id":body["task_id"]}
            return 200,{"ok":True,"found":True}
        self.dispatch_board=DispatchBoard()
        self.http=ThreadingHTTPServer(("127.0.0.1",0),
             handler_for(self.token,fetch,"testnonce",registrar,pair,forward,
                         self.dispatch_board))
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.http.server_close)
        self.addCleanup(self.http.shutdown)
        self.addCleanup(lambda:self.thread.join(timeout=3))

    def request(self,path,headers=None,method="GET",body=None):
        h={"Host":f"127.0.0.1:{WIN_PORT}",**(headers or {})}
        req=Request(f"http://127.0.0.1:{self.http.server_port}"+path,
                    headers=h,method=method,data=body)
        try:
            resp=urlopen(req,timeout=3)
        except HTTPError as exc:
            resp=exc
        with resp:
            data=resp.read()
            return resp.status,dict(resp.headers),data

    def test_login_and_browser_static_html_safety(self):
        code,headers,body=self.request("/")
        self.assertEqual(code,200)
        self.assertIn(b"Fortis Observatory",body)
        self.assertIn(b'textContent',body)
        self.assertIn(b'nonce="testnonce"',body)
        self.assertNotIn(self.token.encode("ascii"),body)
        self.assertIn("Оригинал ещё не получен".encode("utf-8"),body)
        self.assertIn(b"task-preview",body)
        self.assertIn(b"showTime",body)
        self.assertIn(b'id="makePair"',body)
        self.assertIn(b'id="copyPair"',body)
        self.assertEqual(headers.get("Cache-Control"),"no-store")
        self.assertIn("default-src 'none'",headers["Content-Security-Policy"])
        self.assertNotIn("innerHTML",PAGE)

    def test_private_file_launcher_navigation_only_opens_public_shell(self):
        # Edge follows file:// -> http://127.0.0.1:18755/ as a cross-site
        # top-level document navigation. The shell has no secrets.
        file_nav={"Origin":"null", "Sec-Fetch-Site":"cross-site",
                  "Sec-Fetch-Mode":"navigate", "Sec-Fetch-Dest":"document"}
        status,headers,body=self.request("/",headers=file_nav)
        self.assertEqual(status,200)
        self.assertIn(b"Fortis Observatory",body)
        self.assertNotIn(self.token.encode("ascii"),body)
        self.assertEqual(headers.get("Cache-Control"),"no-store")
        no_origin={k:v for k,v in file_nav.items() if k!="Origin"}
        self.assertEqual(self.request("/",headers=no_origin)[0],200)
        # Cross-site subresource/fetch or unrecognized origin remains refused.
        for props in (
            {**file_nav,"Sec-Fetch-Mode":"cors"},
            {**file_nav,"Sec-Fetch-Dest":"empty"},
            {**file_nav,"Origin":"https://evil.example"},
        ):
            self.assertEqual(self.request("/",headers=props)[0],403)
        # The same navigation headers NEVER authorize private endpoints,
        # even if someone provides the valid owner bearer.
        auth={"Authorization":"Bearer "+self.token}
        for path in ("/api/state","/api/notifier-pair?session=rs_"+"a"*32):
            self.assertEqual(self.request(path,headers={**file_nav,**auth})[0],403)
        self.assertEqual(self.request("/?query=1",headers=file_nav)[0],403)
        self.assertFalse(self.recorded)

    def test_manual_owner_pairing_is_not_public(self):
        sid="rs_"+"a"*32
        path="/api/notifier-pair?session="+sid
        self.assertEqual(self.request(path)[0],401)
        self.assertEqual(self.pair_calls,[])
        status,_,payload=self.request(path,headers={"Authorization":"Bearer "+self.token})
        self.assertEqual(status,200)
        pair=json.loads(payload)["pairing"]
        self.assertEqual(pair["origin"],f"http://127.0.0.1:{WIN_PORT}")
        self.assertEqual(pair["reporting_session_id"],sid)
        self.assertEqual(pair["message_writer_key"],"w"*48)
        self.assertNotIn(b"wwww",self.request("/")[2])
        self.assertEqual(self.request(path,headers={
            "Authorization":"Bearer "+self.token,"Origin":"https://evil.example"})[0],403)
        self.assertEqual(self.pair_calls,[sid])

    def test_dispatch_owner_restrictions_live_session_and_ack(self):
        sid="rs_"+"a"*32
        own={"Authorization":"Bearer "+self.token,
             "Origin":f"http://127.0.0.1:{WIN_PORT}",
             "Content-Type":"application/json"}
        pair_path="/api/notifier-pair?session="+sid
        self.assertEqual(self.request(pair_path)[0],401)
        status,_,raw=self.request(pair_path,headers=own)
        self.assertEqual(status,200)
        pair=json.loads(raw)["pairing"]
        self.assertEqual(pair["conversation_id"],"abcdefgh-01234567")
        key=pair["dispatch_key"]
        self.assertGreater(len(key),40)
        self.assertNotEqual(key,pair["observer_key"])
        owner_status_path="/api/dispatch/status?session="+sid
        self.assertEqual(self.request(owner_status_path)[0],401)
        before=json.loads(self.request(owner_status_path,headers=own)[2])
        self.assertTrue(before["paired"])
        self.assertFalse(before["ever_seen"])
        self.assertFalse(before["available"])
        self.assertIsNone(before["last_seen_seconds_ago"])
        self.assertNotIn("dispatch_key",before)
        self.assertNotIn("observer_key",before)
        notifier={"Origin":"https://chatgpt.com",
                  "X-Fortis-Dispatch-Key":key}
        poll="/api/dispatch/poll?session="+sid+"&chat=abcdefgh-01234567"
        bad_payload=json.dumps({"session":sid,"chat":"abcdefgh-01234567",
                                "mode":"send","text":"Сообщение с task_id"}).encode()
        self.assertEqual(self.request("/api/dispatch",headers=own,
                                     method="POST",body=bad_payload)[0],409,
                         "no queue for a tab that has not connected")
        self.assertEqual(self.request(poll,headers=notifier)[0],200)
        online=json.loads(self.request(owner_status_path,headers=own)[2])
        self.assertTrue(online["available"])
        self.assertTrue(online["ever_seen"])
        self.assertIsInstance(online["last_seen_seconds_ago"],int)
        self.assertNotIn("dispatch_key",online)
        self.assertNotIn("observer_key",online)
        self.assertEqual(self.request("/api/dispatch",headers={
            "Origin":f"http://127.0.0.1:{WIN_PORT}","Content-Type":"application/json"},
            method="POST",body=bad_payload)[0],401)
        self.assertEqual(self.request("/api/dispatch",headers={
            **own,"Origin":"https://chatgpt.com"},method="POST",body=bad_payload)[0],403)
        self.assertEqual(self.request(poll,headers={
            **notifier,"X-Fortis-Dispatch-Key":pair["observer_key"]})[0],403)
        status,_,reply=self.request("/api/dispatch",headers=own,
                                    method="POST",body=bad_payload)
        self.assertEqual(status,202)
        did=json.loads(reply)["dispatch_id"]
        status,_,reply=self.request(poll,headers=notifier)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(reply)["command"]["dispatch_id"],did)
        self.assertIsNone(json.loads(self.request(poll,headers=notifier)[2])["command"])
        ack=json.dumps({"session":sid,"chat":"abcdefgh-01234567","dispatch_id":did,
                         "status":"send_initiated","task_id":"task_"+"c"*32}).encode()
        self.assertEqual(self.request("/api/dispatch/ack",headers={
            "Origin":"https://chatgpt.com","Content-Type":"application/json",
            "X-Fortis-Dispatch-Key":pair["observer_key"]},method="POST",body=ack)[0],403)
        self.assertEqual(self.request("/api/dispatch/ack",headers={
            **notifier,"Content-Type":"application/json"},method="POST",body=ack)[0],200)
        result=json.loads(self.request("/api/dispatch/status?session="+sid,
             headers=own)[2])
        self.assertEqual(result["dispatch"]["status"],"send_initiated")
        self.assertEqual(result["dispatch"]["task_id"],"task_"+"c"*32)
        self.assertNotIn("Сообщение".encode("utf-8"),self.request("/api/dispatch/status?session="+sid,
             headers=own)[2])
        self.assertEqual(self.request("/api/dispatch/status?session="+sid)[0],401)
        revoke=json.dumps({"session":sid}).encode()
        self.assertEqual(self.request("/api/dispatch/revoke",headers={
            "Origin":"https://chatgpt.com","Content-Type":"application/json",
            "Authorization":"Bearer "+self.token},method="POST",body=revoke)[0],403)
        self.assertEqual(self.request("/api/dispatch/revoke",headers=own,
                                     method="POST",body=revoke)[0],200)
        self.assertEqual(self.request(poll,headers=notifier)[0],403)
        result=json.loads(self.request("/api/dispatch/status?session="+sid,
             headers=own)[2])
        self.assertFalse(result["available"])

    def test_scoped_module_catalog_and_file_command_are_one_shot_no_send(self):
        sid="rs_"+"a"*32;chat="abcdefgh-01234567"
        owner={"Authorization":"Bearer "+self.token,
               "Origin":f"http://127.0.0.1:{WIN_PORT}",
               "Content-Type":"application/json"}
        pair=json.loads(self.request("/api/notifier-pair?session="+sid,
                                    headers=owner)[2])["pairing"]
        tab={"Origin":"https://chatgpt.com","Content-Type":"application/json",
             "X-Fortis-Dispatch-Key":pair["dispatch_key"]}
        poll=f"/api/dispatch/poll?session={sid}&chat={chat}"
        self.assertEqual(self.request(poll,headers=tab)[0],200)
        catalog=json.dumps({"session":sid,"chat":chat,
            "modules":[{"id":"policy.verification","title":"Проверка"}],
            "default_module_ids":["policy.verification"]}).encode()
        self.assertEqual(self.request("/api/dispatch/modules",headers={
            **tab,"X-Fortis-Dispatch-Key":pair["observer_key"]},
            method="POST",body=catalog)[0],403)
        self.assertEqual(self.request("/api/dispatch/modules",headers={
            **tab,"Origin":"https://evil.example"},
            method="POST",body=catalog)[0],403)
        self.assertEqual(self.request("/api/dispatch/modules",headers=tab,
                                     method="POST",body=catalog)[0],200)
        self.assertEqual(self.request("/api/dispatch/status?session="+sid)[0],401)
        meta=json.loads(self.request("/api/dispatch/status?session="+sid,
                                     headers=owner)[2])
        self.assertTrue(meta["modules_synced"])
        self.assertEqual(meta["modules"][0]["id"],"policy.verification")
        self.assertNotIn("dispatch_key",meta)
        command=json.dumps({"session":sid,"chat":chat,"mode":"file",
            "text":"Точный оригинал 🪐","module_ids":["policy.verification"]},
            ensure_ascii=False).encode("utf-8")
        self.assertEqual(self.request("/api/dispatch",headers={
            **owner,"Authorization":"Bearer wrong"},
            method="POST",body=command)[0],401)
        status,_,response=self.request("/api/dispatch",headers=owner,
                                      method="POST",body=command)
        self.assertEqual(status,202)
        did=json.loads(response)["dispatch_id"]
        polled=json.loads(self.request(poll,headers=tab)[2])["command"]
        self.assertEqual(polled["mode"],"file")
        self.assertEqual(polled["module_ids"],["policy.verification"])
        self.assertEqual(polled["text"],"Точный оригинал 🪐")
        self.assertIsNone(json.loads(self.request(poll,headers=tab)[2])["command"])
        ack=json.dumps({"session":sid,"chat":chat,"dispatch_id":did,
                         "status":"file_attached","task_id":None}).encode()
        self.assertEqual(self.request("/api/dispatch/ack",headers=tab,
                                    method="POST",body=ack)[0],200)
        after=json.loads(self.request("/api/dispatch/status?session="+sid,
                                     headers=owner)[2])
        self.assertEqual(after["dispatch"]["status"],"file_attached")
        self.assertNotIn("text",after["dispatch"])
        self.assertNotIn("module_ids",after["dispatch"])

    def test_profiles_are_scoped_metadata_and_select_notifier_profile_without_mutating(self):
        sid="rs_"+"a"*32;chat="abcdefgh-01234567"
        owner={"Authorization":"Bearer "+self.token,
               "Origin":f"http://127.0.0.1:{WIN_PORT}",
               "Content-Type":"application/json"}
        pairing=json.loads(self.request("/api/notifier-pair?session="+sid,
                                        headers=owner)[2])["pairing"]
        tab={"Origin":"https://chatgpt.com","Content-Type":"application/json",
             "X-Fortis-Dispatch-Key":pairing["dispatch_key"]}
        self.assertEqual(self.request(f"/api/dispatch/poll?session={sid}&chat={chat}",
                                      headers=tab)[0],200)
        profiles=[{"id":"default","name":"Обычный","module_ids":[]},
                  {"id":"repo","name":"Работа с Repo","module_ids":["policy.verification"]}]
        data=json.dumps({"session":sid,"chat":chat,
          "modules":[{"id":"policy.verification","title":"Проверка"}],
          "default_module_ids":["policy.verification"],
          "profiles":profiles,"active_profile_id":"repo"},ensure_ascii=False).encode()
        self.assertEqual(self.request("/api/dispatch/modules",headers=tab,
                                     method="POST",body=data)[0],200)
        self.assertEqual(self.request("/api/dispatch/status?session="+sid)[0],401)
        result=json.loads(self.request("/api/dispatch/status?session="+sid,
                                       headers=owner)[2])
        self.assertEqual(result["active_profile_id"],"repo")
        self.assertEqual(result["profiles"],profiles)
        self.assertNotIn("observer_key",str(result))
        self.assertNotIn("dispatch_key",str(result))
        invalid=json.dumps({"session":sid,"chat":chat,"mode":"insert",
                            "text":"Hello","module_ids":None,"profile_id":"unknown"}).encode()
        self.assertNotEqual(self.request("/api/dispatch",headers=owner,
                                         method="POST",body=invalid)[0],202)
        payload=json.dumps({"session":sid,"chat":chat,"mode":"insert",
                            "text":"Hello","module_ids":None,"profile_id":"default"}).encode()
        status,_,reply=self.request("/api/dispatch",headers=owner,method="POST",body=payload)
        self.assertEqual(status,202)
        polled=json.loads(self.request(f"/api/dispatch/poll?session={sid}&chat={chat}",
                                        headers=tab)[2])["command"]
        self.assertEqual(polled["profile_id"],"default")
        self.assertIsNone(polled["module_ids"])
        ack=json.dumps({"session":sid,"chat":chat,"dispatch_id":json.loads(reply)["dispatch_id"],
                        "status":"inserted","task_id":"task_"+"e"*32}).encode()
        self.assertEqual(self.request("/api/dispatch/ack",headers=tab,
                                      method="POST",body=ack)[0],200)

    def test_complete_notifier_diagnostic_appears_in_authorized_history(self):
        sid="rs_"+"a"*32; chat="abcdefgh-01234567"
        owner={"Authorization":"Bearer "+self.token,
               "Origin":f"http://127.0.0.1:{WIN_PORT}",
               "Content-Type":"application/json"}
        pairing=json.loads(self.request("/api/notifier-pair?session="+sid,
                                        headers=owner)[2])["pairing"]
        tab={"Origin":"https://chatgpt.com","Content-Type":"application/json",
             "X-Fortis-Dispatch-Key":pairing["dispatch_key"]}
        poll=f"/api/dispatch/poll?session={sid}&chat={chat}"
        self.assertEqual(self.request(poll,headers=tab)[0],200)
        enqueue=json.dumps({"session":sid,"chat":chat,"mode":"file",
                            "text":"SENSITIVE ORIGINAL MUST NEVER ENTER EVENT HISTORY",
                            "module_ids":None,"profile_id":None}).encode()
        status,_,response=self.request("/api/dispatch",headers=owner,
                                        method="POST",body=enqueue)
        self.assertEqual(status,202)
        dispatch_id=json.loads(response)["dispatch_id"]
        self.assertEqual(self.request(poll,headers=tab)[0],200)
        detail=("Файл прикреплён, но контекст не добавлен: "
                "Вставка не совпала с исходником посимвольно. "
                "Исходник сохранён; Send не нажимался. Не отправляй до ручной проверки.")
        data={"session":sid,"chat":chat,"dispatch_id":dispatch_id,
              "status":"attachment_only","task_id":None,
              "reason":"context_mismatch","detail":detail}
        evil={**data,"detail":detail+"\nSECRET"}
        self.assertEqual(self.request("/api/dispatch/ack",headers=tab,
                         method="POST",body=json.dumps(evil,ensure_ascii=False).encode())[0],403)
        self.assertEqual(self.request("/api/dispatch/ack",headers=tab,
                         method="POST",body=json.dumps(data,ensure_ascii=False).encode())[0],200)
        code,_,response=self.request("/api/dispatch/status?session="+sid,headers=owner)
        self.assertEqual(code,200)
        history=json.loads(response)["history"]
        self.assertEqual(history[-1]["detail"],detail)
        self.assertEqual(history[-1]["event"],"attachment_only")
        self.assertNotIn("SENSITIVE ORIGINAL MUST NEVER ENTER EVENT HISTORY",str(history))
        self.assertNotIn("detail",str(history[0]))
        self.assertNotIn("detail",str(history[1]))

    def test_prepared_send_http_is_one_shot_with_event_timeline(self):
        sid="rs_"+"a"*32;chat="abcdefgh-01234567";task="task_"+"e"*32
        owner={"Authorization":"Bearer "+self.token,
               "Origin":f"http://127.0.0.1:{WIN_PORT}",
               "Content-Type":"application/json"}
        pairing=json.loads(self.request("/api/notifier-pair?session="+sid,
                                        headers=owner)[2])["pairing"]
        tab={"Origin":"https://chatgpt.com","Content-Type":"application/json",
             "X-Fortis-Dispatch-Key":pairing["dispatch_key"]}
        poll=f"/api/dispatch/poll?session={sid}&chat={chat}"
        self.assertEqual(self.request(poll,headers=tab)[0],200)
        payload=json.dumps({"session":sid,"chat":chat,"mode":"send_prepared",
                            "text":"","module_ids":None,"profile_id":None}).encode()
        self.assertEqual(self.request('/api/dispatch',headers={
            **owner,"Authorization":"Bearer bad"},method="POST",body=payload)[0],401)
        status,_,response=self.request('/api/dispatch',headers=owner,
                                      method='POST',body=payload)
        self.assertEqual(status,202)
        dispatch_id=json.loads(response)["dispatch_id"]
        first=json.loads(self.request(poll,headers=tab)[2])["command"]
        self.assertEqual(first["mode"],"send_prepared")
        self.assertEqual(first["text"],"")
        self.assertIsNone(json.loads(self.request(poll,headers=tab)[2])["command"])
        ack=json.dumps({"session":sid,"chat":chat,"dispatch_id":dispatch_id,
                        "status":"send_initiated","task_id":task}).encode()
        self.assertEqual(self.request('/api/dispatch/ack',headers=tab,
                                      method='POST',body=ack)[0],200)
        self.assertNotEqual(self.request('/api/dispatch/ack',headers=tab,
                                         method='POST',body=ack)[0],200)
        meta=json.loads(self.request('/api/dispatch/status?session='+sid,
                                     headers=owner)[2])
        self.assertEqual(meta["dispatch"]["task_id"],task)
        self.assertEqual([h['event'] for h in meta['history']],
                         ['queued','claimed','send_initiated'])
        self.assertEqual(meta['history'][-1]['task_id'],task)
        self.assertNotIn('text',str(meta['history']))

    def test_notifier_scoped_activity_and_original_requests(self):
        sid="rs_"+"a"*32;task="task_"+"b"*32
        getpath="/api/task-activity?session="+sid+"&task="+task
        auth={"Origin":"https://chatgpt.com","X-Fortis-Observer-Key":"k"*48}
        self.assertEqual(self.request(getpath,headers=auth)[0],200)
        self.assertEqual(self.request(getpath,headers={"Origin":"https://evil.example",
                        "X-Fortis-Observer-Key":"k"*48})[0],403)
        self.assertEqual(self.request("/api/state",headers=auth)[0],403)
        self.assertEqual(self.request(getpath,headers={"Origin":"https://chatgpt.com",
                     "X-Fortis-Observer-Key":"invalid"})[0],403)
        exact="  Оригинал 🗂️\n\nне меняй "
        body=json.dumps({"reporting_session_id":sid,
            "conversation_id":"abcdefgh-01234567","task_id":task,
            "original_text":exact},ensure_ascii=False).encode("utf-8")
        headers={"Origin":"https://chatgpt.com",
                 "Content-Type":"application/json",
                 "X-Fortis-Message-Writer-Key":"w"*48}
        status,_,resp=self.request("/api/user-messages",headers,
                   method="POST",body=body)
        self.assertEqual(status,201)
        self.assertEqual(json.loads(resp)["task_id"],task)
        self.assertEqual(self.browser_calls[-1][3]["original_text"],exact)
        self.assertEqual(self.request("/api/user-messages",{
          **headers,"X-Fortis-Message-Writer-Key":"wrong"},method="POST",body=body)[0],403)
        self.assertEqual(self.request("/api/user-messages",{
          **headers,"Origin":"https://evil.example"},method="POST",body=body)[0],403)
        self.assertEqual(self.request("/api/user-messages",{
          **headers,"Origin":f"http://127.0.0.1:{WIN_PORT}"},method="POST",body=body)[0],403)
        self.assertEqual(self.request("/api/user-messages?evil=1",
          headers,method="POST",body=body)[0],403)
        self.assertEqual(self.request("/api/repo-history",headers,method="POST",body=body)[0],403)
        self.assertNotIn(exact.encode("utf-8"),self.request("/")[2])

    def test_viewer_accepts_exact_user_original_larger_than_64k(self):
        sid = "rs_" + "a" * 32
        task = "task_" + "b" * 32
        original = ("Длинный текст 🌐\\n" * 6500).rstrip()
        self.assertGreater(len(original.encode("utf-8")), 65536)
        request = json.dumps({
            "reporting_session_id": sid,
            "conversation_id": "abcdefgh-01234567",
            "task_id": task,
            "original_text": original
        }, ensure_ascii=False).encode("utf-8")
        status, _, payload = self.request("/api/user-messages", headers={
            "Origin": "https://chatgpt.com",
            "X-Fortis-Message-Writer-Key": "w" * 48,
            "Content-Type": "application/json"
        }, method="POST", body=request)
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(payload)["task_id"], task)
        self.assertEqual(self.browser_calls[-1][3]["original_text"], original)

    def test_unauthorized_guest_cannot_see_archive(self):
        sid="rs_"+"a"*32; task="task_"+"b"*32
        for path in ("/api/state",f"/api/history?session={sid}&task={task}"):
            status,_,raw=self.request(path)
            self.assertEqual(status,401)
            self.assertNotIn(b"original_text",raw)
        self.assertFalse(self.recorded)
        status,_,_=self.request("/api/state",headers={"Authorization":"Bearer wrong"})
        self.assertEqual(status,401)
        self.assertFalse(self.recorded)

    def test_authenticated_state_and_full_exact_unicode_history(self):
        head={"Authorization":"Bearer "+self.token}
        status,_,raw=self.request("/api/state",headers=head)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(raw)["sessions"][0]["title"],"Synthetic Session")
        sid="rs_"+"a"*32; task="task_"+"b"*32
        status,_,tasks=self.request(f"/api/tasks?session={sid}",headers=head)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(tasks)["task_ids"],[task])
        status,_,raw=self.request(f"/api/history?session={sid}&task={task}",headers=head)
        self.assertEqual(status,200)
        obj=json.loads(raw)
        self.assertEqual(obj["original_text"],"<img src=x onerror=alert(1)>")
        self.assertIn("Привет ✨",obj["assistant_messages"][0]["body"])
        self.assertEqual(self.recorded,[("state",None,None),("tasks",sid,None),("history",sid,task)])

    def test_reject_untrusted_origin_host_methods_route(self):
        auth={"Authorization":"Bearer "+self.token}
        for props in ({"Origin":"https://evil.example"},
                      {"Host":"127.0.0.1:9999"},
                      {"Sec-Fetch-Site":"cross-site"}):
            self.assertEqual(self.request("/api/state",headers={**auth,**props})[0],403)
        self.assertEqual(self.request("/api/state",headers=auth,method="POST")[0],403)
        self.assertEqual(self.request("/api/state",headers=auth,method="OPTIONS")[0],405)
        for path in ("/api/owner-token", "/api/observer-pair", "/api/user-messages",
                     "/api/tasks?session=wrong", "/api/history?session=wrong&task=wrong",
                     "/api/history?session=rs_"+"a"*32+"&task=task_"+"b"*32+"&evil=1"):
            self.assertNotEqual(self.request(path,headers=auth)[0],200,path)
        self.assertFalse(self.recorded)

    def test_self_registration_from_edge_and_instruction_fetch(self):
        auth={"Authorization":"Bearer "+self.token,
              "Origin":f"http://127.0.0.1:{WIN_PORT}",
              "Content-Type":"application/json"}
        url="https://chatgpt.com/c/abcdefgh-01234567"
        body=json.dumps({"url":url,"title":"Моя работа"}).encode("utf-8")
        status,_,result=self.request("/api/register",headers=auth,method="POST",body=body)
        self.assertEqual(status,201)
        self.assertEqual(json.loads(result)["session"],"rs_"+"e"*32)
        self.assertEqual(self.registrations,[(url,"Моя работа")])
        self.assertIn(b'id="registerForm"',PAGE.encode())
        self.assertIn(b'id="copyInstructions"',PAGE.encode())
        self.assertIn(b'/api/instructions?session=',PAGE.encode())

    def test_registration_requires_owner_token_and_exact_origin(self):
        url="https://chatgpt.com/c/abcdefgh-01234567"
        body=json.dumps({"url":url,"title":"Test"}).encode()
        good={"Origin":f"http://127.0.0.1:{WIN_PORT}",
              "Content-Type":"application/json"}
        attempts=[
            (good,401),
            ({**good,"Authorization":"Bearer wrong"},401),
            ({"Authorization":"Bearer "+self.token,"Content-Type":"application/json"},403),
            ({**good,"Authorization":"Bearer "+self.token,
              "Origin":"https://evil.example"},403),
            ({**good,"Authorization":"Bearer "+self.token,
              "Sec-Fetch-Site":"cross-site"},403),
            ({**good,"Authorization":"Bearer "+self.token,
              "Host":"127.0.0.1:9999"},403),
            ({**good,"Authorization":"Bearer "+self.token,
              "Content-Type":"text/plain"},415),
        ]
        for headers,wanted in attempts:
            self.assertEqual(self.request("/api/register",headers,method="POST",body=body)[0],wanted)
        self.assertEqual(self.registrations,[])

    def test_registration_rejects_extra_actions_and_bad_urls(self):
        valid={"Authorization":"Bearer "+self.token,
               "Origin":f"http://127.0.0.1:{WIN_PORT}",
               "Content-Type":"application/json"}
        for payload in (
            {"url":"https://evil.example/c/abcdefgh-01234567","title":"Test"},
            {"url":"http://chatgpt.com/c/abcdefgh-01234567","title":"Test"},
            {"url":"https://chatgpt.com/c/abcdefgh-01234567","title":"hello token"},
            {"url":"https://chatgpt.com/c/abcdefgh-01234567","title":"Invalid\nLine"},
            {"url":"https://chatgpt.com/c/abcdefgh-01234567","title":"Test",
             "route":"owner"},
        ):
            response=self.request("/api/register",valid,method="POST",
                                  body=json.dumps(payload).encode())
            self.assertEqual(response[0],400,payload)
        okbody=json.dumps({"url":"https://chatgpt.com/c/abcdefgh-01234567",
                           "title":"Test"}).encode()
        self.assertEqual(self.request("/api/owner-token",valid,method="POST",body=okbody)[0],404)
        self.assertEqual(self.request("/api/register?route=owner",valid,method="POST",body=okbody)[0],404)
        self.assertEqual(self.registrations,[])

    def test_cli_register_uses_only_selected_repo_container_and_dedupes(self):
        cid="abcdefgh-01234567"
        known={"reporting_session_id":"rs_"+"a"*32,
               "task_id":"task_"+"b"*32,
               "conversation_id":cid,"route":"repo"}
        calls=[]
        def runner(cmd,**kwargs):
            calls.append(cmd)
            if cmd[-1]=="state":
                result={"ok":True,"sessions":[known]}
            elif "register" in cmd:
                result={"reporting_session_id":"rs_"+"c"*32,
                        "session_task_id":"task_"+"d"*32,
                        "conversation_id":cid,"route":"repo"}
            else:
                result={"ok":True,"sessions":[]}
            return subprocess.CompletedProcess(cmd,0,
                        stdout=json.dumps(result,ensure_ascii=False).encode("utf-8"))
        url="https://chatgpt.com/c/"+cid
        reused=repo_register("approved-container",url,"Project",runner=runner)
        self.assertFalse(reused["created"])
        self.assertEqual(reused["session"],known["reporting_session_id"])
        self.assertEqual(len(calls),1)
        def empty_then_create(cmd,**kwargs):
            calls.append(cmd)
            if cmd[-1]=="state":
                result={"ok":True,"sessions":[]}
            else:
                result={"reporting_session_id":"rs_"+"c"*32,
                        "session_task_id":"task_"+"d"*32,
                        "conversation_id":cid,"route":"repo"}
            return subprocess.CompletedProcess(cmd,0,stdout=json.dumps(result).encode())
        calls.clear()
        created=repo_register("approved-container",url,"Project",runner=empty_then_create)
        self.assertTrue(created["created"])
        self.assertEqual(calls[1][:5],
                         ["docker.exe","exec","approved-container","python3",DOCKER_SERVICE])
        self.assertEqual(calls[1][5:],["register","--chat-id",cid,"--title","Project"])
        for arg in ("https://evil.example/","--","Injected\nargs"):
            with self.assertRaises(ValueError):
                valid_registration(arg,"Project")

    def test_instructions_scoped_to_valid_session_id(self):
        sid="rs_"+"a"*32
        calls=[]
        def runner(cmd,**kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd,0,stdout="Fortis Repo: тест".encode())
        obj=repo_read("approved-container","instructions",sid,runner=runner)
        self.assertEqual(obj["session"],sid)
        self.assertIn("Fortis Repo",obj["text"])
        self.assertEqual(calls[0][-4:],[DOCKER_SERVICE,"instructions","--session",sid])
        with self.assertRaises(ValueError):
            repo_read("approved-container","instructions","bad",runner=runner)

    def test_fixed_docker_exec_argv_and_readonly_export(self):
        argv_seen=[]
        def runner(cmd, **kwargs):
            argv_seen.append(cmd)
            if cmd[-1]=="state":
                out={"ok":True,"sessions":[]}
            else:
                out={"ok":True,"original_text":"exact AI",
                     "session":"rs_"+"a"*32, "task_id":"task_"+"b"*32}
            return subprocess.CompletedProcess(cmd,0,stdout=json.dumps(out).encode())
        result=repo_read("approved-container","history",
                         "rs_"+"a"*32, "task_"+"b"*32,runner=runner)
        self.assertEqual(result["original_text"],"exact AI")
        cmd=argv_seen[0]
        self.assertEqual(cmd[:4],["docker.exe","exec","approved-container","python3"])
        self.assertEqual(cmd[4],DOCKER_READER)
        self.assertNotIn("exact AI"," ".join(cmd))
        with self.assertRaises(ValueError):
            repo_read("approved-container","history","bad","task_"+"b"*32,runner=runner)
        with self.assertRaises(ValueError):
            repo_read("approved-container","delete",runner=runner)
        with self.assertRaises(ValueError):
            docker_command("--malicious",["hello"],runner=runner)

    def test_manual_service_start_only_if_stopped(self):
        calls=[]
        def already(cmd,**kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd,0,stdout=b'{"state":"running"}')
        self.assertEqual(ensure_repo_running("approved-container",runner=already),"already_running")
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][-2:],[DOCKER_SERVICE,"status"])

        calls.clear()
        def stopped_then_running(cmd,**kwargs):
            calls.append(cmd)
            if cmd[2:4]==["-d","approved-container"]:
                return subprocess.CompletedProcess(cmd,0,stdout=b"")
            if len(calls)==1:
                return subprocess.CompletedProcess(cmd,1,stdout=b"")
            return subprocess.CompletedProcess(cmd,0,stdout=b'{"state":"running"}')
        self.assertEqual(ensure_repo_running("approved-container",runner=stopped_then_running),"started")
        self.assertEqual(calls[1][0:4],["docker.exe","exec","-d","approved-container"])
        self.assertIn("run",calls[1])

    def test_edge_opening_uses_url_without_any_secret(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"Microsoft"/"Edge"/"Application"/"msedge.exe"
            path.parent.mkdir(parents=True)
            path.write_text("synthetic executable", encoding="utf-8")
            launches=[]
            def spawn(argv, **kwargs):
                launches.append((argv,kwargs))
                return None
            url="http://127.0.0.1:18755/"
            ok=open_owner_edge(url,environ={"PROGRAMFILES":folder},launch=spawn)
            self.assertTrue(ok)
            self.assertEqual(launches[0][0],[str(path),url])
            self.assertNotIn(self.token," ".join(launches[0][0]))
            self.assertNotIn("/api/history"," ".join(launches[0][0]))

    def test_no_owner_windows_install_from_repo_linux(self):
        with self.assertRaises(ValueError):
            read_owner_config(platform="linux")

if __name__=="__main__":
    unittest.main()
