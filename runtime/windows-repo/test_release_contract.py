"""Offline checks for staged Windows Repo tunnel source; does not execute Windows code."""
from pathlib import Path
import hashlib
import json
import unittest

BUNDLE = Path(__file__).resolve().parent
REPO = BUNDLE.parents[1]


class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((BUNDLE / 'release-manifest.json').read_text(encoding='utf-8'))

    def test_manifest_is_exact_and_complete(self):
        self.assertEqual(self.manifest['schema_version'], 1)
        self.assertEqual(self.manifest['status'], 'STAGED_SOURCE_ONLY__NOT_WINDOWS_ACCEPTED')
        expected = {
            'repo1/control.ps1',
            'repo1/run-tunnel-quiet-logs.ps1',
            'repo2/Repo2DirectGuard.ps1',
            'repo2/FortisRepo2-quiet-logs.ps1',
        }
        self.assertEqual({entry['path'] for entry in self.manifest['files']}, expected)
        for entry in self.manifest['files']:
            data = (BUNDLE / entry['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest().upper(), entry['sha256'])
            self.assertNotIn(b'BEGIN PRIVATE KEY', data)
            self.assertNotIn(b'github_pat_', data)
            self.assertNotIn(b'ghp_', data)

    def test_current_worker_chain_manifest_is_exact(self):
        current = BUNDLE / 'current'
        manifest = json.loads((current / 'source-manifest.json').read_text(encoding='utf-8'))
        expected = {
            'Repo1-Worker.ps1',
            'Repo2-Worker.ps1',
            'launchers/chatgpt-repo-mode/control.ps1',
            'launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1',
            'launchers/FortisRDGLauncherV2/Common.ps1',
            'launchers/FortisRDGLauncherV2/Start-Fortis.ps1',
            'launchers/FortisRepoPlus2/Repo2DirectGuard.ps1',
            'launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1',
            'launchers/shared/FortisContainerPolicy.ps1',
        }
        self.assertEqual(manifest['schema_version'], 1)
        self.assertEqual(manifest['status'], 'TUNNEL_CANONICAL_SHARED_GUARD_POLICY_GO3C')
        self.assertEqual(manifest['source_repository'], 'tunnel')
        self.assertEqual(manifest['source_ref'], 'tunnel:main')
        self.assertEqual(manifest['source_revision_type'], 'sha256_file_inventory_v1')
        inventory = ''.join(f"{entry['path']}\t{entry['sha256']}\n" for entry in manifest['files'])
        self.assertEqual(hashlib.sha256(inventory.encode()).hexdigest().upper(), manifest['source_revision'])
        self.assertEqual({entry['path'] for entry in manifest['files']}, expected)
        wrapper = (BUNDLE / 'Invoke-FortisRepo.ps1').read_text(encoding='utf-8')
        manifest_hash = hashlib.sha256((current / 'source-manifest.json').read_bytes()).hexdigest().upper()
        self.assertIn(f"$expectedManifestHash = '{manifest_hash}'", wrapper)
        for entry in manifest['files']:
            data = (current / entry['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest().upper(), entry['sha256'])
            self.assertNotIn(b'BEGIN PRIVATE KEY', data)
            self.assertNotIn(b'github_pat_', data)
            self.assertNotIn(b'ghp_', data)

        repo1_worker = (current / 'Repo1-Worker.ps1').read_text(encoding='utf-8-sig')
        repo2_worker = (current / 'Repo2-Worker.ps1').read_text(encoding='utf-8-sig')
        self.assertIn(r"launchers\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1", repo1_worker)
        self.assertIn(r"launchers\FortisRDGLauncherV2\Start-Fortis.ps1", repo2_worker)
        self.assertIn(r"launchers\FortisRepoPlus2\FortisRepo2-quiet-logs.ps1", repo2_worker)

    def test_embedded_pins_still_match_adjacent_sources(self):
        sha = lambda name: hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest().upper().encode()
        repo1 = (BUNDLE / 'repo1/run-tunnel-quiet-logs.ps1').read_bytes()
        repo2 = (BUNDLE / 'repo2/FortisRepo2-quiet-logs.ps1').read_bytes()
        self.assertIn(sha('repo1/control.ps1'), repo1)
        self.assertIn(sha('repo2/Repo2DirectGuard.ps1'), repo2)
        self.assertIn(b"Join-Path $PSScriptRoot 'control.ps1'", repo1)
        self.assertIn(b"Join-Path $PSScriptRoot 'Repo2DirectGuard.ps1'", repo2)
        for data in (repo1, repo2):
            self.assertIn(b'/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js', data)
            self.assertNotIn(b'--mcp.command command=docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs', data)

    def test_wrapper_defaults_preview_and_never_stops_existing_runtime(self):
        wrapper = (BUNDLE / 'Invoke-FortisRepo.ps1').read_text(encoding='utf-8')
        self.assertIn("[ValidateSet('Preview','Start')][string]$Action='Preview'", wrapper)
        self.assertIn("'Repos\\tunnel'", wrapper)
        self.assertIn('Get-FileHash', wrapper)
        self.assertIn('status --porcelain', wrapper)
        self.assertIn('Read-Host', wrapper)
        self.assertIn("'current'", wrapper)
        self.assertIn("source-manifest.json", wrapper)
        self.assertIn('& $repo1Preview -Mode Preview', wrapper)
        self.assertIn('& $repo2Status -Action Status', wrapper)
        self.assertIn('& $repo2Guard -Mode Preview', wrapper)
        self.assertIn('& $repo1Worker', wrapper)
        self.assertIn('& $repo2Worker', wrapper)
        self.assertIn("Join-Path $PSScriptRoot '..\\..'", wrapper)
        self.assertIn('remote get-url origin', wrapper)
        self.assertIn('rev-list --left-right --count', wrapper)
        self.assertNotIn('& $repo1 -Mode Run', wrapper)
        self.assertNotIn('& $repo2 -Action Start', wrapper)
        for command in ('Stop-Process', 'Stop-Service', 'docker stop', 'docker start', 'docker restart', 'docker rm',
                        'docker create', 'wsl --shutdown', 'Start-Process'):
            self.assertNotIn(command, wrapper)
        self.assertNotRegex(wrapper, r'(?m)^\s*git\s+pull\b')

    def test_installed_inventory_is_read_only_and_separate(self):
        script = (BUNDLE / "Preview-WindowsRepoInventory.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-FileHash", script)
        self.assertIn("installed_matches_source", script)
        for forbidden in ("Stop-Process", "Stop-Service", "docker stop", "git pull",
                          "Set-Item", "Remove-Item", "Start-Process", "runtime.key", "Get-Content -LiteralPath $installed"):
            self.assertNotIn(forbidden, script)

    def test_git_attributes_preserve_bytes(self):
        attrs = (REPO / '.gitattributes').read_text(encoding='utf-8')
        self.assertIn('runtime/** -text', attrs)


if __name__ == '__main__':
    unittest.main()
