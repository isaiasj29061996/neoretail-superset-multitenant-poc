"""Run current Superset bootstrap/validators with explicit Lactalis context."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
groups = {
    'supplemental': ['validate_stock_headlines.py', 'validate_osa_industry.py'],
    'bootstrap': ['bootstrap_overview.py', 'bootstrap_overview_quantity.py', 'bootstrap_panorama.py',
                  'bootstrap_stock_optimization.py', 'bootstrap_export.py', 'bootstrap_osa_industry.py',
                  'bootstrap_osa_industry_certified.py', 'bootstrap_embedded.py'],
    'validate': ['validate_overview.py', 'validate_overview_quantity.py', 'validate_panorama.py',
                 'validate_panorama_sales.py', 'validate_panorama_stock.py', 'validate_panorama_comparisons.py',
                 'validate_panorama_details.py', 'validate_panorama_inventory_tabs.py',
                 'validate_panorama_inventory_filters.py', 'validate_panorama_kpi_dimensions.py',
                 'validate_osa_industry_certified.py', 'validate_stock_optimization.py', 'validate_export.py'],
}
selected = groups[sys.argv[1]]
if len(sys.argv) > 2:
    selected = selected[selected.index(sys.argv[2]):]
for script in selected:
    command = ['docker', 'compose', 'exec', '-T', '-e', 'NEORETAIL_VALIDATION_CUSTOMER=290', '-e', 'PROFILE_CUSTOMER_ID=290',
               '-e', 'NEORETAIL_VALIDATION_REDE=CENCOSUD',
               '-e', 'NEORETAIL_VALIDATION_FILTER_MEASURE=quilograma',
               'superset', '/app/.venv/bin/python', '/app/pythonpath/' + script]
    start = time.monotonic()
    log = root / ('generated/lactalis_' + script.replace('.py', '') + '_current.log')
    with log.open('w', encoding='utf-8') as handle:
        result = subprocess.run(command, cwd=root, stdout=handle, stderr=subprocess.STDOUT)
    record = {'script': script, 'id_customer': 290, 'exit_code': result.returncode,
              'seconds': round(time.monotonic() - start, 2), 'log': log.name}
    with (root / 'generated/lactalis_superset_current.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode: raise SystemExit(result.returncode)
