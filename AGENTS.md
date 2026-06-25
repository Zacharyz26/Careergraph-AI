# CareerGraph AI

## Project State

CareerGraph AI is a functional MVP career advisor for students and early-career
candidates. It has a working async analysis workflow, a local workspace/history
layer, and PostgreSQL schema scaffolding. It is not yet a production multi-user
SaaS: it lacks real authentication, billing, deployment hardening, and a durable
background worker queue.

The primary implemented workflow is:

1. Upload a PDF or DOCX resume (`POST /api/v1/resumes/upload`).
2. Create an async analysis job (`POST /api/v1/analysis-jobs`) and poll it
   (`GET /api/v1/analysis-jobs/{job_id}`).
3. The job parses extracted text into a structured `CandidateProfile`,
   recommends evidence-supported career directions, and generates advisor
   guidance (strengths, readiness gaps, resume-safe rewrites, next actions).
4. Completed analyses are saved to the workspace and appear in local history.
5. A pasted job description can optionally be parsed and scored for resume fit.

The product direction is career direction and evidence-grounded resume
improvement. It is not an auto-apply product. Suggestions must use facts already
supported by candidate evidence and must not invent skills, metrics,
qualifications, or experience.

## Architecture

- `frontend/`: Next.js 16, React 19, and TypeScript workflow UI with polling,
  analysis history, and EN/简体中文 localization.
- `backend/`: FastAPI, Pydantic 2. Layered as `api/v1` -> `services` ->
  `workspace_store`. Async analysis runs in-process via `AnalysisJobService`
  (`asyncio` tasks, not a durable queue).
- `docs/`: architecture, API, data model, roadmap, and product planning.
- `scripts/`: local setup helpers.

Persistence is real but has two backends. `WorkspaceStore` writes to PostgreSQL
(SQLAlchemy async, Alembic migrations under `backend/migrations/`) and falls
back to a local JSON file (`WORKSPACE_ENABLE_JSON_FALLBACK`) when PostgreSQL is
unavailable. The JSON fallback is the common path for local development. Note
the current fallback latch is one-way for the process lifetime once a DB call
fails.

Redis and Docker Compose are present as production-oriented scaffolding; the
job runner does not yet use a real queue, and job state held in
`AnalysisJobService` memory is lost on process restart (retry recovers from the
workspace store).

The root `README.md` may lag behind the working tree and must not be treated as
the only source of truth. Inspect current services, API routes, schemas, tests,
frontend components, and relevant files under `docs/` before making
architectural assumptions.

## Scope Guardrails

Unless explicitly requested, do not add:

- Auto-apply or automatic application submission
- LinkedIn / job-board scraping or browser automation
- Real authentication or identity-provider integration
- Payments, billing, or subscription plans

These are deliberate non-goals for the current MVP, not missing wiring. The
header-based workspace identity (`X-CareerGraph-User-Email`) is development
scaffolding only and must not be treated as real authorization.

Keep changes aligned with the existing MVP and preserve the human-in-the-loop,
evidence-grounded behavior. The strongest invariant in the codebase is the
anti-hallucination discipline in `SuggestionService` and the user-facing
sanitizer; do not weaken it.

## Working Norms

- Run the backend test suite before and after changes: `cd backend && pytest -q`
  (99 tests as of this writing).
- Frontend checks: `cd frontend && npm run lint && npm run typecheck`.
- Most AI services degrade gracefully without an `OPENAI_API_KEY` via
  deterministic fallbacks; preserve that behavior when editing services.
