# CareerGraph AI Backend

FastAPI backend for CareerGraph AI's stateless MVP: resume text extraction,
structured candidate profiles, evidence-supported career directions,
advisor-style resume guidance, optional job parsing, and resume-to-job match
scoring.

## Current Backend Scope

Implemented:

- PDF/DOCX text extraction through `POST /api/v1/resumes/upload`.
- Async in-memory analysis jobs through `/api/v1/analysis-jobs`.
- Structured `CandidateProfile` parsing with OpenAI structured output.
- Evidence-supported career direction recommendations.
- Evidence-grounded advisor guidance and resume-safe improvements.
- Optional pasted job description parsing.
- Hybrid deterministic resume-to-job match scoring.
- English and Simplified Chinese language preference support.
- Friendly user-facing errors with detailed technical errors kept in backend
  logs.
- Deterministic fallbacks for direction/advisor behavior where appropriate.

Not implemented yet:

- Authentication or user ownership.
- Database-backed persistence for workflow data.
- Durable background workers or Redis job queues.
- Resume export or version management.
- Auto-apply, scraping, browser automation, payments, or saved job boards.

The in-memory analysis job registry is intentionally lightweight. It prevents
long browser requests in local use, but jobs are lost when the backend process
restarts.

## Setup

```bash
./scripts/setup_backend.sh
cd backend
source .venv/bin/activate
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
OPENAI_BASE_URL=
OPENAI_TIMEOUT_SECONDS=60
OPENAI_PROFILE_TIMEOUT_SECONDS=90
OPENAI_DIRECTION_TIMEOUT_SECONDS=90
OPENAI_ADVISOR_TIMEOUT_SECONDS=90
OPENAI_MAX_RETRIES=1
MATCHING_ENABLE_SEMANTIC=true
MATCHING_ENABLE_LLM_JUDGE=false
CAREER_DIRECTIONS_ENABLE_LLM=true
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

`OPENAI_PROFILE_MODEL`, `OPENAI_DIRECTION_MODEL`, and `OPENAI_ADVISOR_MODEL`
are optional task-specific overrides. Blank values fall back to `OPENAI_MODEL`.

The database and Redis URLs are present for future durable persistence and worker
workflows. Current product workflows do not require the app to read from or
write to PostgreSQL or Redis.

## Main Workflow API

### Upload Resume

`POST /api/v1/resumes/upload`

Accepts a multipart `file` field containing a PDF or DOCX resume. The backend
extracts text and returns:

- sanitized filename
- file type
- extracted text
- character count
- PDF page count when available

This endpoint does not call an LLM and does not store the file.

### Create Analysis Job

`POST /api/v1/analysis-jobs`

```json
{
  "extracted_text": "Resume text from /resumes/upload",
  "preferred_language": "en"
}
```

Returns immediately with a `job_id`, job status, and initial step states.

### Poll Analysis Job

`GET /api/v1/analysis-jobs/{job_id}`

Returns:

- `queued`, `running`, `succeeded`, or `failed`
- current step
- per-step status
- user-facing error message if failed
- partial/final profile, directions, selected direction, and suggestions

Steps:

- `profile_parsing`
- `career_directions`
- `advisor_suggestions`
- `job_matching`, currently skipped in the default resume-only workflow

### Retry Analysis Job

`POST /api/v1/analysis-jobs/{job_id}/retry`

Restarts the in-memory job from the beginning. This is the simplest safe retry
behavior for the stateless MVP.

## Direct API Endpoints

The direct endpoints remain available for compatibility, debugging, and smaller
workflow surfaces:

- `POST /api/v1/resumes/parse-profile`
- `POST /api/v1/career-directions/recommend`
- `POST /api/v1/suggestions/generate`
- `POST /api/v1/jobs/parse`
- `POST /api/v1/matches/score`

### Profile Parsing

`POST /api/v1/resumes/parse-profile`

Converts extracted resume text into a schema-validated `CandidateProfile`.
Evidence excerpts and resume facts are preserved in the source language.
User-facing rationales, strengths, improvement areas, and inferred role
rationales follow `preferred_language` when natural.

### Career Directions

`POST /api/v1/career-directions/recommend`

Ranks up to five evidence-supported career directions from a `CandidateProfile`.
When configured, the LLM proposes directions from a normalized evidence summary
with stable IDs. The service validates citations and computes the final ranking
deterministically. Without an API key or when proposal generation fails, the
deterministic catalog fallback is used.

### Suggestions

`POST /api/v1/suggestions/generate`

Generates advisor guidance in `general`, `career_direction`, or `job_specific`
mode. Resume-ready suggestions must cite valid source evidence and must not add
unsupported metrics, links, certifications, tools, or missing requirements.
Gaps that cannot be added safely are returned separately as evidence to build.

### Job Match

`POST /api/v1/jobs/parse` converts a pasted job description into a structured
`JobProfile`.

`POST /api/v1/matches/score` compares a structured `CandidateProfile` and
`JobProfile`. The final score is deterministic and requirement-centric. Optional
semantic matching can use embeddings when configured; failures fall back to the
deterministic engine.

## Evidence-Grounding Rules

- AI output is not accepted as a candidate fact unless supported by resume
  evidence.
- Resume-ready text must preserve factual meaning.
- Missing capabilities belong in gaps and next actions, not resume-ready text.
- Technical skills and tool names such as Python, C/C++, ComfyUI, LoRA, and
  Stable Diffusion stay in their original/common form.
- User-facing explanations can be English or Simplified Chinese.
- Source evidence excerpts are not translated.

## Error Handling

Provider exceptions, stack traces, model names, request IDs, and environment
variable names are kept in backend logs. API responses return friendly messages,
for example:

- English: `The analysis is taking longer than expected. Please try again.`
- Chinese: `分析时间较长，请稍后重试。`

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

The test suite uses mock LLM responses where needed and does not require network
access or an OpenAI API key.
