# AGENTS.md

## Cursor Cloud specific instructions

Nexus Data Platform is a single-service Python app: a FastAPI backend (`backend/`) that runs
a rule-based multi-agent orchestrator (`agents/`) with a human-approval gate. The frontend
(`frontend/index.html`) is a static HTML/JS page, and `database/schema.sql` is aspirational —
state is held in-memory by `TaskManager`, so all tasks reset whenever the server restarts.

Dependencies are installed by the startup update script into a virtualenv at `.venv` from
`requirements.txt`. The `python3.12-venv` system package is required to create that venv and is
already present in the VM snapshot. Use the `.venv/bin/` executables directly (no activation needed).

Non-obvious caveats:
- All commands MUST be run from the repo root. Modules use absolute package imports
  (`from backend...`, `from agents...`), so running from a subdirectory breaks imports.
- Run the backend (dev mode, hot reload): `.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- Run tests: `.venv/bin/python -m pytest` (from repo root).
- No linter/formatter is configured in this repo.
- The frontend is static and calls the backend at the hardcoded URL `http://127.0.0.1:8000`
  (see `frontend/index.html`). Serve it with `python3 -m http.server 5500` from `frontend/`,
  or just use the FastAPI Swagger UI at `http://127.0.0.1:8000/docs` to exercise the API.
- Core API flow: `POST /tasks` -> `POST /tasks/{id}/run` (status becomes `WAITING_FOR_APPROVAL`)
  -> `POST /tasks/{id}/approval` -> `POST /tasks/{id}/deploy` (status becomes `DEPLOYED`).
