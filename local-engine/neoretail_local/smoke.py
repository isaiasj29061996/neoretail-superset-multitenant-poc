from __future__ import annotations

import psycopg2

from .settings import Settings
from .spark import create_spark


def main() -> None:
    settings = Settings.from_env(require_blob=False)
    with psycopg2.connect(settings.psycopg_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
    spark = create_spark(settings)
    try:
        assert spark.range(1).count() == 1
    finally:
        spark.stop()
    print("OK: PySpark local e PostgreSQL Analytics responderam.")


if __name__ == "__main__":
    main()
