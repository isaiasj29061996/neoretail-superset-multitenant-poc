"""Read-only Azure source inventory; credentials are never printed."""
import json
from pathlib import Path
import sys
import yaml
from azure.storage.blob import BlobServiceClient
import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'local-engine'))
from neoretail_local.scoped_dimensions import BlobRangeReader

values = {}
for line in (root / '.env').read_text(encoding='utf-8-sig').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('\"').strip("'")
try:
    service = BlobServiceClient.from_connection_string(values['AZURE_STORAGE_CONNECTION_STRING'])
    container = values.get('AZURE_STORAGE_CONTAINER', 'neoretail')
    base = values.get('AZURE_BLOB_PREFIX', '').strip('/')
    sources = yaml.safe_load((root / 'config/source_catalog.yaml').read_text(encoding='utf-8'))['sources']
    evidence = []
    for name, source in sources.items():
        path = '/'.join(p for p in [base, source['path']] if p)
        reader = BlobRangeReader(service.get_blob_client(container, path))
        parquet = pq.ParquetFile(reader)
        item = {'name': name, 'path': path, 'bytes': reader.size, 'rows': parquet.metadata.num_rows,
                'columns': parquet.schema_arrow.names, 'etag': reader.etag}
        if name == 'dim_customer':
            rows = parquet.read().to_pylist()
            matches = [r for r in rows if str(r.get('NM_CUSTOMER', r.get('nm_customer', ''))).strip().upper() == 'LACTALIS']
            if len(matches) != 1 or int(matches[0].get('ID_CUSTOMER', matches[0].get('id_customer'))) != 290:
                raise RuntimeError('AMBIGUOUS_LACTALIS_IDENTITY')
            item['lactalis_identity'] = matches
        evidence.append(item)
    prefix = '/'.join(p for p in [base, 'FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/'] if p)
    facts = [{'path': b.name, 'bytes': b.size, 'etag': b.etag} for b in service.get_container_client(container).list_blobs(name_starts_with=prefix) if b.name.endswith('.parquet')]
    if not facts: raise RuntimeError('LACTALIS_FACTS_MISSING')
    result = {'id_customer': 290, 'nm_customer': 'LACTALIS', 'dimensions': evidence, 'facts_prefix': prefix,
              'facts_files': len(facts), 'facts_bytes': sum(f['bytes'] for f in facts), 'facts': facts}
    (root / 'generated/lactalis_source_preflight_current.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({**result, 'facts': 'see evidence file'}, ensure_ascii=False))
except Exception as error:
    print('SOURCE_PREFLIGHT_FAILED: ' + type(error).__name__)
    sys.exit(1)
