"""Shared metrics helpers extracted without changing defaults."""
from __future__ import annotations

import uuid


def metric(label: str, expression: str) -> dict:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": f"metric_{uuid.uuid5(uuid.NAMESPACE_DNS, label).hex[:12]}",
    }


def formatted_metric(label: str, expression: str, d3_format: str) -> dict:
    result = metric(label, expression)
    result["d3Format"] = d3_format
    return result
