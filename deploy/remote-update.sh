#!/bin/sh
# Rebuild SQL Analyst on this VPS. GitHub Actions already reset /opt/sql-analyst to origin/main.
set -eu
APP_DIR="${APP_DIR:-/opt/sql-analyst}"
cd "$APP_DIR"
test -f .env
docker network inspect cca-edge >/dev/null 2>&1 || docker network create cca-edge
docker compose --project-directory . -f deploy/compose.edge.yml up -d --build
curl -fsS --retry 8 --retry-delay 3 --retry-all-errors \
  https://sql-analyst.102-203-81-249.sslip.io/api/health
