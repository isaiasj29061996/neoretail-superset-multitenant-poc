from pathlib import Path
import sys

import pytest
from pyspark.sql import SparkSession


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))

from neoretail_local.gold_serving import (
    AMBEV_LAKE_ONLY,
    AMBEV_SERVING_WINDOWS,
    apply_serving_window,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .appName("neoretail-gold-serving-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_ambev_lake_only_excludes_unused_dashboard_facts():
    assert AMBEV_LAKE_ONLY == {
        "fato_diaria",
        "fato_nivel_atividade",
        "fato_preco",
    }


def test_serving_windows_cover_dashboard_fact_families():
    assert set(AMBEV_SERVING_WINDOWS) == {
        "fato_ivd_tvd",
        "fato_semanal",
        "fato_historico",
        "fato_mensal_causa_osa",
    }


def test_apply_serving_window_uses_source_max_date(spark):
    frame = spark.createDataFrame(
        [
            {"id_customer": 142, "id_time": "2026-01-01", "value": 1},
            {"id_customer": 142, "id_time": "2026-01-08", "value": 2},
            {"id_customer": 142, "id_time": "2026-01-10", "value": 3},
        ]
    )
    filtered, max_date, cutoff = apply_serving_window(frame, "id_time", 3)
    values = [row.value for row in filtered.orderBy("value").collect()]
    assert max_date == "2026-01-10"
    assert cutoff == "2026-01-08"
    assert values == [2, 3]


def test_apply_serving_window_zero_keeps_full_history(spark):
    frame = spark.createDataFrame(
        [
            {"id_time": "2026-01-01", "value": 1},
            {"id_time": "2026-01-10", "value": 2},
        ]
    )
    filtered, max_date, cutoff = apply_serving_window(frame, "id_time", 0)
    assert filtered.count() == 2
    assert max_date is None
    assert cutoff is None
