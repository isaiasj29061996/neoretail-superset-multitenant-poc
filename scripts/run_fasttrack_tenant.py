"""Run one selected tenant sequentially in the aligned runtime; stop at first failure."""
from pathlib import Path
import argparse
import subprocess
import json
import time

ROOT = Path(__file__).resolve().parents[1]
ENGINE = 'neoretail-v9-multitenant-local-engine-1'
STEPS = ['03A', '03B', '03C', '03D', '04', '05', '06', '07', '08', 'marts']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant', required=True)
    parser.add_argument('--from-step', choices=STEPS, default='03A')
    args = parser.parse_args()
    # Runtime verification is mandatory before any data-changing execution.
    subprocess.run(['python', str(ROOT/'scripts/validate_fasttrack_runtime.py')], check=True,
                   stdout=subprocess.DEVNULL)
    output = ROOT/'generated'; output.mkdir(exist_ok=True)
    report_path = output/f'fasttrack_{args.tenant}_pipeline.json'
    report = []
    if args.from_step != STEPS[0] and report_path.exists():
        previous = json.loads(report_path.read_text(encoding='utf-8'))
        report = [entry for entry in previous if STEPS.index(entry['step']) < STEPS.index(args.from_step)]
    for step in STEPS[STEPS.index(args.from_step):]:
        module = {'03D':'partitioned_validation', '06':'gold_serving', 'marts':'marts'}.get(step, 'pipeline')
        command = ['docker', 'exec', ENGINE, 'python', '-m', 'neoretail_local.'+module]
        if module == 'pipeline': command += ['--step', step]
        command += ['--customer', args.tenant]
        print(json.dumps({'tenant':args.tenant, 'step':step, 'status':'started'}), flush=True)
        started = time.monotonic()
        log = output/f'fasttrack_{args.tenant}_{step}.log'
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        report.append({'step':step, 'exit_code':result.returncode, 'seconds':round(time.monotonic()-started,1)})
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report[-1]), flush=True)
        if result.returncode:
            print(log.read_text(encoding='utf-8')[-12000:], flush=True)
            raise SystemExit(result.returncode)

if __name__ == '__main__': main()
