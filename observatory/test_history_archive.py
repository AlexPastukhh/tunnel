"""Source-only synthetic archive and download tests. No real key or guest files."""
import csv
import http.client
from http.server import ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch
from urllib.parse import quote
from zipfile import ZipFile

import history_archive as a
import server


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "archive.sqlite3"
        self.now = time.time()

    def row(self, time_value=None, secret="synthetic_super_private_NEVER_EXPORT"):
        return {"sampled_at": time_value or self.now, "state": "UP", "verified": True,
                "mcp_state": "initialized", "private_key": secret,
                "metrics": {"polled_total": 14, "queue_length": 0,
                            "command_latency_avg_ms": 52.5, "raw_secret": secret}}

    def test_sanitized_archive_and_csv_download(self):
        secret="synthetic_super_private_NEVER_EXPORT"
        a.insert_telemetry(self.db, "g2", self.row())
        a.insert_telemetry(self.db, "repo", self.row(secret=secret))
        data,manifest=a.export_zip(self.db,None,None,("g2","repo"),"csv",{"g2":"unconfigured","repo":"configured"})
        self.assertEqual(manifest["telemetry_samples"],2)
        self.assertEqual(manifest["activity_events"],0)
        self.assertEqual(manifest["activity_sources"]["g2"],"unconfigured")
        with ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(set(z.namelist()), {"manifest.json","metrics.csv","tool_activity.csv"})
            body=z.read("metrics.csv").decode("utf-8-sig")
            self.assertNotIn(secret,body)
            self.assertNotIn("raw_secret",body)
            self.assertNotIn("private_key",body)
            records=list(csv.DictReader(io.StringIO(body)))
            self.assertEqual([x["route"] for x in records],["g2","repo"])
            self.assertEqual(records[0]["queue_length"],"0.0")
            self.assertIn("gapped periods", z.read("manifest.json").decode().lower())

    def test_minute_dedup_json_range(self):
        at=(int(self.now)//60)*60+5
        a.insert_telemetry(self.db,"repo",self.row(at))
        a.insert_telemetry(self.db,"repo",self.row(at+1))
        a.insert_telemetry(self.db,"repo",self.row(at+60))
        self.assertEqual(a.coverage(self.db)["telemetry"]["count"],2)
        z,info=a.export_zip(self.db,at-1,at+30,("repo",),"json")
        with ZipFile(io.BytesIO(z)) as archive:
            rows=json.loads(archive.read("metrics.json"))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]["route"],"repo")
        self.assertEqual(info["telemetry_samples"],1)

    def test_tool_metadata_never_exposes_raw_commands(self):
        records=[{"route":"g2","event_id":"abcdef0123456789",
                  "timestamp":a._iso(self.now),"tool":"start_process","kind":"terminal",
                  "duration_ms":40,"outcome":"unverified","command_present":True,
                  "command":"echo secret_DO_NOT_SHARE","arguments":{"key":"SECRET"}},
                 {"route":"g2","event_id":"abcdef0123456789",
                  "timestamp":a._iso(self.now),"tool":"start_process","kind":"terminal"}]
        a.insert_activity(self.db,records)
        self.assertEqual(a.coverage(self.db)["activity"]["count"],1)
        blob,manifest=a.export_zip(self.db,None,None,("g2",))
        with ZipFile(io.BytesIO(blob)) as archive:
            raw=archive.read("tool_activity.csv")
            self.assertIn(b"start_process",raw)
            self.assertNotIn(b"secret_DO_NOT_SHARE",raw)
            self.assertNotIn(b"SECRET",raw)
            self.assertNotIn(b"echo",raw)
        self.assertEqual(manifest["activity_events"],1)

    def test_retention_and_date_rejections(self):
        old=self.now-a.RETENTION_SECONDS+100
        a.insert_telemetry(self.db,"g2",self.row(old))
        a.prune(self.db,self.now+200)
        self.assertEqual(a.coverage(self.db)["telemetry"]["count"],0)
        with self.assertRaises(ValueError):
            a.export_zip(self.db,self.now,self.now-1,("repo",))
        with self.assertRaises(ValueError):
            a.export_zip(self.db,self.now-91*86400,self.now,("repo",))
        with self.assertRaises(ValueError):
            a.export_zip(self.db,None,None,("bad_route",))
        with self.assertRaises(ValueError):
            a.export_zip(self.db,None,None,("g2",),"raw")
        with self.assertRaises(ValueError):
            a.timestamp("2026-10-16T11:00:00")
        self.assertGreater(a.timestamp("2026-10-16T11:00:00Z"),0)

    def test_http_export_and_rejections(self):
        a.insert_telemetry(self.db,"repo",self.row())
        with patch.object(server,"ARCHIVE_DB",self.db), \
             patch.dict(server.AUDIT_SOURCES,{},clear=True):
            instance=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
            thread=Thread(target=instance.serve_forever,daemon=True)
            thread.start()
            try:
                client=http.client.HTTPConnection("127.0.0.1",instance.server_port,timeout=3)
                client.request("GET","/api/archive-coverage")
                reply=client.getresponse()
                info=json.loads(reply.read())
                self.assertEqual(reply.status,200)
                self.assertEqual(info["telemetry"]["count"],1)
                self.assertEqual(info["activity_sources"]["g2"],"unconfigured")
                client.request("GET","/api/export-history?mode=all&routes=repo&format=csv",
                               headers={"Sec-Fetch-Site":"cross-site"})
                blocked=client.getresponse()
                blocked.read()
                self.assertEqual(blocked.status,403)
                client.request("GET","/api/export-history?mode=all&routes=repo&format=csv")
                result=client.getresponse()
                blob=result.read()
                self.assertEqual(result.status,200)
                self.assertEqual(result.getheader("Content-Type"),"application/zip")
                self.assertIn("attachment;",result.getheader("Content-Disposition"))
                with ZipFile(io.BytesIO(blob)) as archive:
                    data=archive.read("metrics.csv").decode()
                    self.assertIn("repo",data)
                    self.assertNotIn("synthetic_super_private",data)
                from urllib.parse import urlencode
                filters=urlencode({"mode":"range","routes":"repo","format":"json",
                    "from":a._iso(self.now-60),"to":a._iso(self.now+60)})
                client.request("GET","/api/export-history?"+filters)
                valid=client.getresponse()
                self.assertEqual(valid.status,200)
                with ZipFile(io.BytesIO(valid.read())) as archive:
                    self.assertEqual(len(json.loads(archive.read("metrics.json"))),1)
                client.request("GET","/api/export-history?mode=range&routes=repo")
                bad=client.getresponse()
                self.assertEqual(bad.status,400)
                self.assertEqual(json.loads(bad.read())["error"],"invalid_export_filters")
                client.request("GET","/api/export-history?mode=all&routes=evil")
                bad=client.getresponse()
                self.assertEqual(bad.status,400)
                bad.read()
                client.close()
            finally:
                instance.shutdown()
                instance.server_close()
                thread.join(timeout=3)


if __name__=="__main__":
    unittest.main()
