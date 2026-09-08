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
# # NeoRetail V8.1 Local - 04 Approve facts
# Executa a etapa 04 no PySpark local e PostgreSQL Analytics.

# %%
from neoretail_local.pipeline import run_step

result = run_step("04")
result
