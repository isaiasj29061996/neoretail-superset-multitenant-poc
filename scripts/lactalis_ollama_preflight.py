"""Resource and completed-gate evidence before the explicitly authorized model pull."""
import ctypes
import json
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
out=root/'generated'
def read(name): return json.loads((out/name).read_text(encoding='utf-8'))
def run(args, content=None): return subprocess.check_output(args,cwd=root,input=content,text=True,encoding='utf-8')
for layer in ('bronze','silver','gold'): assert read('lactalis_'+layer+'_isolation.json')['passed']
assert read('lactalis_sql_current.json')['passed']
latest={}
for line in (out/'lactalis_superset_current.jsonl').read_text().splitlines():
    r=json.loads(line)
    if r['script'].startswith('validate_'): latest[r['script']]=r
assert len(latest)==15 and all(r['exit_code']==0 for r in latest.values())
guest=read('lactalis_guest_current.json'); assert guest['session_customer']==290 and len(guest['dashboards'])==8
mock=json.loads((out/'lactalis_http_assistant_current.log').read_text(encoding='utf-8').splitlines()[-1]); assert mock['passed'] and mock['health']['provider']=='mock'
class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
m=Memory(); m.length=ctypes.sizeof(m); assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
disk=json.loads(run(['powershell','-NoProfile','-Command','Get-PSDrive C | Select-Object Name,Used,Free | ConvertTo-Json -Compress']))
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in run(['docker','compose','exec','-T','local-engine','cat','/proc/meminfo']).splitlines()) if k in ('MemTotal','MemAvailable')}
probe="""from pathlib import Path
import json
markers=[b'org.apache.'+b'spark',b'pyspark.'+b'daemon',b'pyspark.'+b'worker']
active=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:
  if any(m in p.read_bytes() for m in markers): active.append(p.parent.name)
 except OSError: pass
print(json.dumps(active))
"""
spark=json.loads(run(['docker','compose','exec','-T','local-engine','python','-'],probe)); assert not spark
raw=run(['docker','compose','ps','--all','--format','json'])
containers=[{k:r.get(k) for k in ('Service','State','Health','ExitCode')} for r in (json.loads(line) for line in raw.splitlines() if line.strip())]
assert all(r['State']=='running' and r['Health']=='healthy' for r in containers if r['Service'] in ('superset-db','analytics-db','redis','superset','local-engine','embedded-app'))
result={'gates_passed':True,'validators':len(latest),'disk':disk,'windows_memory_total_bytes':m.total,'windows_memory_available_bytes':m.available,'docker_memory':mem,'spark_pids':spark,'containers':containers,'model':'llama3.1:8b','estimated_model_download_bytes':4900000000,'estimate_source':'https://ollama.com/library/llama3.1:8b'}
assert disk['Free']>30*1024**3
(out/'lactalis_ollama_preflight_current.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result))
