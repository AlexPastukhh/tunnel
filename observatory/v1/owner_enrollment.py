"""Owner-approved, durable per-chat Tampermonkey enrollment.

An unauthenticated localhost claimant NEVER receives capabilities until the
owner has approved that exact 256-bit claimant in the owner-bearer Viewer.
Only SHA-256 digests survive restart, under the already owner-ACL-protected
Windows Viewer directory. Commands remain transient and at-most-once.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import threading
import time

CHAT = re.compile(r"[A-Za-z0-9-]{8,100}\Z")
SID = re.compile(r"rs_[0-9a-f]{32}\Z")
PROOF = re.compile(r"[0-9a-f]{64}\Z")
MAX_PENDING = 32
MAX_DISCOVERED = 200
PENDING_TTL = 180
APPROVED_LIVE_TTL = 25  # Notifier enroll heartbeat every 7 sec; do not show 3-min stale tabs.
FILENAME = "approved-notifiers.json"


def tab_title(value):
    """Optional private display text, never an archive title or identity."""
    if value is None:
        return None
    if (not isinstance(value, str) or len(value) > 128 or
            len(value.encode("utf-8")) > 512 or
            re.search(r"[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]", value)):
        raise ValueError("invalid_tab_title")
    return value.strip()



class Enrollment:
    def __init__(self, directory, pairing, clock=time.monotonic):
        self.directory = Path(directory)
        self.path = self.directory / FILENAME
        self.pairing = pairing  # sid -> owner_pair(..), never called before approval
        self.clock = clock
        self.lock = threading.RLock()
        self.pending = {}
        self.discovered = {}
        self.approved_titles = {}
        self.approved_live = {}  # transient heartbeat per approved session
        self.cached_pair = {}
        self.approved = self._load()

    def _load(self):
        if self.path.is_symlink():
            raise ValueError("enrollment_symlink_denied")
        if not self.path.exists():
            return {}
        if self.path.stat().st_size > 64000:
            raise ValueError("enrollment_oversized")
        raw = json.loads(self.path.read_text(encoding="ascii"))
        if not isinstance(raw, dict) or raw.get("version") != 1 or not isinstance(raw.get("grants"), dict):
            raise ValueError("enrollment_invalid")
        grants = raw["grants"]
        if len(grants) > 256 or any(not SID.fullmatch(sid) or
            not isinstance(v, dict) or set(v) not in ({"chat", "sha256"}, {"chat", "sha256", "task_intents"}) or
            ("task_intents" in v and type(v["task_intents"]) is not bool) or
            not CHAT.fullmatch(v["chat"]) or not PROOF.fullmatch(v["sha256"])
            for sid,v in grants.items()):
            raise ValueError("enrollment_invalid_grants")
        return grants

    def _save(self):
        if self.path.is_symlink() or not self.directory.is_dir() or self.directory.is_symlink():
            raise ValueError("enrollment_path_denied")
        payload = json.dumps({"version":1,"grants":self.approved},sort_keys=True,separators=(",",":"))
        temp = self.directory / ("."+FILENAME+".new")
        if temp.exists() or temp.is_symlink():
            raise ValueError("enrollment_temp_collision")
        fd = os.open(temp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd,"w",encoding="ascii") as out:
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp,self.path)
        finally:
            if temp.exists(): temp.unlink()

    def _prune(self):
        limit=self.clock()-PENDING_TTL
        for key,value in list(self.pending.items()):
            if value["created"] < limit:
                del self.pending[key]
        for key, value in list(self.discovered.items()):
            if value["last_seen"] < limit:
                del self.discovered[key]

        for sid, entry in list(self.approved_titles.items()):
            if sid not in self.approved or entry["last_seen"] < limit:
                del self.approved_titles[sid]
        for sid, stamp in list(self.approved_live.items()):
            if sid not in self.approved or stamp < self.clock() - APPROVED_LIVE_TTL:
                del self.approved_live[sid]

    def _remember_discovery(self, chat, digest, title=None):
        # Current-tab presence only. Titles stay in owner memory, not approvals.
        for sid, grant in self.approved.items():
            if grant["chat"] == chat and hmac.compare_digest(grant["sha256"], digest):
                self.approved_live[sid] = self.clock()
                self.discovered.pop((chat, digest), None)
                if title is not None:
                    self.approved_titles[sid] = {"title": title, "last_seen": self.clock()}
                return
        key = (chat, digest)
        if key in self.discovered or len(self.discovered) < MAX_DISCOVERED:
            prior = self.discovered.get(key, {})
            self.discovered[key] = {"last_seen": self.clock(),
                                    "title": prior.get("title", "") if title is None else title}

    def discover(self, chat, proof, title=None):
        if not isinstance(chat, str) or not CHAT.fullmatch(chat):
            raise ValueError("invalid_discovery_chat")
        title = tab_title(title)
        digest = self._hash(proof)
        with self.lock:
            self._prune()
            self._remember_discovery(chat, digest, title)
        # Backward compatible reply. Discovery is not registration or approval.
        return {"ok": True, "status": "not_registered"}

    def discovered_for_owner(self):
        with self.lock:
            self._prune()
            grouped = {}
            for (chat, digest), entry in self.discovered.items():
                item = grouped.setdefault(chat, {"chat": chat, "fingerprints": [],
                                                "last_seen_seconds_ago": PENDING_TTL,
                                                "blocked": False, "title": entry.get("title", "")})
                if item["title"] != entry.get("title", ""):
                    item["title"] = ""
                item["fingerprints"].append(digest[:12])
                item["last_seen_seconds_ago"] = min(item["last_seen_seconds_ago"],
                    max(0, int(self.clock() - entry["last_seen"])))
                item["blocked"] = any(g["chat"] == chat for g in self.approved.values())
            for item in grouped.values():
                item["fingerprints"].sort()
            return {"ok": True, "chats": sorted(grouped.values(),
                     key=lambda i: (i["last_seen_seconds_ago"], i["chat"])),
                    "available_sessions": sorted(self.approved_live),
                    "connected_sessions": sorted(self.approved),
                    "session_titles": {sid: entry["title"] for sid, entry in self.approved_titles.items()
                                       if entry["title"]}}

    def connect_discovered(self, chat, fingerprint, register, valid_session):
        """Explicit owner click: exact fresh claimant, registration, then approval.

        The handler serializes registration, supplies trusted callbacks, and
        requires the owner bearer + same origin. No capability is returned.
        """
        if (not isinstance(chat, str) or not CHAT.fullmatch(chat) or
                not isinstance(fingerprint, str) or
                not re.fullmatch(r"[a-f0-9]{12}", fingerprint)):
            raise ValueError("invalid_discovery_selection")
        with self.lock:
            self._prune()
            # An exact completed retry is read-only/idempotent, even if the
            # original successful response was lost or the tab has since closed.
            approved = [(sid, g) for sid, g in self.approved.items()
                        if g["chat"] == chat and g["sha256"].startswith(fingerprint)]
            if len(approved) == 1:
                sid, grant = approved[0]
                if valid_session(sid, chat):
                    return {"ok": True, "created": False, "session": sid,
                            "conversation_id": chat, "approved": True,
                            "task_intents": grant.get("task_intents", False)}
            matches = [(digest, entry) for (cid, digest), entry in self.discovered.items()
                       if cid == chat]
            if (len(matches) != 1 or not matches[0][0].startswith(fingerprint) or
                    any(g["chat"] == chat for g in self.approved.values())):
                raise ValueError("discovery_missing_ambiguous_or_granted")
            digest, _ = matches[0]
            if len(self.pending) >= MAX_PENDING:
                raise ValueError("enrollment_busy")
            result = register("https://chatgpt.com/c/" + chat, "ChatGPT " + chat[:12])
            if (not isinstance(result, dict) or result.get("ok") is not True or
                    type(result.get("created")) is not bool or
                    result.get("conversation_id") != chat or
                    not isinstance(result.get("session"), str) or
                    not SID.fullmatch(result["session"]) or
                    not valid_session(result["session"], chat)):
                raise ValueError("discovery_registration_mismatch")
            sid = result["session"]
            self.pending[(sid, digest)] = {"chat": chat, "created": self.clock()}
            self.approve(sid, chat, fingerprint, valid_session)
            self.discovered.pop((chat, digest), None)
            return {"ok": True, "created": result["created"], "session": sid,
                    "conversation_id": chat, "approved": True,
                    "task_intents": False}

    @staticmethod
    def _hash(proof):
        if not isinstance(proof,str) or not PROOF.fullmatch(proof):
            raise ValueError("invalid_claimant_proof")
        return hashlib.sha256(bytes.fromhex(proof)).hexdigest()

    def announce(self, sid, chat, proof, valid_session, title=None):
        if not SID.fullmatch(sid or "") or not CHAT.fullmatch(chat or "") or not valid_session(sid,chat):
            raise ValueError("unknown_session")
        title = tab_title(title)
        digest = self._hash(proof)
        with self.lock:
            self._prune()
            self._remember_discovery(chat, digest, title)
            granted=self.approved.get(sid)
            if granted and granted["chat"]==chat and hmac.compare_digest(granted["sha256"],digest):
                # Owner already approved this exact client; no new grant merely by URL.
                if sid not in self.cached_pair:
                    self.cached_pair[sid] = self.pairing(sid)
                return {"ok":True,"status":"approved","pairing":self.cached_pair[sid]}
            # Ignore other clients if one approved: require explicit owner revoke.
            if granted:
                return {"ok":True,"status":"already_approved_for_other_client"}
            key=(sid,digest)
            if key not in self.pending:
                if len(self.pending)>=MAX_PENDING:
                    return {"ok":True,"status":"enrollment_busy"}
                self.pending[key]={"chat":chat,"created":self.clock()}
            return {"ok":True,"status":"awaiting_owner"}

    def pending_for(self,sid):
        if not SID.fullmatch(sid or ""): raise ValueError("bad_session")
        with self.lock:
            self._prune()
            items=[{"fingerprint":digest[:12],"chat":entry["chat"]}
                   for (session,digest),entry in self.pending.items() if session==sid]
            return {"ok":True,"session":sid,"pending":items,
                    "approved":sid in self.approved,
                    "task_intents":self.approved.get(sid,{}).get("task_intents",False)}

    def approve(self,sid,chat,fingerprint,valid_session):
        if (not SID.fullmatch(sid or "") or not CHAT.fullmatch(chat or "") or
            not isinstance(fingerprint,str) or not re.fullmatch(r"[a-f0-9]{12}",fingerprint) or
            not valid_session(sid,chat)):
            raise ValueError("invalid_approval")
        with self.lock:
            self._prune()
            matches=[(digest,item) for (session,digest),item in self.pending.items()
                     if session==sid and digest.startswith(fingerprint) and item["chat"]==chat]
            if len(matches)!=1 or sid in self.approved:
                raise ValueError("approval_not_unique_or_existing")
            digest,_=matches[0]
            self.approved[sid]={"chat":chat,"sha256":digest}
            try:self._save()
            except Exception:
                del self.approved[sid]
                raise
            title = self.discovered.get((chat, digest), {}).get("title", "")
            if title:
                self.approved_titles[sid] = {"title": title, "last_seen": self.clock()}
            self.discovered.pop((chat, digest), None)
            # Stop any competing claimant from reusing pending approvals.
            self.pending={key:value for key,value in self.pending.items() if key[0]!=sid}
            return {"ok":True,"approved":True,"session":sid}

    def enable_task_intents(self, sid, chat, valid_session):
        if (not SID.fullmatch(sid or "") or not CHAT.fullmatch(chat or "") or
                not valid_session(sid, chat)):
            raise ValueError("invalid_intent_grant")
        with self.lock:
            prior = self.approved.get(sid)
            if not prior or prior["chat"] != chat:
                raise ValueError("approved_notifier_required")
            self.approved[sid] = {**prior, "task_intents": True}
            try:
                self._save()
            except Exception:
                self.approved[sid] = prior
                raise
            self.cached_pair.pop(sid, None)
            return {"ok": True, "session": sid, "task_intents": True}

    def revoke(self,sid):
        if not SID.fullmatch(sid or ""): raise ValueError("bad_session")
        with self.lock:
            removed=self.approved.pop(sid,None)
            try:self._save()
            except Exception:
                if removed is not None:self.approved[sid]=removed
                raise
            self.pending={key:value for key,value in self.pending.items() if key[0]!=sid}
            self.cached_pair.pop(sid,None)
            self.approved_titles.pop(sid, None)
            self.approved_live.pop(sid, None)
            return {"ok":True,"revoked":removed is not None}
