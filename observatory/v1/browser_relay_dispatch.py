"""Narrow, credential-forwarding browser relay helper, executed *inside* Repo Docker.

Input: one small JSON envelope on stdin, no argv secrets. Output: one JSON
{status, body} envelope. Only the two read-only per-session endpoints and the
per-session conditional user-original writer are accessible. In particular no
Docker owner HTTP bearer, archive/history, enrollment, pairing or admin API.
"""
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

SID_RE = re.compile(r"rs_[0-9a-f]{32}\Z")
TASK_RE = re.compile(r"task_[0-9a-f]{32}\Z")
KEY_RE = re.compile(r"[A-Za-z0-9_-]{40,70}\Z")
MAX_RAW = 4 * 1024 * 1024
UPSTREAM = "http://127.0.0.1:18754"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def validate(data):
    if not isinstance(data, dict) or set(data) != {"method", "path", "key", "body"}:
        raise ValueError("bad_envelope")
    method, path, key, body = (data[k] for k in ("method", "path", "key", "body"))
    if not isinstance(path, str) or len(path) > 280 or not isinstance(key, str):
        raise ValueError("bad_request")
    if not KEY_RE.fullmatch(key):
        raise ValueError("invalid_capability")
    uri = urlsplit(path)
    if uri.scheme or uri.netloc or uri.fragment:
        raise ValueError("untrusted_uri")
    if method == "GET":
        if uri.path not in ("/api/task-activity", "/api/observer-status") or body is not None:
            raise ValueError("forbidden_route")
        parsed = parse_qs(uri.query, strict_parsing=True, keep_blank_values=True)
        expected = {"session", "task"} if uri.path == "/api/task-activity" else {"session"}
        if set(parsed) != expected or any(len(v) != 1 for v in parsed.values()):
            raise ValueError("bad_query")
        if not SID_RE.fullmatch(parsed["session"][0]) or (
            "task" in expected and not TASK_RE.fullmatch(parsed["task"][0])):
            raise ValueError("bad_ids")
        headers = {"X-Fortis-Observer-Key": key}
        payload = None
    elif method == "POST" and uri.path in ("/api/task-intents", "/api/task-send-state"):
        from owner_notifier_bridge import validate_task_metadata
        if uri.query:
            raise ValueError("forbidden_query")
        validate_task_metadata(uri.path, body)
        headers = {"X-Fortis-Task-Intent-Key": key, "Content-Type": "application/json"}
        payload = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    elif method == "POST":
        if uri.path != "/api/user-messages" or uri.query:
            raise ValueError("forbidden_route")
        if not isinstance(body, dict) or set(body) != {
                "reporting_session_id", "conversation_id", "task_id", "original_text"}:
            raise ValueError("bad_body")
        if not SID_RE.fullmatch(str(body.get("reporting_session_id"))) or not TASK_RE.fullmatch(
                str(body.get("task_id"))):
            raise ValueError("bad_ids")
        if not isinstance(body["conversation_id"], str) or not re.fullmatch(
                r"[A-Za-z0-9-]{8,100}", body["conversation_id"]):
            raise ValueError("bad_conversation")
        if not isinstance(body["original_text"], str) or not body["original_text"].strip() or len(
                body["original_text"].encode("utf-8")) > 512 * 1024:
            raise ValueError("invalid_original")
        headers = {"X-Fortis-Message-Writer-Key": key, "Content-Type": "application/json"}
        payload = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        if len(payload) > 4 * 1024 * 1024:
            raise ValueError("too_large")
    else:
        raise ValueError("unsupported_method")
    return method, path, headers, payload


def forward(data, opener=None, upstream=UPSTREAM):
    try:
        method, path, headers, payload = validate(data)
    except (ValueError, TypeError):
        return {"status": 403, "body": {"ok": False, "error": "relay_refused"}}
    try:
        request = Request(upstream + path, data=payload, headers=headers, method=method)
        client = opener or build_opener(NoRedirect())
        try:
            response = client.open(request, timeout=4)
        except HTTPError as error:
            response = error
        with response:
            code = response.status
            raw = response.read(160001)
        if len(raw) > 160000 or code not in (200, 201, 400, 401, 403, 404, 409, 503):
            raise ValueError("unsafe_reply")
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("invalid_reply")
        # No raw request payload or capability in the returned result.
        return {"status": code, "body": result}
    except (ValueError, TypeError, URLError, TimeoutError, OSError, UnicodeError):
        return {"status": 503, "body": {"ok": False, "error": "relay_upstream_unavailable"}}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_RAW + 1)
        if len(raw) > MAX_RAW:
            raise ValueError("envelope_too_large")
        data = json.loads(raw.decode("utf-8"))
        response = forward(data)
    except (ValueError, TypeError, UnicodeError):
        response = {"status": 403, "body": {"ok": False, "error": "relay_refused"}}
    # stdout is the only IPC reply; no logging raw user text or secret keys.
    sys.stdout.write(json.dumps(response, ensure_ascii=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
