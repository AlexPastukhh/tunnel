"""Unified Fortis Repo Observatory: events, user originals and assistant text.

Runs only inside Fortis Repo Docker on container loopback. Plain chat text in
the internal Repo volume is accessible to authorized Repo tool processes;
NOT owner-Windows-private. Does not auto-start with Docker.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import sys
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from server import Application, handler_for, repo_bootstrap
from store import _dir
from repo_messages import RepoMessages
from repo_pending import poll_pending

DEFAULT_ROOT = Path("/workspace/repo/fortis-observatory-repo-v1")
DEFAULT_PORT = 18754
TOKEN_NAME = ".repo-http-token"


def confined(root):
    root = _dir(root)
    base = Path("/workspace/repo").resolve(strict=True)
    if not root.is_relative_to(base) or root == base:
        raise ValueError("repo_state_must_be_within_internal_volume")
    if sys.platform != "linux":
        raise ValueError("repo_service_linux_only")
    return root


def secure_folder(folder):
    if not folder.exists():
        folder.mkdir(mode=0o700, parents=True)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("unsafe_repo_state_directory")
    attrs = folder.stat()
    if attrs.st_uid != os.geteuid() or stat.S_IMODE(attrs.st_mode) != 0o700:
        raise ValueError("repo_state_requires_private_mode_0700")


def token_at(root, create):
    path = root / TOKEN_NAME
    if not path.exists() and create:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as out:
            out.write(secrets.token_urlsafe(40))
            out.flush()
            os.fsync(out.fileno())
    if path.is_symlink() or not path.is_file():
        raise ValueError("repo_token_not_available")
    attrs = path.stat()
    if attrs.st_uid != os.geteuid() or stat.S_IMODE(attrs.st_mode) != 0o600:
        raise ValueError("repo_token_must_be_private")
    tok = path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{40,90}", tok):
        raise ValueError("bad_repo_token")
    return tok


def serve(root, port):
    root = confined(root)
    os.umask(0o077)
    secure_folder(root)
    archive = root / "archive"
    inbox_base = root / "inbox"
    inbox = inbox_base / "repo"
    msg_inbox = inbox_base / "messages"
    quarantine = root / "quarantine"
    quarantined_messages = quarantine / "messages"
    for folder in (archive, inbox_base, inbox, msg_inbox, quarantine, quarantined_messages):
        secure_folder(folder)
    lock_file = root / ".service.lock"
    if lock_file.is_symlink():
        raise ValueError("linked_lock_refused")
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(fd, "r+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        token = token_at(root, True)
        app = Application(archive, {"repo": inbox},
                          {"repo": str(inbox)}, token,
                          allow_private_user_messages=True)
        app.repo_messages = RepoMessages(app.store, msg_inbox, quarantined_messages)
        server = ThreadingHTTPServer(("127.0.0.1", port), handler_for(app))
        pid = root / ".service.pid"
        if pid.is_symlink():
            raise ValueError("linked_pid_refused")
        pid.write_text(str(os.getpid()), encoding="ascii")
        pid.chmod(0o600)

        def poll():
            with app.lock:
                try:
                    poll_pending(root, app.store)
                    app.store.poll()
                    app.repo_messages.poll()
                except Exception:
                    app.store.recent_ingest = {
                        "state": "failed", "accepted": 0, "rejected": 0,
                        "duplicate": 0, "unknown_session": 0,
                        "deferred_session": 0, "retryable": 0, "error": 1,
                    }
        def sampler():
            while not app.stop.wait(3):
                poll()
        def shutdown(_signal, _frame):
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        poll()
        worker = threading.Thread(target=sampler, daemon=True)
        worker.start()
        print(f"REPO_OBSERVATORY_READY loopback=127.0.0.1:{port} "
              "repo_unified_archive=true full_messages=true", flush=True)
        try:
            server.serve_forever()
        finally:
            app.stop.set()
            server.server_close()
            worker.join(timeout=3)
            if pid.is_file() and pid.read_text(encoding="ascii").strip() == str(os.getpid()):
                pid.unlink()



def api_call(root, port, path, payload=None):
    token = token_at(confined(root), False)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "Bearer " + token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers,
                  method="POST" if data is not None else "GET")
    with urlopen(req, timeout=3) as response:
        return json.load(response)


def status(root, port):
    try:
        obj = api_call(root, port, "/api/state")
    except (HTTPError, URLError, TimeoutError) as err:
        print("REPO_OBSERVATORY_NOT_RESPONDING", type(err).__name__)
        return 1
    if not obj.get("ok"):
        print("REPO_OBSERVATORY_UNHEALTHY")
        return 1
    print(json.dumps({"state": "running", "port": port,
                      "sessions": len(obj.get("sessions", [])),
                      "ingest": obj.get("ingest", {}).get("state", "unknown"),
                      "unified_archive": "repo_volume", "user_writer": True,
                      "assistant_spool": True,
                      "messages_ingest": obj.get("messages_ingest", {})}))
    return 0


def sessions(root, port):
    obj = api_call(root, port, "/api/state")
    print(json.dumps({"sessions": [
        {"reporting_session_id": s["reporting_session_id"],
         "conversation_id": s["conversation_id"],
         "events_count": s["events_count"], "state": s["state"]}
        for s in obj.get("sessions", [])]}, ensure_ascii=False))
    return 0


def register(root, port, chat_id, title):
    if not chat_id or not re.fullmatch(r"[A-Za-z0-9-]{8,100}", chat_id):
        raise ValueError("chat_id_must_be_valid")
    obj = api_call(root, port, "/api/sessions",
                   {"url": "https://chatgpt.com/c/" + chat_id,
                    "route": "repo", "title": title})
    meta = obj["session"]
    print(json.dumps({"reporting_session_id": meta["reporting_session_id"],
                      "session_task_id": meta["task_id"],
                      "conversation_id": meta["conversation_id"],
                      "route": "repo", "archive": "repo_volume"}))
    return 0


def instructions(root, port, session_id):
    if not session_id or not re.fullmatch(r"rs_[0-9a-f]{32}", session_id):
        raise ValueError("bad_session_id")
    # Read the registered session from the Docker archive FIRST.
    # An already-running older Observatory HTTP process might still return
    # deprecated legacy prompt text with enrollment IDs. Never relay that
    # old text into an AI conversation for Repo sessions.
    from store import Store
    session = Store(confined(root) / "archive")._session(session_id)
    if session is None:
        raise ValueError("session_missing")
    if session.get("route") == "repo":
        print(repo_bootstrap())
        return 0
    # Non-Repo legacy routes retain their separate old Windows sender guides.
    obj = api_call(root, port, "/api/instructions?session=" + quote(session_id))
    print(obj["text"])
    return 0


def history(root, port, session_id, task_id):
    if not session_id or not re.fullmatch(r"rs_[0-9a-f]{32}", session_id):
        raise ValueError("bad_session_id")
    if not task_id or not re.fullmatch(r"task_[0-9a-f]{32}", task_id):
        raise ValueError("bad_task_id")
    obj = api_call(root, port, "/api/repo-history?session=" + quote(session_id) +
                   "&task=" + quote(task_id))
    print(json.dumps(obj, ensure_ascii=False))
    return 0


def archive_original(root, port, session_id, task_id, body):
    # Explicit Repo-local manual original writer for testing/integration.
    # Not a browser bridge and not an automatic retrieval from ChatGPT.
    if not re.fullmatch(r"rs_[0-9a-f]{32}", session_id or ""):
        raise ValueError("bad_session_id")
    if not re.fullmatch(r"task_[0-9a-f]{32}", task_id or ""):
        raise ValueError("bad_task_id")
    # Owner bearer exists only within the Docker Repo service. Fetch writer
    # capability via localhost without disclosing it to CLI output.
    pair = api_call(root, port, "/api/message-writer-pair?session=" + quote(session_id))["pairing"]
    req = Request(f"http://127.0.0.1:{port}/api/user-messages",
                  data=json.dumps({"reporting_session_id": session_id,
                                   "conversation_id": pair["conversation_id"],
                                   "task_id": task_id, "original_text": body},
                                  ensure_ascii=False).encode("utf-8"),
                  headers={"Content-Type": "application/json",
                           "X-Fortis-Message-Writer-Key": pair["message_writer_key"]},
                  method="POST")
    # The bearer is not required for this writer request.
    with urlopen(req, timeout=3) as response:
        receipt = json.load(response)
    print(json.dumps({"ok": receipt["ok"], "task_id": task_id,
                      "status": receipt["status"], "archived": receipt["archived"],
                      "sha256": receipt["sha256"]}))
    return 0


def stop(root):
    # Refuse to signal reused PID or other processes.
    root = confined(root)
    pid_file = root / ".service.pid"
    if pid_file.is_symlink() or not pid_file.is_file():
        raise ValueError("repo_service_pid_missing")
    pid = int(pid_file.read_text(encoding="ascii").strip())
    if pid <= 1:
        raise ValueError("invalid_pid")
    cmdline = Path("/proc") / str(pid) / "cmdline"
    if not cmdline.is_file():
        raise ValueError("repo_process_not_running")
    argv = cmdline.read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace")
    if "repo_service.py run" not in argv or "--state-dir " + str(root) not in argv:
        raise ValueError("repo_process_identity_mismatch")
    os.kill(pid, signal.SIGTERM)
    print("REPO_OBSERVATORY_STOP_SIGNAL_SENT", pid)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("run", "status", "sessions", "register", "bootstrap", "instructions",
                                           "history", "archive-original", "stop"))
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--chat-id", help="Conversation ID only, no message text")
    parser.add_argument("--title", default="Repo Session")
    parser.add_argument("--session", help="reporting_session_id")
    parser.add_argument("--task", help="per-message task ID for history/original")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("invalid_port")
    try:
        if args.action == "run":
            return serve(args.state_dir, args.port)
        if args.action == "status":
            return status(args.state_dir, args.port)
        if args.action == "sessions":
            return sessions(args.state_dir, args.port)
        if args.action == "register":
            return register(args.state_dir, args.port, args.chat_id, args.title)
        if args.action == "bootstrap":
            # The bootstrap deliberately needs NO session, owner bearer or
            # running HTTP service. No IDs are printed into chat history.
            print(repo_bootstrap())
            return 0
        if args.action == "instructions":
            return instructions(args.state_dir, args.port, args.session)
        if args.action == "history":
            return history(args.state_dir, args.port, args.session, args.task)
        if args.action == "archive-original":
            raw = sys.stdin.buffer.read(512 * 1024 + 1)
            if len(raw) > 512 * 1024:
                raise ValueError("original_too_large")
            return archive_original(args.state_dir, args.port, args.session,
                                    args.task, raw.decode("utf-8"))
        return stop(args.state_dir)
    except (ValueError, OSError, KeyError, HTTPError, URLError) as err:
        print("REPO_OBSERVATORY_ERROR", type(err).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
