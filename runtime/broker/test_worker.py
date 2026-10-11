#!/usr/bin/env python3
"""Offline security and flow tests. No real GitHub, Windows worker, or snapshots."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import uuid
import zipfile

DIR = Path(__file__).resolve().parent
def load(name):
    spec = importlib.util.spec_from_file_location(name, DIR / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="broker-v1-offline-")
        self.addCleanup(self.tmp.cleanup)
        r = Path(self.tmp.name)
        for sub in ("private", "claims", "requests", "in", "out", "repos/safe"):
            (r / sub).mkdir(parents=True, exist_ok=True)
        w = load("worker")
        self.w = w
        w.ROOT, w.CLAIMS, w.JOURNAL = r/"private", r/"claims", r/"requests"
        w.INBOX, w.OUTBOX = r/"in", r/"out"
        w.REPO_ROOT, w.REGISTRY = r/"repos", r/"registry.json"
        w.PERMITS, w.STATE = w.ROOT/"permits.json", w.ROOT/"issued-snapshots.json"
        w.REGISTRY.write_text(json.dumps({"repositories": {
            "safe": {"path": str(r/"repos"/"safe"), "transport": "private_bridge",
                     "transport_repository": "AlexPastukhh/chatgpt-snapshot-transfer", "export_enabled": True},
            "public": {"path": str(r/"repos"/"safe"), "transport": "public_synthetic_test_only",
                       "classification": "synthetic", "export_enabled": True}
        }}))
        self.sha, self.calls = "a"*64, []
        def pretend(action, **kw):
            self.calls.append((action, kw))
            if action == "preview":
                return {"status":"preview", "repo_alias":kw["repo"],
                        "transport_repository":"AlexPastukhh/chatgpt-snapshot-transfer",
                        "selection_sha256":self.sha, "selected_files":2, "selected_bytes":18,
                        "selected_sample":["a.txt","b.txt"],"over_total_limit":False,
                        "over_file_limit":[]}
            if action == "snapshot":
                return {"status":"waiting_artifact","snapshot_id":kw["snapshot_id"]}
            if action == "status":
                return {"status":"ready", "snapshot_id":kw["snapshot_id"],"artifact_id":333}
            if action == "list":return {"repositories":[]}
            raise AssertionError("unexpected operation")
        w.bridge = pretend
    def req(self, op, **kw):
        return {"version":1, "id":str(uuid.uuid4()), "op":op, **kw}
    def test_no_export_without_specific_grant(self):
        with self.assertRaises(PermissionError):
            self.w.handle(self.req("snapshot",repo="safe"))
        self.assertEqual(len([n for n, _ in self.calls if n == "snapshot"]), 0)
    def test_reviewed_bytes_binding_one_use_and_recovery(self):
        with self.assertRaises(PermissionError):
            self.w.grant("safe",5,"b"*64)
        grant = self.w.grant("safe",5,self.sha)
        self.assertEqual(grant["selected_sample"],["a.txt","b.txt"])
        request = self.req("snapshot",repo="safe")
        first = self.w.handle(request)
        self.assertEqual(first["status"],"waiting_artifact")
        duplicate = self.w.handle(request)
        self.assertEqual(duplicate["result"]["status"],"ready")
        recovered = self.w.handle(self.req("recover",request_id=request["id"]))
        self.assertEqual(recovered["snapshot_id"],first["snapshot_id"])
        self.assertEqual(recovered["result"]["artifact_id"],333)
        self.assertEqual(len([n for n,_ in self.calls if n=="snapshot"]),1)
        with self.assertRaises(PermissionError):
            self.w.handle(self.req("snapshot",repo="safe"))
    def test_public_transport_denied_before_any_permit(self):
        with self.assertRaises(PermissionError):
            self.w.grant("public",5,self.sha)
        with self.assertRaises(PermissionError):
            self.w.handle(self.req("snapshot",repo="public"))
    def test_invalid_operation_denied(self):
        with self.assertRaises(ValueError):
            self.w.handle(self.req("exec", command="whoami"))
    def test_standing_alias_repeat_snapshot_without_permit(self):
        config=json.loads(self.w.REGISTRY.read_text())
        config["repositories"]["safe"]["broker_snapshot_enabled"]=True
        self.w.REGISTRY.write_text(json.dumps(config))
        for _ in range(2):
            response=self.w.handle(self.req("snapshot",repo="safe"))
            self.assertEqual(response["status"],"waiting_artifact")
        snapshots=[kw for name,kw in self.calls if name=="snapshot"]
        self.assertEqual(len(snapshots),2)
        self.assertEqual([kw["expected_selection_sha256"] for kw in snapshots],[self.sha,self.sha])
        journals=[json.loads(p.read_text()) for p in self.w.JOURNAL.glob("*.json")]
        self.assertEqual([j["authorization"] for j in journals],["standing_alias","standing_alias"])
        self.assertFalse(self.w.PERMITS.exists())

    def test_standing_optin_must_be_boolean_and_private(self):
        for invalid in ("true",1,[],None):
            config=json.loads(self.w.REGISTRY.read_text())
            config["repositories"]["safe"]["broker_snapshot_enabled"]=invalid
            self.w.REGISTRY.write_text(json.dumps(config))
            with self.assertRaises(PermissionError):
                self.w.handle(self.req("snapshot",repo="safe"))
        config["repositories"]["safe"]["broker_snapshot_enabled"]=True
        config["repositories"]["public"]["broker_snapshot_enabled"]=True
        self.w.REGISTRY.write_text(json.dumps(config))
        with self.assertRaises(PermissionError):
            self.w.handle(self.req("snapshot",repo="public"))
        self.assertFalse(any(n=="snapshot" for n,_ in self.calls))

    def test_legacy_export_enabled_never_implies_standing_approval(self):
        # The pre-existing V1 export_enabled flag alone must not grant standing rights.
        config=json.loads(self.w.REGISTRY.read_text())
        self.assertTrue(config["repositories"]["safe"]["export_enabled"])
        self.assertNotIn("broker_snapshot_enabled",config["repositories"]["safe"])
        with self.assertRaises(PermissionError):
            self.w.handle(self.req("snapshot",repo="safe"))
        self.assertFalse(any(n=="snapshot" for n,_ in self.calls))

    def test_policy_mode_conflict_rejected_before_export(self):
        config=json.loads(self.w.REGISTRY.read_text())
        config["repositories"]["safe"].update({
            "broker_snapshot_enabled":True,
            "snapshot_ignore_file":"policies/safe.snapshotignore",
            "selection_mode":"all",
        })
        self.w.REGISTRY.write_text(json.dumps(config))
        with self.assertRaisesRegex(PermissionError,"snapshot_ignore_requires_exclude_mode"):
            self.w.handle(self.req("snapshot",repo="safe"))
        self.assertFalse(any(n=="snapshot" for n,_ in self.calls))
        # An explicitly configured exclude mode is allowed.
        config["repositories"]["safe"]["selection_mode"]="exclude"
        self.w.REGISTRY.write_text(json.dumps(config))
        self.assertEqual(self.w.handle(self.req("snapshot",repo="safe"))["status"],"waiting_artifact")

    def test_replay_after_interrupted_standing_snapshot_uses_journal(self):
        config=json.loads(self.w.REGISTRY.read_text())
        config["repositories"]["safe"]["broker_snapshot_enabled"]=True
        self.w.REGISTRY.write_text(json.dumps(config))
        original=self.w.bridge
        calls=[]
        def interrupted(action, **kw):
            if action=="snapshot":
                calls.append(kw)
                raise RuntimeError("simulated transport result lost")
            return original(action,**kw)
        self.w.bridge=interrupted
        request=self.req("snapshot",repo="safe")
        with self.assertRaises(RuntimeError):
            self.w.handle(request)
        journal=json.loads((self.w.JOURNAL/(request["id"]+".json")).read_text())
        self.assertEqual(journal["state"],"uncertain")
        self.assertEqual(len(calls),1)
        # On retry original UUID returns status, without a second publication.
        self.w.bridge=original
        prior=self.w.handle(request)
        self.assertEqual(prior["operation"],"snapshot")
        self.assertEqual(prior["result"]["status"],"ready")
        self.assertEqual(len(calls),1)

    def test_standing_revoke_stops_new_snapshot_without_rewriting_history(self):
        config=json.loads(self.w.REGISTRY.read_text())
        config["repositories"]["safe"]["broker_snapshot_enabled"]=True
        self.w.REGISTRY.write_text(json.dumps(config))
        self.assertEqual(self.w.handle(self.req("snapshot",repo="safe"))["status"],"waiting_artifact")
        config["repositories"]["safe"]["broker_snapshot_enabled"]=False
        self.w.REGISTRY.write_text(json.dumps(config))
        with self.assertRaisesRegex(PermissionError,"snapshot_requires_single_use_windows_approval"):
            self.w.handle(self.req("snapshot",repo="safe"))
        self.assertEqual(len([n for n,_ in self.calls if n=="snapshot"]),1)

    def test_interrupted_claim_does_not_repeat_snapshot(self):
        req=self.req("snapshot",repo="safe")
        claim=self.w.CLAIMS/(req["id"]+".json")
        claim.write_text(json.dumps(req))
        self.w.run_once()
        answer=json.loads((self.w.OUTBOX/(req["id"]+".json")).read_text())
        self.assertFalse(answer["ok"])
        self.assertEqual(len([n for n,_ in self.calls if n=="snapshot"]),0)

class ZipTests(unittest.TestCase):
    def test_archive_validation(self):
        v=load("verify_artifact")
        with tempfile.TemporaryDirectory(prefix="broker-zip-offline-") as dirname:
            root=Path(dirname)
            data={"README.md":b"test","src/file.txt":b"hello"}
            manifest={"snapshot_id":"mock-sid-20261011","files":[{"path":k,
                      "bytes":len(value),"sha256":hashlib.sha256(value).hexdigest()}
                      for k,value in data.items()]}
            manifest["selection_sha256"] = hashlib.sha256(json.dumps(
                [(entry["path"],entry["sha256"],entry["bytes"]) for entry in manifest["files"]],
                ensure_ascii=False,separators=(",", ":")).encode("utf-8")).hexdigest()
            for mode in ("good","extra","modified","traversal","symlink","wrong-selection"):
                arc=root/(mode+".zip")
                with zipfile.ZipFile(arc,"w") as z:
                    for name, value in data.items():
                        z.writestr("repo/"+name,b"altered" if mode=="modified" and name=="README.md" else value)
                    z.writestr("_bridge/manifest.json",json.dumps(manifest))
                    if mode=="extra":z.writestr("repo/extra",b"extra")
                    if mode=="traversal":z.writestr("../outside.txt",b"unsafe")
                    if mode=="symlink":
                        entry=zipfile.ZipInfo("repo/link")
                        entry.create_system=3
                        entry.external_attr=(stat.S_IFLNK|0o777)<<16
                        z.writestr(entry,"README.md")
                output=root/("dest-"+mode)
                if mode=="good":
                    report=v.verify(arc,output,manifest["snapshot_id"],manifest["selection_sha256"])
                    self.assertEqual(report["files"],2)
                    self.assertEqual((output/"repo/README.md").read_bytes(),b"test")
                else:
                    with self.assertRaises(ValueError):
                        v.verify(arc,output,manifest["snapshot_id"],
                                 "f"*64 if mode=="wrong-selection" else manifest["selection_sha256"])
                    self.assertFalse(output.exists())

if __name__=="__main__":
    unittest.main(verbosity=2)