# Development Roadmap

## Current MVP: Implemented

- Monorepo with FastAPI backend and Next.js frontend.
- PDF/DOCX resume upload and text extraction.
- Structured `CandidateProfile` parsing.
- Evidence-supported career direction recommendation.
- Advisor-style guidance for selected career directions.
- Separation between resume-ready improvements and evidence to build next.
- Optional job description parsing and resume-to-job match scoring.
- Hybrid deterministic match scoring with optional semantic matching.
- In-memory async analysis jobs with step-level progress and retry.
- English and Simplified Chinese UI/advisor language preference support.
- Friendly user-facing error handling for AI/provider failures.
- Backend and frontend validation commands.

## Current MVP: Intentional Limits

- Stateless user workflow.
- In-memory analysis jobs only.
- No authentication.
- No persisted resumes, jobs, facts, matches, suggestions, or versions.
- No resume export.
- No payments.
- No auto-apply, scraping, or browser automation.
- No saved job board or batch matching.

## Phase 1: Stabilize the MVP

- Add more representative resume and job fixtures.
- Add regression tests for English/Chinese output behavior.
- Improve timeout and retry observability.
- Add lightweight cost/latency logging for AI tasks.
- Add stronger frontend tests around analysis job polling and failure states.
- Refine UX copy for failed jobs, partial results, and retry.

## Phase 2: Durable Workflow Infrastructure

- Persist analysis jobs and step states.
- Introduce a durable worker queue, likely Redis-backed.
- Persist uploaded resume metadata and extracted text.
- Persist generated profiles, direction results, and advisor output.
- Add cleanup/retention policies for uploaded and generated data.
- Add operational logs, metrics, and failure dashboards.

## Phase 3: Authenticated Product Foundation

- Add authentication and user ownership boundaries.
- Add repository-level authorization checks.
- Add user-scoped resumes, jobs, matches, and suggestions.
- Add saved analysis history.
- Add privacy and data deletion controls.

## Phase 4: Human Review and Resume Versions

- Implement suggestion accept/edit/reject state transitions.
- Store verified facts and user corrections.
- Save target-specific resume versions.
- Compare versions and track change history.
- Add export only after evidence and review flows are durable.

## Phase 5: Product Expansion

- Saved job board.
- Batch comparison across multiple jobs.
- Portfolio/project evidence analysis.
- 30/60/90 day evidence-building roadmap.
- User-initiated job import where permitted.
- Deployment hardening and production security review.

## Out of Scope Unless Explicitly Revisited

- Automatic application submission.
- LinkedIn scraping.
- Browser automation for applications.
- Fabricating resume claims, credentials, links, metrics, or experience.
- Hiring probability promises.
