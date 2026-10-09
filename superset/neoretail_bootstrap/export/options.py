"""Shared, tenant-scoped Export indicator options; no business arithmetic."""

INDICATORS = (
    "Venda",
    "Cobertura estoque",
    "Estoque",
    "Estoque em Trânsito",
    "ISV (%)",
    "OSA (%)",
    "Perda OSA vol.",
    "Perda OSA R$",
    "Preço médio (R$)",
)

def indicator_sql() -> str:
    values = ",\n    ".join(f"('{value}')" for value in INDICATORS)
    return (
        "SELECT customers.id_customer, options.indicador\n"
        "FROM (SELECT DISTINCT id_customer FROM gold.dim_customer) customers\n"
        f"CROSS JOIN (VALUES\n    {values}\n) AS options(indicador)"
    )
