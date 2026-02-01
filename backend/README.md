**Database Migrations (Alembic)**
- **Install:** using `uv` (recommended) or `pip`.
```bash
cd backend
uv add alembic
# or
pip install alembic
```
- **Init done:** Alembic is already configured in this repo:
	- Config: [backend/alembic.ini](backend/alembic.ini)
	- Env: [backend/alembic/env.py](backend/alembic/env.py)
	- Versions: [backend/alembic/versions](backend/alembic/versions)
- **Create a migration:** (autogenerate from current models)
```bash
alembic revision --autogenerate -m "add/update tables"
```
- **Apply migrations:**
```bash
alembic upgrade head
```
- **Rollback one step:**
```bash
alembic downgrade -1
```
- **Notes:**
	- Ensure `DATABASE_URL` is set in `.env` before running commands.
	- Autogenerate reads metadata from `src.database.db.Base` and imports `src.model`.
**Observability (Grafana OTLP)**
- **Goal:** Export traces and metrics from the FastAPI backend to Grafana via OTLP.
- **Prereqs:** Grafana Cloud OTLP gateway URL and API key.

**Env Vars**
- **`OTEL_EXPORTER_OTLP_ENDPOINT`**: OTLP HTTP endpoint, e.g. `https://otlp-gateway-<region>.grafana.net:4318`.
- **`OTEL_EXPORTER_OTLP_HEADERS`**: Comma-separated headers, e.g. `Authorization=Bearer <API_KEY>`.
- Optional: **`OTEL_SERVICE_NAME`**, **`OTEL_SERVICE_VERSION`**, **`OTEL_ENVIRONMENT`**.
- Optional: **`SEND_TO_LOGFIRE`**: Set to `false` to avoid sending data to Logfire.

**Run**
```bash
cd backend
uvicorn main:app --port 8000
```

If the env is set, OpenTelemetry exporters initialize automatically and send data to Grafana. You should see spans for HTTP requests and periodic metrics.

**Notes**
- Logs via OTLP can be added next; traces and metrics are enabled now.
- If you prefer auto-instrumentation, you can use the `opentelemetry-instrument` CLI with the same env vars to run uvicorn.
