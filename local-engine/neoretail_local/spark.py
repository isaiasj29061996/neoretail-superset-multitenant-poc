from __future__ import annotations

from pyspark.sql import SparkSession

from .settings import Settings


def create_spark(settings: Settings) -> SparkSession:
    warehouse = settings.data_root / "spark-warehouse"
    builder = (
        SparkSession.builder.appName("NeoRetail-V9-Multitenant")
        .master(settings.spark_master)
        .config("spark.driver.memory", settings.spark_driver_memory)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.warehouse.dir", str(warehouse))
        .config("spark.jars", "/usr/share/java/postgresql.jar")
        .config("spark.ui.enabled", "false")
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
