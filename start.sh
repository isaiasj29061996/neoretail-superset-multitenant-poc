#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
[ -f .env ] || cp .env.example .env
mkdir -p generated certs
docker compose config --quiet
docker compose up -d --remove-orphans "$@"
docker compose ps -a
printf '%s\n' 'Embedded: http://localhost:3000' 'Superset: http://localhost:8088' 'PySpark/Jupyter: http://localhost:8888' 'PostgreSQL Analytics: localhost:5433'
