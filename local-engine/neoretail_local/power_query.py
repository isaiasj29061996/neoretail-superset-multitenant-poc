"""Equivalencias PySpark das consultas M extraidas do modelo semantico."""

from __future__ import annotations

from difflib import get_close_matches
from typing import Any

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T

from .silver import normalize_frame


LINEAGE_COLUMNS = (
    "id_customer",
    "_customer_name",
    "_source_file",
    "_retailer",
    "_fact_family",
    "_candidate_status",
    "_ingested_at",
    "_silver_source_table",
    "_silver_refreshed_at",
)

TYPE_MAP: dict[str, T.DataType] = {
    "text": T.StringType(),
    "long": T.LongType(),
    "double": T.DoubleType(),
    "date": T.DateType(),
    "timestamp": T.TimestampType(),
    "decimal_19_4": T.DecimalType(19, 4),
}


def _require(frame: DataFrame, columns: list[str], query_name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        suggestions = {
            column: get_close_matches(column, frame.columns, n=3, cutoff=0.72)
            for column in missing
        }
        suggestions = {key: value for key, value in suggestions.items() if value}
        suffix = f"; nomes semelhantes encontrados: {suggestions}" if suggestions else ""
        raise RuntimeError(
            f"{query_name}: colunas ausentes na fonte: {missing}{suffix}"
        )


def _apply_aliases(
    frame: DataFrame,
    aliases: dict[str, Any],
) -> DataFrame:
    """Consolida variacoes reais de schema no nome canonico esperado pelo M."""

    result = frame
    for target, alternatives in aliases.items():
        candidates = [target]
        candidates.extend(
            [alternatives] if isinstance(alternatives, str) else list(alternatives)
        )
        available = [column for column in candidates if column in result.columns]
        if available:
            result = result.withColumn(
                target,
                F.coalesce(*(F.col(column) for column in available)),
            )
    return result


def apply_fact_contract(
    frame: DataFrame,
    definition: dict[str, Any],
    query_name: str,
) -> DataFrame:
    """Aplica selecao, derivacoes, nulos, nomes e tipos na mesma ordem logica do M."""

    if definition.get("passthrough"):
        return frame
    frame = _apply_aliases(frame, definition.get("aliases", {}))
    columns = list(definition.get("columns", []))
    _require(frame, columns, query_name)
    lineage = [column for column in LINEAGE_COLUMNS if column in frame.columns]
    result = frame.select(*(columns + lineage))

    derived = definition.get("derived_date")
    if derived:
        result = result.withColumn(
            derived["target"],
            F.make_date(
                F.col(derived["year"]).cast("int"),
                F.col(derived["month"]).cast("int"),
                F.lit(int(derived.get("day", 1))),
            ),
        )
    for source, target in definition.get("rename", {}).items():
        result = result.withColumnRenamed(source, target)
    for column, value in definition.get("fill_nulls", {}).items():
        if column in result.columns:
            result = result.withColumn(
                column,
                F.when(F.col(column).isNull(), F.lit(value)).otherwise(F.col(column)),
            )
    for column in definition.get("drop_after_derive", []):
        result = result.drop(column)
    for column, type_name in definition.get("types", {}).items():
        if type_name not in TYPE_MAP:
            raise RuntimeError(f"{query_name}: tipo nao suportado: {type_name}")
        if column not in result.columns:
            raise RuntimeError(f"{query_name}: coluna tipada ausente: {column}")
        result = result.withColumn(column, F.col(column).cast(TYPE_MAP[type_name]))
    return result


def _normalized(frame: DataFrame) -> DataFrame:
    result = normalize_frame(frame)
    return result.drop("_silver_refreshed_at")


def _finish(
    frame: DataFrame,
    source: str,
    id_customer: int,
    customer_name: str,
) -> DataFrame:
    result = (
        frame.withColumn("id_customer", F.lit(int(id_customer)).cast("long"))
        .withColumn("_customer_name", F.lit(customer_name))
    )
    return (
        result.withColumn("_silver_source_table", F.lit(source))
        .withColumn("_silver_refreshed_at", F.current_timestamp())
    )


def _region(column: str):
    uf = F.col(column)
    return (
        F.when(uf.isin("SP", "RJ", "ES", "MG"), "Sudeste")
        .when(uf.isin("RS", "SC", "PR"), "Sul")
        .when(uf.isin("DF", "GO", "MT", "MS"), "Centro-Oeste")
        .when(uf.isin("AC", "AP", "AM", "PA", "RO", "RR", "TO"), "Norte")
        .when(uf.isin("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"), "Nordeste")
        .otherwise("N/C")
    )


def _remove_accent_value(column: str):
    source = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
    target = "AAAAAEEEEIIIIOOOOOUUUUC"
    value = F.translate(F.upper(F.col(column)), source, target)
    value = F.regexp_replace(value, r"[^A-Z0-9_ /]", "")
    value = F.regexp_replace(value, r"[ /]", "_")
    return F.regexp_replace(value, r"_+", "_")


def transform_dimensions(
    raw: dict[str, DataFrame],
    customer_name: str,
    id_customer: int,
) -> dict[str, DataFrame]:
    """Executa as oito consultas dimensionais M na ordem de dependencia."""

    customer = _normalized(raw["dim_customer_raw"]).select("nm_customer", "id_customer")
    customer = (
        customer.dropDuplicates()
        .withColumn("id_customer", F.col("id_customer").cast("long"))
        .withColumn("nm_customer", F.col("nm_customer").cast("string"))
        .dropDuplicates(["id_customer"])
        .filter(F.upper(F.trim(F.col("nm_customer"))) == customer_name)
        .filter(F.col("id_customer") == F.lit(id_customer))
    )
    customer = _finish(customer, "dim_customer_raw", id_customer, customer_name)

    aux_local = _normalized(raw["dim_varejo_contratado_raw"])
    _require(aux_local, ["nm_customer", "cd_retailer", "id_customer", "id_retailer"], "AUX_CONTRATADO_LOCAL")
    aux_local = (
        aux_local.withColumn("id_customer", F.col("id_customer").cast("long"))
        .filter(F.upper(F.trim(F.col("nm_customer"))) == customer_name)
        .filter(F.col("id_customer") == F.lit(id_customer))
        .filter(~F.col("cd_retailer").isin("GPA", "GPA2", "MLUIZA"))
        .withColumn("id_retailer", F.col("id_retailer").cast("string"))
        .sort("cd_retailer")
    )
    aux_local = _finish(
        aux_local, "dim_varejo_contratado_raw", id_customer, customer_name
    )

    itens = _normalized(raw["dim_itens_raw"])
    _require(itens, ["id_customer", "id_item", "cd_ean", "desc_produto"], "DIM_ITENS")
    customer_keys = customer.select(
        F.col("id_customer").cast("long").alias("id_customer")
    ).dropDuplicates()
    itens = itens.withColumn("id_customer", F.col("id_customer").cast("long")).join(
        customer_keys, "id_customer", "left_semi"
    )
    itens = (
        itens.withColumn("item", F.concat(F.col("cd_ean"), F.lit(" - "), F.col("desc_produto")))
        .withColumnRenamed("desc_hierarquia_1", "hierarquia_1")
        .withColumnRenamed("desc_hierarquia_2", "hierarquia_2")
        .withColumnRenamed("desc_hierarquia_3", "hierarquia_3")
        .withColumnRenamed("desc_hierarquia_4", "hierarquia_4")
        .withColumnRenamed("nm_brand", "descricao_marca")
        .withColumn("id_item", F.col("id_item").cast("string"))
        .withColumn("cd_ean", F.col("cd_ean").cast("string"))
        .dropDuplicates(["id_customer", "id_item"])
    )
    itens = _finish(itens, "dim_itens_raw", id_customer, customer_name)

    conversao = _normalized(raw["dim_conversao_raw"])
    _require(conversao, ["id_customer", "id_item"], "DIM_CONVERSAO")
    conversao = conversao.withColumn("id_customer", F.col("id_customer").cast("long")).join(
        customer_keys, "id_customer", "left_semi"
    ).sort("id_item")
    conversao = _finish(conversao, "dim_conversao_raw", id_customer, customer_name)

    catalogo = _normalized(raw["dim_catalogo_produtos_raw"])
    _require(catalogo, ["industria", "id_segment", "categoria", "sub_segmento", "segmento"], "DIM_CATALOGO_PRODUTOS")
    catalogo = (
        catalogo.filter(F.upper(F.trim(F.col("industria"))) == customer_name)
        .drop("medida", "sabor", "pack", "relacao_pack", "cod_arvore_mercadologica")
        .withColumn("medida", F.lit("unidade"))
        .withColumn("id_segment", F.col("id_segment").cast("string"))
        .withColumn("categoria", F.col("categoria").cast("string"))
        .withColumn("sub_segmento", F.col("sub_segmento").cast("string"))
    )
    catalogo = _finish(
        catalogo, "dim_catalogo_produtos_raw", id_customer, customer_name
    )

    allowed_segments = [
        "AGUA_DE_COCO", "AGUA_MINERAL", "BEBIDA_ALCOOLICA_MISTA",
        "CERVEJA", "ISOTONICO", "REFRIGERANTE",
    ]
    aux_segmento = (
        catalogo.filter(F.upper(F.trim(F.col("industria"))) == customer_name)
        .select("segmento")
        .dropDuplicates()
        .withColumn("segmento", _remove_accent_value("segmento"))
        .filter(F.col("segmento").isin(*allowed_segments))
        .sort("segmento")
    )
    aux_segmento = _finish(
        aux_segmento, "dim_catalogo_produtos", id_customer, customer_name
    )

    local = _normalized(raw["dim_local_raw"])
    required_local = ["id_retailer", "id_location", "cnpj_completo", "uf", "cod_loja", "nome_da_loja"]
    _require(local, required_local, "DIM_LOCAL")
    text_columns = ["tipo_local", "microregiao", "endereco", "bandeira", "uf", "cidade", "bairro", "nome_da_loja", "nome_razao_social", "grupo_economico", "id_retailer", "id_location", "cod_loja"]
    local = local.withColumn("id_location_type", F.col("id_location_type").cast("long")).withColumn("dh_updated", F.col("dh_updated").cast("timestamp"))
    for column in text_columns:
        if column in local.columns:
            local = local.withColumn(column, F.col(column).cast("string"))
    contracted = aux_local.select("id_retailer", "id_customer", "nm_customer").dropDuplicates(
        ["id_customer", "id_retailer"]
    )
    local = local.join(contracted, "id_retailer", "inner").withColumnRenamed("cnpj_completo", "cnpj")
    padded = F.lpad(F.col("cnpj").cast("string"), 14, "0")
    local = (
        local.withColumn("cnpj_formatado", F.concat(
            F.substring(padded, 1, 2), F.lit("."), F.substring(padded, 3, 3), F.lit("."),
            F.substring(padded, 6, 3), F.lit("/"), F.substring(padded, 9, 4), F.lit("-"), F.substring(padded, 13, 2)))
        .withColumn("regiao", _region("uf"))
        .withColumn("loja", F.concat(F.col("cod_loja"), F.lit(" - "), F.col("nome_da_loja")))
        .withColumnRenamed("cidade", "cidade")
        .withColumnRenamed("bandeira", "bandeira")
        .withColumnRenamed("grupo_economico", "rede")
        .drop("microregiao", "dh_updated", "id_location_type", "nome_razao_social", "endereco")
    )
    local = _finish(
        local, "dim_local_raw+aux_contratado_local", id_customer, customer_name
    ).dropDuplicates(["id_customer", "id_location"])

    catalogo_local = _normalized(raw["dim_local_raw"])
    catalogo_local = (
        catalogo_local.withColumn("id_retailer", F.col("id_retailer").cast("string"))
        .join(contracted.select("id_retailer"), "id_retailer", "left_semi")
        .withColumnRenamed("cnpj_completo", "cnpj")
        .withColumnRenamed("cidade", "cidade")
        .withColumnRenamed("bandeira", "bandeira")
        .withColumnRenamed("grupo_economico", "rede")
        .withColumnRenamed("tipo_local", "tipo_local")
        .drop("cod_loja", "nome_razao_social", "bairro", "cidade", "endereco", "microregiao", "dh_updated", "id_location_type")
    )
    for column in ["bandeira", "uf", "nome_da_loja", "rede", "id_retailer", "id_location", "cnpj"]:
        if column in catalogo_local.columns:
            catalogo_local = catalogo_local.withColumn(column, F.col(column).cast("string"))
    catalogo_local = catalogo_local.withColumn("regiao", _region("uf")).filter(F.col("rede") != "GPA").sort("rede")
    catalogo_local = _finish(
        catalogo_local, "dim_local_raw", id_customer, customer_name
    ).dropDuplicates(["id_customer", "id_location"])

    return {
        "dim_customer": customer,
        "aux_contratado_local": aux_local,
        "dim_itens": itens,
        "dim_conversao": conversao,
        "dim_catalogo_produtos": catalogo,
        "aux_contratado_segmento": aux_segmento,
        "dim_local": local,
        "dim_catalogo_local": catalogo_local,
    }


def build_activity_dimension(
    fact: DataFrame,
    id_customer: int,
    customer_name: str,
) -> DataFrame:
    _require(fact, ["tp_activity_level", "nm_activity_level"], "DIM_NIVEL_ATIVIDADE")
    result = fact.select("tp_activity_level", "nm_activity_level").dropDuplicates()
    result = (
        result.withColumn(
            "nm_activity_level",
            F.when(F.col("nm_activity_level").isNull() | (F.col("nm_activity_level") == ""), "Não Informado")
            .otherwise(F.col("nm_activity_level")),
        )
        .withColumn("tp_activity_level", F.coalesce(F.col("tp_activity_level"), F.lit("I")))
        .withColumn(
            "id",
            F.when(F.col("nm_activity_level") == "Fast Mover", 1)
            .when(F.col("nm_activity_level") == "Slow Mover", 2)
            .when(F.col("nm_activity_level") == "Ultra Slow Mover", 3)
            .when(F.col("nm_activity_level") == "New Mover", 4)
            .when(F.col("nm_activity_level") == "Non Mover", 5)
            .when(F.col("nm_activity_level") == "Não Informado", 6)
            .otherwise(999)
            .cast("long"),
        )
        .sort("id")
    )
    return _finish(result, "fato_nivel_atividade", id_customer, customer_name)
