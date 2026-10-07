from pathlib import Path
import sys

import pytest
import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))

from neoretail_local.power_query import apply_fact_contract, transform_dimensions
from neoretail_local.partitioned_daily import build_partitioned_daily_facts
from neoretail_local.silver import normalize_frame


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .appName("neoretail-power-query-contract-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def contract():
    return yaml.safe_load(
        (ROOT / "config/power_query_contracts.yaml").read_text(encoding="utf-8")
    )


def test_monthly_fact_recreates_power_query_date_and_types(spark):
    source = spark.createDataFrame([{
        "vl_month": "9", "vl_year": "2026", "id_item": 10,
        "ID_LOCATION": 20, "QTD_PERDA_OSA": "1.5", "VL_PERDA_OSA": "9.75", "QTD_PROBLEMAS_OSA": "2",
        "QTD_ITENS_ATIVOS": "3", "VOLUME_UNIDADES": "4.5", "FATURAMENTO": "5.5",
        "PRECO_MEDIO": "6.5", "CAUSA_OSA": "causa", "MOTIVO_OSA": "motivo",
    }])
    normalized = normalize_frame(source, id_customer=259, customer_name="3CORACOES")
    definition = contract()["fact_families"]["mensal_causa_osa"]
    result = apply_fact_contract(normalized, definition, "FATOS_MENSAL_CAUSA_OSA")
    row = result.first()
    assert str(row.data) == "2026-09-01"
    assert row.id_item == "10"
    assert row.qtd_problemas_osa == 2
    assert row.vl_perda_osa == 9.75
    assert "vl_month" not in result.columns


def test_daily_fact_accepts_plural_days_without_changing_silver_name(spark):
    definition = contract()["fact_families"]["fato_diaria"]
    values = {
        "ID_TIME": "2026-09-02", "ID_ITEM": "10", "ID_LOCATION": "20",
        "VOLUME_UNIDADES": 1, "FATURAMENTO": 2, "ESTOQUE_UNIDADES": 3,
        "ESTOQUE_TRANSITO": 4, "RUP": 0, "EST_VIRTUAL": 0,
        "DIAS_SEM_VENDAS": 5, "NIVEL_ATIVIDADE": "A",
        "QTD_ITENS_ATIVOS": 1, "QTD_PERDA_OSA": 0,
        "QTD_PROBLEMAS_OSA": 0, "QTD_ITEM_ATIVO_OSA": 1,
        "STATUS_ITEM_GERAL": 1, "DEMANDA_MEDIA": 1,
        "ESTOQUE_CD": 1, "PRECO_MEDIO_REF": 9.9,
    }
    source = normalize_frame(
        spark.createDataFrame([values]), id_customer=259, customer_name="3CORACOES"
    )
    result = apply_fact_contract(source, definition, "FATOS_PARTICULAR_DIARIA")
    row = result.first()
    assert row.dias_sem_venda == 5.0
    assert "dias_sem_vendas" not in result.columns


def test_etl_calc_v2_fills_only_power_query_nulls_and_uses_currency(spark):
    definition = contract()["fact_families"]["etl_calc_v2"]
    values = {column: None for column in definition["columns"]}
    values.update({"id_location": 1, "id_item": 2, "expectativa_vendas": 3})
    typed_row = {column: 1 for column in definition["columns"]}
    typed_row.update({"id_location": 9, "id_item": 9})
    source = normalize_frame(
        spark.createDataFrame([values, typed_row]),
        id_customer=259,
        customer_name="3CORACOES",
    )
    result = apply_fact_contract(source, definition, "CALCULO_OPORTUNIDADES")
    row = result.filter(F.col("id_location") == "1").first()
    assert row.id_location == "1"
    assert row.max_tp_activity_level == "I"
    assert row.estoque_unidades == 0.0
    assert str(result.schema["tvd"].dataType) == "DecimalType(19,4)"
    assert row.perda_osa_rup_m0 is None


def test_dimensions_apply_customer_and_retailer_contracts(spark):
    raw = {
        "dim_customer_raw": spark.createDataFrame([
            {"NM_CUSTOMER": "3CORACOES", "ID_CUSTOMER": 259},
            {"NM_CUSTOMER": "OUTRO", "ID_CUSTOMER": 2},
        ]),
        "dim_varejo_contratado_raw": spark.createDataFrame([
            {"NM_CUSTOMER": "3CORACOES", "CD_RETAILER": "CARREFOUR", "ID_CUSTOMER": 259, "ID_RETAILER": "10"},
            {"NM_CUSTOMER": "3CORACOES", "CD_RETAILER": "GPA", "ID_CUSTOMER": 259, "ID_RETAILER": "20"},
        ]),
        "dim_itens_raw": spark.createDataFrame([
            {"ID_CUSTOMER": 259, "ID_ITEM": 100, "CD_EAN": "789", "DESC_PRODUTO": "Cafe", "NM_BRAND": "Marca"},
            {"ID_CUSTOMER": 2, "ID_ITEM": 200, "CD_EAN": "000", "DESC_PRODUTO": "Outro", "NM_BRAND": "Marca"},
        ]),
        "dim_conversao_raw": spark.createDataFrame([
            {"id_customer": 259, "id_item": 100}, {"id_customer": 2, "id_item": 200},
        ]),
        "dim_catalogo_produtos_raw": spark.createDataFrame([
            {"INDUSTRIA": "3CORACOES", "ID_SEGMENT": 1, "CATEGORIA": "Cafe", "SUB_SEGMENTO": "Po", "SEGMENTO": "CERVEJA", "MEDIDA": "kg", "SABOR": "x", "PACK": "x", "RELACAO_PACK": "x", "COD_ARVORE_MERCADOLOGICA": "x"},
        ]),
        "dim_local_raw": spark.createDataFrame([
            {"ID_RETAILER": "10", "ID_LOCATION": "30", "CNPJ_COMPLETO": "12345678000190", "UF": "SP", "COD_LOJA": "1", "NOME_DA_LOJA": "Loja", "ID_LOCATION_TYPE": 1, "DH_UPDATED": "2026-09-01", "GRUPO_ECONOMICO": "Rede", "CIDADE": "Sao Paulo", "BANDEIRA": "B", "TIPO_LOCAL": "L"},
            {"ID_RETAILER": "20", "ID_LOCATION": "40", "CNPJ_COMPLETO": "123", "UF": "SP", "COD_LOJA": "2", "NOME_DA_LOJA": "GPA", "ID_LOCATION_TYPE": 1, "DH_UPDATED": "2026-09-01", "GRUPO_ECONOMICO": "GPA", "CIDADE": "Sao Paulo", "BANDEIRA": "B", "TIPO_LOCAL": "L"},
        ]),
    }
    result = transform_dimensions(raw, "3CORACOES", 259)
    assert result["dim_customer"].count() == 1
    assert result["dim_itens"].first().item == "789 - Cafe"
    assert result["dim_local"].first().regiao == "Sudeste"
    assert result["dim_local"].first().cnpj_formatado == "12.345.678/0001-90"
    assert result["aux_contratado_segmento"].first().segmento == "CERVEJA"
    assert result["dim_catalogo_local"].count() == 1


@pytest.mark.parametrize('customer_id,customer_name', [(142, 'AMBEV'), (290, 'LACTALIS')])
def test_partitioned_customer_daily_builds_dashboard_contracts(spark, customer_id, customer_name):
    row = {
        "id_time": "2026-09-09", "id_location": 20, "id_item": 10,
        "ID_CUSTOMER": customer_id, "VL_QUANTITY_SOLD": 2.0,
        "VL_SALES_TOTAL_VALUE": 20.0, "VL_QUANTITY_IN_STOCK": 8.0,
        "VL_STOCK_IN_WAREHOUSE": 3.0, "VL_SECURITY_STOCK": 2.0,
        "VL_MAX_STOCK": 12.0, "VL_SALES_PRICE": 10.0, "VL_PRICE_COST": 7.0,
        "VL_QUANTITY_OUT_OF_STOCK": 0, "VL_QUANTITY_VIRTUAL_STOCK": 0,
        "VL_STOCK_IN_TRANSFER": 1.0, "BL_OSA_ISSUE": 1,
        "TP_OSA_PRODUCT_CLASS": 1, "VL_QUANTITY_SALE_PREDICTED": 3.0,
        "VL_AVERAGE_DEMAND_TRUNCATED": 1.5, "VL_QUANTITY_OSA_LOST_SALES": 1.0,
        "VL_VALUE_OSA_LOST_SALES": 10.0, "VL_AVERAGE_YEARLY_STOCK_TURNOVER": 4.0,
        "VL_AVERAGE_MONTHLY_STOCK_TURNOVER": 2.0, "TP_ACTIVITY_LEVEL": "F",
        "TP_OSA_ROOT_CAUSE": "RUPTURA", "VL_TVD": 5.0, "VL_IVD": 0.0,
        "VL_DAYS_WITH_NO_SALE": 1, "QUANTITY_VALID_ITEM": 1, "BL_RCA_VALID": 1,
    }
    result = build_partitioned_daily_facts(spark.createDataFrame([row]), customer_id, customer_name=customer_name)
    assert set(result) == {
        "fato_diaria", "fato_semanal", "fato_historico", "fato_ivd_tvd",
        "fato_nivel_atividade", "fato_mensal_causa_osa", "fato_preco",
        "etl_calc_v2", "calculo_oportunidades",
    }
    assert result["fato_diaria"].first().id_customer == customer_id
    assert result["fato_preco"].first().customer == customer_name
    assert result["fato_semanal"].first().cd_week == "2026-37"
    opportunity = result["calculo_oportunidades"].first()
    assert str(opportunity.tvd) == "5.0000"
    assert opportunity.regra_critico == "F"
    osa = result["fato_mensal_causa_osa"].first()
    assert osa.vl_perda_osa == 10.0
    assert osa.qtd_perda_osa == 1.0
    assert osa.motivo_osa == "Ruptura na loja"


def test_partitioned_source_rejects_null_or_foreign_identity(spark):
    from neoretail_local.partitioned_daily import REQUIRED, _base
    columns = sorted(REQUIRED)
    for invalid in (None, '142', '17066'):
        row = {column: '0' for column in columns}
        row['id_customer'] = invalid
        frame = spark.createDataFrame([tuple(row[c] for c in columns)], ', '.join(c + ' string' for c in columns))
        with pytest.raises(RuntimeError, match='tenant'):
            _base(frame, 290)
