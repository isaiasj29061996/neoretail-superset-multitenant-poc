# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # NeoRetail V8.1 Local - 02C Bronze market candidates
# Descobre os Parquets usados por FATO_MERCADO conforme o Power Query.
# Comece em inventario e altere para `False` para materializar na Bronze.

# %%
from neoretail_local.market import run

MAX_FILES = 0
INVENTORY_ONLY = True

# %%
result = run(max_files=MAX_FILES, inventory_only=INVENTORY_ONLY)
result
