import pg from "pg";

const { Pool } = pg;

export function createReadOnlyQuery(config = {}) {
  const pool = new Pool({
    host: config.host || "analytics-db",
    port: Number(config.port || 5432),
    database: config.database || "analytics",
    user: config.user || "analytics",
    password: config.password || "analytics",
    max: Number(config.poolSize || 4),
    connectionTimeoutMillis: Number(config.connectionTimeoutMs || 3000),
    idleTimeoutMillis: 10000,
    application_name: "neoretail_governed_assistant",
  });
  const statementTimeoutMs = Math.min(Math.max(Number(config.statementTimeoutMs || 8000), 1000), 30000);

  async function query(sql, params) {
    const client = await pool.connect();
    try {
      await client.query("BEGIN READ ONLY");
      await client.query(`SET LOCAL statement_timeout = '${statementTimeoutMs}ms'`);
      const result = await client.query(sql, params);
      await client.query("COMMIT");
      return result;
    } catch (error) {
      await client.query("ROLLBACK").catch(() => {});
      throw error;
    } finally {
      client.release();
    }
  }

  return { query, close: () => pool.end() };
}
