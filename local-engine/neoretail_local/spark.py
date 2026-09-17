from __future__ import annotations

from pyspark.sql import SparkSession

from .settings import Settings


def create_spark(settings: Settings) -> SparkSession:
    warehouse = settings.data_root / "spark-warehouse"

    # A origem diaria particionada da AMBEV e muito maior que as fontes
    # anteriores da POC. Em local[*], todos os cores podem executar shuffles
    # simultaneamente e pressionar a memoria do mesmo processo JVM. Limitamos
    # a concorrencia somente quando o usuario manteve o default local[*].
    spark_master = settings.spark_master
    if (
        settings.customer.source_layout == "partitioned_customer_daily_v1"
        and spark_master == "local[*]"
    ):
        spark_master = "local[4]"

    builder = (
        SparkSession.builder.appName("NeoRetail-V9-Multitenant")
        .master(spark_master)
        .config("spark.driver.memory", settings.spark_driver_memory)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.warehouse.dir", str(warehouse))
        .config("spark.jars", "/usr/share/java/postgresql.jar")
        .config("spark.ui.enabled", "false")
        # Mantem os shuffles do processamento local em um numero controlado de
        # particoes. O AQE ainda pode coalescer particoes pequenas em runtime.
        .config("spark.sql.shuffle.partitions", "32")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
    )
    if settings.lake_format == "delta":
        from delta import configure_spark_with_delta_pip

        builder = (
            builder.config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
        )
        builder = configure_spark_with_delta_pip(builder)
    return builder.getOrCreate()
