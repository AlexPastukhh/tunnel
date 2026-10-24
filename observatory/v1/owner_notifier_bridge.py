"""Windows-owner viewer's NARROW Notifier original transport via existing Repo Docker.

No owner bearer, archive reads, generic docker commands, or Windows archive.
Credentials and exact original travel in docker exec STDIN, never argv or logs.
Pairing is explicitly revealed only to the owner-authenticated UI action.
"""
import json
import re
import subprocess

SID = re.compile(r"rs_[0-9a-f]{32}\Z")
CHAT = re.compile(r"[A-Za-z0-9-]{8,100}\Z")
TASK = re.compile(r"task_[0-9a-f]{32}\Z")
KEY = re.compile(r"[A-Za-z0-9_-]{40,70}\Z")
CONTAINER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,119}\Z")
LOCAL_ORIGIN = "http://127.0.0.1:18755"
PAIR_HELPER = "/workspace/repos/tunnel/observatory/v1/repo_browser_pair.py"
RELAY_HELPER = "/workspace/repos/tunnel/observatory/v1/browser_relay_dispatch.py"


def owner_pair(container, sid, executor=subprocess.run, docker_cli="docker.exe",
               task_intents=False):
    if not isinstance(container, str) or not CONTAINER.fullmatch(container) or (
            not isinstance(sid, str) or not SID.fullmatch(sid)):
        raise ValueError("invalid_pair_request")
    argv = [docker_cli, "exec", container, "python3", PAIR_HELPER,
            "--session", sid, "--writer"]
    if task_intents:
        argv.append("--task-intents")
    result = executor(argv, capture_output=True, timeout=12, check=False)
    if result.returncode or len(result.stdout) > 4096:
        raise ValueError("pair_unavailable")
    obj = json.loads(result.stdout.decode("utf-8"))
    if (not isinstance(obj, dict) or obj.get("reporting_session_id") != sid or
            not CHAT.fullmatch(obj.get("conversation_id") or "") or
            obj.get("origin") != "http://127.0.0.1:18754" or
            not KEY.fullmatch(obj.get("observer_key") or "") or
            not KEY.fullmatch(obj.get("message_writer_key") or "")):
        raise ValueError("invalid_pair")
    if task_intents and not KEY.fullmatch(obj.get("task_intent_key") or ""):
        raise ValueError("invalid_intent_pair")
    return {**obj, "origin": LOCAL_ORIGIN}


def scoped_request(container, method, path, key, body=None,
                   executor=subprocess.run, docker_cli="docker.exe"):
    if not isinstance(container, str) or not CONTAINER.fullmatch(container):
        raise ValueError("bad_container")
    if not isinstance(key, str) or not KEY.fullmatch(key):
        raise ValueError("invalid_capability")
    if method == "GET":
        from urllib.parse import urlsplit, parse_qs
        uri = urlsplit(path)
        expected = ({"session", "task"} if uri.path == "/api/task-activity" else
                    {"session"} if uri.path == "/api/observer-status" else None)
        if uri.scheme or uri.netloc or uri.fragment or not expected or body is not None:
            raise ValueError("forbidden_get")
        parsed = parse_qs(uri.query, strict_parsing=True)
        if (set(parsed) != expected or any(len(v) != 1 for v in parsed.values())
                or not SID.fullmatch(parsed["session"][0]) or
                ("task" in expected and not TASK.fullmatch(parsed["task"][0]))):
            raise ValueError("bad_get")
    elif method == "POST" and path in ("/api/task-intents", "/api/task-send-state"):
        validate_task_metadata(path, body)
    elif method == "POST":
        if path != "/api/user-messages" or not isinstance(body, dict) or set(body) != {
                "reporting_session_id", "conversation_id", "task_id", "original_text"}:
            raise ValueError("bad_user_post")
        if (not SID.fullmatch(str(body["reporting_session_id"])) or
                not CHAT.fullmatch(str(body["conversation_id"])) or
                not TASK.fullmatch(str(body["task_id"])) or
                not isinstance(body["original_text"], str) or
                not body["original_text"].strip() or
                len(body["original_text"].encode("utf-8")) > 512 * 1024):
            raise ValueError("bad_original")
    else:
        raise ValueError("forbidden_method")
    envelope = json.dumps({"method": method, "path": path, "key": key,
                           "body": body}, ensure_ascii=True).encode("ascii")
    if len(envelope) > 4 * 1024 * 1024:
        raise ValueError("too_large")
    result = executor([docker_cli, "exec", "-i", container, "python3", RELAY_HELPER],
                      input=envelope, capture_output=True, timeout=12, check=False)
    if result.returncode != 0 or len(result.stdout) > 180000:
        raise ValueError("relay_unavailable")
    reply = json.loads(result.stdout.decode("utf-8"))
    status, data = reply.get("status"), reply.get("body")
    if status not in (200, 201, 400, 401, 403, 404, 409, 503) or not isinstance(data, dict):
        raise ValueError("bad_relay_response")
    return status, data


def validate_task_metadata(path, body):
    """Pure allowlist shared by Windows bridge and Repo relay; no text fields."""
    fields = {"version", "reporting_session_id", "conversation_id", "task_id"}
    if path == "/api/task-intents":
        fields |= {"prepared_at_client_ms"}
        timestamp = "prepared_at_client_ms"
    elif path == "/api/task-send-state":
        fields |= {"revision", "phase", "observed_at_client_ms"}
        timestamp = "observed_at_client_ms"
    else:
        raise ValueError("forbidden_metadata_route")
    if (not isinstance(body, dict) or set(body) != fields or
            type(body.get("version")) is not int or body["version"] != 1 or
            not isinstance(body["reporting_session_id"], str) or not SID.fullmatch(body["reporting_session_id"]) or
            not isinstance(body["conversation_id"], str) or not CHAT.fullmatch(body["conversation_id"]) or
            not isinstance(body["task_id"], str) or not TASK.fullmatch(body["task_id"]) or
            type(body[timestamp]) is not int or not 0 < body[timestamp] < 4102444800000):
        raise ValueError("invalid_task_metadata")
    if path == "/api/task-send-state" and (
            type(body["revision"]) is not int or not 1 <= body["revision"] <= 1000000 or
            not isinstance(body["phase"], str) or body["phase"] not in {
                "send_requested", "send_unconfirmed", "send_observed", "send_not_attempted"}):
        raise ValueError("invalid_send_metadata")
    if len(json.dumps(body, ensure_ascii=True).encode("ascii")) > 1024:
        raise ValueError("metadata_too_large")
