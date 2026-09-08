#!/bin/sh
set -eu

mkdir -p /data/raw-cache /data/lake/bronze /data/lake/silver /data/lake/gold

exec jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --ServerApp.token="${JUPYTER_TOKEN:-neoretail-v81-local}" \
  --ServerApp.root_dir=/workspace
