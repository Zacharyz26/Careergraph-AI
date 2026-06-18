# Architecture

## Overview

CareerGraph AI is a monorepo with a Next.js frontend and FastAPI backend. The
current product is a stateless MVP for evidence-grounded career intelligence,
not a production multi-user SaaS.

The main workflow turns a resume into:

- a structured evidence profile
- realistic career direction hypotheses
- readiness gaps
- advisor-style guidance
- resume-safe improvements and next actions

Optional job match remains secondary to the career direction workflow.

## Runtime Shape

```text
Browser / Next.js
  -> FastAPI /api/v1
    -> document parser
    -> in-memory analysis job service
    -> profile, direction, suggestion, job, and match services
    -> OpenAI structured output where configured
```

The application includes PostgreSQL, Redis, SQLAlchemy models, and Docker
Compose scaffolding for future production architecture. The currently
implemented business workflow does not persist resumes, profiles, jobs, matches,
or suggestions.

## Frontend

`frontend/` is a Next.js 16, React 19, TypeScript workspace UI.

It provides:

- PDF/DOCX resume upload.
- Ready-to-analyze state after upload.
- Async job creation and polling.
- Step-level progress UI.
- Evidence profile panel.
- Career direction cards and selected-direction details.
- Advisor guidance sections.
- Optional job description match panel.
- Lightweight English/Simplified Chinese UI dictionary.

## Backend

`backend/` is a FastAPI app using Pydantic 2 schemas and service-layer business
logic.

Key areas:

- `app/api/v1/`: HTTP routes.
- `app/schemas/`: request and response contracts.
- `app/services/`: parsing, direction recommendation, suggestion, matching, and
  in-memory analysis job orchestration.
- `app/models/` and `app/repositories/`: production-oriented persistence
  scaffolding, not used by the main MVP workflow yet.

## Async Analysis Jobs

The Analyze button now creates an in-memory job:

1. `POST /api/v1/analysis-jobs`
2. Backend returns a `job_id` immediately.
3. Frontend polls `GET /api/v1/analysis-jobs/{job_id}`.
4. Backend updates step status and partial results.
5. Failed jobs can be restarted with
   `POST /api/v1/analysis-jobs/{job_id}/retry`.

Steps:

- Profile Parsing
- Career Directions
- Advisor/Suggestions
- Job Matching, skipped in the default resume-only workflow

This avoids holding a single browser request open for the full AI workflow. It
is intentionally not durable: jobs are process-local and disappear on backend
restart.

## AI and Evidence-Grounding

CareerGraph AI uses LLMs as structured assistants, not as authorities.

Principles:

- Candidate facts must come from resume evidence.
- Resume-ready improvements must cite valid source evidence.
- Missing capabilities are represented as readiness gaps and next actions, not
  as resume claims.
- Deterministic code validates and ranks career directions.
- Deterministic matching computes final job-fit scores.
- Provider failures return friendly errors and keep technical details in logs.

## Career Direction Recommendations

The direction recommender follows proposal, validation, and ranking:

1. Build an evidence summary from the structured profile.
2. Optionally ask an LLM for structured direction proposals with evidence IDs.
3. Remove unsupported citations and evidence-free directions.
4. Downgrade skill-only primary fits.
5. Deterministically rank directions by evidence strength, diversity,
   directness, role-family consistency, seniority fit, and gap severity.
6. Fall back to a deterministic catalog when LLM proposal generation is
   unavailable.

## Advisor Guidance

Suggestions are split into distinct concepts:

- strongest evidence
- readiness gaps
- resume-ready improvements
- positioning advice
- next actions
- evidence to build next

The service validates LLM output and removes unsupported claims. Deterministic
fallbacks produce conservative guidance when an API key is missing or generation
fails.

## Matching

The optional job match flow is requirement-centric:

1. Parse pasted job text into a structured `JobProfile`.
2. Convert profile content into evidence records.
3. Match requirements through deterministic exact/token/taxonomy rules.
4. Optionally use embeddings for semantic paraphrases.
5. Optionally use an LLM judge only for ambiguous evidence pairs.
6. Compute final scores deterministically.

Job matching is a secondary feature and does not drive the default career
direction workflow.

## Language Support

The MVP supports English and Simplified Chinese through:

- frontend local UI dictionary
- `preferred_language` request fields
- backend prompt instructions
- localized user-facing errors

Schema field names, enum values, and API contracts remain stable. Resume
evidence excerpts stay in the source language. Resume-ready rewrites preserve
the source resume language when appropriate.

## Future Architecture

The next major architecture step is durable state:

- persistent analysis jobs
- Redis or another worker queue
- persisted resumes, profiles, facts, jobs, matches, suggestions, and versions
- authenticated ownership boundaries
- object storage for uploaded files
- observability, cost tracking, and deployment hardening
