"""Owner-side Windows-local narrow HTTP relay for Fortis Repo Docker.

NOT a second Observatory or archive. Review/pin/copy this script to an
owner-ACL-protected installation; it refuses execution from Repo RW source.
Before deployment, confirm the named Docker container and Windows guest
negative accessibility. This module alone never starts a service.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

WIN_PORT = 18754
UPSTREAM_HELPER = "/workspace/repos/tunnel/observatory/v1/browser_relay_dispatch.py"
PAIR_HELPER = "/workspace/repos/tunnel/observatory/v1/repo_browser_pair.py"
SID_RE = re.compile(r"rs_[0-9a-f]{32}\Z")
ALLOWED_ORIGINS = frozenset(("https://chatgpt.com", "https://chat.openai.com"))
KEY_RE = re.compile(r"[A-Za-z0-9_-]{40,70}\Z")
CONTAINER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,119}\Z")
MAX_REQUEST = 4 * 1024 * 1024


def request_guard(method, path, headers, body):
    if headers.get("Host") != f"127.0.0.1:{WIN_PORT}":
        return None
    origin = headers.get("Origin")
    if origin not in (None, *ALLOWED_ORIGINS):
        return None
    if headers.get("Transfer-Encoding") or headers.get("Authorization") or headers.get("Cookie"):
        return None
    if len(path) > 280 or not path.startswith("/api/"):
        return None
    uri = urlsplit(path)
    if uri.scheme or uri.netloc or uri.fragment:
        return None
    if method == "GET":
        if uri.path not in ("/api/observer-status", "/api/task-activity") or body is not None:
            return None
        key = headers.get("X-Fortis-Observer-Key")
        allowed = {"X-Fortis-Observer-Key", "Host", "Origin", "Referer", "Sec-Fetch-Site",
                   "Sec-Fetch-Mode", "Sec-Fetch-Dest", "Accept", "Accept-Encoding",
                   "User-Agent", "Connection"}
    elif method == "POST":
        if uri.path != "/api/user-messages" or uri.query:
            return None
        if not isinstance(body, bytes) or not 0 < len(body) <= MAX_REQUEST:
            return None
        if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return None
        key = headers.get("X-Fortis-Message-Writer-Key")
        allowed = {"X-Fortis-Message-Writer-Key", "Host", "Origin", "Referer", "Content-Type",
                   "Content-Length", "Sec-Fetch-Site", "Sec-Fetch-Mode",
                   "Sec-Fetch-Dest", "Accept", "Accept-Encoding",
                   "User-Agent", "Connection"}
    else:
        return None
    if not isinstance(key, str) or not KEY_RE.fullmatch(key):
        return None
    # Browsers/extensions add benign varying transport headers.
    # Do not forward *any* of them to Docker: forward only the pinned key.
    # Credential and injected Host/Origin are checked separately above.
    try:
        obj = json.loads(body.decode("utf-8")) if body is not None else None
    except (UnicodeError, ValueError, TypeError):
        return None
    return {"method": method, "path": path, "key": key, "body": obj}


def docker_exec(container, envelope, docker_cli="docker.exe", runner=subprocess.run):
    if not isinstance(container, str) or not CONTAINER_RE.fullmatch(container):
        raise ValueError("invalid_container")
    payload = json.dumps(envelope, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(payload) > 4 * 1024 * 1024:
        raise ValueError("too_large")
    # Fixed argv: no injected shell, API secrets, original body or query values.
    command = [docker_cli, "exec", "-i", container, "python3", UPSTREAM_HELPER]
    output = runner(command, input=payload, capture_output=True, timeout=8, check=False)
    if output.returncode != 0 or len(output.stdout) > 160000:
        raise ValueError("docker_unavailable")
    try:
        response = json.loads(output.stdout.decode("utf-8"))
        if (not isinstance(response, dict) or set(response) != {"status", "body"} or
                response["status"] not in (200, 201, 400, 401, 403, 404, 409, 503) or
                not isinstance(response["body"], dict)):
            raise ValueError("invalid_reply")
    except (ValueError, UnicodeError):
        raise ValueError("invalid_reply") from None
    return response


def handler_for(execute):
    class Handler(BaseHTTPRequestHandler):
        server_version = "FortisRepoNarrowRelay"
        sys_version = ""

        def log_message(self, fmt, *args):
            # NEVER write path, headers, secret capabilities, user text or body.
            pass

        def _json(self, code, body):
            encoded = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("ascii")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(encoded)

        def do_OPTIONS(self):
            self._json(405, {"ok": False, "error": "not_supported"})

        def do_HEAD(self):
            self._json(405, {"ok": False, "error": "not_supported"})

        def do_GET(self):
            self._dispatch(None)

        def do_POST(self):
            if self.headers.get("Transfer-Encoding"):
                self._json(403, {"ok": False, "error": "relay_refused"})
                return
            try:
                lengths = self.headers.get_all("Content-Length", [])
                if len(lengths) != 1 or not lengths[0].isdigit():
                    raise ValueError()
                size = int(lengths[0])
                if not 0 < size <= MAX_REQUEST:
                    raise ValueError()
                body = self.rfile.read(size)
                if len(body) != size:
                    raise ValueError()
            except (ValueError, OSError):
                self._json(403, {"ok": False, "error": "relay_refused"})
                return
            self._dispatch(body)

        def _dispatch(self, body):
            keys = ("X-Fortis-Observer-Key", "X-Fortis-Message-Writer-Key",
                    "Origin", "Host", "Authorization", "Cookie", "Transfer-Encoding")
            if any(len(self.headers.get_all(key, [])) > 1 for key in keys):
                self._json(403, {"ok": False, "error": "relay_refused"})
                return
            envelope = request_guard(self.command, self.path, dict(self.headers), body)
            if envelope is None:
                self._json(403, {"ok": False, "error": "relay_refused"})
                return
            try:
                response = execute(envelope)
            except (ValueError, OSError, subprocess.SubprocessError):
                self._json(503, {"ok": False, "error": "relay_unavailable"})
                return
            self._json(response["status"], response["body"])
    return Handler


def owner_pairing_code(container, session, writer=False, docker_cli="docker.exe",
                       runner=subprocess.run):
    """Output must go to owner console only, NEVER back to the bridge HTTP."""
    if not CONTAINER_RE.fullmatch(container or "") or not SID_RE.fullmatch(session or ""):
        raise ValueError("invalid_pairing_scope")
    cmd = [docker_cli, "exec", container, "python3", PAIR_HELPER,
           "--session", session]
    if writer:
        cmd.append("--writer")
    result = runner(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                    timeout=8, check=False)
    if result.returncode != 0 or len(result.stdout) > 1000:
        raise ValueError("pairing_unavailable")
    obj = json.loads(result.stdout.decode("ascii"))
    if (not isinstance(obj, dict) or obj.get("reporting_session_id") != session or
            obj.get("origin") != "http://127.0.0.1:18754" or
            not KEY_RE.fullmatch(obj.get("observer_key", "")) or
            (writer and not KEY_RE.fullmatch(obj.get("message_writer_key", "")) or
            (not writer and "message_writer_key" in obj))):
        raise ValueError("invalid_pairing_reply")
    return obj


def owner_readiness_guard(container=None):
    if sys.platform != "win32":
        raise ValueError("windows_only")
    local = Path(os.environ["LOCALAPPDATA"]).resolve()
    expected = local / "FortisObservatoryV1" / "Relay"
    source = Path(__file__).resolve()
    if source.parent != expected.resolve() or source.is_symlink() or expected.is_symlink():
        raise ValueError("run_from_pinned_owner_local_install_only")
    config_file = expected / "approved-owner.json"
    if (not config_file.is_file() or config_file.is_symlink() or
            config_file.stat().st_size > 2048):
        raise ValueError("owner_approval_config_required")
    config = json.loads(config_file.read_text(encoding="utf-8"))
    if (not isinstance(config, dict) or set(config) != {"owner_sid", "container"} or
            not isinstance(config["owner_sid"], str) or not re.fullmatch(
                r"S-1-5-(?:[0-9]+-){2,}[0-9]+", config["owner_sid"]) or
            not isinstance(config["container"], str) or
            not CONTAINER_RE.fullmatch(config["container"]) or
            config["container"] != container):
        raise ValueError("approved_owner_or_container_mismatch")
    # Verify the actual Windows process identity, not merely USERNAME/profile.
    who = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"],
                         capture_output=True, check=False, timeout=4)
    if who.returncode != 0:
        raise ValueError("cannot_verify_windows_identity")
    ids = re.findall(rb"S-1-5-(?:[0-9]+-){2,}[0-9]+", who.stdout)
    if len(ids) != 1 or ids[0].decode("ascii") != config["owner_sid"]:
        raise ValueError("not_approved_windows_owner")
    # The config itself MUST have independently verified NTFS ACL; a copied
    # config and SID comparison do not isolate against Docker-enabled guests.
    cli = shutil.which("docker.exe")
    if not cli:
        raise ValueError("docker_cli_not_available")
    return cli


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("serve", "pair"))
    parser.add_argument("--container", required=True, help="Reviewed exact Docker container name/ID")
    parser.add_argument("--session", help="Session ID, only for owner console pair action")
    parser.add_argument("--writer", action="store_true", help="Explicit per-session full-text writer grant")
    args = parser.parse_args(argv)
    if not CONTAINER_RE.fullmatch(args.container):
        parser.error("invalid_container")
    try:
        docker_cli = owner_readiness_guard(args.container)
    except (ValueError, KeyError, OSError, TypeError,
            json.JSONDecodeError, subprocess.SubprocessError) as err:
        parser.error(str(err))
    if args.action == "pair":
        try:
            code = owner_pairing_code(args.container, args.session, args.writer, docker_cli)
        except (ValueError, OSError, subprocess.SubprocessError):
            parser.error("pairing_unavailable")
        print("FORTIS_OWNER_LOCAL_PAIRING_CODE_PRIVATE_CONSOLE_ONLY", flush=True)
        print(json.dumps(code, ensure_ascii=True, separators=(",", ":")), flush=True)
        return
    if args.session or args.writer:
        parser.error("pair_options_only_for_pair_action")
    server = ThreadingHTTPServer(("127.0.0.1", WIN_PORT),
                                 handler_for(lambda req: docker_exec(args.container, req, docker_cli)))
    print("FORTIS_RELAY_READY=owner_local_127.0.0.1:18754; routes=three; no_owner_bearer", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
