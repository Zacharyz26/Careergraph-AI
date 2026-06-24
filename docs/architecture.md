# Architecture

## Overview

CareerGraph AI is a monorepo with a Next.js frontend and FastAPI backend. The
current product is an evidence-grounded AI career advisor workspace for resume
analysis, career direction recommendation, and advisor-style next steps.

It is an MVP with local workspace history and production-oriented persistence
scaffolding. It is not yet a production multi-user SaaS with real auth, billing,
deployment hardening, or durable workers.

## Runtime Shape

```text
Browser / Next.js
  -> FastAPI /api/v1
    -> resume parser
    -> async analysis job service
    -> profile, direction, suggestion, job, and match services
    -> workspace store
    -> OpenAI structured output where configured
```

The main workflow turns a resume into:

- a structured evidence profile
- realistic career direction hypotheses
- a selected-direction Advisor Report
- readiness gaps
- advisor guidance
- resume-safe improvements and next actions

Optional pasted job match remains secondary.

## Frontend

`frontend/` is a Next.js 16, React 19, TypeScript workspace UI.

It provides:

- PDF/DOCX resume upload.
- Ready-to-analyze state after upload.
- Async job creation and polling.
- Step-level progress UI.
- Evidence profile panel.
- Career direction ranking cards.
- Full-width selected-direction Advisor Report.
- Advisor guidance and suggestion review controls.
- Analysis history and saved analysis reopening.
- Lightweight English/Simplified Chinese UI dictionary.

## Backend

`backend/` is a FastAPI app using Pydantic 2 schemas and service-layer business
logic.

Key areas:

- `app/api/v1/`: HTTP routes.
- `app/schemas/`: request and response contracts.
- `app/services/`: parsing, direction recommendation, suggestion, matching,
  analysis job orchestration, and workspace storage.
- `app/models/`: SQLAlchemy models for future durable SaaS workspace data.
- `migrations/`: Alembic migrations for PostgreSQL schema setup.

## Async Analysis Jobs

The Analyze button creates a process-local async job:

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

The job runner avoids long browser requests but is not a durable production
queue. Jobs are process-local while running.

## Workspace Storage

The workspace layer supports:

- saved uploaded resume metadata and extracted text
- saved completed analysis results
- saved profile, directions, selected direction, and suggestions
- suggestion review status and edited text
- analysis history and reopening previous analyses

Storage modes:

- PostgreSQL through SQLAlchemy models when configured.
- JSON fallback at `.careergraph_workspace.json` for local development when
  `WORKSPACE_ENABLE_JSON_FALLBACK=true`.

The current workspace user is resolved from `X-CareerGraph-User-Email` or a
development default user in non-production. This creates an ownership boundary
for local MVP work, but it is not real authentication.

## AI and Evidence-Grounding

CareerGraph uses LLMs as structured assistants, not as authorities.

Principles:

- Candidate facts must come from resume evidence.
- Resume-ready improvements must cite valid source evidence.
- Missing capabilities are represented as readiness gaps and next actions, not
  resume claims.
- Deterministic code validates career direction citations and ranking.
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

Suggestions are separated into:

- strongest evidence
- readiness gaps
- resume-ready improvements
- positioning advice
- next actions
- evidence to build next

The service validates LLM output and removes unsupported claims. Deterministic
fallbacks produce conservative guidance when generation fails.

## Matching

The optional job match flow is requirement-centric:

1. Parse pasted job text into a structured `JobProfile`.
2. Convert profile content into evidence records.
3. Match requirements through deterministic exact/token/taxonomy rules.
4. Optionally use embeddings for semantic paraphrases.
5. Optionally use an LLM judge only for ambiguous evidence pairs.
6. Compute final scores deterministically.

Job matching does not drive the default career direction workflow.

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

The next architecture milestones are:

- real authentication and authorization
- production PostgreSQL-only persistence
- durable analysis job state
- worker queue for long AI tasks
- privacy controls for deletion/export
- observability, cost tracking, and deployment hardening
