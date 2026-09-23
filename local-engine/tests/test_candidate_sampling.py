from neoretail_local.candidates import Candidate, select_candidate_fraction


def _candidate(index: int, size: int = 100) -> Candidate:
    return Candidate(
        blob_path=f"FATO/CUSTOMER/DAILY/NM_CUSTOMER=AMBEV/part-{index:04d}.parquet",
        relative_path=f"part-{index:04d}.parquet",
        file_name=f"part-{index:04d}.parquet",
        family="customer_daily",
        retailer=f"part_{index:04d}",
        bronze_table="candidate_customer_daily",
        size_bytes=size,
        last_modified=None,
    )


def test_fraction_is_deterministic_and_not_prefix_based():
    source = [_candidate(index) for index in range(100)]
    first = select_candidate_fraction(source, 0.35)
    second = select_candidate_fraction(list(reversed(source)), 0.35)
    assert [row.blob_path for row in first] == [row.blob_path for row in second]
    assert len(first) == 35
    assert {row.file_name for row in first} != {row.file_name for row in source[:35]}


def test_fraction_targets_source_bytes_when_files_have_different_sizes():
    source = [_candidate(index, size=(index + 1) * 10) for index in range(20)]
    selected = select_candidate_fraction(source, 0.35)
    total = sum(row.size_bytes for row in source)
    chosen = sum(row.size_bytes for row in selected)
    assert chosen >= total * 0.35
    assert chosen < total


def test_full_fraction_keeps_every_file():
    source = [_candidate(index) for index in range(10)]
    assert len(select_candidate_fraction(source, 1.0)) == 10
