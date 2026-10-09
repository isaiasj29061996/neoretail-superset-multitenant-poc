"""Independent relational oracle for the current PBIP annual SUMX contract."""
import json,sqlite3
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
CASES=[('all12_blank',[None]*12,12,None),('12_existing_all_blank',[None]*12,12,None),
 ('no_iterator_members',[],0,None),('no_fact_rows_calendar_exists',[],12,0),
 ('blank_values',[1,None,2,None,3]+[None]*7,12,6),('blank_zero',[0]+[None]*11,12,0),
 ('all_zero',[0]*12,12,0),('one_value',[7]+[None]*11,12,7),('positive',[2]*12,12,24),
 ('negative',[-2]*12,12,-24),('mixed',[8,-3]+[None]*10,12,5),('blank_missing_fact',[None],2,0)]
@pytest.mark.parametrize('name,values,member_count,expected',CASES,ids=[x[0] for x in CASES])
def test_sumx_annual_nullable_returns(name,values,member_count,expected):
 c=sqlite3.connect(':memory:')
 c.execute('CREATE TABLE calendar(month INTEGER PRIMARY KEY)')
 c.execute('CREATE TABLE monthly(month INTEGER PRIMARY KEY, roi REAL)')
 c.executemany('INSERT INTO calendar VALUES (?)',[(i,) for i in range(member_count)])
 c.executemany('INSERT INTO monthly VALUES (?,?)',list(enumerate(values)))
 # An existing BLANK ROI is not an absent fact row: absence invokes frozen
 # ROI IF(BLANK=0 || BLANK=0,0,DIVIDE(...)) in that calendar month.
 actual=c.execute('SELECT SUM(CASE WHEN m.month IS NULL THEN 0 ELSE m.roi END) FROM calendar c LEFT JOIN monthly m ON c.month=m.month').fetchone()[0]
 assert actual==expected
 assert c.execute('SELECT COUNT(*) FROM monthly').fetchone()[0]==len(values)
 c.close()
def test_exact_current_roi_annual_dax_and_closure():
 d=json.loads((ROOT/'generated/pbip_roi_annual_dax_20261008.json').read_text('utf-8'))
 source=ROOT/'generated/pbi_lactalis_reference_20261008/NeoRetail Pocket RF.SemanticModel/definition/tables/_Metricas.tmdl'
 raw=source.read_text('utf-8-sig')
 for m in d['measures'].values():assert m['dax'] in raw
 annual=d['measures']['ROI Anual']['dax']
 assert "VALUES('0_0_CALENDARIO'[AnoMes])" in annual and 'SUMX(' in annual
 assert "MAX('0_0_CALENDARIO'[DATA])" in annual and '-12,' in annual and 'MONTH' in annual
 assert "REMOVEFILTERS('0_0_DIM_PERIODO')" in annual
