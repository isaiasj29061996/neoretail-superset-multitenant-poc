from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .customers import Customer, resolve_customer


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} nao configurada no .env")
    return value


def env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} precisa ser inteiro") from exc
    return max(value, minimum)


@dataclass(frozen=True)
class Settings:
    connection_string: str
    container: str
    blob_prefix: str
    source_catalog_path: Path
    approved_facts_path: Path
    metric_contracts_path: Path
    power_query_contracts_path: Path
    customers_config_path: Path
    customer: Customer
    data_root: Path
    output_dir: Path
    lake_format: str
    discovery_max_files: int
    spark_master: str
    spark_driver_memory: str
    analytics_host: str
    analytics_port: int
    analytics_database: str
    analytics_user: str
    analytics_password: str

    @classmethod
    def from_env(
        cls,
        *,
        require_blob: bool = True,
        customer_selector: str | int | None = None,
    ) -> "Settings":
        connection_string = required("AZURE_STORAGE_CONNECTION_STRING") if require_blob else os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING", ""
        ).strip()
        lake_format = os.getenv("LOCAL_LAKE_FORMAT", "parquet").strip().lower()
        if lake_format not in {"parquet", "delta"}:
            raise RuntimeError("LOCAL_LAKE_FORMAT deve ser parquet ou delta")
        customers_config_path = Path(
            os.getenv("CUSTOMERS_CONFIG_PATH", "/workspace/config/customers.yaml")
        )
        customer = resolve_customer(
            customers_config_path,
            customer_selector or os.getenv("NEORETAIL_CUSTOMER"),
        )
        return cls(
            connection_string=connection_string,
            container=os.getenv("AZURE_STORAGE_CONTAINER", "neoretail").strip() or "neoretail",
            blob_prefix=os.getenv("AZURE_BLOB_PREFIX", "").strip().strip("/"),
            source_catalog_path=Path(os.getenv("SOURCE_CATALOG_PATH", "/workspace/config/source_catalog.yaml")),
            approved_facts_path=Path(os.getenv("APPROVED_FACTS_PATH", "/workspace/config/approved_facts.yaml")),
            metric_contracts_path=Path(os.getenv("METRIC_CONTRACTS_PATH", "/workspace/config/metric_contracts.yaml")),
            power_query_contracts_path=Path(
                os.getenv(
                    "POWER_QUERY_CONTRACTS_PATH",
                    "/workspace/config/power_query_contracts.yaml",
                )
            ),
            customers_config_path=customers_config_path,
            customer=customer,
            data_root=Path(os.getenv("LOCAL_DATA_ROOT", "/data")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "/workspace/generated")),
            lake_format=lake_format,
            discovery_max_files=env_int("LOCAL_DISCOVERY_MAX_FILES", 5000),
            spark_master=os.getenv("SPARK_MASTER", "local[*]").strip(),
            spark_driver_memory=os.getenv("SPARK_DRIVER_MEMORY", "4g").strip(),
            analytics_host=os.getenv("ANALYTICS_DB_HOST", "analytics-db").strip(),
            analytics_port=env_int("ANALYTICS_DB_PORT", 5432),
            analytics_database=os.getenv("ANALYTICS_DB_NAME", "analytics").strip(),
            analytics_user=os.getenv("ANALYTICS_DB_USER", "analytics").strip(),
            analytics_password=os.getenv("ANALYTICS_DB_PASSWORD", "analytics"),
        )

    @property
    def id_customer(self) -> int:
        return self.customer.id_customer

    @property
    def nm_customer(self) -> str:
        return self.customer.nm_customer

    @property
    def customer_source_prefix(self) -> str:
        return self.customer.source_prefix

    @property
    def jdbc_url(self) -> str:
        return (
            f"jdbc:postgresql://{self.analytics_host}:{self.analytics_port}/"
            f"{self.analytics_database}"
        )

    @property
    def psycopg_dsn(self) -> str:
        return (
            f"host={self.analytics_host} port={self.analytics_port} "
            f"dbname={self.analytics_database} user={self.analytics_user} "
            f"password={self.analytics_password}"
        )
