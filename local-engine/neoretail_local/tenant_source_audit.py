"""Discover a registered tenant's real Azure daily source before activation."""
import argparse
import io
import json
import os
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc
import yaml
from azure.storage.blob import BlobServiceClient
from azure.core import MatchConditions
from .customers import resolve_tenant
from .partitioned_daily import REQUIRED
from .silver_contracts import canonical_column_mapping


def source_period(container, files):
    """Read every real footer; download one date column only if stats are absent."""
    bounds = []
    rows = 0
    empty = []
    available = set()
    variants = set()
    manifest = []
    for blob in files:
        client = container.get_blob_client(blob.name)
        version = {'etag':blob.etag,'match_condition':MatchConditions.IfNotModified}
        tail = client.download_blob(offset=blob.size-8,length=8,**version).readall()
        assert tail[-4:] == b'PAR1', ('invalid parquet footer',blob.name)
        length = int.from_bytes(tail[:4],'little')
        assert 0 < length <= blob.size-8, ('invalid parquet metadata length',blob.name)
        footer = client.download_blob(offset=blob.size-8-length,length=length+8,**version).readall()
        parquet = pq.ParquetFile(io.BytesIO(b'PAR1'+footer))
        mapping = canonical_column_mapping(parquet.schema_arrow.names)
        columns = set(mapping.values())
        available.update(columns)
        variants.add(tuple(sorted(columns)))
        assert {'id_time','id_customer','id_location','id_item'} <= columns, ('missing source identity/date keys',blob.name)
        date_column = next(c for c,value in mapping.items() if value == 'id_time')
        rows += parquet.metadata.num_rows
        manifest.append({'path':blob.name,'etag':blob.etag,'bytes':blob.size,'rows':parquet.metadata.num_rows})
        if not parquet.metadata.num_rows:
            empty.append(blob.name)
            continue
        complete = True
        for group in range(parquet.metadata.num_row_groups):
            rg = parquet.metadata.row_group(group)
            column = next(rg.column(i) for i in range(rg.num_columns) if rg.column(i).path_in_schema == date_column)
            stats = column.statistics
            if stats and stats.has_min_max:
                bounds.append((str(stats.min),str(stats.max)))
            elif not stats or stats.num_values:
                complete = False
        if not complete:
            table = pq.read_table(io.BytesIO(client.download_blob(**version).readall()),columns=[date_column])
            values = pc.min_max(table.column(0)).as_py()
            if values['min'] is not None:
                bounds.append((str(values['min']),str(values['max'])))
    assert bounds, 'source has no dated records'
    # Historical files have fewer metric columns. Preserve the existing source
    # evolution contract; require the complete dataset's fields, not every file's.
    assert REQUIRED <= available, ('unsupported complete source layout',sorted(REQUIRED-available))
    return {'min_date':min(v[0] for v in bounds),'max_date':max(v[1] for v in bounds),
            'rows':rows,'files_inspected':len(files),'empty_files':empty,'schema_variants':len(variants),
            'manifest':manifest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant',required=True)
    args = parser.parse_args()
    tenant = resolve_tenant(Path(os.getenv('CUSTOMERS_CONFIG_PATH','/workspace/config/customers.yaml')),args.tenant)
    root = os.getenv('AZURE_BLOB_PREFIX','').strip('/')
    container = BlobServiceClient.from_connection_string(os.environ['AZURE_STORAGE_CONNECTION_STRING']).get_container_client(os.getenv('AZURE_STORAGE_CONTAINER','neoretail'))
    daily = '/'.join(p for p in (root,'FATO/CUSTOMER/DAILY/') if p)
    matches = [p.name.rstrip('/') for p in container.walk_blobs(name_starts_with=daily,delimiter='/')
               if p.name.rstrip('/').rsplit('/',1)[-1] == 'NM_CUSTOMER='+tenant.nm_customer]
    assert len(matches)==1, ('actual source prefix not unique or absent',tenant.tenant_key,matches)
    prefix = matches[0]
    files = [b for b in container.list_blobs(name_starts_with=prefix+'/') if b.name.lower().endswith('.parquet')]
    assert files, 'no parquet source'
    period = source_period(container,files)
    empty = set(period['empty_files'])
    sample = min((f for f in files if f.name not in empty),key=lambda f:f.size)
    table = pq.read_table(io.BytesIO(container.download_blob(sample.name,etag=sample.etag,
        match_condition=MatchConditions.IfNotModified).readall()))
    mapping = canonical_column_mapping(table.column_names)
    table = table.rename_columns([mapping[c] for c in table.column_names])
    missing = sorted(REQUIRED-set(table.column_names))
    assert not missing, ('source layout unsupported',missing)
    identities = table.column('id_customer').to_pylist()
    assert identities and all(i==tenant.id_customer for i in identities), 'sample has null/foreign identity'
    dates = table.column('id_time').to_pylist()
    catalog = yaml.safe_load(Path(os.getenv('SOURCE_CATALOG_PATH','/workspace/config/source_catalog.yaml')).read_text(encoding='utf-8'))
    dimensions = []
    for name, definition in catalog['sources'].items():
        path = '/'.join(p for p in (root,definition['path']) if p)
        assert container.get_blob_client(path).exists(), ('missing dimension',name)
        dimensions.append({'name':name,'path':path})
    identity_path = next(d['path'] for d in dimensions if d['name']=='dim_customer')
    identity = pq.read_table(io.BytesIO(container.download_blob(identity_path).readall()))
    mapping = canonical_column_mapping(identity.column_names)
    identity = identity.rename_columns([mapping[c] for c in identity.column_names])
    corporate = [r for r in identity.select(['id_customer','nm_customer']).to_pylist() if r['id_customer']==tenant.id_customer]
    assert corporate and all(r['nm_customer'].strip()==tenant.nm_customer for r in corporate), ('corporate identity mismatch',corporate)
    report = {'tenant_key':tenant.tenant_key,'id_customer':tenant.id_customer,'nm_customer':tenant.nm_customer,
              'source_prefix':prefix[len(root)+1:] if root else prefix,
              'source_layout':'partitioned_customer_daily_v1','files':len(files),'bytes':sum(f.size for f in files),
              'sample':{'path':sample.name,'rows':len(identities),'ids':sorted(set(identities)),
                        'min_date':str(min(dates)),'max_date':str(max(dates))},
              'dimensions':dimensions,'corporate_identity':corporate,'full_date_range':period}
    output = Path(os.getenv('OUTPUT_DIR','/workspace/generated'))/f'fasttrack_source_{tenant.id_customer}.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__': main()
