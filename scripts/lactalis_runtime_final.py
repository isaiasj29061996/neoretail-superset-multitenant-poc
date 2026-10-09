"""Capture final health/resource evidence without exposing environment secrets."""
import ctypes
import json
from pathlib import Path
import subprocess
import urllib.request
root=Path(__file__).resolve().parents[1]
out=root/'generated'
def run(args): return subprocess.check_output(args,cwd=root,text=True,encoding='utf-8')
compose=['docker','compose','-f','docker-compose.yml','-f','docker-compose.assistant.yml']
containers=[{k:r.get(k) for k in ('Service','State','Health','ExitCode')} for r in (json.loads(line) for line in run(compose+['ps','--all','--format','json']).splitlines() if line.strip())]
assert all(r['State']=='running' and r['Health']=='healthy' for r in containers if r['Service']!='superset-init')
assert any(r['Service']=='ollama' and r['Health']=='healthy' for r in containers)
models=run(compose+['exec','-T','ollama','ollama','list']); assert any(line.split()[0]=='llama3.1:8b' for line in models.splitlines()[1:])
http={}
for name,url in [('embedded','http://localhost:3000/'),('superset','http://localhost:8088/health'),('jupyter','http://localhost:8888/')]:
 with urllib.request.urlopen(url,timeout=20) as response: http[name]=response.status
assert all(code==200 for code in http.values())
latest={}
for line in (out/'lactalis_http_current.jsonl').read_text().splitlines():
 r=json.loads(line); latest[r['probe']]=r
assert latest['ollama']['exit_code']==0
ports=run(compose+['port','analytics-db','5432']).strip()
result={'containers':containers,'models':models.strip(),'http':http,'analytics_published_port':ports,'assistant_probes':latest,'git_branch':run(['git','branch','--show-current']).strip(),'git_head':run(['git','rev-parse','HEAD']).strip()}
(out/'lactalis_runtime_final.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(out/'lactalis_stats_final.txt').write_text(run(['docker','stats','--no-stream']),encoding='utf-8')
(out/'lactalis_worktree_final.txt').write_text(run(['git','status','--short']),encoding='utf-8')
print(json.dumps(result))
