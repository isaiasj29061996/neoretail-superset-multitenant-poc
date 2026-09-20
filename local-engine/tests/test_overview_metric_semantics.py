from pathlib import Path


HOST_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path("/repo") if Path("/repo/.git").exists() else HOST_ROOT


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_tvd_serving_excludes_power_bi_location_types_in_both_dimensions():
    sql = _read("analytics-db/marts/30_neoretail_serving_marts.sql")

    assert "LEFT JOIN gold.dim_catalogo_local catalogo" in sql
    assert "catalogo.id_customer = o.id_customer" in sql
    assert "catalogo.id_location = o.id_location" in sql
    assert "COALESCE(o.tipo_local, '')" in sql
    assert "COALESCE(catalogo.tipo_local, '')" in sql
    assert sql.count("'LOJA VIRTUAL'") >= 2
    assert sql.count("'CD'") >= 2
    assert sql.count("'DEPÓSITO'") >= 2


def test_ivd_serving_uses_ultra_slow_risk_and_both_location_dimensions():
    sql = _read("analytics-db/marts/31_overview_performance.sql")

    assert "LEFT JOIN gold.dim_catalogo_local catalogo" in sql
    assert "catalogo.id_customer = f.id_customer" in sql
    assert "catalogo.id_location = f.id_location" in sql
    assert "c.regra_critico = 'U'" in sql
    assert "COALESCE(c.ivd, 0) > 0" in sql
    assert "c.id_item IS NOT NULL" in sql


def test_overview_uses_daily_query_for_filtered_last_nonblank_and_monthly_visual():
    bootstrap = _read("superset/bootstrap_overview.py")

    assert bootstrap.count('semantic_period="month_last_nonblank"') == 2
    assert bootstrap.count('time_grain_sqla="P1D"') >= 2
    assert bootstrap.count("show_tasks=True") >= 2


def test_overview_keeps_native_filter_and_rls_contracts():
    bootstrap = _read("superset/bootstrap_overview.py")
    sql = _read("analytics-db/marts/30_neoretail_serving_marts.sql")

    for column in (
        "rede",
        "bandeira",
        "uf",
        "cidade",
        "tipo_local",
        "loja",
        "descricao_marca",
        "hierarquia_1",
        "hierarquia_2",
        "hierarquia_3",
        "item",
    ):
        assert f'"{column}"' in bootstrap

    assert "o.id_customer" in sql
    assert "ix_nr_tvd_daily_customer_data" in sql
    assert "ON gold.nr_tvd_daily (id_customer, data)" in sql


def test_remaining_uncertified_metrics_are_recorded():
    certification = _read("docs/metric_certification_overview.md")

    assert "PENDENTE_CALENDARIO_M0" in certification
    assert "COUNT(ID_ITEM)" in certification
    assert "COUNT DISTINCT" not in certification


def test_giro_and_osa_use_additive_components_for_u3m():
    bootstrap = _read("superset/bootstrap_overview.py")

    assert 'semantic_profile="weighted_average"' in bootstrap
    assert 'semantic_profile="one_minus_ratio"' in bootstrap
    assert '"giro_sum": metric' in bootstrap
    assert '"giro_count": metric' in bootstrap
    assert '"osa_problem": metric' in bootstrap
    assert '"osa_active": metric' in bootstrap


def test_overview_default_path_is_compact_and_falls_back_for_detail_filters():
    bootstrap = _read("superset/bootstrap_overview.py")
    sql = _read("analytics-db/marts/37_interactive_p1_summary.sql")

    assert "def overview_semantic_sql()" in bootstrap
    assert "SELECT * FROM gold.nr_overview_default_summary" in bootstrap
    assert "SELECT * FROM gold.nr_overview_summary" in bootstrap
    assert 'database, "nr_overview_interactive"' in bootstrap
    assert "CREATE MATERIALIZED VIEW gold.nr_overview_default_summary" in sql
    assert "GROUP BY data, id_customer, tp_activity_level, activity_level" in sql
    assert "NULL::text AS rede" in sql
