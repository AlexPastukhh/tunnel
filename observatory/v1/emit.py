"""Opt-in file-first sender. STAGED_ONLY is not accepted Observatory delivery.

A staged JSON remains in a local authorized inbox while Observatory is off.
The receiver may resequence distinct V2 events with colliding sender hints.
"""
import argparse
import json
from pathlib import Path
import uuid
from store import stage, ALL_EVENTS, ROUTES, STAGES, MESSAGE_EVENTS, MESSAGE_SUMMARIES


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage a Fortis Observatory work event")
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--task", required=True, help="V2: one ID per user message, reused for all its events")
    parser.add_argument("--version", type=int, choices=(1, 2), default=1)
    parser.add_argument("--session-task", help="V2: enrollment task ID, not the message task ID")
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    parser.add_argument("--sequence", type=int, required=True,
                        help="Sender order hint (per reporting session). V2 importer resolves collisions.")
    parser.add_argument("--event", choices=sorted(ALL_EVENTS), required=True)
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args(argv)
    event = {"version": args.version, "event_id": uuid.uuid4().hex,
             "reporting_session_id": args.session, "task_id": args.task,
             "sequence": args.sequence, "route": args.route,
             "event": args.event, "stage": args.stage, "summary": args.summary}
    if args.version == 2:
        if not args.session_task:
            print("NOT_STAGED: V2 requires --session-task")
            return 1
        event["session_task_id"] = args.session_task
        if args.event in MESSAGE_EVENTS:
            if args.summary != MESSAGE_SUMMARIES[args.event]:
                print("NOT_STAGED: use exact safe message marker, not message text")
                return 1
    try:
        path = stage(args.inbox, event)
    except (ValueError, OSError):
        print("NOT_STAGED: invalid data or inaccessible inbox")
        return 1
    print("STAGED_ONLY:", path.name, "(not an acceptance receipt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
