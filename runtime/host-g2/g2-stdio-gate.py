"""G2 test-only stdio boundary: pass minimal environment to Desktop Commander.

This wrapper is for the FortisHostG1 trial, not a hard security boundary
against processes running as the same Windows SID.
Never print secret values or use this with alexa's production runtime key.
"""
import os
import subprocess
import sys

NODE = "C:/Tools/desktop-commander-runtime/node.exe"
DESKTOP_COMMANDER = (
    "C:/Tools/desktop-commander/node_modules/"
    "@wonderwhy-er/desktop-commander/dist/index.js"
)

ALLOWED_ENV = {
    "systemroot", "windir", "comspec", "path", "pathext",
    "temp", "tmp", "userprofile", "appdata", "localappdata",
    "homedrive", "homepath", "username", "userdomain",
    "programdata", "programfiles", "programfiles(x86)",
    "processor_architecture", "number_of_processors"
}

def child_environment():
    env = {k: v for k, v in os.environ.items() if k.casefold() in ALLOWED_ENV}
    # Fixed non-secret override; never inherit this switch from the caller.
    env["DESKTOP_COMMANDER_DISABLE_MCP_UI"] = "1"
    return env

def self_test():
    sentinel = "G2_SYNTHETIC_TEST_SENTINEL"
    os.environ["CONTROL_PLANE_API_KEY"] = sentinel
    script = (
        "const k=['CONTROL_PLANE_API_KEY','OPENAI_API_KEY','OPENAI_ADMIN_KEY'];"
        "const found=k.filter(n=>Object.prototype.hasOwnProperty.call(process.env,n));"
        "const hidden=process.env.DESKTOP_COMMANDER_DISABLE_MCP_UI==='1';"
        "process.stdout.write(found.length ? 'FAIL: secret-related names forwarded' "
        ": !hidden ? 'FAIL: MCP UI is not disabled' "
        ": 'PASS: secret-related names absent; MCP UI disabled');"
        "process.exitCode=(found.length||!hidden)?1:0;"
    )
    completed = subprocess.run(
        [NODE, "-e", script], env=child_environment(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20
    )
    print(completed.stdout or "FAIL: empty stdout")
    if completed.returncode != 0:
        print("FAIL: Node self-test exit code", completed.returncode)
    return completed.returncode

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) != 1:
        print("G2 wrapper: unexpected args; refusing launch", file=sys.stderr)
        sys.exit(2)
    # Strict non-secret child environment; do not hand down runtime/admin API keys.
    sys.exit(subprocess.call(
        [NODE, DESKTOP_COMMANDER],
        stdin=sys.stdin.buffer, stdout=sys.stdout.buffer, stderr=sys.stderr.buffer,
        env=child_environment(),
    ))
