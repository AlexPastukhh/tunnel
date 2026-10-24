"""Fortis Repo sender for a single current user request.

The registered Docker session is verified locally. Metadata and full AI
message bodies are staged in separate private Repo-volume inboxes.
No owner credentials or historical chat identity is required in prompts.
"""
import argparse
from pathlib import Path
import re
import sys

from repo_service import DEFAULT_ROOT, confined
from store import Store


def enrollment(state_dir, session, chat_id):
    """Require the exact registered Repo session+Chat pair, including offline."""
    if (not re.fullmatch(r"rs_[0-9a-f]{32}", session or "") or
            not re.fullmatch(r"[A-Za-z0-9-]{8,100}", chat_id or "")):
        raise ValueError("invalid_context")
    root = confined(Path(state_dir))
    entry = Store(root / "archive")._session(session)
    if not entry or entry.get("route") != "repo" or entry.get("conversation_id") != chat_id:
        raise ValueError("session_chat_mismatch")
    token = entry.get("task_id")
    if not isinstance(token, str) or not re.fullmatch(r"task_[0-9a-f]{32}", token):
        raise ValueError("session_enrollment_invalid")
    return root, token


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_ROOT)
    commands = parser.add_subparsers(dest="action", required=True)
    event = commands.add_parser("event", help="Stage a metadata event for the current message")
    message = commands.add_parser("message", help="Stage full AI text through UTF-8 stdin")
    for cmd in (event, message):
        cmd.add_argument("--session", help="optional reporting_session_id from current Notifier message; otherwise retain pending current-chat context")
        cmd.add_argument("--chat-id", required=True, help="conversation_id from current Notifier message")
        cmd.add_argument("--task", required=True, help="per-user-message task_id from current Notifier message")
    event.add_argument("--event", choices=("user_message","assistant_message","started",
        "progress","checkpoint","blocked","completed","failed"), required=True)
    event.add_argument("--stage", choices=("planning","editing","testing","waiting_tool","reviewing","other"),
                       required=True)
    event.add_argument("--summary", required=True, help="safe metadata, never quote user text")
    event.add_argument("--detail-stdin", action="store_true",
        help="Read a bounded long-form event explanation from UTF-8 stdin")
    event.add_argument("--sequence", type=int, default=0,
        help="optional sender order hint; archive reassigns collisions")
    message.add_argument("--kind", choices=("interim","final"),required=True)
    message.add_argument("--message-id", default=None, help="reuse existing ID for an exact retry")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"task_[0-9a-f]{32}", args.task):
        print("NOT_STAGED: invalid current message task ID")
        return 1
    if args.session is None:
        # Missing browser pairing must not discard a valid current chat/task.
        # No registration, guessed session or HTTP readiness check here.
        from repo_pending import stage_pending
        from repo_messages import MAX_MESSAGE_BYTES
        import uuid
        try:
            root = confined(args.state_dir)
            if args.action == "event":
                detail = None
                if args.detail_stdin:
                    raw = sys.stdin.buffer.read(8193)
                    if len(raw) > 8192:
                        raise ValueError("detail_too_large")
                    detail = raw.decode("utf-8")
                data = {"event": args.event, "stage": args.stage,
                        "summary": args.summary, "sequence": args.sequence, "detail": detail}
                rid = None
            else:
                raw = sys.stdin.buffer.read(MAX_MESSAGE_BYTES + 1)
                if len(raw) > MAX_MESSAGE_BYTES:
                    raise ValueError("message_too_large")
                data = {"kind": args.kind, "body": raw.decode("utf-8")}
                mid = args.message_id or ("msg_" + uuid.uuid4().hex)
                if not re.fullmatch(r"msg_[0-9a-f]{32}", mid):
                    raise ValueError("invalid_message_id")
                rid = mid[4:]
            path = stage_pending(root, args.action, args.chat_id, args.task, data, rid)
        except (OSError, ValueError, UnicodeError):
            print("NOT_STAGED: invalid current context, data, inbox or capacity")
            return 1
        print("STAGED_ONLY:", path.name, "(waiting for exact chat registration; not an acceptance receipt)")
        if args.action == "message" and args.kind == "final":
            # Preserve this current-chat identity until exact registration.
            # Completed is reported only after the full message is staged.
            data = {"event": "completed", "stage": "other",
                    "summary": "AI сообщил о завершении ответа",
                    "sequence": 0, "detail": None}
            try:
                done = stage_pending(root, "event", args.chat_id, args.task,
                                     data, mid[4:])
            except (OSError, ValueError, UnicodeError):
                print("COMPLETED_NOT_STAGED: final queued; check task before retry")
            else:
                print("COMPLETION_STAGED_ONLY:", done.name,
                      "(waiting for exact chat registration; not a receipt)")
        return 0
    try:
        root, session_task = enrollment(args.state_dir,args.session,args.chat_id)
    except (OSError, ValueError, UnicodeError):
        print("NOT_STAGED: session/chat not registered or Repo archive unavailable")
        return 1
    if args.action == "event":
        import uuid
        from repo_pending import stage_event
        try:
            detail = None
            if args.detail_stdin:
                raw = sys.stdin.buffer.read(8193)
                if len(raw) > 8192:
                    raise ValueError("detail_too_large")
                detail = raw.decode("utf-8")
            item = {"version": 2, "event_id": uuid.uuid4().hex,
                    "reporting_session_id": args.session,
                    "session_task_id": session_task, "task_id": args.task,
                    "sequence": args.sequence, "route": "repo",
                    "event": args.event, "stage": args.stage, "summary": args.summary}
            staged = stage_event(root, item, detail)
        except (OSError, ValueError, UnicodeError):
            print("NOT_STAGED: invalid event, details or unavailable inbox")
            return 1
        print("STAGED_ONLY:", staged.name, "(not an acceptance receipt)")
        return 0
    from repo_message_sender import main as message_sender
    argv=["--state-dir",str(root),"--session",args.session,
          "--session-task",session_task,"--task",args.task,"--kind",args.kind]
    if args.message_id:
        argv += ["--message-id",args.message_id]
    return message_sender(argv)


if __name__ == "__main__":
    raise SystemExit(main())
