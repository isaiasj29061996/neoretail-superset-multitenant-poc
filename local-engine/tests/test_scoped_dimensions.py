import io
from types import SimpleNamespace
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from neoretail_local.scoped_dimensions import BlobRangeReader, select_dimension


def test_customer_identity_is_intersection_and_nulls_fail_closed():
    frame = pa.table({'ID_CUSTOMER': [290, 142, 17066, None, 290], 'NM_CUSTOMER': ['LACTALIS', 'AMBEV', 'PANDURATA', 'LACTALIS', 'OTHER']})
    assert select_dimension(frame, 290, 'LACTALIS').to_pylist() == [{'ID_CUSTOMER': 290, 'NM_CUSTOMER': 'LACTALIS'}]


def test_industry_catalog_and_shared_locations_are_scoped():
    catalog = pa.table({'industria': [' Lactalis ', 'AMBEV'], 'id_segment': [1, 2]})
    assert select_dimension(catalog, 290, 'LACTALIS')['id_segment'].to_pylist() == [1]
    shared = pa.table({'ID_RETAILER': [1, 2, 3], 'ID_LOCATION': [10, 20, 30]})
    assert select_dimension(shared, 290, 'LACTALIS', {'2'})['ID_LOCATION'].to_pylist() == [20]
    with pytest.raises(RuntimeError):
        select_dimension(shared, 290, 'LACTALIS')
    with pytest.raises(RuntimeError):
        select_dimension(pa.table({'unknown': [1]}), 290, 'LACTALIS')


def test_remote_reads_are_bounded_and_bound_to_etag():
    data = io.BytesIO()
    pq.write_table(pa.table({'ID_CUSTOMER': [290, 142]}), data)
    payload = data.getvalue()
    calls = []
    class Blob:
        def get_blob_properties(self): return SimpleNamespace(size=len(payload), etag='version-1')
        def download_blob(self, **kwargs):
            calls.append(kwargs)
            start = kwargs['offset']
            return SimpleNamespace(readall=lambda: payload[start:start + kwargs['length']])
    reader = BlobRangeReader(Blob())
    assert pq.ParquetFile(reader).read()['ID_CUSTOMER'].to_pylist() == [290, 142]
    assert all(c['etag'] == 'version-1' and c['length'] <= len(payload) for c in calls)
    reader.seek(len(payload))
    assert reader.read() == b''
