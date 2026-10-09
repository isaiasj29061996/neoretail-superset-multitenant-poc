"""Protect non-additive multi-retail metrics from the single-retail fast path."""
from jinja2 import Environment
from bootstrap_osa_industry_certified import monthly_overview_sql

def render(filters):
    env = Environment()
    env.filters['where_in'] = lambda values: '(' + ','.join("'" + str(v).replace("'", "''") + "'" for v in values) + ')'
    return env.from_string(monthly_overview_sql()).render(
        get_filters=lambda name, **kwargs: [f for f in filters if f['col'] == name])

def retail(values, op='IN'):
    return {'col': 'rede', 'op': op, 'val': values}

def test_single_retail_uses_compact_context():
    sql = render([retail(['CENCOSUD'])])
    assert 'FROM gold.nr_osa_monthly_retail' in sql
    assert 'FROM gold.fato_historico' not in sql

def test_two_retails_keep_combined_context_not_average_of_percentages():
    sql = render([retail(['CENCOSUD', 'SAVEGNAGO'])])
    assert 'FROM gold.nr_osa_monthly_retail' not in sql
    assert 'FROM gold.fato_historico' in sql

def test_not_in_and_additional_dimension_keep_detail():
    for filters in ([retail(['CENCOSUD'], 'NOT IN')],
                    [retail(['CENCOSUD']), {'col': 'uf', 'op': 'IN', 'val': ['BA']} ]):
        sql = render(filters)
        assert 'FROM gold.nr_osa_monthly_retail' not in sql
        assert 'FROM gold.fato_historico' in sql

def test_measure_alone_keeps_default_context():
    sql = render([{'col': 'nm_measure', 'op': 'IN', 'val': ['quilograma']}])
    assert 'FROM gold.nr_osa_monthly_default' in sql
    assert 'FROM gold.nr_osa_monthly_retail' not in sql

if __name__ == '__main__':
    for check in (test_single_retail_uses_compact_context,
                  test_two_retails_keep_combined_context_not_average_of_percentages,
                  test_not_in_and_additional_dimension_keep_detail,
                  test_measure_alone_keeps_default_context):
        check()
    print('4 OSA routing checks passed')
