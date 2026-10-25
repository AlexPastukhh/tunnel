"""Structural Windows layout evidence only: never proves real Windows ACL."""
import unittest

from checker.model import ContractError
from checker.windows_layout import RootSpec, normalize_windows_path, overlapping, review_windows_layout


def basic():
    return (
        RootSpec("agent_write", r"C:\Agent\Repos"),
        RootSpec("agent_write", r"C:\Agent\Files"),
        RootSpec("source", r"C:\Agent\Repos\project"),
        RootSpec("app", r"C:\Owner\ProjectChecker\App"),
        RootSpec("tools", r"C:\Owner\ProjectChecker\Tools"),
        RootSpec("policies", r"C:\Owner\ProjectChecker\Rules"),
        RootSpec("state", r"C:\Owner\ProjectChecker\State"),
        RootSpec("approved", r"C:\Owner\Approved\Scripts"),
    )


class WindowsLayoutTests(unittest.TestCase):
    def test_separate_paths_still_need_native_windows_evidence(self):
        result = review_windows_layout(basic())
        self.assertEqual(result.status, "NEEDS_NATIVE_WINDOWS_VERIFICATION")
        self.assertTrue(any(f.code == "WINDOWS_HANDLE_ACL_EVIDENCE_REQUIRED" for f in result.findings))
        self.assertFalse(hasattr(result, "approved"))

    def test_agent_alias_casefold_blocks(self):
        changed = list(basic())
        changed[3] = RootSpec("app", r"c:\AGENT\Repos\Project\APP")
        report = review_windows_layout(tuple(changed))
        self.assertEqual(report.status, "BLOCKED")
        self.assertIn("AGENT_WRITE_OVERLAP", {f.code for f in report.findings})

    def test_agent_parent_of_policy_blocks(self):
        changed = list(basic())
        changed[5] = RootSpec("policies", r"C:\Agent\Files\policies")
        report = review_windows_layout(tuple(changed))
        self.assertIn("AGENT_WRITE_OVERLAP", {f.code for f in report.findings})

    def test_approved_within_source_blocks(self):
        changed = list(basic())
        changed[7] = RootSpec("approved", r"C:\Agent\Repos\project\approved")
        codes = {f.code for f in review_windows_layout(tuple(changed)).findings}
        self.assertIn("SOURCE_TRUSTED_OVERLAP", codes)

    def test_approved_inside_app_blocks(self):
        changed = list(basic())
        changed[7] = RootSpec("approved", r"C:\Owner\ProjectChecker\App\Approved")
        self.assertIn("APPROVED_INSTALL_OVERLAP",
                      {f.code for f in review_windows_layout(tuple(changed)).findings})

    def test_unc_and_namespace_not_supported(self):
        for candidate in (r"\\server\share\abc", r"\\?\C:\Trusted", r"\Device\HarddiskVolume1\thing",
                          "//host/share", "relative/path", "$HOME/file", "%USERPROFILE%\\foo",
                          "C:/Trusted/../Repo", "C:/Trusted//rules", "C:/Trusted/X.",
                          "C:/Trusted/X ", "C:/Trusted/a:b", r"C:\Safe\CON.txt", r"C:\Safe\LPT9"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ContractError):
                    normalize_windows_path(candidate)

    def test_missing_roles_and_invalid_role_block(self):
        review = review_windows_layout((RootSpec("weird", r"C:\where"), RootSpec("source", r"C:\Repo")))
        self.assertEqual(review.status, "BLOCKED")
        self.assertIn("UNKNOWN_ROLE", {f.code for f in review.findings})
        self.assertIn("MISSING_ROOT", {f.code for f in review.findings})

    def test_same_directory_and_casefolded_parent_overlaps(self):
        self.assertTrue(overlapping(r"C:\Owner\App", r"c:/owner/APP"))
        self.assertTrue(overlapping(r"C:\Owner\App", r"C:\Owner"))
        self.assertFalse(overlapping(r"C:\Owner\App2", r"C:\Owner\App"))


if __name__ == "__main__":
    unittest.main()
