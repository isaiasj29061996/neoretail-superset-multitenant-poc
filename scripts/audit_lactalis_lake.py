"""Full read-only lake isolation gate; counts come from current Parquet files."""
import argparse
import json
from pathlib import Path
import pyarrow.dataset as ds
import pyarrow.parquet as pq

parser = argparse.ArgumentParser()
parser.add_argument('--layer', required=True, choices=['bronze', 'silver', 'gold'])
args = parser.parse_args()
root = Path('/data/lake') / args.layer
result = []
failed = False
for table in sorted(root.iterdir()):
    if not table.is_dir(): continue
    files = sorted(table.rglob('*.parquet'))
    if not files: continue
    data = ds.dataset([str(f) for f in files], format='parquet')
    rows = sum(pq.read_metadata(f).num_rows for f in files)
    identity_columns = [c for c in data.schema.names if c.lower() in ('id_customer', 'nm_customer', '_customer_name', 'customer', 'industria')]
    ids, names, nulls = set(), set(), 0
    for batch in data.to_batches(columns=identity_columns, batch_size=262144) if identity_columns else []:
        for column in identity_columns:
            values = batch.column(column)
            nulls += values.null_count
            unique = values.unique().to_pylist()
            if column.lower() == 'id_customer': ids.update(int(v) for v in unique if v is not None)
            else: names.update(str(v).strip().upper() for v in unique if v is not None)
    if ids - {290} or names - {'LACTALIS'} or nulls: failed = True
    if not identity_columns:
        if table.name != 'dim_local_raw': failed = True
        else:
            aux = ds.dataset([str(f) for f in (root / 'dim_varejo_contratado_raw').rglob('*.parquet')], format='parquet').to_table()
            key = next(c for c in aux.column_names if c.lower() == 'id_retailer')
            allowed = {str(x) for x in aux[key].to_pylist()}
            key = next(c for c in data.schema.names if c.lower() == 'id_retailer')
            actual = {str(x) for x in data.to_table(columns=[key])[key].to_pylist()}
            if actual - allowed: failed = True
    item = {'layer': args.layer, 'table': table.name, 'rows': rows, 'ids': sorted(ids), 'names': sorted(names), 'null_identity': nulls, 'bytes': sum(f.stat().st_size for f in files)}
    result.append(item)
    print(json.dumps(item), flush=True)
report = {'passed': not failed, 'id_customer': 290, 'tables': result}
Path(f'/workspace/generated/lactalis_{args.layer}_isolation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
if failed: raise SystemExit('ISOLATION_GATE_FAILED')
