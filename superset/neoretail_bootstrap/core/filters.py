"""Shared filters helpers extracted without changing defaults."""
from __future__ import annotations


def _jinja_filter_predicates(
    alias: str,
    activity_expression: str | None = None,
    overrides: dict[str, str] | None = None,
) -> str:
    """Push native IN filters below the business aggregation."""
    columns = {
        "rede": "rede", "bandeira": "bandeira", "uf": "uf", "cidade": "cidade",
        "tipo_local": "tipo_local", "loja": "loja", "regiao": "regiao",
        "descricao_marca": "descricao_marca", "hierarquia_1": "hierarquia_1",
        "hierarquia_2": "hierarquia_2", "hierarquia_3": "hierarquia_3", "item": "item",
        "tp_activity_level": activity_expression or "tp_activity_level",
    }
    lines = []
    overrides = overrides or {}
    for column, expression in columns.items():
        qualified = overrides.get(column, expression)
        qualified = qualified if "." in qualified else f"{alias}.{qualified}"
        lines.extend((
            f"{{% for filter in get_filters('{column}', remove_filter=True) %}}",
            "{% if filter.get('op') == 'IN' %}",
            f"  AND {qualified} IN {{{{ filter.get('val') | where_in }}}}",
            "{% elif filter.get('op') == 'NOT IN' %}",
            f"  AND {qualified} NOT IN {{{{ filter.get('val') | where_in }}}}",
            "{% endif %}",
            "{% endfor %}",
        ))
    return "\n".join(lines)
