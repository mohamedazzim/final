# Court Cause-List Pipeline Summary

## Purpose
- Provide court administrators with a reliable way to discover active courts for a specific hearing date, fetch their complete cause lists, and persist them centrally for analytics and UI consumption.

## Architecture Snapshot
- **Frontend**: Next.js admin dashboard exposes "Discover Courts" and "Fetch Data from Selected Courts" workflows. The proxy API delegates every secured action to the backend.
- **Backend**: FastAPI service (`backend/routers/scraper.py`, `backend/scraper.py`) orchestrates discovery, filtering, sanitization, and persistence using SQLAlchemy models (`backend/models.py`).
- **Data Source**: The Madras High Court JSON endpoint (`result.php?file=cause_<DATE>.xml`) returns the full cause list for the requested day; we fetch it once per run and reuse it for all court filters.
- **Database**: SQLite (default) stores `Cause`, `User`, and audit tables. `reset_db.py` can rebuild the schema and seed only `admin/admin` credentials.

## Court Discovery & Selection
1. Admin chooses a hearing date in the dashboard and calls `GET /scraper/discover-courts`.
2. The backend iterates through configured court numbers (defaults 1-75), inspecting the JSON payload for each and returning only courts with live cases.
3. The UI presents the filtered list so operators can select any subset to fetch.

## Court-Wise Fetching & Persistence
1. Admin submits the selected courts to `POST /scraper/fetch-court-data` with the target date.
2. Backend logs contextual metadata (date, court list) and fetches the full JSON feed a single time for efficiency.
3. For every requested court, `process_court_cases` filters the master JSON, composes clean case numbers, sanitizes petitioner/respondent/advocate/raw text, and prepares SQLAlchemy objects.
4. Cases insert via `bulk_save_objects`, committing per court to keep transactions tight and rollback impact minimal.
5. The endpoint returns per-court success counts and the overall `total_cases_saved`. Admin UI surfaces these stats immediately.

## Performance Notes
- Because the JSON feed downloads only once, run time scales primarily with the number of courts processed. Typical runs finish in under a minute for ~30 courts on standard broadband.
- Bottlenecks observed previously (SQLite type-binding errors) are eliminated by coercing every textual field through the new `sanitize_text` helper, so inserts now proceed without retries.
- Further speed-ups are available by parallelizing court filtering or batching DB commits, but current synchronous flow keeps logging and error isolation straightforward.

## Monitoring & Logging
- `ScraperLog` entries track start/stop messages, sample court diagnostics, and per-court outcomes. Query with `GET /scraper/logs` or view via helper scripts (`backend/run_fetch_endpoint.py`).
- `GET /scraper/status` summarizes last run time, status, and total persisted cases; the admin dashboard polls this endpoint for live indicators.
- Errors bubble up both in the HTTP response and the log stream so operators can diagnose failing courts quickly.

## Operational Runbook
1. (Optional) Reset database with `python reset_db.py` to wipe dummy records and keep only `admin/admin`.
2. Sign in to the admin dashboard, choose a hearing date, and click **Discover Courts**.
3. Review the returned list, select the desired court numbers, then trigger **Fetch Data from Selected Courts**.
4. Watch the log panel for per-court updates; upon completion confirm `total_cases_saved` reflects expectations.
5. Use the admin cases listing to verify entries, or inspect the SQLite DB directly (`backend/database.py` defines the path) for deeper checks.
