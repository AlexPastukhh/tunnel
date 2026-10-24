"""Stage a full assistant message via stdin into the internal Fortis Repo volume.

IMPORTANT: supplied body is plain text accessible to authorized Fortis Repo
processes; not Windows-owner-secret. Never include body in argv, logs or Git.
"""
import argparse
import sys
import uuid
from pathlib import Path

from repo_messages import MAX_MESSAGE_BYTES, stage_assistant
from repo_pending import stage_event
from repo_service import DEFAULT_ROOT, confined


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage assistant text without Observatory being online")
    parser.add_argument("--session", required=True)
    parser.add_argument("--session-task", required=True, help="enrollment task ID")
    parser.add_argument("--task", required=True, help="one task ID per user message")
    parser.add_argument("--message-id", default=None, help="reuse on retry for idempotency")
    parser.add_argument("--kind", choices=("interim", "final"), required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    try:
        root = confined(args.state_dir)
        payload = sys.stdin.buffer.read(MAX_MESSAGE_BYTES + 1)
        if len(payload) > MAX_MESSAGE_BYTES:
            raise ValueError("message_too_large")
        body = payload.decode("utf-8")
        mid = args.message_id or ("msg_" + uuid.uuid4().hex)
        message = {"version": 1, "reporting_session_id": args.session,
                   "session_task_id": args.session_task, "task_id": args.task,
                   "message_id": mid, "role": "assistant",
                   "kind": args.kind, "body": body}
        inbox = root / "inbox" / "messages"
        path = stage_assistant(inbox, message)
    except (OSError, ValueError, UnicodeError):
        print("NOT_STAGED: invalid data, inbox or capacity")
        return 1
    print("STAGED_ONLY:", path.name, "message_id:", mid,
          "(not an Observatory acceptance receipt)")
    if args.kind == "final":
        # One final -> one deterministic completion event, using the same
        # task/session enrollment. Never mark completed if message staging failed.
        # A retry with --message-id preserves event identity (archive de-duplicates).
        item = {"version": 2, "event_id": mid[4:],
                "reporting_session_id": args.session,
                "session_task_id": args.session_task, "task_id": args.task,
                "sequence": 0, "route": "repo", "event": "completed",
                "stage": "other", "summary": "AI сообщил о завершении ответа"}
        try:
            completed_path = stage_event(root, item)
        except (OSError, ValueError):
            # The full final is already durably queued. A nonzero return here
            # could cause an unsafe replay of the whole response.
            print("COMPLETED_NOT_STAGED: final is queued; check task status before retry")
        else:
            print("COMPLETION_STAGED_ONLY:", completed_path.name,
                  "(not an Observatory acceptance receipt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
