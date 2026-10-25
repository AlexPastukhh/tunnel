"""Run only the existing isolated Docker Tk/Xvfb QA installation; no host install."""
import os
import select
import subprocess
from pathlib import Path


def main():
    base = Path("/workspace/repo/project-checker-devtools/tk-qa")
    root = base / "root"
    server_path = base / "Xvfb-relocated"
    if not server_path.is_file():
        raise SystemExit("Isolated Docker QA tree missing; no automatic system installation")
    environment = dict(os.environ)
    environment.update(
        LD_LIBRARY_PATH=str(root / "usr/lib/x86_64-linux-gnu") + ":" + str(root / "usr/lib"),
        PYTHONPATH=str(root / "usr/lib/python3.11") + ":" + str(root / "usr/lib/python3.11/lib-dynload"),
        TCL_LIBRARY=str(root / "usr/share/tcltk/tcl8.6"), TK_LIBRARY=str(root / "usr/share/tcltk/tk8.6"),
        FONTCONFIG_FILE=str(base / "fonts.conf"), PATH=str(root / "usr/bin") + ":/usr/local/bin:/usr/bin:/bin",
        PYTHONDONTWRITEBYTECODE="1")
    read_fd, write_fd = os.pipe()
    with (base / "xvfb.log").open("wb") as log:
        server = subprocess.Popen([str(server_path), "-displayfd", str(write_fd), "-screen", "0", "1280x900x24",
            "-nolisten", "tcp", "-ac", "-xkbdir", str(root / "usr/share/X11/xkb")],
            env=environment, pass_fds=(write_fd,), stdout=log, stderr=log)
        os.close(write_fd)
        try:
            if not select.select([read_fd], [], [], 10)[0]:
                raise RuntimeError("Virtual display readiness timeout")
            display = os.read(read_fd, 100).decode().strip()
            if not display:
                raise RuntimeError((base / "xvfb.log").read_text(errors="replace")[-2000:])
            environment["DISPLAY"] = ":" + display
            with (base / "gui-smoke.log").open("wb") as output:
                completed = subprocess.run(["/workspace/repo/project-checker-devtools/semgrep-venv/bin/python",
                    "-B", "-m", "devtools.gui_workflow_smoke"], env=environment, stdout=output,
                    stderr=subprocess.STDOUT, timeout=240)
            print((base / "gui-smoke.log").read_text(errors="replace"))
            return completed.returncode
        finally:
            os.close(read_fd)
            server.terminate()
            server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
