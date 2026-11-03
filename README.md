# Spotlight — Ken's Acting Board
Acting ONLY. Beginner + intermediate jobs only (Ken's order 2026-11-03).
FastAPI + SQLite, modeled on ClaimBoard/Workspace.
- `/` board — roles + platforms, APPROVE — MILLI APPLIES FOR ME
- `/operator` — Milli's pipeline panel (no password, Ken's order)
- `/admin` — add/edit/mark-paid (no password, Ken's order)
Statuses: found → saved → applied → audition → callback → booked → paid / passed
Run: `SPOTLIGHT_DB=/data/spotlight.db uvicorn app:app --host 0.0.0.0 --port $PORT`
