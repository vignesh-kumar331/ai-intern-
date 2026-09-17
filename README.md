# AI Support Ticket Intelligence

End-to-end AI Engineer assessment implementation for the DOTMappers IT Pvt. Ltd. support-ticket sprint. The brief requires CSV ingestion/querying, natural-language analytics, anomaly detection, a REST API and a minimal UI, with an LLM used for natural-language understanding.

## What this repository implements

- CSV ingestion into SQLite using the supplied `support_tickets.csv`.
- LLM-powered natural-language query planning with Ollama.
- Pydantic validation and parameterized SQLite queries; the LLM never writes executable SQL.
- Resolution-time anomaly detection using `Q3 + 1.5 × IQR`.
- Unresolved High/Critical tickets older than 24 hours.
- FastAPI REST API and responsive browser UI.
- Tests, GitHub Actions CI, Docker support and zero paid services.

## Architecture

```text
Browser UI -> FastAPI -> Ollama -> validated QueryPlan -> safe SQL -> SQLite
                         \-> deterministic anomaly engine -> SQLite
```

The design deliberately separates language understanding from data execution. This reduces SQL-injection risk and prevents arbitrary model-generated SQL from executing.

## Dataset

The supplied schema contains: `ticket_id`, `created_at`, `category`, `priority`, `status`, `response_time_hrs`, `resolution_time_hrs`, `agent_id`, `customer_rating`, and `issue_summary`. The supplied CSV contains 500 rows. Null resolution time and customer rating values are preserved for unresolved tickets.

## Local setup

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:3b
uvicorn app.main:app
```

Open `http://127.0.0.1:8000`.

## API

- `GET /api/health`
- `GET /api/stats`
- `POST /api/query`
- `GET /api/anomalies`

Example:

```json
POST /api/query
{"question":"How many tickets are currently open?"}
```

## Assessment sample results

- Open tickets: **111**
- Critical tickets not resolved within 12 hours: **34**
- Average Technical customer rating: **3.74**
- Agent resolution aggregation is supported.

Date phrases such as `this week` and `this month` are interpreted relative to the latest timestamp in the supplied dataset so historical assessment data remains meaningful.

## LLM safety

1. Ollama receives a strict system prompt with the available schema and allowed values.
2. The model returns structured JSON, not SQL.
3. Pydantic validates the JSON.
4. The query engine maps validated fields to an allowlist of SQL fragments.
5. User-derived values are bound with SQLite parameters.
6. A deterministic safety-net parser keeps smoke tests usable if Ollama is unavailable; normal operation uses the local LLM.

## Anomaly detection

Two transparent rules are used:

- Long resolution: `resolution_time_hrs > Q3 + 1.5 × IQR`.
- Stale high priority: `High/Critical` + `Open/Escalated` + older than 24 hours relative to the latest dataset timestamp.

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
  llm.py
  main.py
  query_engine.py
  schemas.py
  static/index.html
data/support_tickets.csv
tests/test_query_engine.py
Dockerfile
docker-compose.yml
requirements.txt
```

## Limitations and scaling

The NL planner intentionally supports a controlled analytics vocabulary. For production scale, SQLite could be replaced by PostgreSQL, with caching, observability, authentication, richer semantic metrics, model evaluation and asynchronous processing. The assessment scope does not require authentication or production deployment infrastructure.
