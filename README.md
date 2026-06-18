# CareerGraph AI

CareerGraph AI is an evidence-grounded AI career intelligence workspace for
students and early-career candidates. It helps a user upload a resume, build a
structured evidence profile, recommend realistic career directions, identify
readiness gaps, generate advisor-style guidance, and optionally compare the
resume against a pasted job description.

The current product is a stateless MVP. It is not an auto-apply product, not a
scraper, and not a persistent multi-user SaaS yet.

## GitHub Description

Evidence-grounded AI career advisor workspace for resume analysis, career
direction recommendations, readiness gaps, and resume-safe next actions.

## What Makes It Different

CareerGraph AI treats a resume as evidence, not as permission to invent better
claims. The backend uses structured schemas, deterministic validation, and
source evidence checks so advisor guidance can improve positioning without
fabricating skills, metrics, credentials, links, projects, or experience.

The core product question is:

> Given the evidence already present in this resume, what career directions are
> realistic, what gaps remain, and what should the candidate do next?

## Current MVP Features

- PDF and DOCX resume upload with text extraction.
- Async analysis jobs for the main Analyze workflow.
- Step-level progress for:
  - Profile Parsing
  - Career Directions
  - Advisor/Suggestions
  - Job Matching, currently skipped unless a separate job description is used.
- Structured `CandidateProfile` extraction from resume text.
- Evidence-supported career direction recommendations.
- Selected-direction advisor guidance:
  - strongest evidence
  - readiness gaps
  - resume-ready improvements
  - evidence to build next
  - practical next actions
- Optional job description parsing and resume-to-job match scoring.
- English and Simplified Chinese UI/advisor language support.
- Resume evidence excerpts are preserved in the source language.
- Resume-ready rewrites preserve the resume source language when appropriate.
- Friendly localized error messages for user-facing failures.
- Backend tests for parsing, matching, career directions, suggestions, and
  async analysis jobs.

## MVP Scope

Implemented today:

- Stateless resume upload and text extraction.
- Stateless profile parsing, direction recommendation, advisor generation, and
  optional job matching.
- In-memory async analysis jobs. Jobs are lost if the backend restarts.
- Task-specific OpenAI model and timeout configuration.
- Deterministic fallbacks for career directions and advisor guidance when
  appropriate.
- Local development CORS for both `localhost` and `127.0.0.1`.

Intentionally not implemented yet:

- Authentication.
- User accounts or ownership checks.
- Database-backed persistence for resumes, jobs, facts, matches, or suggestions.
- Durable background workers.
- Payments.
- Resume export.
- Auto-apply or automatic application submission.
- LinkedIn scraping or browser automation.
- Saved job boards or batch matching.

PostgreSQL, Redis, SQLAlchemy models, and Docker Compose are present as
production-oriented scaffolding, but the main MVP workflows are currently
stateless and in-memory.

## Architecture

```text
frontend/  Next.js 16, React 19, TypeScript workspace UI
backend/   FastAPI, Pydantic 2, OpenAI structured output, deterministic services
docs/      Architecture, API, data model, roadmap, and planning notes
scripts/   Local setup helpers
```

The current Analyze flow:

1. Frontend uploads a PDF/DOCX resume to `/api/v1/resumes/upload`.
2. User clicks Analyze.
3. Frontend creates an async job with `POST /api/v1/analysis-jobs`.
4. Backend immediately returns a `job_id`.
5. Frontend polls `GET /api/v1/analysis-jobs/{job_id}`.
6. Backend updates step status and partial results as profile, directions, and
   advisor guidance complete.
7. Failed jobs can be retried with `POST /api/v1/analysis-jobs/{job_id}/retry`.

The job runner is intentionally simple: it uses an in-memory registry and
`asyncio.create_task()`. This avoids long browser requests while keeping the
MVP lightweight.

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/Zacharyz26/Careergraph-AI.git
cd Careergraph-AI

./scripts/setup_backend.sh
./scripts/setup_frontend.sh
```

Or install manually:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

### 2. Configure environment

Backend:

```bash
cd backend
cp .env.example .env
```

Set at least:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

Optional task-specific model and timeout settings:

```dotenv
OPENAI_PROFILE_MODEL=
OPENAI_DIRECTION_MODEL=
OPENAI_ADVISOR_MODEL=
OPENAI_PROFILE_TIMEOUT_SECONDS=90
OPENAI_DIRECTION_TIMEOUT_SECONDS=90
OPENAI_ADVISOR_TIMEOUT_SECONDS=90
```

Frontend:

```bash
cd frontend
cp .env.example .env.local
```

Default:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The frontend API client appends `/api/v1` automatically. A base URL already
ending in `/api/v1` is also accepted.

### 3. Run locally

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

Open:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`

Both `http://localhost:3000` and `http://127.0.0.1:3000` are supported in local
development when `ALLOWED_ORIGINS` uses the example value.

## API Overview

Base path: `/api/v1`

- `POST /resumes/upload`: upload PDF/DOCX and extract text.
- `POST /analysis-jobs`: create an async resume analysis job.
- `GET /analysis-jobs/{job_id}`: poll job status, step progress, and partial
  results.
- `POST /analysis-jobs/{job_id}/retry`: retry a failed analysis job.
- `POST /resumes/parse-profile`: direct profile parsing endpoint.
- `POST /career-directions/recommend`: direct career direction endpoint.
- `POST /suggestions/generate`: direct advisor/suggestion endpoint.
- `POST /jobs/parse`: parse a pasted job description.
- `POST /matches/score`: score a structured profile against a structured job.

See [docs/api_design.md](docs/api_design.md) for endpoint details.

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

Near-term improvements:

- Durable job storage and worker queue.
- Persisted resumes, profiles, facts, jobs, matches, and suggestions.
- Review workflow for accepting/editing/rejecting suggestions.
- Resume versioning and export.
- Stronger evaluation fixtures for hallucination prevention and multilingual
  behavior.
- Deployment, observability, cost controls, and security hardening.

Longer-term possibilities:

- Saved job board and batch comparison.
- Portfolio/project evidence analysis.
- User-initiated job import where permitted.
- Authenticated multi-user SaaS.

Auto-apply, scraping, and automatic application submission remain outside the
product scope.
