# Data Model

This document describes the current MVP workspace data model and the intended
durable SaaS direction.

CareerGraph AI now has local workspace history and PostgreSQL schema
scaffolding. The implemented product is still not a complete production
multi-user SaaS.

## Implemented MVP Workspace Data

The workspace layer stores:

- uploaded resume metadata
- extracted resume text
- completed analysis job results
- parsed `CandidateProfile`
- career direction recommendations
- selected career direction
- generated advisor suggestions
- suggestion review status and edited text

Storage can use:

- PostgreSQL through SQLAlchemy models and Alembic migrations.
- JSON fallback at `.careergraph_workspace.json` for local development.

## Current Ownership Model

Workspace records include a user email ownership key.

Current user resolution:

- `X-CareerGraph-User-Email` request header when provided.
- `WORKSPACE_DEFAULT_USER_EMAIL` in non-production development.
- Production mode requires a workspace user header.

This is an MVP ownership scaffold, not real authentication. Future auth should
replace this with identity-provider-backed users and repository-level
authorization.

## Core Entities

- `User`: account/ownership boundary and future billing/subscription anchor.
- `Resume`: uploaded resume metadata and extracted source text.
- `Analysis`: completed analysis job result for one resume.
- `CandidateProfile`: structured education, skills, experience, projects, and
  goals generated from resume evidence.
- `Suggestion`: advisor item with review state, source evidence references,
  risk/quality metadata, and optional edited text.

## Future Entities

These are planned but not fully implemented product surfaces:

- `VerifiedFact`: atomic claim linked to source resume evidence and user
  verification.
- `ResumeVersion`: target-specific content snapshot and change log.
- `Job`: pasted/imported job description and parsed requirements.
- `Match`: resume-job score, evidence coverage, gaps, and recommendation.
- `AgentRun`: model, latency, token use, cost, status, and error summaries.
- `Subscription` or `Plan`: billing/subscription metadata.

## Integrity Rules

- Suggestions should not become resume-ready claims without valid source
  evidence.
- User edits/reviews should be preserved separately from generated text.
- Missing capabilities belong in gaps and next actions, not resume-ready text.
- Match scores represent document fit, not interview or hiring probability.
- Historical versions and review decisions should be append-oriented once
  durable versioning exists.
- Repository queries must enforce real user ownership once authentication is
  implemented.

## Persistence Status

Implemented:

- workspace history
- saved analyses
- saved extracted resume text
- saved suggestion review state
- PostgreSQL schema scaffolding
- JSON fallback for local MVP use

Not production complete:

- real auth-backed ownership
- production retention/deletion controls
- encrypted object storage for uploaded files
- durable async worker state
- billing/subscription enforcement
- versioned resume export
