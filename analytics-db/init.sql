CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

COMMENT ON SCHEMA audit IS 'Evidencias, inventarios e quality gates multitenant da V9';
COMMENT ON SCHEMA bronze IS 'Registro local das fontes aprovadas do Azure Blob';
COMMENT ON SCHEMA silver IS 'Camada padronizada local';
COMMENT ON SCHEMA gold IS 'Camada de consumo exclusiva do Superset';
