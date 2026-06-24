# API Design

Base path: `/api/v1`

The API supports the current evidence-grounded career advisor MVP. The main
frontend flow uses async analysis jobs plus workspace history. Direct endpoints
remain available for compatibility and smaller workflow surfaces.

## System

- `GET /health`: process health check mounted at the app root, not under
  `/api/v1`.

## Analysis Jobs

### `POST /analysis-jobs`

Creates an async resume analysis job and returns immediately.

Request:

```json
{
  "extracted_text": "Resume text returned by /resumes/upload",
  "preferred_language": "en",
  "resume_id": "optional-resume-id"
}
```

Response includes:

- `job_id`
- `queued | running | succeeded | failed`
- step states
- preferred language
- partial/final results when available

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

`job_matching` is skipped in the default resume-only workflow.

### `POST /analysis-jobs/{job_id}/retry`

Restarts a failed job from the beginning.

Running jobs are process-local. Completed results can be saved to workspace
storage, but this is not a production-grade background job system yet.

## Resumes and Profiles

### `POST /resumes/upload`

Uploads a PDF or DOCX resume as multipart form data and extracts text.

Response:

- `resume_id`
- `filename`
- `file_type`
- `extracted_text`
- `character_count`
- `page_count` when available

When workspace storage is enabled, resume metadata and extracted text can be
stored for local history/reopening.

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

## Workspace

### `GET /workspace/analyses`

Lists saved analyses for the current workspace user.

### `GET /workspace/analyses/{analysis_id}`

Returns a saved resume and analysis result so the frontend can reopen a previous
analysis.

### `PATCH /workspace/analyses/{analysis_id}/suggestions/{review_id}`

Updates suggestion review state.

Supported review statuses are intended for human review workflows such as
pending, accepted, edited, and rejected. This does not generate resume exports.

Workspace ownership currently comes from `X-CareerGraph-User-Email` or the
development default user. This is not real auth.

## Jobs

### `POST /jobs/parse`

Parses pasted job description text into a structured `JobProfile`.

The parser extracts required/preferred skills, responsibilities,
qualifications, education requirements, experience requirements, role family,
seniority, employment type, location, remote policy, and supported metadata when
present.

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
- UUIDs are used for jobs, resumes, analyses, and future durable contracts.
- Current workspace ownership is an MVP scaffold.
- Production auth, pagination, durable idempotency, and rate-limit headers are
  future public API work.
