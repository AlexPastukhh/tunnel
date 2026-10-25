"""Internal child handshake: launch nothing until the parent contains this process."""
import json
import os
import subprocess
import sys


def main():
    request = json.loads(sys.stdin.buffer.read(8 * 1024 * 1024))
    argv, environment = request["argv"], request["env"]
    os.chdir(request["cwd"])
    if os.name == "posix":
        os.execve(argv[0], argv, environment)
    return subprocess.call(argv, shell=False, env=environment, stdin=subprocess.DEVNULL)


if __name__ == "__main__":
    raise SystemExit(main())
