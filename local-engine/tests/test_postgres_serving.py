from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-engine"))

from neoretail_local.postgres_serving import _type_family, _types_compatible


def test_numeric_type_family_covers_spark_postgres_variants():
    assert _type_family("bigint") == "numeric"
    assert _type_family("double precision") == "numeric"
    assert _type_family("numeric(19,4)") == "numeric"


def test_numeric_widening_is_compatible():
    assert _types_compatible("double precision", "bigint")
    assert _types_compatible("numeric(19,4)", "integer")


def test_text_variants_are_compatible():
    assert _types_compatible("text", "character varying(255)")


def test_text_to_numeric_remains_blocked():
    assert not _types_compatible("double precision", "text")
