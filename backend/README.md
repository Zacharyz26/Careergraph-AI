# CareerGraph AI Backend

FastAPI backend for CareerGraph AI, an evidence-grounded AI career advisor
workspace.

The backend extracts resume text, parses structured candidate profiles,
recommends realistic career directions, generates advisor guidance, supports an
async analysis job flow, stores local workspace history, and optionally scores a
resume against a pasted job description.

## Current Backend Scope

Implemented:

- PDF/DOCX text extraction via `POST /api/v1/resumes/upload`.
- Async analysis jobs via `/api/v1/analysis-jobs`.
- Structured `CandidateProfile` parsing with OpenAI structured output.
- Evidence-supported career direction recommendations.
- Evidence-grounded advisor guidance and resume-safe improvements.
- Suggestion review state for accept/edit/reject style workflows.
- Workspace history endpoints for saved analyses.
- PostgreSQL models and Alembic migrations for workspace entities.
- JSON fallback workspace store for local development.
- Optional pasted job description parsing.
- Hybrid deterministic resume-to-job match scoring.
- English and Simplified Chinese language preference support.
- Friendly user-facing errors with technical details kept in backend logs.

Not production-ready yet:

- Real authentication or identity provider integration.
- Billing, subscriptions, or payments.
- Production-grade authorization beyond the current workspace owner scaffold.
- Durable background workers or Redis-backed job queues.
- Production deployment, observability, secrets management, or rate limiting.
- Resume export or generated resume documents.
- Auto-apply, scraping, browser automation, or saved job boards.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

Run:

```bash
uvicorn app.main:app --reload
```

API:

- Base URL: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

## Environment Variables

Common settings:

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_PROFILE_MODEL=
OPENAI_DIRECTION_MODEL=
OPENAI_ADVISOR_MODEL=
OPENAI_JUDGE_MODEL=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TIMEOUT_SECONDS=60
OPENAI_PROFILE_TIMEOUT_SECONDS=90
OPENAI_DIRECTION_TIMEOUT_SECONDS=90
OPENAI_ADVISOR_TIMEOUT_SECONDS=90
OPENAI_MAX_RETRIES=1
MATCHING_ENABLE_SEMANTIC=true
MATCHING_ENABLE_LLM_JUDGE=false
CAREER_DIRECTIONS_ENABLE_LLM=true
WORKSPACE_DEFAULT_USER_EMAIL=local@careergraph.local
WORKSPACE_ENABLE_JSON_FALLBACK=true
WORKSPACE_FALLBACK_STORE_PATH=.careergraph_workspace.json
DATABASE_URL=postgresql+asyncpg://careergraph:careergraph@localhost:5432/careergraph
DATABASE_CONNECT_TIMEOUT_SECONDS=2
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Task-specific model variables are optional. Blank task-specific values fall
back to `OPENAI_MODEL`.

`DATABASE_URL` and migrations exist for production-oriented persistence work.
For local MVP development, `WORKSPACE_ENABLE_JSON_FALLBACK=true` lets the app
store workspace history in `.careergraph_workspace.json` if PostgreSQL is not
available.

## Workspace Storage

The current workspace layer stores:

- uploaded resume metadata and extracted text
- completed analysis job results
- generated candidate profiles, career directions, selected direction, and
  suggestions
- suggestion review statuses and edited text

Ownership is currently based on `X-CareerGraph-User-Email` or
`WORKSPACE_DEFAULT_USER_EMAIL` in non-production environments. This is an MVP
development scaffold, not real authentication.

## Main Workflow API

### Upload Resume

`POST /api/v1/resumes/upload`

Accepts a multipart `file` field containing a PDF or DOCX resume. The backend
extracts text and returns resume metadata, extracted text, character count, and
PDF page count when available.

### Create Analysis Job

`POST /api/v1/analysis-jobs`

```json
{
  "extracted_text": "Resume text from /resumes/upload",
  "preferred_language": "en",
  "resume_id": "optional-uploaded-resume-id"
}
```

Returns immediately with a `job_id`, job status, and initial step states.

### Poll Analysis Job

`GET /api/v1/analysis-jobs/{job_id}`

Returns job status, step progress, user-facing errors, and partial/final
profile, directions, selected direction, and suggestions.

### Retry Analysis Job

`POST /api/v1/analysis-jobs/{job_id}/retry`

Restarts a failed job from the beginning.

## Workspace API

- `GET /api/v1/workspace/analyses`
- `GET /api/v1/workspace/analyses/{analysis_id}`
- `PATCH /api/v1/workspace/analyses/{analysis_id}/suggestions/{review_id}`

These endpoints support local analysis history, reopening previous analyses,
and saving suggestion review state.

## Direct API Endpoints

Direct endpoints remain available for compatibility and debugging:

- `POST /api/v1/resumes/parse-profile`
- `POST /api/v1/career-directions/recommend`
- `POST /api/v1/suggestions/generate`
- `POST /api/v1/jobs/parse`
- `POST /api/v1/matches/score`

## Evidence-Grounding Rules

- AI output is not accepted as a candidate fact unless supported by resume
  evidence.
- Resume-ready text must preserve factual meaning.
- Missing capabilities belong in gaps and next actions, not resume-ready text.
- Technical skills and tool names stay in their original/common form.
- User-facing explanations can be English or Simplified Chinese.
- Source evidence excerpts are not translated.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

The test suite uses mocks where needed and should not require an OpenAI API key.
