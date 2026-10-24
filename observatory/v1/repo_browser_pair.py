"""Owner-console-only pairing code from the live Docker service.

Run through a separately reviewed Windows-owner local docker exec, never
through a ChatGPT tool whose output is recorded in chat. Contains per-session
observer/writer capabilities; deliberately prints NOTHING else.
"""
import argparse
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from repo_service import DEFAULT_PORT, DEFAULT_ROOT, api_call


def pairing(session, writer=False, root=DEFAULT_ROOT, port=DEFAULT_PORT, task_intents=False):
    if not isinstance(session, str) or not re.fullmatch(r"rs_[0-9a-f]{32}", session):
        raise ValueError("bad_session_id")
    path = "/api/message-writer-pair" if writer else "/api/observer-pair"
    data = api_call(root, port, path + "?session=" + quote(session))
    obj = data["pairing"]
    if (obj.get("reporting_session_id") != session or
            obj.get("origin") != "http://127.0.0.1:18754" or
            (writer and "message_writer_key" not in obj)):
        raise ValueError("invalid_pairing_reply")
    if task_intents:
        grant = api_call(root, port, "/api/task-intent-pair", {
            "version": 1, "reporting_session_id": session,
            "conversation_id": obj["conversation_id"]})["pairing"]
        if (grant.get("reporting_session_id") != session or
                grant.get("conversation_id") != obj["conversation_id"] or
                not re.fullmatch(r"[A-Za-z0-9_-]{40,70}", grant.get("task_intent_key") or "")):
            raise ValueError("invalid_task_intent_pair")
        obj = {**obj, "task_intent_key": grant["task_intent_key"]}
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--writer", action="store_true",
                        help="Explicitly request per-session original-text writer key")
    parser.add_argument("--task-intents", action="store_true",
                        help="Explicitly grant metadata-only task registration and Send observations")
    args = parser.parse_args()
    try:
        result = pairing(args.session, args.writer, task_intents=args.task_intents)
    except (ValueError, KeyError, OSError, HTTPError, URLError):
        print("PAIRING_UNAVAILABLE", file=sys.stderr)
        return 1
    # Deliberately sensitive; only the locally approved owner's console.
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
