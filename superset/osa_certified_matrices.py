"""Compatibility facade for certified OSA matrix contracts."""
from neoretail_bootstrap.panorama.filters import WEEKLY_FILTER_COLUMNS
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from neoretail_bootstrap.core.metrics import formatted_metric
from neoretail_bootstrap.osa_certified.matrices import (
    MATRIX_SCOPES, DIMENSION_OVERRIDES, _measure_filter, _period_rows,
    matrix_period_sql, TABLE_VALUE, TABLE_QTY, TABLE_PROBLEMS, TABLE_OSA,
)
