"""Exercise the real startup scripts with a fake Docker CLI; no services started."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
function docker {
    $a = @($args)
    [System.IO.File]::AppendAllText($global:testLog, (ConvertTo-Json -Compress -InputObject $a) + "`n")
    $global:LASTEXITCODE = 0
    if ($a -contains 'config' -and $a -contains 'json') {
        return (@{services=@{'embedded-app'=@{environment=@{LLM_PROVIDER=$env:TEST_PROVIDER; OLLAMA_MODEL='llama3.1:8b'}}}} | ConvertTo-Json -Depth 6 -Compress)
    }
    if ($a -contains 'ps' -and $a -contains 'local-engine') { return 'engine-id' }
    if ($a -contains 'exec' -and $a -contains 'local-engine') {
        if ($env:TEST_SCENARIO -eq 'spark') { $global:LASTEXITCODE = 10 }
        return
    }
    if ($a -contains 'up' -and $a -contains 'ollama' -and $env:TEST_SCENARIO -eq 'unavailable') { $global:LASTEXITCODE = 1; return }
    if ($a -contains 'run') { $global:pulled = $true }
    if ($a -contains 'list') {
        if ($env:TEST_SCENARIO -eq 'installed' -or $global:pulled) { return 'llama3.1:8b hash 4GB now' }
        return 'llama3.1:8b-extra hash 4GB now'
    }
    if ($a -contains 'exec' -and $a -contains 'embedded-app') {
        $available = $env:TEST_PROVIDER -eq 'mock' -or $env:TEST_SCENARIO -eq 'installed' -or $global:pulled
        $model = if ($env:TEST_PROVIDER -eq 'mock') { 'deterministic' } else { 'llama3.1:8b' }
        $status = if ($available) { 'ok' } else { 'degraded' }
        $code = if ($env:TEST_SCENARIO -eq 'unavailable') { 'OLLAMA_UNAVAILABLE' } else { 'MODEL_NOT_FOUND' }
        return (@{status=$status; enabled=$true; available=$available; provider=$env:TEST_PROVIDER; model=$model; errorCode=$code} | ConvertTo-Json -Compress)
    }
}
$global:pulled = $false
$global:testLog = Join-Path $PSScriptRoot 'calls.jsonl'
$env:ASSISTANT_ENABLED = 'original'
& (Join-Path $PSScriptRoot 'start.ps1') FLAGS
$resultCode = $LASTEXITCODE
if ($env:ASSISTANT_ENABLED -ne 'original') { throw 'Environment was not restored' }
exit $resultCode
'''


class StartupTests(unittest.TestCase):
    def run_start(self, flags='', provider='mock', scenario='missing'):
        scratch = ROOT / 'generated'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='neoretail-start-', dir=scratch) as directory:
            target = Path(directory).resolve()
            self.assertTrue(target.is_relative_to(scratch.resolve()))
            (target / 'scripts').mkdir()
            for name in ('start.ps1', 'bootstrap-ollama.ps1'):
                shutil.copyfile(ROOT / name, target / name)
            (target / 'scripts/container-health.ps1').write_text(
                'function Wait-NeoRetailHealthy {}\nfunction Wait-NeoRetailOneShot {}\n', encoding='utf-8')
            (target / 'health.ps1').write_text('$global:LASTEXITCODE = 0', encoding='utf-8')
            (target / '.env').write_text('DO_NOT_CHANGE=true\n', encoding='utf-8')
            wrapper = target / 'test.ps1'
            wrapper.write_text(MOCK.replace('FLAGS', flags), encoding='utf-8')
            import os
            env = {**os.environ, 'TEST_PROVIDER': provider, 'TEST_SCENARIO': scenario}
            run = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(wrapper)],
                                 env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual((target / '.env').read_text(), 'DO_NOT_CHANGE=true\n')
            log = target / 'calls.jsonl'
            calls = [json.loads(line) for line in log.read_text(encoding='utf-8-sig').splitlines()] if log.exists() else []
            return run, calls

    def test_normal_and_rebuild_never_start_ollama(self):
        for flags in ('', '-Rebuild'):
            run, calls = self.run_start(flags)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertFalse(any('ollama' in call or 'ollama-model-init' in call for call in calls))
            self.assertFalse(any('docker-compose.assistant.yml' in call for call in calls))

    def test_pull_requires_assistant(self):
        run, calls = self.run_start('-PullModel')
        self.assertEqual(run.returncode, 1)
        self.assertFalse(any('up' in call or 'run' in call for call in calls))

    def test_mock_uses_overlay_without_ollama(self):
        run, calls = self.run_start('-Assistant')
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertFalse(any('ollama' in call for call in calls))
        embedded = [c for c in calls if 'up' in c and 'embedded-app' in c]
        self.assertEqual(len(embedded), 1)
        self.assertIn('docker-compose.assistant.yml', embedded[0])

    def test_mock_rejects_pull(self):
        run, calls = self.run_start('-Assistant -PullModel')
        self.assertEqual(run.returncode, 1)
        self.assertFalse(any('up' in call or 'run' in call for call in calls))

    def test_missing_and_unavailable_are_degraded_without_pull(self):
        for scenario, code in [('missing', 'MODEL_NOT_FOUND'), ('unavailable', 'OLLAMA_UNAVAILABLE')]:
            run, calls = self.run_start('-Assistant', 'ollama', scenario)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn(code, run.stdout)
            self.assertFalse(any('run' in call for call in calls))

    def test_pull_only_when_absent_and_authorized(self):
        for scenario, count in [('missing', 1), ('installed', 0)]:
            run, calls = self.run_start('-Assistant -PullModel', 'ollama', scenario)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(sum('run' in call for call in calls), count)
            up = [c for c in calls if 'up' in c]
            self.assertLess(next(i for i,c in enumerate(up) if 'local-engine' in c), next(i for i,c in enumerate(up) if 'ollama' in c))
            self.assertLess(next(i for i,c in enumerate(up) if 'ollama' in c), next(i for i,c in enumerate(up) if 'embedded-app' in c))

    def test_spark_blocks_ollama(self):
        run, calls = self.run_start('-Assistant', 'ollama', 'spark')
        self.assertEqual(run.returncode, 1)
        self.assertIn('SPARK_ACTIVE', run.stdout)
        self.assertFalse(any('up' in c and 'ollama' in c for c in calls))


if __name__ == '__main__':
    unittest.main()
