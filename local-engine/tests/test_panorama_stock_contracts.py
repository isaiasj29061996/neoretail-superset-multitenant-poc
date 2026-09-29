from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def bootstrap_text():
    return (ROOT / "superset" / "bootstrap_panorama.py").read_text(encoding="utf-8")


def test_stock_monthly_matches_power_bi_dax_components():
    bootstrap = "".join(bootstrap_text().split())
    assert "SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8ASstock_cost_sum" in bootstrap
    assert "SUM(COALESCE(estoque_unidades,0))::float8ASstock_qty_base" in bootstrap
    assert "(m.stock_qty_base*f.conversion_factor)::float8ASstock_qty_sum" in bootstrap


def test_stock_weekly_matches_power_bi_dax_components():
    bootstrap = "".join(bootstrap_text().split())
    assert "FROMgold.fato_semanalw" in bootstrap
    assert "(w.stock_qty_base*f.conversion_factor)::float8ASstock_qty_sum" in bootstrap
    assert "ORDERBYcd_weekDESC" in bootstrap
    assert "week_rank<=13" in bootstrap


def test_stock_card_preserves_literal_dax_u3m_asymmetry():
    bootstrap = bootstrap_text()
    transform = (
        ROOT
        / "superset"
        / "frontend-plugin"
        / "plugin-chart-neoretail-kpi"
        / "src"
        / "transformProps.js"
    ).read_text(encoding="utf-8")
    assert 'semantic_profile="stock_bundle"' in bootstrap
    assert "profile === 'stock_bundle'" in transform
    assert "values.reduce((sum, value) => sum + value, 0) / 3" in transform
    assert "latestStock?.values[index] == null ? null : latestStock.values[index] / 3" in transform
    assert 'summary_count=2' in bootstrap
    assert 'timeline_limit=13' in bootstrap
    assert 'labels="Estoque Preço Custo|Estoque Quantidade"' in bootstrap
    assert 'formats="currency|quantity"' in bootstrap


def test_stock_monthly_and_weekly_use_one_slice_each():
    bootstrap = bootstrap_text()
    assert 'add("stock_mensal", monthly_stock' in bootstrap
    assert 'add("stock_semanal", weekly_stock_card' in bootstrap
    assert 'summary_query_scope="summary"' in bootstrap
    assert 'timeline_query_scope="timeline"' in bootstrap
    assert 'stock_summary_' not in bootstrap


def test_stock_conversion_filter_reaches_both_stock_datasets():
    bootstrap = bootstrap_text()
    assert '"nr_panorama_stock_monthly_interactive"' in bootstrap
    assert '"nr_panorama_stock_weekly_card_interactive"' in bootstrap
    assert 'filter_targets["nm_measure"] = conversion_options.id' in bootstrap
    assert "monthly_stock.id" in bootstrap
    assert "weekly_stock_card.id" in bootstrap


def test_stock_change_does_not_replace_other_panorama_sections():
    bootstrap = bootstrap_text()
    assert 'add(f"giro_roi_{period}"' in bootstrap
    assert 'add(f"osa_{period}"' in bootstrap
    assert 'f"gap_{period}"' in bootstrap
