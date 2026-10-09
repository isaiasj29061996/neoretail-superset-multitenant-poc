"""Freeze authoritative PBIP DAX: C16 guard is ordinary equality, not strict."""
import json,re
from pathlib import Path
import pytest
D=json.loads((Path(__file__).parent/'fixtures/pbip_c16_dax_20261008.json').read_text('utf-8'))
@pytest.mark.parametrize('name',['MARKUP MTD','MARKUP Mes Ant','MARKUP U3M','ROI'])
def test_exact_guard_operator_and_branch(name):
 dax=D['measures'][name]['dax']
 assert re.search(r'IF\(\s*vSellOut = 0\s*\|\| vVendaCusto = 0,\s*0,',dax)
 assert '==' not in dax and 'SWITCH' not in dax and 'BLANK(' not in dax
 assert 'DIVIDE(' in dax
 assert 'EstoqueCusto = 0' not in dax and '[Estoque Custo] = 0' not in dax
@pytest.mark.parametrize('name',['MARKUP MTD','MARKUP Mes Ant','MARKUP U3M','ROI Mes Ant','ROI U3M','ROI Anual'])
def test_current_pbip_dax_literal_and_dependency_closure(name):
 root=Path(__file__).resolve().parents[2]
 tmdl=root/'generated/pbi_lactalis_reference_20261008/NeoRetail Pocket RF.SemanticModel/definition/tables/_Metricas.tmdl'
 text=tmdl.read_text('utf-8-sig')
 pending=[name];seen=set()
 while pending:
  n=pending.pop()
  if n in seen:continue
  seen.add(n);dax=D['measures'][n]['dax'];assert dax in text
  pending.extend(x for x in re.findall(r'\[([^]\n]+)\]',dax) if x in D['measures'])
 assert name in seen

@pytest.mark.parametrize('extra_zero,expected',[(False,None),(True,0)])
def test_annual_sumx_blank_reduction_oracle(extra_zero,expected):
 # Explicit AnoMes filter retains exactly the 12 monthly contexts. Each
 # ROI DIVIDE is BLANK when Sell/Cost are nonzero and stock cost is BLANK.
 # A calendar month with no facts instead emits 0 via C16, changing the sum.
 import sqlite3
 c=sqlite3.connect(':memory:')
 c.execute('CREATE TABLE monthly_roi (value REAL)')
 c.executemany('INSERT INTO monthly_roi VALUES (?)',[(None,)]*12)
 if extra_zero:c.execute('INSERT INTO monthly_roi VALUES (0)')
 assert c.execute('SELECT SUM(value) FROM monthly_roi').fetchone()[0]==expected
 c.close()
