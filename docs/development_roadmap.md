# Development Roadmap

## Current MVP: Implemented

- Monorepo with FastAPI backend and Next.js frontend.
- PDF/DOCX resume upload and text extraction.
- Async analysis jobs with step-level progress and retry.
- Structured `CandidateProfile` parsing.
- Evidence-supported career direction recommendation.
- Full selected-direction Advisor Report.
- Advisor-style guidance for selected career directions.
- Separation between resume-ready improvements and evidence to build next.
- Suggestion review state for accept/edit/reject workflows.
- Local analysis history and saved analysis reopening.
- Workspace storage through PostgreSQL when available, with JSON fallback for
  local development.
- Optional pasted job description parsing and resume-to-job match scoring.
- Hybrid deterministic match scoring with optional semantic matching.
- English and Simplified Chinese UI/advisor language preference support.
- Friendly localized error handling for AI/provider failures.
- Backend and frontend validation commands.

## Current MVP: Intentional Limits

- No real authentication or identity provider.
- No production-grade authorization.
- No billing, subscriptions, payments, or plan enforcement.
- No production deployment hardening.
- No durable worker queue.
- No resume export.
- No auto-apply, scraping, or browser automation.
- No saved job board or batch job discovery.
- No guarantee that local JSON fallback is appropriate for production data.

## Phase 1: Launch-Readiness Hardening

- Add more representative resume fixtures.
- Add regression tests for English/Chinese output behavior.
- Improve timeout and retry observability.
- Add cost/latency logging for AI tasks.
- Add frontend tests around analysis job polling, history reopening, and failure
  states.
- Add privacy copy and local data handling notes in the UI.
- Improve validation around saved workspace records.

## Phase 2: Production Workspace Foundation

- Replace header/default-user ownership with real authentication.
- Make PostgreSQL the required production workspace store.
- Add repository-level authorization checks.
- Add retention and deletion policies.
- Add migration and seed documentation.
- Add backup/restore guidance for production data.

## Phase 3: Durable AI Job Infrastructure

- Persist running job state durably.
- Introduce a worker queue, likely Redis-backed.
- Add idempotency for analysis job creation/retry.
- Add operational logs, metrics, and failure dashboards.
- Add model cost tracking and rate-limit controls.

## Phase 4: Human Review and Resume Versions

- Deepen suggestion accept/edit/reject transitions.
- Store verified facts and user corrections.
- Save target-specific resume versions.
- Compare versions and track change history.
- Add export only after evidence and review flows are durable.

## Phase 5: Product Expansion

- Portfolio/project evidence analysis.
- Personalized evidence-building roadmaps.
- Interview preparation based on selected direction and evidence gaps.
- Application tracking without auto-apply.
- User-initiated job import where permitted.

## Out of Scope Unless Explicitly Revisited

- Automatic application submission.
- LinkedIn scraping.
- Restrictive job board scraping.
- Browser automation for applications.
- Fabricating resume claims, credentials, links, metrics, or experience.
- Hiring probability promises.
