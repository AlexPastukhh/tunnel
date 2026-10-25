"""Only this fixed installed launcher constructs the native context."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if os.name != "nt" or not sys.flags.isolated or not sys.flags.no_site:
    raise SystemExit("Use Start-Checker.cmd in the installed Windows folder")
# The installed ._pth pins all Python search paths. No site/.pth/usercustomize imports.
dll_paths = []
for folder in (root / "python/DLLs", root / "pydeps/pywin32_system32"):
    if folder.is_dir():
        dll_paths.append(os.add_dll_directory(str(folder)))
os.chdir(root)

from checker.environment import configure_gui_environment
configure_gui_environment(root)

from checker.installed import InstalledAuthority
try:
    # Verify the installed context before loading GUI scripts/libraries.
    authority = InstalledAuthority(root)
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from checker.gui import DesktopApp
    app = DesktopApp(tk, ttk, filedialog, messagebox,
                     authority.profile.state_root / "projects.json", installed_context=authority)
    app.root.mainloop()
except Exception as exc:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, str(exc), "Project Checker: установка не подтверждена", 0x10)
    raise SystemExit(2)
