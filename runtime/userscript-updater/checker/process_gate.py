"""Internal child handshake: launch nothing until the parent contains this process."""
import json
import os
import subprocess
import sys


def main():
    request = json.loads(sys.stdin.buffer.read(8 * 1024 * 1024))
    argv, environment = request["argv"], request["env"]
    trace = request.get("trace_phases") is True
    # Fixed labels only, enabled for owner-only safe setup fixtures. No argv,
    # environment, source paths or scan output in these diagnostic markers.
    def phase(label):
        if trace:
            print("checker-gate:" + label, file=sys.stderr, flush=True)
    phase("request_received")
    os.chdir(request["cwd"])
    phase("child_launch")
    if os.name == "posix":
        os.execve(argv[0], argv, environment)
    result = subprocess.call(argv, shell=False, env=environment, stdin=subprocess.DEVNULL)
    phase("child_exited")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
