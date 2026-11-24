# Deploy SQL Analyst (portfolio VPS)

**Live URL (after setup):** `https://sql-analyst.102-203-81-249.sslip.io`  
Same sslip pattern as [warehouse-ledger](https://github.com/JoshStevens582/warehouse-ledger) on `102.203.81.249`.

## Prerequisites

- Docker on the VPS (`cca-edge` network exists — see ledger `deploy/rackzar.md`)
- `OPENAI_API_KEY` on the server (never commit `.env`)

## 1. Clone and configure

```bash
sudo mkdir -p /opt/sql-analyst
sudo chown "$USER:$USER" /opt/sql-analyst
cd /opt/sql-analyst
git clone https://github.com/JoshStevens582/sql-analyst.git .
cp .env.example .env
# Edit .env: set OPENAI_API_KEY=sk-...
```

## 2. Run the container (edge)

```bash
docker compose -f deploy/compose.edge.yml up -d --build
```

Do **not** merge `docker-compose.yml` on the VPS — that file publishes `8088` for local dev. **HTTPS only** through Caddy. Smoke check:

```bash
docker exec sql-analyst curl -fsS http://127.0.0.1:8088/api/health
curl -fsS https://sql-analyst.102-203-81-249.sslip.io/api/health
```

## 3. Caddy (Atlas web container)

Append `deploy/caddy-sql-analyst.caddy` to `/opt/atlas/deploy/Caddyfile`, then rebuild Atlas `web` (same flow as ledger in `warehouse-ledger/deploy/rackzar.md`).

```bash
grep -q 'sql-analyst.102-203-81-249.sslip.io' /opt/atlas/deploy/Caddyfile || \
  { echo >> /opt/atlas/deploy/Caddyfile; cat /opt/sql-analyst/deploy/caddy-sql-analyst.caddy >> /opt/atlas/deploy/Caddyfile; }
cd /opt/atlas && docker compose -f docker-compose.yml -f deploy/compose.counter-edge.yml up -d --build web
```

## 4. Smoke test

```bash
curl -fsS https://sql-analyst.102-203-81-249.sslip.io/api/health
curl -fsS https://sql-analyst.102-203-81-249.sslip.io/api/meta
```

Browser: open the host above and run a demo question from the README.

## Local Docker only

```bash
docker compose up -d --build
open http://127.0.0.1:8088
```