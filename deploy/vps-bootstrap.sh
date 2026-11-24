#!/usr/bin/env bash
# Run on the VPS as the deploy user (same host as warehouse-ledger).
set -euo pipefail

HOST="sql-analyst.102-203-81-249.sslip.io"
APP_DIR="${APP_DIR:-/opt/sql-analyst}"
ATLAS_DIR="${ATLAS_DIR:-/opt/atlas}"

echo "=== SQL Analyst deploy (${HOST}) ==="
docker network create cca-edge 2>/dev/null || true

if [ ! -d "${APP_DIR}/.git" ]; then
  echo "Clone ${APP_DIR} first (see deploy/DEPLOY.md)."
  exit 1
fi

cd "${APP_DIR}"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Set OPENAI_API_KEY in ${APP_DIR}/.env then re-run."
  exit 1
fi

docker compose -f deploy/compose.edge.yml up -d --build

if [ -d "${ATLAS_DIR}/deploy" ]; then
  if ! grep -q "${HOST}" "${ATLAS_DIR}/deploy/Caddyfile"; then
    echo >> "${ATLAS_DIR}/deploy/Caddyfile"
    cat "${APP_DIR}/deploy/caddy-sql-analyst.caddy" >> "${ATLAS_DIR}/deploy/Caddyfile"
  fi
  (cd "${ATLAS_DIR}" && docker compose -f docker-compose.yml -f deploy/compose.counter-edge.yml up -d --build web)
else
  echo "Atlas not at ${ATLAS_DIR}; append deploy/caddy-sql-analyst.caddy to your Caddyfile manually."
fi

echo "Smoke: curl -fsS https://${HOST}/api/health"