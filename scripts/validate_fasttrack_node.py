"""Run Node regressions with Python/Node context parity in a disposable image."""
import base64
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
code = "import json; from dataclasses import asdict; from pathlib import Path; from neoretail_local.customers import load_customer_registry; print(json.dumps([asdict(c) for c in load_customer_registry(Path('/workspace/config/customers.yaml'))[1]]))"
contexts = subprocess.check_output(['docker','exec','neoretail-v9-multitenant-local-engine-1','python','-c',code])
script = ('cp -R /repo/embedded-app /tmp/tenant-app && '
          'ln -s /app/node_modules /tmp/tenant-app/node_modules && '
          'ln -s /tmp/tenant-app /tmp/embedded-app && '
          'ln -s /repo/config /tmp/config && '
          'ln -s /repo/local-engine /tmp/local-engine && '
          'cp /app/public/app.bundle.js /tmp/tenant-app/public/app.bundle.js && '
          'cd /tmp/tenant-app && node --test tests/tenant-registry.test.js assistant/tests/*.test.js')
command = ['docker','run','--rm','--network','none',
           '-e','TENANT_PYTHON_CONTEXTS_B64='+base64.b64encode(contexts).decode(),
           '-v',str(ROOT)+':/repo:ro','--entrypoint','sh',
           'neoretail-v9-multitenant-embedded-app','-c',script]
result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
(ROOT/'generated/fasttrack_node_tests.log').write_text(result.stdout,encoding='utf-8')
print(result.stdout[-3000:])
raise SystemExit(result.returncode)
