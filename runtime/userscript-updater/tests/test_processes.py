import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from checker.processes import (RunControl, Cancelled, DeadlineExceeded, execute,
                               check_windows_socket_temp, WINDOWS_IPC_TEMP_MAX_BYTES)


class ProcessControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(self.root)}

    def test_real_process_output_and_deadline(self):
        result = RunControl(10).run([sys.executable, "-c", "print('fixture-ok')"],
                                   cwd=self.root, env=self.env)
        self.assertEqual(result.stdout.strip(), "fixture-ok")
        with self.assertRaises(DeadlineExceeded):
            RunControl(0.15).run([sys.executable, "-c", "import time; time.sleep(20)"],
                                 cwd=self.root, env=self.env)

    def test_short_private_temp_allows_real_socket_from_long_working_directory(self):
        cwd = self.root / ("nested-working-directory-" * 5)
        cwd.mkdir()
        env = dict(self.env, TEMP=str(cwd), TMP=str(cwd), TMPDIR=str(cwd))
        code = ("import json,os,socket,pathlib; "
                "root=pathlib.Path(os.environ['TMP']); "
                "s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); "
                "s.bind(str(root/'osp0000.tmp')); s.close(); "
                "print(json.dumps({'temporary':str(root)}))")
        result = execute([sys.executable, "-c", code], control=RunControl(10),
                         cwd=cwd, env=env, timeout=5, temporary_parent=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        scratch = Path(json.loads(result.stdout)["temporary"])
        self.assertEqual(scratch.parent, self.root)
        self.assertNotEqual(scratch, cwd)
        self.assertFalse(scratch.exists())
        self.assertTrue(cwd.is_dir())
        self.assertEqual(env["TMP"], str(cwd))

    def test_windows_socket_temp_utf8_budget_refuses_long_paths_before_launch(self):
        old_workspace = (r"C:\Users\alexa\AppData\Local\ProjectChecker-Test\state"
                         r"\setup-validation-abcdefgh\effective\checker-policy-abcdefgh")
        short_state = r"C:\Users\alexa\AppData\Local\ProjectChecker-Test\state\abcdefgh"
        self.assertGreater(len(old_workspace.encode("utf-8")), WINDOWS_IPC_TEMP_MAX_BYTES)
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            check_windows_socket_temp(old_workspace)
        check_windows_socket_temp(short_state)
        check_windows_socket_temp("/" + "a" * (WINDOWS_IPC_TEMP_MAX_BYTES - 1))
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            check_windows_socket_temp("/" + "é" * (WINDOWS_IPC_TEMP_MAX_BYTES // 2))

        # Simulate the Windows UTF-8 guard, not global os.name (which breaks pathlib).
        long_state = self.root / ("x" * 90)
        long_state.mkdir()
        env = dict(self.env, TEMP="original", TMP="original", TMPDIR="original")
        original = env.copy()
        with patch("checker.processes._WINDOWS", True), \
             patch("checker.processes.subprocess.run") as launched:
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                execute([sys.executable, "-c", "print('must-not-run')"],
                        cwd=self.root, env=env, temporary_parent=long_state)
            launched.assert_not_called()
        self.assertEqual(list(long_state.iterdir()), [])
        self.assertEqual(env, original)

    def test_private_temp_cleanup_on_real_child_deadline_preserves_state(self):
        state = self.root / "state"
        state.mkdir()
        marker = state / "keep-owner-file.txt"
        marker.write_text("do not delete", encoding="utf-8")
        env = dict(self.env, TEMP="owner-temp", TMP="owner-tmp", TMPDIR="owner-tmpdir")
        original = env.copy()
        code = "import os,time; print(os.environ['TMP'], flush=True); time.sleep(20)"
        with self.assertRaises(DeadlineExceeded) as raised:
            execute([sys.executable, "-c", code], control=RunControl(10),
                    cwd=self.root, env=env, timeout=0.8, temporary_parent=state)
        scratch = Path(raised.exception.stdout.strip())
        self.assertEqual(scratch.parent, state)
        self.assertFalse(scratch.exists())
        self.assertEqual(list(state.iterdir()), [marker])
        self.assertEqual(marker.read_text(encoding="utf-8"), "do not delete")
        self.assertEqual(env, original)

    def test_deadline_keeps_bounded_output_after_cleanup(self):
        code = ("import sys,time; "
                "print('x'*12000+'stdout-ready',flush=True); "
                "print('y'*12000+'stderr-ready',file=sys.stderr,flush=True); time.sleep(20)")
        argv = [sys.executable, "-c", code]
        with self.assertRaises(DeadlineExceeded) as raised:
            RunControl(10).run(argv, cwd=self.root, env=self.env, timeout=0.6)
        error = raised.exception
        self.assertEqual(error.command, tuple(argv))
        self.assertLessEqual(len(error.stdout.encode("utf-8")), 8192)
        self.assertLessEqual(len(error.stderr.encode("utf-8")), 8192)
        self.assertIn("stdout-ready", error.stdout)
        self.assertIn("stderr-ready", error.stderr)

    @unittest.skipUnless(os.name == "posix", "POSIX tree proof; Windows Job Object needs native QA")
    def test_cancel_kills_actual_child_tree(self):
        marker = self.root / "child-pid"
        code = ("import subprocess,sys,time,pathlib; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                f"pathlib.Path({str(marker)!r}).write_text(str(p.pid)); time.sleep(30)")
        control, errors = RunControl(10), []
        def run():
            try:
                control.run([sys.executable, "-c", code], cwd=self.root, env=self.env)
            except Exception as exc:
                errors.append(exc)
        thread = threading.Thread(target=run)
        thread.start()
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(marker.exists(), "Actual child was not started")
        child_pid = int(marker.read_text())
        control.cancel()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertIsInstance(errors[0], Cancelled)
        status = Path(f"/proc/{child_pid}/stat")
        self.assertTrue(not status.exists() or status.read_text().split()[2] == "Z",
                        "Child must not remain running after cancellation")
