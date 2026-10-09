"""Real Parquet metadata preflight with synthetic blobs, without Azure or Spark jobs."""
from datetime import date
from types import SimpleNamespace


def make_blob(tmp_path, name, dates, complete=True, statistics=True):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from neoretail_local.partitioned_daily import REQUIRED
    columns = REQUIRED if complete else {'id_time','id_customer','id_location','id_item'}
    data = {c.upper():[290 if c == 'id_customer' else 1]*len(dates) for c in columns}
    data['ID_TIME'] = dates
    path = tmp_path/name
    pq.write_table(pa.table(data),path,write_statistics=statistics)
    return SimpleNamespace(name=name,size=path.stat().st_size,etag='"'+name+'"',path=path)


class LocalBlobs:
    def __init__(self, blobs):
        self.blobs = {b.name:b for b in blobs}
        self.requests = []

    def get_blob_client(self, name):
        blob = self.blobs[name]
        def download_blob(offset=None,length=None,**version):
            assert version['etag'] == blob.etag
            self.requests.append((name,offset,length))
            raw = blob.path.read_bytes()
            start = offset or 0
            content = raw[start:] if length is None else raw[start:start+length]
            return SimpleNamespace(readall=lambda:content)
        return SimpleNamespace(download_blob=download_blob)


def test_full_source_period_reads_old_and_new_schema_footers(tmp_path):
    from neoretail_local.tenant_source_audit import source_period
    old = make_blob(tmp_path,'old.parquet',[date(2024,5,1)],complete=False)
    new = make_blob(tmp_path,'new.parquet',[date(2026,10,4),date(2026,10,5)])
    source = LocalBlobs([old,new])
    result = source_period(source,[old,new])
    assert (result['min_date'],result['max_date'],result['rows']) == ('2024-05-01','2026-10-05',3)
    assert result['files_inspected'] == 2 and result['schema_variants'] == 2
    assert all(offset is not None for _,offset,_ in source.requests), 'no full file needed for complete footer statistics'
    assert [f['etag'] for f in result['manifest']] == [old.etag,new.etag]


def test_source_period_reads_dates_when_footer_statistics_are_absent(tmp_path):
    from neoretail_local.tenant_source_audit import source_period
    blob = make_blob(tmp_path,'no-stats.parquet',[date(2024,5,1),None,date(2026,10,5)],statistics=False)
    source = LocalBlobs([blob])
    result = source_period(source,[blob])
    assert (result['min_date'],result['max_date'],result['rows']) == ('2024-05-01','2026-10-05',3)
    assert source.requests[-1] == (blob.name,None,None)


def test_download_binds_content_to_etag_and_reuses_verified_cache(tmp_path,monkeypatch):
    from neoretail_local import candidates
    requests = []
    def download(**options):
        requests.append(options)
        assert options['etag'] == 'version-1'
        return SimpleNamespace(readinto=lambda stream:stream.write(b'version-one-content'))
    blob = SimpleNamespace(get_blob_properties=lambda:SimpleNamespace(etag='version-1'),download_blob=download)
    monkeypatch.setattr(candidates,'blob_service',lambda settings:SimpleNamespace(get_blob_client=lambda *args:blob))
    settings = SimpleNamespace(data_root=tmp_path,container='source')
    candidate = SimpleNamespace(blob_path='FATO/source.parquet')
    target = candidates.download_candidate(settings,candidate)
    assert target.read_bytes() == b'version-one-content'
    assert target.with_suffix('.parquet.etag').read_text() == 'version-1'
    assert candidates.download_candidate(settings,candidate) == target
    assert len(requests) == 1


def test_changed_source_download_preserves_previous_cache_and_cleans_partial(tmp_path,monkeypatch):
    import pytest
    from neoretail_local import candidates
    target = tmp_path/'raw-cache/FATO/source.parquet'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'previous-snapshot')
    target.with_suffix('.parquet.etag').write_text('previous-version')
    def changed(**options):
        assert options['etag'] == 'new-version'
        raise RuntimeError('source changed after properties were read')
    blob = SimpleNamespace(get_blob_properties=lambda:SimpleNamespace(etag='new-version'),download_blob=changed)
    monkeypatch.setattr(candidates,'blob_service',lambda settings:SimpleNamespace(get_blob_client=lambda *args:blob))
    with pytest.raises(RuntimeError,match='source changed'):
        candidates.download_candidate(SimpleNamespace(data_root=tmp_path,container='source'),
                                      SimpleNamespace(blob_path='FATO/source.parquet'))
    assert target.read_bytes() == b'previous-snapshot'
    assert target.with_suffix('.parquet.etag').read_text() == 'previous-version'
    assert not list(target.parent.glob('*.part'))
