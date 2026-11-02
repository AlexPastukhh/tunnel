"""Offline source-contract checks for the released GO-3C shared policy."""
from pathlib import Path
import base64
import hashlib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parent
CURRENT = ROOT / "current"


class Go3CSharedPolicyContract(unittest.TestCase):
    def test_release_manifest_is_exact_and_pinned(self):
        manifest = json.loads((CURRENT / "source-manifest.json").read_text(encoding="utf-8"))
        expected = {
            "Repo1-Worker.ps1",
            "Repo2-Worker.ps1",
            "launchers/chatgpt-repo-mode/control.ps1",
            "launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1",
            "launchers/FortisRDGLauncherV2/Common.ps1",
            "launchers/FortisRDGLauncherV2/Start-Fortis.ps1",
            "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1",
            "launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1",
            "launchers/shared/FortisContainerPolicy.ps1",
        }
        self.assertEqual(manifest["status"], "TUNNEL_CANONICAL_SHARED_GUARD_POLICY_GO3C")
        self.assertEqual(manifest["source_repository"], "tunnel")
        self.assertEqual(manifest["source_ref"], "tunnel:main")
        self.assertEqual(manifest["source_revision_type"], "sha256_file_inventory_v1")
        self.assertEqual({x["path"] for x in manifest["files"]}, expected)
        inventory = "".join(f"{x['path']}\t{x['sha256']}\n" for x in manifest["files"])
        self.assertEqual(hashlib.sha256(inventory.encode()).hexdigest().upper(), manifest["source_revision"])
        for entry in manifest["files"]:
            data = (CURRENT / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest().upper(), entry["sha256"])
            self.assertNotIn(b"BEGIN PRIVATE KEY", data)
            self.assertNotIn(b"github_pat_", data)
            self.assertNotIn(b"ghp_", data)

    def test_dispatcher_is_manifest_pinned_and_owner_gated(self):
        wrapper = (ROOT / "Invoke-FortisRepo.ps1").read_text(encoding="utf-8")
        digest = hashlib.sha256((CURRENT / "source-manifest.json").read_bytes()).hexdigest().upper()
        self.assertIn(f"$expectedManifestHash = '{digest}'", wrapper)
        self.assertIn("'launchers/shared/FortisContainerPolicy.ps1'", wrapper)
        self.assertIn("[ValidateSet('Preview','Start')][string]$Action='Preview'", wrapper)
        self.assertIn("Type START ' + $Repo", wrapper)
        self.assertIn("Join-Path $PSScriptRoot '..\\..'", wrapper)
        self.assertNotIn("GO-3C is source-review only", wrapper)

    def test_shared_policy_is_the_only_common_policy_source(self):
        policy = (CURRENT / "launchers/shared/FortisContainerPolicy.ps1").read_text(encoding="utf-8")
        repo1 = (CURRENT / "launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1").read_text(encoding="utf-8")
        repo2 = (CURRENT / "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1").read_text(encoding="utf-8")
        common = (CURRENT / "launchers/FortisRDGLauncherV2/Common.ps1").read_text(encoding="utf-8-sig")
        quiet = (CURRENT / "launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1").read_text(encoding="utf-8")
        for source in (repo1, repo2, common, quiet):
            self.assertIn("FortisContainerPolicy.ps1", source)
        for value in (
            "S-1-5-21-303538662-3368424508-2654684973-1001",
            "fortis-repo-workspace",
            "fortis-r7-client",
            "fortis-repo-egress",
            "rdg-personal_agents",
            "8589934592",
            "2000000000",
            "A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A",
        ):
            self.assertIn(value, policy)
            for source in (repo1, repo2, common, quiet):
                self.assertNotIn(value, source)
        self.assertNotIn("2c84fabebb34265e53b020f21a11683a4c68cbb41", "\n".join(x.read_text(encoding="utf-8", errors="ignore") for x in CURRENT.rglob("*.ps1")))
        self.assertNotIn("a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500", policy)
        self.assertNotIn("defaultShell", policy)
        self.assertNotIn("telemetryEnabled", policy)
        policy_text = policy
        anchor = re.search(r"(?m)^    PolicySourceSha256 = '([0-9A-F]{64})'$", policy_text)
        self.assertIsNotNone(anchor)
        normalized = re.sub(r"(?m)^    PolicySourceSha256 = '[0-9A-F]{64}'$", "    PolicySourceSha256 = '<SELF>'", policy_text)
        self.assertEqual(hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper(), anchor.group(1))
        self.assertIn("Get-FortisObjectValue $_ 'Type' ''", policy_text)
        self.assertIn("Effective Docker mount metadata is incomplete", policy_text)
        self.assertIn("function ConvertFrom-FortisDockerInspectObject", policy_text)
        self.assertIn("--format '{{json .}}'", policy_text)
        self.assertNotIn("$requestedMounts.Count -notin @(3,4)", policy_text)
        self.assertIn("function Assert-FortisPolicyIntegrity", policy_text)
        self.assertIn("Assert-FortisPolicyIntegrity", policy_text)
        for source in (repo1, repo2, common, quiet):
            self.assertNotIn("5ABCDDB76CED91673B02A98CE577E03EBD87B3B9E249C6959081C42A054F528A", source)
        preload = re.search(r"QuietNodeOption = '--import=data:text/javascript;base64,([^']+)'", policy)
        self.assertIsNotNone(preload)
        decoded = base64.b64decode(preload.group(1), validate=True)
        self.assertEqual(hashlib.sha256(decoded).hexdigest(), "a18a0d409cd1e40bcb6bbb82935a041297aec43de34c65ac26015fa1f7422eb3")
        self.assertIn("QuietPreloadSha256", policy)
        self.assertNotIn("--import=data:text/javascript;base64", repo1)
        self.assertNotIn("--import=data:text/javascript;base64", quiet)
        self.assertNotIn("/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js", repo1)
        self.assertNotIn("/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js", quiet)

    def test_repo2_integrity_chain_and_container_id_flow(self):
        quiet = (CURRENT / "launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1").read_text(encoding="utf-8")
        guard = (CURRENT / "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1").read_text(encoding="utf-8")
        guard_hash = hashlib.sha256((CURRENT / "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1").read_bytes()).hexdigest().upper()
        self.assertIn(guard_hash, quiet)
        self.assertNotIn("5ABCDDB76CED91673B02A98CE577E03EBD87B3B9E249C6959081C42A054F528A", quiet)
        self.assertIn("__FORTIS_CONTAINER_ID__", quiet)
        self.assertIn("-ContainerId $ContainerId", quiet)
        self.assertIn("REPO2_DIRECT_GUARD_PASS:' + $context.ContainerId", guard)
        worker = (CURRENT / "Repo2-Worker.ps1").read_text(encoding="utf-8-sig")
        start = (CURRENT / "launchers/FortisRDGLauncherV2/Start-Fortis.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("$containerId = [string]$prepareOutput[0]", worker)
        self.assertIn("-ContainerId $containerId", worker)
        self.assertIn("Write-Output $id", start)

    def test_repo1_and_repo2_use_shared_id_bound_exec(self):
        repo1 = (CURRENT / "launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1").read_text(encoding="utf-8")
        repo2 = (CURRENT / "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1").read_text(encoding="utf-8")
        common = (CURRENT / "launchers/FortisRDGLauncherV2/Common.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("Invoke-FortisDockerExec", repo1)
        self.assertIn("$fortisContainer", repo1)
        self.assertIn("Get-FortisContainerContext -ContainerId $ContainerId", repo2)
        self.assertIn("Start-FortisContainer -Context $context", common)
        self.assertIn("$script:FortisContainerId", common)
        self.assertIn("Repair-FortisLinuxRuntimeConfig", repo1)
        self.assertIn("Repair-FortisLinuxRuntimeConfig", (CURRENT / "launchers/FortisRepoPlus2/Repo2DirectGuard.ps1").read_text(encoding="utf-8"))
        self.assertNotIn("$script:FortisImageId", common)
        self.assertNotIn("function Assert-FortisSecurity", common)

    def test_manifest_and_shared_js_are_stable(self):
        policy = (CURRENT / "launchers/shared/FortisContainerPolicy.ps1").read_text(encoding="utf-8")
        self.assertIn("MaxMemoryBytes", policy)
        self.assertIn("MaxNanoCpus", policy)
        self.assertIn("MaxPids", policy)
        self.assertIn("RequiredMounts", policy)
        self.assertIn("OptionalMounts", policy)
        self.assertIn("LinuxSecurityVerified", policy)
        self.assertIn("Repair-FortisLinuxRuntimeConfig", policy)
        self.assertNotIn("directHash", policy)
        self.assertNotIn("FortisImageId", policy)


if __name__ == "__main__":
    unittest.main()
