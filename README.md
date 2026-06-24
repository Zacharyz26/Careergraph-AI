# CareerGraph AI

Evidence-grounded AI career advisor workspace for resume analysis, realistic
career direction recommendations, readiness gaps, and resume-safe next actions.

CareerGraph AI helps a user upload a resume, build a structured evidence
profile, compare supported career directions, inspect why a direction fits,
generate advisor-style guidance, and optionally compare the resume against a
pasted job description.

The product is an MVP. It has a local workspace/history layer and PostgreSQL
schema scaffolding, but it is not yet a production multi-user SaaS with real
authentication, billing, deployment hardening, or durable background workers.

## What Makes It Different

CareerGraph treats the resume as evidence. It should not invent skills,
metrics, credentials, links, projects, publications, or experience. Guidance is
split into:

- what the resume already supports
- what is missing or weak
- what can safely be improved in resume wording
- what evidence should be built next

The core product question is:

> Given the evidence already present in this resume, what career directions are
> realistic, what gaps remain, and what should the candidate do next?

## Current Features

- PDF and DOCX resume upload with text extraction.
- Async resume analysis job flow with polling and retry.
- Step-level progress for profile parsing, career directions, advisor
  suggestions, and skipped/default job matching.
- Structured `CandidateProfile` extraction.
- Evidence-supported career direction ranking.
- Full-width selected-direction Advisor Report with:
  - recommendation logic
  - key supporting evidence
  - why the direction fits
  - role positioning
  - demonstrated strengths
  - readiness gaps
  - growth roadmap
  - example titles
- Advisor guidance for the selected direction:
  - strongest evidence
  - readiness gaps
  - resume-ready improvements
  - positioning advice
  - recommended next actions
  - evidence to build next
- Suggestion review state prepared for accept/edit/reject workflows.
- Local analysis history and saved analysis reopening.
- Optional pasted job description parsing and resume-to-job fit scoring.
- English and Simplified Chinese UI/advisor language support.
- Friendly localized errors for user-facing failures.
- Task-specific OpenAI model and timeout configuration.

## MVP Scope and Limitations

Implemented today:

- Local resume upload and text extraction.
- Main async analysis workflow.
- Local workspace history and suggestion review state.
- PostgreSQL models and Alembic migrations for future durable workspace data.
- JSON fallback storage for local development when PostgreSQL is unavailable.
- Header/default-user based workspace ownership for MVP development.
- Direct API endpoints for profile parsing, direction recommendation,
  suggestions, job parsing, and match scoring.

Not implemented as production features:

- Real authentication or identity provider integration.
- Production-grade authorization beyond the current workspace owner scaffold.
- Billing, subscriptions, plans, or payments.
- Production deployment, monitoring, rate limiting, or secrets management.
- Durable worker queue such as Redis/Celery/RQ.
- Resume export or generated resume documents.
- Auto-apply or automatic application submission.
- LinkedIn scraping, Indeed scraping, browser automation, or unrestricted web
  crawling.
- Production retention/deletion controls.

## Architecture

```text
frontend/  Next.js 16, React 19, TypeScript workspace UI
backend/   FastAPI, Pydantic 2, OpenAI structured output, service layer
docs/      Architecture, API, data model, roadmap, planning notes
scripts/   Local setup helpers
```

Main flow:

1. Upload a PDF/DOCX resume to `POST /api/v1/resumes/upload`.
2. The backend extracts text and stores local workspace metadata when enabled.
3. Click Analyze.
4. The frontend creates an async job with `POST /api/v1/analysis-jobs`.
5. The backend returns a `job_id` immediately.
6. The frontend polls `GET /api/v1/analysis-jobs/{job_id}`.
7. The backend produces profile, directions, selected direction, and advisor
   suggestions.
8. Completed analyses appear in local analysis history.

The async job runner is intentionally simple and process-local. Workspace data
can be stored in PostgreSQL when configured, with JSON fallback for local MVP
use.

## Local Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set at least:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

Useful local defaults:

```dotenv
WORKSPACE_ENABLE_JSON_FALLBACK=true
WORKSPACE_FALLBACK_STORE_PATH=.careergraph_workspace.json
WORKSPACE_DEFAULT_USER_EMAIL=local@careergraph.local
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Run:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Default frontend config:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WORKSPACE_USER_EMAIL=
```

Open:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend docs: `http://localhost:8000/docs`

For WSL/networked local development, run the backend on `0.0.0.0` and set
`NEXT_PUBLIC_API_BASE_URL` to the reachable backend host.

## API Overview

Base path: `/api/v1`

- `POST /resumes/upload`
- `POST /resumes/parse-profile`
- `POST /analysis-jobs`
- `GET /analysis-jobs/{job_id}`
- `POST /analysis-jobs/{job_id}/retry`
- `POST /career-directions/recommend`
- `POST /suggestions/generate`
- `POST /jobs/parse`
- `POST /matches/score`
- `GET /workspace/analyses`
- `GET /workspace/analyses/{analysis_id}`
- `PATCH /workspace/analyses/{analysis_id}/suggestions/{review_id}`

See [docs/api_design.md](docs/api_design.md) for more detail.

## Testing

Backend:

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Roadmap

Highest-priority next steps:

- Replace MVP header/default-user ownership with real authentication.
- Make PostgreSQL the required production workspace store.
- Persist async job state durably and move long AI work to a worker queue.
- Add privacy controls for data deletion/export of stored workspace data.
- Add stronger reliability, observability, and cost controls.
- Expand human review workflows for suggestions and resume changes.
- Add evaluation fixtures for hallucination prevention and multilingual quality.

Out of scope for now:

- Auto-apply.
- Scraping restricted job boards or LinkedIn.
- Browser automation.
- Hiring probability promises.
- Fabricating resume claims.
