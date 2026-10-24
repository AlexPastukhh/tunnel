"""Sensitive pairing never printed in ChatGPT. Synthetic Docker stdout only."""
import json
import subprocess
import unittest

from owner_notifier_bridge import owner_pair, scoped_request, LOCAL_ORIGIN, PAIR_HELPER, RELAY_HELPER

SID='rs_'+'a'*32
TASK='task_'+'b'*32
CHAT='abcdefff-1234'
KEY='k'*48
WRITER='w'*48


class NarrowOwnerBrowserBridge(unittest.TestCase):
    def test_explicit_owner_pair_retargets_only_transport_origin(self):
        seen=[]
        sample={"version":1,"origin":"http://127.0.0.1:18754",
                "conversation_id":CHAT,"reporting_session_id":SID,
                "observer_key":KEY,"message_writer_key":WRITER}
        def fake(argv,**kwargs):
            seen.append(argv)
            return subprocess.CompletedProcess(argv,0,stdout=json.dumps(sample).encode())
        pair=owner_pair("fortis-repo-test",SID,executor=fake)
        self.assertEqual(pair["origin"],LOCAL_ORIGIN)
        self.assertEqual(pair["reporting_session_id"],SID)
        self.assertEqual(pair["message_writer_key"],WRITER)
        self.assertEqual(seen[0],["docker.exe","exec","fortis-repo-test",
                                  "python3",PAIR_HELPER,"--session",SID,"--writer"])
        for bad in ("../evil","--privileged",""):
            with self.assertRaises(ValueError):
                owner_pair(bad,SID,executor=fake)
        with self.assertRaises(ValueError):
            owner_pair("fortis-repo-test","wrong",executor=fake)

    def test_original_and_keys_are_stdin_only_and_routes_fixed(self):
        seen=[]
        original="  мой  🔒\\n<private>\\n"
        body={"reporting_session_id":SID,"conversation_id":CHAT,
              "task_id":TASK,"original_text":original}
        def fake(argv,**kwargs):
            seen.append((argv,kwargs))
            return subprocess.CompletedProcess(argv,0,stdout=json.dumps({
                "status":201,"body":{"ok":True,"task_id":TASK}
            }).encode())
        status,receipt=scoped_request("fortis-repo-test","POST","/api/user-messages",
                 WRITER,body,executor=fake)
        self.assertEqual(status,201)
        self.assertEqual(receipt["task_id"],TASK)
        argv,kw=seen[0]
        self.assertEqual(argv,["docker.exe","exec","-i","fortis-repo-test",
                                "python3",RELAY_HELPER])
        self.assertNotIn(WRITER," ".join(argv))
        self.assertNotIn(original," ".join(argv))
        envelope=json.loads(kw["input"])
        self.assertEqual(envelope["body"]["original_text"],original)
        self.assertEqual(envelope["key"],WRITER)
        self.assertEqual(scoped_request("fortis-repo-test","GET",
                 "/api/task-activity?session="+SID+"&task="+TASK,KEY,
                 executor=fake)[0],201)
        self.assertEqual(scoped_request("fortis-repo-test","GET",
                 "/api/observer-status?session="+SID,KEY,executor=fake)[0],201)

    def test_never_exposes_private_archive_or_generic_admin_routes(self):
        def deny(*args,**kwargs):
            self.fail("Denied route must not call Docker!")
        for method,path,key,body in [
            ("GET","/api/repo-history?session="+SID+"&task="+TASK,KEY,None),
            ("GET","/api/state",KEY,None),
            ("GET","/api/message-writer-pair?session="+SID,KEY,None),
            ("GET","/api/task-activity?session=wrong&task="+TASK,KEY,None),
            ("POST","/api/register",WRITER,{}),
            ("POST","/api/user-messages",WRITER,{
                "reporting_session_id":SID,"conversation_id":CHAT,
                "task_id":TASK,"original_text":"x"*(512*1024+1)}),
            ("POST","/api/user-messages",WRITER,{
                "reporting_session_id":SID,"conversation_id":CHAT,
                "task_id":TASK,"original_text":""})
        ]:
            with self.assertRaises(ValueError):
                scoped_request("fortis-repo-test",method,path,key,body,executor=deny)


if __name__=="__main__":
    unittest.main()
