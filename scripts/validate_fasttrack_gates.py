"""Run and retain read-only actual-runtime Guest evidence; stop on any failure."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tenants',nargs='+',type=int,choices=[17066,290,16868],required=True)
    parser.add_argument('--tokens-only',action='store_true')
    args=parser.parse_args()
    subprocess.run(['python',str(ROOT/'scripts/validate_fasttrack_runtime.py')],check=True,stdout=subprocess.DEVNULL)
    label='_'.join(map(str,args.tenants))
    if args.tokens_only: label += '_tokens'
    log=ROOT/f'generated/fasttrack_guest_{label}.log'
    print(json.dumps({'guest_gate':'started','tenants':args.tenants}),flush=True)
    # Transfer only in memory through stdin, never command arguments or files.
    credentials=subprocess.check_output(['docker','exec','neoretail-v9-multitenant-embedded-app-1','node','-e',
        "const p=process.env.DEMO_USER_PASSWORD; if(!p) throw Error('DEV login unavailable'); console.log(JSON.stringify({password:p,port:process.env.PORT||3000}));"],text=True,encoding='utf-8')
    with log.open('w',encoding='utf-8') as output:
        command=['docker','exec','-i','neoretail-v9-multitenant-superset-1','python',
            '/app/pythonpath/validate_fasttrack_guest.py','--embedded-credentials-stdin','--tenants',*map(str,args.tenants)]
        if args.tokens_only: command.append('--tokens-only')
        result=subprocess.run(command,input=credentials,text=True,encoding='utf-8',stdout=output,stderr=subprocess.STDOUT)
    del credentials
    text=log.read_text(encoding='utf-8')
    if result.returncode:
        print(text[-12000:],flush=True)
        raise SystemExit(result.returncode)
    prefix='FASTTRACK_TOKEN_REPORT=' if args.tokens_only else 'FASTTRACK_REPORT='
    line=next(line for line in reversed(text.splitlines()) if line.startswith(prefix))
    report=json.loads(line.split('=',1)[1])
    (ROOT/f'generated/fasttrack_guest_{label}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if args.tokens_only:
        print(json.dumps(report),flush=True)
        return
    print(json.dumps({'guest_gate':'PASS','tenants':args.tenants,
        'chart_checks':len(report['charts']),'isolation_checks':len(report['isolation']),
        'empty_charts':[{'tenant':c['tenant'],'chart':c['chart']} for c in report['charts'] if not c['rows']],
        'denied_token_checks':len(report['denied_tokens']),'native_filter_checks':len(report['native_filters']),
        'inventory_filter_checks':len(report['filters']),'period_checks':len(report['periods']),'cache_checks':len(report['cache'])}),flush=True)

if __name__ == '__main__': main()
