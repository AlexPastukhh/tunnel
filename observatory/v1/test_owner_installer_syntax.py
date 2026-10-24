"""Static PowerShell 5.1 compatibility regression for protected owner installer.

Real Windows Parser::ParseFile still must be run by the owner before install.
"""
import re
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
class OwnerInstallerSyntax(unittest.TestCase):
    def test_all_six_sha_source_and_installed_hash_lookups_are_single_line(self):
        text=(HERE/"Install-FortisObservatoryViewer.ps1").read_text(encoding="utf-8")
        self.assertNotRegex(text,r"-LiteralPath[ \t]*\r?\n")
        assignments=re.findall(
            r"^\$(\w+)[ \t]*=[ \t]*\(Get-FileHash -Algorithm SHA256"
            r" -LiteralPath \(Join-Path \$(source|install) '([^'\r\n]+)'\)\)\.Hash$",
            text,re.M)
        self.assertEqual(len(assignments),12)
        files=[
            'owner_viewer.py','owner_notifier_bridge.py','owner_dispatch.py',
            'owner_enrollment.py','Start-FortisObservatoryAuto.cmd',
            'Enable-FortisObservatoryAutoStart.ps1']
        for scope in ('source','install'):
            self.assertEqual({filename for _,where,filename in assignments if where==scope},
                             set(files))
        for p in ("ExpectedViewerSha256","ExpectedBridgeSha256",
                  "ExpectedDispatchSha256","ExpectedEnrollmentSha256",
                  "ExpectedAutoCmdSha256","ExpectedAutoEnableSha256"):
            self.assertIn("$"+p,text)

    def test_document_pins_are_current_and_no_install_commands_changed(self):
        import hashlib
        docs=(HERE/"OWNER_VIEWER_MANUAL_SETUP.md").read_text(encoding="utf-8")
        for file in ('owner_viewer.py','owner_notifier_bridge.py','owner_dispatch.py',
                     'owner_enrollment.py','Start-FortisObservatoryAuto.cmd',
                     'Enable-FortisObservatoryAutoStart.ps1'):
            sha=hashlib.sha256((HERE/file).read_bytes()).hexdigest()
            self.assertIn(sha,docs,file)

if __name__=="__main__":
    unittest.main()
