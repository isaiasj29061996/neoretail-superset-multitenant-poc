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
# # NeoRetail V8.1 Local - 02A Bronze dimensions
# Baixa as seis fontes dimensionais/auxiliares aprovadas e grava na Bronze local.

# %%
from neoretail_local.pipeline import run_step

result = run_step("02")
result
