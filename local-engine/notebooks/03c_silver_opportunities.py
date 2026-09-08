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
# # NeoRetail V8.1 Local - 03C Calculo de oportunidades
# Consolida o ETL_CALC_V2 na tabela Silver `calculo_oportunidades`.
# As colunas calculadas existentes sao preservadas. Nenhuma formula e inventada
# enquanto a exportacao completa do Power Query nao for validada.

# %%
from neoretail_local.pipeline import run_step

result = run_step("03C")
result
