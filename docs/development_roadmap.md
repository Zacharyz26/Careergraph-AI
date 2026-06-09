# Development Roadmap

## Phase 0: Foundation

- Establish monorepo, typed schemas, service boundaries, and local infrastructure.
- Add CI, formatting, linting, migrations, and test database fixtures.
- Define authentication and file retention policies.

## Phase 1: Resume Ingestion

- Validate and store PDF/DOCX uploads.
- Integrate document parsing with fallback parsers.
- Build source blocks, candidate profile extraction, and verified fact review.
- Measure parsing accuracy against a representative resume fixture set.

## Phase 2: Job Parsing and Matching

- Parse pasted job descriptions into typed requirements.
- Implement deterministic filters and skill normalization.
- Add embeddings and calibrated component scoring.
- Return evidence and gaps alongside every score.

## Phase 3: Human-Reviewed Suggestions

- Generate suggestions constrained by verified facts.
- Implement accept, edit, reject, and regenerate transitions.
- Save approved changes as versioned resume content.
- Add hallucination and unsupported-claim evaluation.

## Phase 4: Product Completion

- Add ATS-readable rendering and export.
- Add 30/60/90 day roadmap generation.
- Add observability, cost controls, security review, and deployment automation.
- Run accessibility, privacy, and end-to-end acceptance testing.

## Later Versions

- Saved job board and batch comparison.
- User-initiated job-link import where permitted.
- GitHub project evidence analysis.
- Browser extension for saving jobs, without automatic application submission.
