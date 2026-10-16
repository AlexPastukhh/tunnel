"""Read-only, privacy-minimizing Desktop Commander tool-history inspector.

Tool history is incomplete and may contain sensitive arguments and outputs.
This module never persists the source, and the web/API result NEVER includes
commands, arguments, output, filenames, prompts, or tokens.
"""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

DEFAULT_SOURCE = Path.home() / ".claude-server-commander" / "tool-history.jsonl"
MAX_TAIL_BYTES = 16 * 1024 * 1024
MAX_LINE_BYTES = 512 * 1024
MAX_RECORDS = 1000
TOOLS = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,95}$")
ROUTES = {"repo", "g2"}
SHELL_TOOLS = {"start_process", "execute_command", "execute", "interact_with_process"}


def kind(tool: str) -> str:
    if tool in SHELL_TOOLS or tool in {"read_process_output", "list_processes", "list_sessions"}:
        return "terminal"
    if tool.startswith(("read_", "write_", "edit_", "move_", "create_", "get_file_", "list_directory")):
        return "files"
    if "search" in tool or "find" in tool:
        return "search"
    if tool in {"get_config", "set_config_value", "get_recent_tool_calls"}:
        return "config"
    return "other"


def safe_record(source: dict, route: str) -> dict:
    if not isinstance(source, dict) or route not in ROUTES:
        raise ValueError("invalid record/route")
    tool = source.get("toolName")
    tool = tool if isinstance(tool, str) and TOOLS.fullmatch(tool) else "unknown"
    when = source.get("timestamp")
    when = when if isinstance(when, str) and len(when) <= 64 and re.fullmatch(r"[0-9T:.\-+Z]+", when) else None
    duration = source.get("duration")
    duration = duration if type(duration) in (int, float) and 0 <= duration <= 86400000 else None
    # No tool output is parsed into an "OK" assertion: outputs may be truncated or
    # state "process started" before a subsequent failure.
    output = source.get("output")
    outcome = "error" if isinstance(output, dict) and output.get("isError") is True else "unverified"
    args = source.get("arguments")
    command_present = (
        tool in SHELL_TOOLS and isinstance(args, dict)
        and any(isinstance(args.get(k), str) and bool(args[k]) for k in ("command", "input", "chars"))
    )
    # Tool history contains no reliable chat/conversation ID.
    identity = json.dumps([route, source.get("timestamp"), tool, source.get("arguments")],
                          ensure_ascii=True, sort_keys=True, default=str).encode("utf-8", "replace")
    return {
        "event_id": hashlib.sha256(identity).hexdigest()[:16],
        "route": route,
        "timestamp": when,
        "tool": tool,
        "kind": kind(tool),
        "duration_ms": duration,
        "outcome": outcome,
        "command_present": command_present,
        "chat_id": None,
    }


def _read_lines(path: Path, cap: int) -> tuple[list[str], bool]:
    # No following symlinks: do not let a read-only dashboard unknowingly
    # consume credentials from a redirected source path.
    if path.is_symlink():
        raise ValueError("symlink audit source refused")
    if not path.is_file():
        return [], False
    size = path.stat().st_size
    truncated = size > cap
    with path.open("rb") as reader:
        if truncated:
            reader.seek(size - cap)
            reader.readline()  # discard partial line
        tail = deque(maxlen=MAX_RECORDS)
        while True:
            raw = reader.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAX_LINE_BYTES and not raw.endswith(b"\n"):
                # Skip the rest of this oversized record, without parsing it.
                reader.readline()
                continue
            tail.append(raw.decode("utf-8", "replace"))
    return list(tail), truncated


def records(path: Path, route: str, limit: int = 50, tool: str | None = None) -> dict:
    if route not in ROUTES:
        raise ValueError("route must be repo or g2")
    if not isinstance(limit, int):
        raise ValueError("invalid limit")
    limit = min(200, max(1, limit))
    path = Path(path).expanduser()
    raw, truncated = _read_lines(path, MAX_TAIL_BYTES)
    result = []
    bad = 0
    for line in raw:
        try:
            source = json.loads(line)
            if not isinstance(source, dict):
                raise ValueError("record is not an object")
            if tool and source.get("toolName") != tool:
                continue
            result.append(safe_record(source, route))
        except (ValueError, TypeError, json.JSONDecodeError):
            bad += 1
    return {
        "route": route,
        "source_state": "available" if path.is_file() else "unavailable",
        "source_recent_window_incomplete": truncated or len(raw) >= MAX_RECORDS,
        "invalid_records_in_window": bad,
        "returned": min(len(result), limit),
        "events": result[-limit:],
        "limits": "DC rolling history, not a complete audit; no chat prompts, arguments, output or commands in API",
    }


def unsafe_local_commands(path: Path, route: str, limit: int, tool: str | None = None) -> list[dict]:
    """Explicit direct-console forensic viewing. NEVER use this via HTTP/API."""
    if not sys.stdout.isatty():
        raise PermissionError("exact commands require an interactive local terminal, not MCP or redirection")
    raw, _ = _read_lines(Path(path).expanduser(), MAX_TAIL_BYTES)
    events = []
    for line in raw:
        try:
            original = json.loads(line)
        except ValueError:
            continue
        if not isinstance(original, dict):
            continue
        name = original.get("toolName")
        if name not in SHELL_TOOLS or (tool and tool != name):
            continue
        args = original.get("arguments")
        if not isinstance(args, dict):
            continue
        content = next((args[k] for k in ("command", "input", "chars")
                        if isinstance(args.get(k), str) and args[k]), None)
        if content:
            events.append({"route": route, "tool": name, "timestamp": original.get("timestamp"),
                           "exact_command_or_input": content})
    return events[-max(1, min(limit, 100)):]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fortis read-only Desktop Commander activity history")
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--tool")
    parser.add_argument("--json", action="store_true", help="metadata only, NEVER includes commands")
    parser.add_argument("--watch", action="store_true", help="poll at most once per 3 seconds")
    parser.add_argument("--unsafe-show-commands-local", action="store_true",
                        help="interactive local terminal only: print exact command/input; MAY CONTAIN SECRETS")
    args = parser.parse_args(argv)
    if args.unsafe_show_commands_local and (args.json or args.watch):
        parser.error("sensitive command view must not use JSON or watch")
    seen = set()
    while True:
        if args.unsafe_show_commands_local:
            for item in unsafe_local_commands(args.source, args.route, args.limit, args.tool):
                print(str(item["timestamp"]), str(item["tool"]), "\n" + item["exact_command_or_input"])
        else:
            report = records(args.source, args.route, args.limit, args.tool)
            if args.json:
                print(json.dumps(report, ensure_ascii=False))
            else:
                print(f"{args.route} history: {report['source_state']}; rolling/truncated: {report['source_recent_window_incomplete']}")
                for ev in report["events"]:
                    ident = ev["event_id"]
                    if args.watch and ident in seen:
                        continue
                    print(ev["timestamp"], ev["tool"], ev["kind"],
                          ev["duration_ms"], "ms", ev["outcome"],
                          "command available locally" if ev["command_present"] else "")
                    seen.add(ident)
        if not args.watch:
            break
        time.sleep(3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
