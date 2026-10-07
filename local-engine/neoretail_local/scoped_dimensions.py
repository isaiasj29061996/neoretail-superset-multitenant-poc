"""Read Azure Parquet by ranges; persist only selected customer dimensions."""
from __future__ import annotations
import io
import json
from azure.core import MatchConditions
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


class BlobRangeReader(io.RawIOBase):
    def __init__(self, blob):
        self.blob = blob
        properties = blob.get_blob_properties()
        self.size, self.etag, self.position = properties.size, properties.etag, 0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        if self.position < 0: raise ValueError('Negative position')
        return self.position
    def read(self, size=-1):
        length = min(self.size - self.position, size if size >= 0 else self.size)
        if length <= 0: return b''
        result = self.blob.download_blob(offset=self.position, length=length, etag=self.etag,
                                        match_condition=MatchConditions.IfNotModified).readall()
        self.position += len(result)
        return result


def select_dimension(table, customer_id, customer_name, retailers=()):
    columns = {name.strip().lower(): name for name in table.column_names}
    mask = None
    for key, value in [('id_customer', str(customer_id)), ('nm_customer', customer_name), ('industria', customer_name)]:
        if key in columns:
            column = pc.cast(table[columns[key]], pa.string())
            condition = pc.equal(pc.utf8_upper(pc.utf8_trim_whitespace(column)), value.upper())
            mask = condition if mask is None else pc.and_(mask, condition)
    if mask is None:
        if 'id_retailer' not in columns or not retailers:
            raise RuntimeError('Dimension has no customer identity or verified shared retailer relation')
        mask = pc.is_in(pc.cast(table[columns['id_retailer']], pa.string()), value_set=pa.array(sorted(retailers)))
    return table.filter(pc.fill_null(mask, False))


def materialize_dimensions(settings, catalog, service):
    sources = catalog['sources']
    order = ['dim_customer', 'dim_varejo_contratado', 'dim_itens', 'dim_conversao', 'dim_catalogo_produtos', 'dim_local']
    if set(sources) != set(order):
        raise RuntimeError('Scoped dimensions require explicit review of the source catalog')
    root = settings.data_root / 'raw-cache' / f'id_customer={settings.id_customer}'
    root.mkdir(parents=True, exist_ok=True)
    retailers, evidence, result = set(), [], {}
    for name in order:
        source = sources[name]
        path = '/'.join(p.strip('/') for p in [settings.blob_prefix, source['path']] if p)
        reader = BlobRangeReader(service.get_blob_client(settings.container, path))
        parquet = pq.ParquetFile(reader)
        target = root / (source['bronze_table'] + '.parquet')
        temporary = target.with_suffix('.partial')
        count = 0
        with pq.ParquetWriter(temporary, parquet.schema_arrow, compression='snappy') as writer:
            for batch in parquet.iter_batches(batch_size=65536):
                selected = select_dimension(pa.Table.from_batches([batch]), settings.id_customer, settings.nm_customer, retailers)
                if name == 'dim_varejo_contratado':
                    column = next(c for c in selected.column_names if c.lower() == 'id_retailer')
                    retailers.update(str(x) for x in selected[column].to_pylist() if x is not None)
                if selected.num_rows:
                    writer.write_table(selected)
                count += selected.num_rows
        if not count: raise RuntimeError(f'{name}: scoped source returned no rows')
        temporary.replace(target)
        result[source['bronze_table']] = target
        evidence.append({'source': path, 'table': source['bronze_table'], 'rows': count,
                         'source_rows': parquet.metadata.num_rows, 'source_bytes': reader.size,
                         'etag': reader.etag, 'id_customer': settings.id_customer,
                         'scope': 'contracted_retailers' if name == 'dim_local' else 'customer_identity'})
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    (settings.output_dir / f'scoped_dimensions_{settings.id_customer}.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    return result
