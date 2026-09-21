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
    # Keep the accented literal ASCII-safe because PowerShell 5 pipelines can
    # otherwise publish it to psql as question marks.
    assert sql.count("U&'DEP\\00D3SITO'") >= 2


def test_ivd_serving_uses_ultra_slow_risk_and_both_location_dimensions():
    sql = _read("analytics-db/marts/31_overview_performance.sql")

    assert "LEFT JOIN gold.dim_catalogo_local catalogo" in sql
    assert "catalogo.id_customer = f.id_customer" in sql
    assert "catalogo.id_location = f.id_location" in sql
    assert "c.regra_critico = 'U'" in sql
    assert "COALESCE(c.ivd, 0) > 0" in sql
    assert "c.id_item IS NOT NULL" in sql
    assert sql.count("U&'DEP\\00D3SITO'") >= 2


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


def test_critical_reconciliation_is_three_way_and_sql_publish_is_utf8_safe():
    validator = _read("superset/validate_stock_headlines.py")
    publisher = _read("create-superset-kpi-views.ps1")
    serving = _read("analytics-db/marts/30_neoretail_serving_marts.sql")

    assert "def independent_counts" in validator
    assert "def mart_counts" in validator
    assert "def latest_chart_counts" in validator
    assert '"source_rows is inventory, not a critical-item count"' in validator
    assert "Reconciliação divergente" in validator
    assert "$OutputEncoding = [System.Text.UTF8Encoding]::new($false)" in publisher
    assert "Get-Content -Raw -Encoding UTF8" in publisher
    assert serving.index("DROP MATERIALIZED VIEW IF EXISTS gold.nr_osa_semantic_default") < serving.index(
        "DROP MATERIALIZED VIEW IF EXISTS gold.nr_overview_default_summary"
    )


def test_remaining_uncertified_metrics_are_recorded():
    certification = _read("docs/metric_certification_overview.md")

    assert "PENDENTE_CALENDARIO_M0" in certification
    assert "COUNT(id_item)" in certification
    assert "COUNT DISTINCT" not in certification.upper()


def test_giro_and_osa_use_additive_components_for_u3m():
    bootstrap = _read("superset/bootstrap_overview.py")

    assert 'semantic_profile="weighted_average"' in bootstrap
    assert 'semantic_profile="osa_bundle"' in bootstrap
    assert '"giro_sum": metric' in bootstrap
    assert '"giro_count": metric' in bootstrap
    assert '"osa_problem": metric' in bootstrap
    assert '"osa_active": metric' in bootstrap


def test_overview_default_path_is_compact_and_falls_back_for_detail_filters():
    bootstrap = _read("superset/bootstrap_overview.py")
    sql = _read("analytics-db/marts/37_interactive_p1_summary.sql")

    assert "def overview_semantic_sql()" in bootstrap
    assert "SELECT * FROM gold.nr_overview_semantic_default" in bootstrap
    assert "history_filtered" in bootstrap
    assert 'database, "nr_overview_interactive"' in bootstrap
    assert "CREATE MATERIALIZED VIEW gold.nr_overview_default_summary" in sql
    assert "GROUP BY data, id_customer, tp_activity_level, activity_level" in sql
    assert "NULL::text AS rede" in sql


def test_conversion_selector_and_regional_sellout_are_explicit():
    sql = _read("analytics-db/marts/39_overview_semantic_certification.sql")
    bootstrap = _read("superset/bootstrap_overview.py")

    assert "gold.nr_conversion_options" in sql
    assert "c.id_customer = h.id_customer" in sql
    assert "c.id_item::text = h.id_item" in sql
    assert "MAX(c.conversion_rate)" in sql
    assert "WHEN faturamento_sum > 0 THEN faturamento_sum" in sql
    assert "GROUP BY data, id_customer, regiao, nm_measure" in sql
    assert '("nm_measure", "Medida", [])' in bootstrap
    assert '"multiSelect": column != "nm_measure"' in bootstrap
    assert "conversion_filters|length != 1" in bootstrap
    assert "conversion_filters[0].get('val')|length != 1" in bootstrap


def test_quantity_stock_and_ratio_profiles_match_dax_shapes():
    sql = _read("analytics-db/marts/39_overview_semantic_certification.sql")
    bootstrap = _read("superset/bootstrap_overview.py")
    transform = _read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js")

    assert "WHEN nm_measure = 'valor' THEN SUM(faturamento_sum)" in sql
    assert "SUM(stock_units_sum) * MAX(conversion_rate)" in sql
    assert 'semantic_profile="stock_bundle"' in bootstrap
    assert "profile === 'roi'" in transform
    assert "profile === 'markup'" in transform
    assert "profile === 'osa_bundle'" in transform
    assert "if (!profile) return null" in transform


def test_osa_uses_monthly_cause_source_and_non_distinct_alert_counts():
    sql = _read("analytics-db/marts/39_overview_semantic_certification.sql")
    bootstrap = _read("superset/bootstrap_overview.py")

    assert "FROM gold.fato_mensal_causa_osa f" in sql
    assert "b.loss_qty_sum * f.conversion_rate * (b.price_sum / b.price_count)" in sql
    assert "COUNT(o.id_item) FILTER" in sql
    assert "a.nm_activity_level = 'Fast Mover'" in sql
    assert "o.max_tp_activity_level = 'S'" in sql
    assert "COUNT(DISTINCT" not in sql
    assert "show_tasks=True" in bootstrap
    assert 'semantic_profile="osa_bundle"' in bootstrap


def test_activity_bars_are_allowlisted_and_ordered():
    transform = _read("superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js")
    expected = ["Fast Mover", "Slow Mover", "Ultra Slow Mover", "New Mover"]

    positions = [transform.index(f"'{level}'", transform.index("ALLOWED_ACTIVITY_LEVELS")) for level in expected]
    assert positions == sorted(positions)
    assert "ALLOWED_ACTIVITY_LEVELS.includes(row.category)" in transform
    assert ".filter(category => categories.has(category))" in transform


def test_calendar_anchor_remains_explicitly_partial_without_source_contract():
    certification = _read("docs/metric_certification_overview.md")
    repository_text = "\n".join(
        _read(path) for path in (
            "config/power_query_contracts.yaml",
            "docs/power_query_parity.md",
            "superset/bootstrap_overview.py",
        )
    )

    assert "0_0_CALENDARIO[M0]" not in repository_text
    assert "PENDENTE_CALENDARIO_M0" in certification
