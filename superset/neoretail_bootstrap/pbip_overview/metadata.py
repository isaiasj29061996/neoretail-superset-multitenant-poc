"""Read schema from the matching PBIP serving output during bootstrap.

Superset introspection otherwise executes the interactive SQL with no selection,
which is a real BLANK context, not the dashboard's saved unit context. Schema is
identical: migration 50 materializes the same interactive projection per mode.
Only the schema probe is substituted; persisted SQL remains the full contract.
"""
from neoretail_bootstrap.core.metadata import upsert_dataset

PROBE_SOURCES=frozenset(('nr_pbip_overview_semantic_v3','nr_pbip_osa_semantic_v3','nr_pbip_giro_v3','nr_pbip_daily_headlines'))

def upsert_serving_dataset(session, model, database, name, *, sql, probe_source):
    if probe_source not in PROBE_SOURCES:
        raise ValueError('Only matching PBIP serving schemas can be probed')
    dataset=upsert_dataset(session,model,database,name,
        sql='SELECT * FROM gold.'+probe_source+' LIMIT 1')
    dataset.sql=sql
    session.flush()
    return dataset
