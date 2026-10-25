"""Minimal analyzer environment, with explicit Windows system/tool paths."""
import os
import sys
from pathlib import Path


def analyzer_environment(root: Path, config=None):
    if os.name == "nt":
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        if not ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer)):
            raise OSError("Cannot locate Windows system directory")
        windows = Path(buffer.value)
        python = Path(sys.executable).parent
        paths = [python, python / "Scripts", python.parent / "pydeps/Scripts",
                 python.parent / "pydeps/bin", python.parent / "pydeps/pywin32_system32", windows / "System32"]
        if config:
            paths.append(config.executable.parent)
            if config.node:
                paths.append(config.node.parent)
        env = {"SystemRoot": str(windows), "WINDIR": str(windows),
               "USERPROFILE": str(root), "APPDATA": str(root), "LOCALAPPDATA": str(root),
               "TEMP": str(root), "TMP": str(root)}
        path = os.pathsep.join(map(str, dict.fromkeys(paths)))
    else:
        env, path = {}, "/usr/local/bin:/usr/bin:/bin"
    env.update(PATH=path, LC_ALL="C.UTF-8", NODE_OPTIONS="", HOME=str(root),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               SEMGREP_SEND_METRICS="off", SEMGREP_ENABLE_VERSION_CHECK="false")
    return env


def configure_gui_environment(root: Path):
    """Pin Tcl/Tk startup scripts before importing tkinter in the installed launcher."""
    if os.name != "nt":
        return
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT",
                "NODE_OPTIONS", "NODE_PATH", "TCLLIBPATH", "TCL_LIBRARY", "TK_LIBRARY"):
        os.environ.pop(key, None)
    os.environ["TCL_LIBRARY"] = str(root / "python/tcl/tcl8.6")
    os.environ["TK_LIBRARY"] = str(root / "python/tcl/tk8.6")
    os.environ["TCLLIBPATH"] = ""
    os.environ["HOME"] = str(root / ".gui-home")
