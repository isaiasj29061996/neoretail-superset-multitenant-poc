#!/bin/sh
set -eu

CURRENT_STEP="inicio"
trap 'status=$?; if [ "$status" -ne 0 ]; then echo "ERRO superset-init na etapa: $CURRENT_STEP (exit $status)" >&2; fi' EXIT

CURRENT_STEP="migracao do banco de metadata"
echo "[superset-init 1/4] Executando superset db upgrade..."
superset db upgrade

CURRENT_STEP="criacao do usuario administrador"
echo "[superset-init 2/4] Verificando usuario administrador..."
if ! superset fab list-users 2>/dev/null | grep -q "${SUPERSET_ADMIN_USERNAME}"; then
  superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME}" \
    --firstname NeoRetail \
    --lastname POC \
    --email "${SUPERSET_ADMIN_EMAIL}" \
    --password "${SUPERSET_ADMIN_PASSWORD}"
fi

CURRENT_STEP="inicializacao de roles e permissoes"
echo "[superset-init 3/4] Executando superset init..."
superset init

CURRENT_STEP="bootstrap do PostgreSQL Analytics"
echo "[superset-init 4/4] Validando PostgreSQL Analytics local..."
/app/.venv/bin/python /app/pythonpath/bootstrap_analytics.py

CURRENT_STEP="concluido"
echo "superset-init concluido com sucesso."
