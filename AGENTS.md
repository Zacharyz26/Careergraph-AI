# CareerGraph AI

## Project State

CareerGraph AI is a functional, stateless MVP for students and early-career
candidates. It is not yet a persistent multi-user SaaS.

The primary implemented workflow is:

1. Upload a PDF or DOCX resume.
2. Parse extracted text into a structured `CandidateProfile`.
3. Recommend evidence-supported career directions.
4. Generate evidence-grounded resume improvement suggestions.
5. Optionally parse a pasted job description and score resume-to-job fit.

The product direction is career direction and evidence-grounded resume
improvement. It is not an auto-apply product. Suggestions must use facts already
supported by candidate evidence and must not invent skills, metrics,
qualifications, or experience.

## Architecture

- `frontend/`: Next.js 16, React 19, and TypeScript workflow UI.
- `backend/`: FastAPI, Pydantic 2, parsing, matching, recommendation, and
  suggestion services.
- `docs/`: architecture, API, data model, roadmap, and product planning.
- `scripts/`: local setup helpers.

SQLAlchemy models, PostgreSQL, pgvector, Redis, and Docker Compose are present
as production-oriented scaffolding. Most currently implemented business
workflows are stateless and should not be assumed to read from or write to a
database. Repository methods, persisted API operations, background jobs,
verified-fact storage, version management, and review state transitions remain
largely unimplemented.

The root `README.md` may lag behind the working tree and must not be treated as
the only source of truth. Inspect current services, API routes, schemas, tests,
frontend components, and relevant files under `docs/` before making
architectural assumptions.

## Scope Guardrails

Unless explicitly requested, do not add:

- Auto-apply or automatic application submission
- LinkedIn scraping
- Browser automation
- Authentication
- Payments
- Database persistence

Keep changes aligned with the existing stateless MVP and preserve the
human-in-the-loop, evidence-grounded behavior.

## Immediate Priority

The current frontend opens and the resume file picker works, but selecting a
PDF or DOCX appears to do nothing. The next task is to debug the complete upload
execution path:

`ResumeUploader` file selection -> workflow handler -> frontend API request ->
FastAPI `/api/v1/resumes/upload` -> response/error rendering.

Do not assume the failure is persistence-related. Check browser event handling,
request execution, API base URL/CORS, backend availability, multipart handling,
and whether loading or error state is visible.
