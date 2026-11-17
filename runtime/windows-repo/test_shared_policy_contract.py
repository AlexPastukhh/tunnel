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
        self.assertIn("eval(Buffer.from('$encodedSource','base64').toString('utf8'))", policy_text)
        self.assertIn("GetFileName([string]$execCommand[0])", policy_text)
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


class Repo1HeadroomRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        cls.node = shutil.which("node")
        if not cls.node:
            raise RuntimeError("Node is required for the executable Repo1 regression tests")
        cls.launcher = CURRENT / "launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1"
        cls.source = cls.launcher.read_text(encoding="utf-8")
        cls.probe = re.search(r"\$fortisHeadroomProbeCode = @'\n(.*?)\n'@", cls.source, re.S).group(1)

    def run_probe(self, overrides=None):
        import subprocess
        files = {"memory.max": str(4096 * 2**20), "memory.current": str(3926 * 2**20),
                 "memory.stat": "anon 314904576\ninactive_file 614465536\nactive_file 2946965504\n",
                 "pids.max": "512", "pids.current": "169"}
        files.update(overrides or {})
        harness = """const vm=require('vm'),fs=require('fs');
const input=JSON.parse(fs.readFileSync(0,'utf8')),output=[];
const fakeFs={readFileSync(path){const key=path.replace('/sys/fs/cgroup/','');
 if(input.files[key]===null||input.files[key]===undefined)throw Error('Unavailable counter');return input.files[key];}};
vm.runInNewContext(input.code,{require(name){if(name!=='fs')throw Error('Unexpected dependency');return fakeFs;},
 process:{stdout:{write(value){output.push(value);}}}},{timeout:1000});
if(output.length!==1)throw Error('Unexpected probe output');process.stdout.write(output[0]);"""
        result = subprocess.run([self.node, "-e", harness], input=json.dumps({"code": self.probe, "files": files}), text=True, capture_output=True, timeout=10, check=True)
        return json.loads(result.stdout)

    def test_cache_heavy_container_can_start(self):
        result = self.run_probe()
        self.assertEqual(result["status"], "PASS")
        self.assertLess(result["memoryLimitBytes"] - result["memoryCurrentBytes"], 256 * 2**20)
        self.assertEqual(result["memoryHeadroomBytes"], 756 * 2**20)

    def test_real_memory_shortage_and_active_cache_are_not_credited(self):
        for stat in ("inactive_file 0\n", "inactive_file 0\nactive_file 3600000000\nshmem 3600000000\n"):
            with self.subTest(stat=stat):
                self.assertEqual(self.run_probe({"memory.stat": stat})["status"], "MEMORY_HEADROOM_LOW")

    def test_memory_threshold_is_unchanged(self):
        for free, expected in [(255, "MEMORY_HEADROOM_LOW"), (256, "PASS")]:
            with self.subTest(free=free):
                result = self.run_probe({"memory.current": str((4096 - free) * 2**20), "memory.stat": "inactive_file 0\n"})
                self.assertEqual(result["status"], expected)

    def test_pid_threshold_is_unchanged(self):
        for spare, expected in [(47, "PID_HEADROOM_LOW"), (48, "PASS")]:
            with self.subTest(spare=spare):
                self.assertEqual(self.run_probe({"pids.current": str(512 - spare)})["status"], expected)

    def test_counter_errors_fail_closed(self):
        cases = [{"memory.stat": x} for x in [None, "", "inactive_file bad\n", "inactive_file 0\ninactive_file 0\n", "inactive_file 9999999999\n"]]
        cases += [{key: value} for key in ["memory.max", "memory.current", "pids.max", "pids.current"] for value in [None, "max", "-1", "1.5", "9007199254740992"]]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.run_probe(overrides), {"status": "RESOURCE_COUNTERS_INVALID"})

    def test_quiet_canary_keeps_progress_and_result(self):
        import os, subprocess
        policy = (CURRENT / "launchers/shared/FortisContainerPolicy.ps1").read_text(encoding="utf-8")
        option = re.search(r"QuietNodeOption = '([^']+)'", policy).group(1)
        code = re.search(r"\$fortisQuietProbeCode = @'\n(.*?)\n'@", self.source, re.S).group(1)
        env = os.environ.copy(); env["NODE_OPTIONS"] = option
        result = subprocess.run([self.node, "-e", code], env=env, text=True, capture_output=True, timeout=10, check=True)
        messages = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(messages, [
            {"jsonrpc": "2.0", "method": "notifications/progress", "params": {"progressToken": "fortis-quiet-preview", "progress": 1}},
            {"jsonrpc": "2.0", "id": 1, "result": {"quietPreloadOk": True}},
        ])

    def test_powershell_reports_specific_failure_without_running_launcher(self):
        import os, shutil, subprocess
        pwsh = os.environ.get("FORTIS_TEST_PWSH") or shutil.which("pwsh")
        if not pwsh:
            self.skipTest("PowerShell is unavailable; executable Node regression tests still run")
        script = """$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($env:FORTIS_HEADROOM_SOURCE,[ref]$tokens,[ref]$errors)
if($errors.Count -ne 0){throw 'Launcher syntax failed'}
$fn=@($ast.FindAll({param($n)$n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-FortisRepo1Headroom'},$true))
if($fn.Count -ne 1){throw 'Headroom assertion is missing'}
. ([scriptblock]::Create($fn[0].Extent.Text))
$output=@(foreach($probe in ($env:FORTIS_HEADROOM_FIXTURES | ConvertFrom-Json)) {
 try {Assert-FortisRepo1Headroom -Probe $probe; 'PASS'} catch {$_.Exception.Message}
})
$output | ConvertTo-Json -Compress
"""
        fixtures = [self.run_probe(), self.run_probe({"memory.stat": "inactive_file 0\n"}),
                    self.run_probe({"pids.current": "511"}), self.run_probe({"memory.stat": None})]
        env = os.environ.copy(); env["FORTIS_HEADROOM_SOURCE"] = str(self.launcher)
        env["FORTIS_HEADROOM_FIXTURES"] = json.dumps(fixtures)
        result = subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script], env=env, text=True, capture_output=True, timeout=30, check=True)
        messages = json.loads(result.stdout)
        self.assertEqual(messages[0], "PASS")
        self.assertIn("estimated memory headroom 170 MiB < 256 MiB", messages[1])
        self.assertIn("PID headroom 1 < 48", messages[2])
        self.assertIn("counters are missing, invalid or inconsistent", messages[3])
        self.assertTrue(all("Nothing started or repaired" in msg for msg in messages[1:]))

if __name__ == "__main__":
    unittest.main()
