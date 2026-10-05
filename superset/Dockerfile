FROM node:20-bookworm-slim AS neoretail-frontend

ARG SUPERSET_VERSION=6.0.0
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN curl -fsSL "https://github.com/apache/superset/archive/refs/tags/${SUPERSET_VERSION}.tar.gz" \
  | tar -xz --strip-components=1

WORKDIR /src/superset-frontend
RUN --mount=type=cache,id=neoretail-superset-npm,target=/root/.npm \
    npm ci --no-audit --no-fund
RUN apt-get update \
 && apt-get install -y --no-install-recommends zstd \
 && rm -rf /var/lib/apt/lists/*
COPY frontend-plugin/plugin-chart-neoretail-kpi \
  /src/superset-frontend/plugins/plugin-chart-neoretail-kpi
COPY frontend-plugin/register-plugin.mjs /tmp/register-plugin.mjs
RUN node /tmp/register-plugin.mjs
COPY frontend-extension/setupExtensions.ts \
  /src/superset-frontend/src/setup/setupExtensions.ts
RUN NODE_OPTIONS=--max-old-space-size=4096 npm run build

FROM apache/superset:6.0.0

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && (/app/.venv/bin/python -m ensurepip --upgrade >/dev/null 2>&1 || true)

RUN /app/.venv/bin/python -m pip install --no-cache-dir \
      psycopg2-binary redis

COPY superset_config.py neoretail_publication.py smoke_publication.py bootstrap_analytics.py init.sh /app/pythonpath/
COPY bootstrap_*.py osa_certified_matrices.py /app/pythonpath/
COPY neoretail_bootstrap/ /app/pythonpath/neoretail_bootstrap/
COPY --from=neoretail-frontend /src/superset/static/assets /app/superset/static/assets
USER superset
