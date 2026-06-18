# API Design

Base path: `/api/v1`

The current API is an MVP contract for stateless resume analysis. Existing
direct endpoints remain available, but the main frontend Analyze flow now uses
asynchronous analysis jobs.

## System

- `GET /health`: process health check. This endpoint is mounted at the app root,
  not under `/api/v1`.

## Main Analysis Jobs

### `POST /analysis-jobs`

Creates an in-memory analysis job and returns immediately.

Request:

```json
{
  "extracted_text": "Resume text returned by /resumes/upload",
  "preferred_language": "en"
}
```

Response includes:

- `job_id`
- `queued | running | succeeded | failed`
- step states
- preferred language
- partial results when available

### `GET /analysis-jobs/{job_id}`

Polls job status.

Step keys:

- `profile_parsing`
- `career_directions`
- `advisor_suggestions`
- `job_matching`

Step statuses:

- `pending`
- `running`
- `succeeded`
- `failed`
- `skipped`

Results may include:

- `profile`
- `career_directions`
- `selected_direction`
- `suggestions`

`job_matching` is skipped in the default resume-only workflow. Optional job
match remains a separate user-triggered flow.

### `POST /analysis-jobs/{job_id}/retry`

Restarts a failed job from the beginning. This is intentionally simple for the
stateless MVP.

Jobs are process-local and not durable across backend restarts.

## Resumes and Profiles

### `POST /resumes/upload`

Uploads a PDF or DOCX resume as multipart form data and extracts text. This
endpoint does not call an LLM and does not store the file.

Response:

- `filename`
- `file_type`
- `extracted_text`
- `character_count`
- `page_count` when available

### `POST /resumes/parse-profile`

Direct endpoint for parsing extracted resume text into a `CandidateProfile`.

Request:

```json
{
  "extracted_text": "Resume text",
  "preferred_language": "zh"
}
```

Evidence excerpts and resume facts stay in the source language. User-facing
rationales and summaries can follow the requested language.

### Placeholder resume endpoints

These routes exist as placeholders and return `501 Not Implemented`:

- `GET /resumes/{resume_id}`
- `GET /resumes/{resume_id}/status`

## Career Directions

### `POST /career-directions/recommend`

Ranks up to five evidence-supported career directions from a structured
`CandidateProfile`.

Request:

```json
{
  "candidate_profile": {},
  "preferred_language": "en"
}
```

The service may use an LLM to propose directions, but deterministic code
validates evidence citations and computes final ranking. If LLM proposal
generation is unavailable, a deterministic catalog fallback is used.

## Suggestions

### `POST /suggestions/generate`

Generates evidence-grounded advisor guidance.

Modes:

- `general`
- `career_direction`
- `job_specific`

Career-direction mode accepts either `target_direction` or a full
`career_direction_result`. Job-specific mode requires both `job_profile` and
`match_result`.

The response separates:

- `overall_summary`
- `resume_ready_improvements`
- `positioning_advice`
- `evidence_gaps`
- `recommended_next_actions`
- `missing_but_not_addable`
- `warnings`

Resume-ready improvements are the only resume-ready text. Missing skills,
unsupported credentials, unsupported metrics, and other gaps must not be added
to resume-ready text.

### Placeholder review endpoint

`PATCH /suggestions/{suggestion_id}` currently returns `501 Not Implemented`.
Persistent suggestion review is future work.

## Jobs

### `POST /jobs/parse`

Parses pasted job description text into a structured `JobProfile`.

The parser extracts required/preferred skills, responsibilities,
qualifications, education requirements, experience requirements, role family,
seniority, employment type, location, remote policy, and supported metadata when
present.

### Placeholder job endpoints

These are not implemented yet:

- `POST /jobs`
- `GET /jobs/{job_id}`

## Matches

### `POST /matches/score`

Scores a structured `CandidateProfile` against a structured `JobProfile`.

The engine:

- indexes candidate evidence from skills, experience, projects, education,
  papers, patents, certifications, leadership, and languages
- normalizes job requirements
- applies deterministic exact, token, taxonomy, and transferable matching
- optionally uses embeddings for semantic similarity
- optionally uses an LLM judge for ambiguous evidence pairs
- computes final aggregate scores deterministically

Response includes requirement-level decisions, evidence, missing skills,
transferable matches, component scores, risk penalties, explanation, and
recommendation label.

### Placeholder match endpoints

These are not implemented yet:

- `POST /matches`
- `GET /matches/{match_id}`

## Language

Endpoints that trigger AI career/advisor output accept:

```json
{
  "preferred_language": "en"
}
```

Supported values:

- `en`
- `zh`

API field names and enum values do not change. User-facing explanations can be
generated in the selected language. Resume evidence excerpts should remain in
the source language.

## Error Handling

Backend logs keep technical provider details. API responses should not expose
OpenAI exception classes, stack traces, request IDs, API keys, or environment
variable names.

Examples of user-facing errors:

- English: `The analysis is taking longer than expected. Please try again.`
- Chinese: `分析时间较长，请稍后重试。`

## Conventions

- Request and response bodies use Pydantic v2 schemas.
- The current MVP is stateless except for process-local analysis jobs.
- UUIDs appear in job and future persistence-oriented contracts.
- Authentication, pagination, durable idempotency, and rate-limit headers are
  future public API work.
