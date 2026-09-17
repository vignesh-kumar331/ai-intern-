# AI Support Ticket Intelligence

End-to-end Python implementation for the DOTMappers AI Engineer assessment: CSV ingestion/querying, natural-language support-ticket analytics, anomaly detection, REST API and minimal UI using a local LLM.

## Features

- Supplied 500-row support-ticket dataset preserved exactly in a compressed bootstrap payload.
- On first startup, the payload recreates `data/support_tickets.csv`; the CSV is then ingested into SQLite.
- Ollama local LLM converts natural language into a validated structured `QueryPlan`.
- The model never produces executable SQL. The application builds allowlisted, parameterized SQL.
- Resolution anomaly detection with `Q3 + 1.5 × IQR`.
- High/Critical Open/Escalated tickets older than 24 hours.
- FastAPI: `/api/health`, `/api/stats`, `/api/query`, `/api/anomalies`.
- Responsive browser UI at `/`.
- Automated tests, GitHub Actions CI, Docker support and no paid APIs.

## Architecture

```text
Browser -> FastAPI -> Ollama -> JSON QueryPlan -> Pydantic -> Safe SQL -> SQLite
                         \-> deterministic anomaly engine -> SQLite
```

The LLM handles language understanding; deterministic application code handles data access and anomaly rules.

## Quick start

Requirements: Python 3.11+ and Ollama.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:3b
uvicorn app.main:app
```

Open `http://127.0.0.1:8000`.

If `data/support_tickets.csv` is absent, the application automatically recreates the supplied assessment CSV from `data/dataset_payload.py` before ingestion. This keeps the repository self-contained while avoiding a large raw data blob in Git.

## API

- `GET /api/health` — service, row count and LLM availability.
- `GET /api/stats` — dataset totals by status, priority and category.
- `POST /api/query` — natural-language analytics.
- `GET /api/anomalies` — anomaly findings.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How many tickets are currently open?"}'
```

## Assessment examples

The supplied dataset gives these checks:

- Open tickets: **111**
- Critical tickets not resolved within 12 hours: **34**
- Average Technical customer rating: **3.74**
- Agent resolution aggregation is supported.

The planner supports common phrases including `this week`, `this month`, `last 7 days`, and `last 30 days`, interpreted relative to the dataset's latest timestamp.

## LLM and safety

The Ollama system prompt exposes only the real schema and allowed categorical values. The model returns JSON; Pydantic validates it; the query engine uses a fixed metric/group allowlist and SQLite parameters. If Ollama is unavailable, a deterministic parser handles common assessment questions so the API remains testable; `/api/health` and `/api/query` expose whether the LLM was available/used.

## Anomaly detection

1. **Long resolution:** `resolution_time_hrs > Q3 + 1.5 × IQR`.
2. **Stale high priority:** `High/Critical` + `Open/Escalated` + older than 24 hours relative to the latest dataset timestamp.

## Testing

```bash
pytest -q
```

## Docker

```bash
ollama pull qwen2.5:3b
docker compose up --build
```

## Project structure

```text
app/
  anomalies.py
  config.py
  database.py
  dataset_payload.py
  llm.py
  main.py
  query_engine.py
  schemas.py
  static/index.html
data/
  dataset_payload.py
tests/test_smoke.py
Dockerfile
docker-compose.yml
requirements.txt
.github/workflows/ci.yml
```

## Limitations / future improvements

The NL vocabulary is intentionally controlled for safety and predictable assessment behavior. With more time: richer semantic metrics, model evaluation, PostgreSQL for larger data, caching, observability, authentication, asynchronous workloads and production deployment controls.
