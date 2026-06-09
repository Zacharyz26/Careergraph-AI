# Data Model

## Core Entities

- `User`: account identity and ownership boundary.
- `Resume`: uploaded file metadata, raw text, parser version, and processing state.
- `ResumeBlock`: ordered source text with section and layout metadata.
- `CandidateProfile`: structured education, skills, experience, projects, and goals.
- `VerifiedFact`: atomic claim linked back to a resume block and user verification.
- `ResumeVersion`: target-specific content snapshot and change log.
- `Job`: raw job description, parsed requirements, source, and processing state.
- `Match`: resume-job score, component scores, evidence, gaps, and recommendation.
- `Suggestion`: original and proposed text, source fact IDs, risk, and review status.
- `AgentRun`: trace, model, latency, token use, cost, status, and error summaries.

## Important Relationships

- A user owns resumes, profiles, facts, jobs, matches, and versions.
- A resume contains many source blocks and verified facts.
- A candidate profile is generated from one resume in the initial MVP.
- A match joins one resume and one job.
- A suggestion belongs to a resume-job context and cites one or more facts.
- A resume version records approved changes without replacing the source resume.

## Integrity Rules

- Suggestions cannot be promoted without at least one valid `source_fact_id`.
- User corrections take precedence over extracted claims.
- Match scores represent document fit, not interview or hiring probability.
- Historical versions and review decisions are append-oriented for auditability.
- Authentication ownership checks must be applied in repository queries.

The scaffold uses PostgreSQL-specific UUID, JSONB, and array types. pgvector
columns will be introduced with the embedding implementation and migrations.
