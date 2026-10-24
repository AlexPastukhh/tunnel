"""Owner enrollment over localhost with fake repo, no real secrets or Windows."""
import hashlib
import json
from pathlib import Path
from http.server import ThreadingHTTPServer
import tempfile
import threading
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from owner_enrollment import Enrollment
from owner_dispatch import DispatchBoard
from owner_viewer import handler_for,WIN_PORT

CID="abcdefgh-01234567"
SID="rs_"+"a"*32
PROOF="b"*64
FP=hashlib.sha256(bytes.fromhex(PROOF)).hexdigest()[:12]

class HTTPEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dispatch=DispatchBoard()
        self.pair_calls=0
        def pair(sid):
            self.pair_calls+=1
            return {"version":1,"origin":f"http://127.0.0.1:{WIN_PORT}",
                "conversation_id":CID,"reporting_session_id":sid,
                "observer_key":"o"*48,"message_writer_key":"w"*48,
                "dispatch_key":self.dispatch.pair(sid,CID)}
        self.enrollment=Enrollment(self.tmp.name,pair)
        def read(kind,sid,task):
            return {"ok":True,"sessions":[{"conversation_id":CID,
                "reporting_session_id":SID,"route":"repo","title":"test"}]}
        self.bearer="synthetic_owner_bearer"
        self.srv=ThreadingHTTPServer(("127.0.0.1",0),
            handler_for(self.bearer,read,"nonce",None,None,None,
                        self.dispatch,self.enrollment))
        self.thread=threading.Thread(target=self.srv.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(lambda:self.thread.join(timeout=2))

    def req(self,path,body=None,auth=False,origin=None):
        headers={"Host":f"127.0.0.1:{WIN_PORT}"}
        if auth:headers["Authorization"]="Bearer "+self.bearer
        if origin:headers["Origin"]=origin
        if body is not None:
            headers["Content-Type"]="application/json"
            data=json.dumps(body).encode()
        else:data=None
        request=Request(f"http://127.0.0.1:{self.srv.server_port}"+path,
                        data=data,headers=headers)
        try:response=urlopen(request,timeout=5)
        except HTTPError as error:response=error
        with response:
            return response.status,json.loads(response.read())

    def test_owner_approval_and_reboot_without_menu_or_send(self):
        pending=self.req("/api/notifier/enroll",{"chat":CID,"proof":PROOF},
                         origin="https://chatgpt.com")
        self.assertEqual(pending[0],200)
        self.assertEqual(pending[1]["status"],"awaiting_owner")
        self.assertNotIn("pairing",pending[1])
        self.assertEqual(self.pair_calls,0)
        pending_path="/api/notifier/pending?session="+SID
        self.assertEqual(self.req(pending_path)[0],401)
        status,list_result=self.req(pending_path,auth=True)
        self.assertEqual(status,200)
        self.assertEqual(list_result["pending"][0]["fingerprint"],FP)
        self.assertNotIn(PROOF,json.dumps(list_result))
        approval={"session":SID,"chat":CID,"fingerprint":FP}
        self.assertEqual(self.req("/api/notifier/approve",approval)[0],403)
        self.assertEqual(self.req("/api/notifier/approve",approval,auth=True,
            origin="https://evil.example")[0],403)
        self.assertEqual(self.req("/api/notifier/approve",approval,auth=True,
            origin=f"http://127.0.0.1:{WIN_PORT}")[0],200)
        self.assertEqual(self.pair_calls,0)
        accepted=self.req("/api/notifier/enroll",{"chat":CID,"proof":PROOF},
                          origin="https://chatgpt.com")[1]
        self.assertEqual(accepted["status"],"approved")
        self.assertEqual(accepted["pairing"]["dispatch_key"],self.dispatch._sessions[SID]["key"])
        self.assertEqual(self.pair_calls,1)
        self.assertNotIn("observer_key",json.dumps(self.req(pending_path,auth=True)))
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":CID,"proof":"c"*64},origin="https://chatgpt.com")[1]["status"],
            "already_approved_for_other_client")
        stored=Path(self.tmp.name,"approved-notifiers.json").read_text()
        self.assertNotIn(PROOF,stored)
        after_reboot=Enrollment(self.tmp.name,lambda sid:{"reporting_session_id":sid})
        self.assertEqual(after_reboot.announce(SID,CID,PROOF,
            lambda sid,chat:sid==SID and chat==CID)["status"],"approved")
        self.assertEqual(self.req("/api/notifier/revoke",
            {"session":SID},auth=True,origin=f"http://127.0.0.1:{WIN_PORT}")[0],200)
        self.assertFalse(self.dispatch.status(SID)["paired"])
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":CID,"proof":PROOF},origin="https://chatgpt.com")[1]["status"],
            "awaiting_owner")

    def test_unregistered_no_capabilities_and_origin_boundaries(self):
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":"unknown-chat","proof":PROOF},origin="https://chatgpt.com")[1]["status"],
            "not_registered")
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":CID,"proof":PROOF},origin="https://evil.example")[0],403)
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":CID,"proof":"weak"},origin="https://chatgpt.com")[0],403)
        self.assertEqual(self.req("/api/notifier/enroll",
            {"chat":CID,"proof":PROOF,"unexpected":"field"},origin="https://chatgpt.com")[0],403)
        self.assertEqual(self.pair_calls,0)

if __name__=="__main__":unittest.main()
