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
# # NeoRetail V8.1 Local - 01 Discover Blob
# Executa a etapa 01 no PySpark local e PostgreSQL Analytics.

# %%
from neoretail_local.pipeline import run_step

result = run_step("01")
result
