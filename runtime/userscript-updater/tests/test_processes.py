import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from checker.processes import RunControl, Cancelled, DeadlineExceeded


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
