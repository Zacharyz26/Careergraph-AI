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
certifications, leadership, languages, and inferred-role signals.

When an LLM is configured, the service sends a normalized evidence summary with
stable IDs and requests 8 to 12 structured direction proposals. The service
then removes unsupported citations, rejects directions without evidence,
downgrades skill-only primary fits, suppresses generic internship paths when
specialized evidence is strong, and computes the final ranking
deterministically. The LLM never assigns final rank or score.

If no API key is available or generation fails, the current deterministic
cross-domain catalog is used as fallback. Responses include score ranges rather
than false precision, evidence-based strengths and gaps, conservative
seniority, positioning advice, and example job titles. Sparse profiles may
return fewer than five low-confidence directions.

## Suggestions

- `POST /suggestions/generate`: generate evidence-grounded resume improvements
  in `general`, `career_direction`, or `job_specific` mode.
- `PATCH /suggestions/{suggestion_id}`: accept, edit, reject, or regenerate.

`candidate_profile` is required. Career-direction mode accepts a target label or
a complete career direction result. Job-specific mode requires both the parsed
job profile and match result. Complete context automatically selects the
corresponding mode when the mode field is omitted.

The service creates stable evidence IDs from candidate skills, work, projects,
papers, patents, education, certifications, leadership, and languages.
Structured LLM output may improve wording, organization, and positioning, but
the service validates every cited evidence item before returning a suggestion.
Resume-ready suggestions without valid evidence are removed. New metrics, links,
certifications, unsupported taxonomy concepts, and missing job requirements are
also removed from suggested resume text.

Unsupported gaps are returned separately in `missing_but_not_addable`. Every
suggestion includes its source evidence, risk level, related requirement or
direction, and mandatory user-review flag. Without an API key, the deterministic
fallback only emphasizes existing evidence verbatim.

## Conventions

- UUIDs identify persisted resources.
- Long-running operations return `202 Accepted` and a processing state.
- Request and response bodies use Pydantic v2 schemas.
- Errors use FastAPI's standard `detail` envelope initially.
- Authentication, pagination, idempotency keys, and rate-limit headers will be
  specified before public deployment.
