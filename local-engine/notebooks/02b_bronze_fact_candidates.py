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
# # NeoRetail V8.1 Local - 02B Bronze fact candidates
# Descobre e materializa fatos da 3CORACOES na Bronze, sem promover para Gold.
# A primeira execucao fica em inventario por seguranca. Troque para `False`
# somente quando quiser materializar os Parquets da familia selecionada.

# %%
from neoretail_local.candidates import run

FAMILY = "all"
MAX_FILES = 0
INVENTORY_ONLY = False

# %%
result = run(
    family=FAMILY,
    max_files=MAX_FILES,
    inventory_only=INVENTORY_ONLY,
)
result
