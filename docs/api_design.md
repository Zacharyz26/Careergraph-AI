# API Design

Base path: `/api/v1`

## System

- `GET /health`: process health check.

## Resumes and Profiles

- `POST /resumes/upload`: upload a PDF or DOCX and extract its text.
- `POST /resumes/parse-profile`: parse extracted text into content intelligence
  and generic, evidence-based target role inferences. Role family and seniority
  use controlled taxonomies for stable downstream matching and analytics.
- `GET /resumes/{resume_id}`: fetch resume metadata.
- `GET /resumes/{resume_id}/status`: fetch processing state.
- Planned: `POST /resumes/analyze-layout` using the original PDF/DOCX and layout
  metadata for layout, ATS, and template intelligence.
- Planned: `GET /resumes/{resume_id}/profile`.
- Planned: `GET /resumes/{resume_id}/facts`.
- Planned: `PATCH /facts/{fact_id}` for user verification or correction.
- Planned: resume version list, create, compare, and export endpoints.

## Jobs

- `POST /jobs/parse`: parse pasted text into an evidence-bearing `JobProfile`.
- `POST /jobs`: persist and parse a pasted job description.
- `GET /jobs/{job_id}`: fetch raw and structured job data.

## Matches

- `POST /matches/score`: score a structured candidate profile against a
  structured job profile with hybrid, requirement-centric MVP scoring.
  The response contains requirement-level `full_match`, `partial_match`,
  `transferable_match`, or `missing` decisions with candidate evidence.
- `POST /matches`: start matching one resume against one job.
- `GET /matches/{match_id}`: fetch score components, evidence, and gaps.

### Match Scoring Design

- Candidate evidence is indexed from skills, experience, projects, papers,
  patents, education, certifications, and languages.
- Job requirements are normalized from required skills, preferred skills,
  responsibilities, qualifications, education requirements, and experience
  requirements.
- Matching proceeds through exact text, normalized tokens, shared taxonomy
  concepts, explicitly transferable concept relationships, and optional
  embedding similarity.
- Embeddings are batched in memory and are not persisted. Missing configuration
  or provider failures fall back to deterministic matching.
- An optional structured LLM evidence judge may review ambiguous pairs only. It
  can select only evidence supplied by the engine and never assigns aggregate
  scores.
- A taxonomy match is possible only when the candidate profile contains evidence
  expressing that concept. The taxonomy does not add candidate capabilities.
- Aggregate output includes required and preferred coverage, responsibility
  alignment, education fit, seniority fit, evidence strength, and risk penalty.
- Missing required skills, qualifications, education, and experience
  requirements create explicit risks and deterministic score penalties.

## Career Directions

- `POST /career-directions/recommend`: rank up to five career directions from a
  structured `CandidateProfile`.

The service evaluates a controlled cross-domain direction catalog against
candidate skills, work evidence, projects, papers, patents, education,
certifications, and inferred-role signals. Recommendations require direct
candidate evidence; inferred roles cannot create unsupported directions.
Responses include score ranges rather than false precision, evidence-based
strengths and gaps, conservative seniority, positioning advice, and example job
titles. Sparse profiles may return fewer than five low-confidence directions.

## Suggestions

- `POST /suggestions/generate`: generate fact-grounded suggestions for a match.
- `PATCH /suggestions/{suggestion_id}`: accept, edit, reject, or regenerate.

## Conventions

- UUIDs identify persisted resources.
- Long-running operations return `202 Accepted` and a processing state.
- Request and response bodies use Pydantic v2 schemas.
- Errors use FastAPI's standard `detail` envelope initially.
- Authentication, pagination, idempotency keys, and rate-limit headers will be
  specified before public deployment.
