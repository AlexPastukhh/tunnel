"""Cross-user HTTP boundary regression using synthetic token and fake data.

Does not use real Windows processes, guest ACLs, owner files, or actual API keys.
Native owner and guest acceptance must occur separately after authorized start.
"""
import http.client
from http.server import ThreadingHTTPServer
import json
from threading import Thread
import unittest
from unittest.mock import patch

import server

TEST_TOKEN="SYNTHETIC_TEST_ONLY_OWNER_BEARER_256_BITS_NOT_REAL"
API_READS=(
    "/api/session",
    "/api/tunnels",
    "/api/activity?limit=10",
    "/api/archive-coverage",
    "/api/export-history?mode=all&routes=repo&format=json",
    "/api/repo-status",
    "/api/repo-history?minutes=10",
    "/api/g2-history?minutes=10",
    "/api/snapshot",
    "/api/history?minutes=10",
    "/api/incidents",
    "/api/incidents/timeout-20261016T010101.123456Z",
    "/api/incidents/timeout-20261016T010101.123456Z/export",
)


class OwnerApiBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.patch=patch.object(server,"OWNER_AUTH_TOKEN",TEST_TOKEN)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.server=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
        self.thread=Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup_server)

    def cleanup_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def req(self,method,path,headers=None,body=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=3)
        conn.request(method,path,body=body,headers=headers or {})
        r=conn.getresponse()
        payload=r.read()
        status=r.status
        hdrs=dict(r.getheaders())
        conn.close()
        return status,payload,hdrs

    def test_guest_without_token_cannot_access_any_api_even_safe_get(self):
        # Unauthorized calls must not reach privileged handlers.
        with patch.object(server,"native_tunnels",side_effect=AssertionError("privileged function called")), \
             patch.object(server,"create_incident",side_effect=AssertionError("mutated incident")):
            for path in API_READS:
                with self.subTest(path=path):
                    status,data,headers=self.req("GET",path)
                    self.assertEqual(status,401)
                    self.assertNotIn(b"archive",data)
            status,data,_=self.req("POST","/api/incidents",{"Content-Type":"application/json"},'{"note":"canary"}')
            self.assertEqual(status,401)
            status,data,_=self.req("HEAD","/api/export-history")
            self.assertEqual(status,401)
            self.assertEqual(data,b"")

    def test_stale_and_fake_host_and_cross_site_tokens_rejected(self):
        statuses=(
            {"Authorization":"Bearer wrong-token"},
            {"Authorization":"Basic " + TEST_TOKEN},
            {"Authorization":"Bearer "+TEST_TOKEN,"Host":"outside.example"},
            {"Authorization":"Bearer "+TEST_TOKEN,"Sec-Fetch-Site":"cross-site"},
        )
        for headers in statuses:
            with self.subTest(headers=tuple(headers.keys())):
                status,_,_=self.req("GET","/api/session",headers)
                self.assertEqual(status,401)

    def test_authorized_owner_can_read_synthetic_api_data(self):
        auth={"Authorization":"Bearer "+TEST_TOKEN}
        code,body,headers=self.req("GET","/api/session",auth)
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)["role"],"owner-authorized")
        self.assertIn("default-src 'none'",headers["Content-Security-Policy"])
        with patch.object(server,"native_tunnels",return_value={"ok":True,"repo":{"state":"UP"},"g2":{"state":"UNKNOWN"}}):
            status,data,_=self.req("GET","/api/tunnels",auth)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)["repo"]["state"],"UP")
        self.assertNotIn(TEST_TOKEN.encode(),body+data)

    def test_noninteractive_owner_launch_refused_without_side_effects(self):
        from types import SimpleNamespace
        with patch.object(server.sys, "stdin", SimpleNamespace(isatty=lambda: False)), \
             patch.object(server, "OWNER_AUTH_TOKEN", None):
            with self.assertRaises(SystemExit) as result:
                server.main()
            self.assertIn("interactive owner console", str(result.exception))
            self.assertIsNone(server.OWNER_AUTH_TOKEN)

    def test_disabled_by_default_and_no_token_leak_from_static(self):
        with patch.object(server,"OWNER_AUTH_TOKEN",None):
            status,_,_=self.req("GET","/api/session",{"Authorization":"Bearer "+TEST_TOKEN})
        self.assertEqual(status,401)
        for path in ("/index.html","/app.js"):
            status,body,_=self.req("GET",path)
            self.assertEqual(status,200)
            self.assertNotIn(TEST_TOKEN.encode(),body)
        status,_,_=self.req("GET","/server.py")
        self.assertEqual(status,404)


if __name__=="__main__":
    unittest.main()
