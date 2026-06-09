# Architecture

## Overview

CareerGraph AI is a monorepo with a Next.js web client, a FastAPI application,
PostgreSQL persistence, and Redis-backed asynchronous work planned for document
and AI pipelines. The MVP is resume intelligence software, not an auto-apply or
browser automation product.

## Layers

- `frontend/`: user workflows and human review surfaces.
- `backend/app/api/`: versioned HTTP transport and request validation.
- `backend/app/services/`: deterministic application workflows and business rules.
- `backend/app/agents/`: future bounded AI orchestrators that call services and
  return schema-validated outputs.
- `backend/app/repositories/`: ownership-scoped persistence adapters.
- `backend/app/models/`: SQLAlchemy 2 database entities.
- `backend/app/schemas/`: Pydantic v2 API and agent contracts.

## MVP Flow

1. A user uploads a PDF or DOCX resume.
2. A document parser extracts text and ordered source blocks.
3. Profile extraction produces a candidate profile and traceable verified facts.
4. A pasted job description is parsed into explicit requirements.
5. Matching combines rules, keyword coverage, taxonomy normalization, semantic
   similarity, and evidence-based explanation.
6. Suggestions must cite verified facts and enter a human review queue.
7. Accepted or edited suggestions can create a new resume version with a change log.

## Design Constraints

- AI output is never treated as a trusted fact without source evidence.
- Hard constraints and deterministic checks remain outside LLM prompts.
- Agent outputs use typed schemas and are persisted with run metadata.
- Resource access will be scoped to the authenticated user.
- Raw files, extracted text, and model inputs require retention and privacy controls.
- Auto-apply, automatic submission, and browser automation are outside the MVP.

## Resume Analysis Boundaries

Candidate Profile parsing is **content intelligence**. It receives extracted
text and can identify stated facts, evidence-based strengths, content gaps, and
generic target roles supported by education, experience, projects, skills,
certifications, tools, and industry signals. Role inference is not hardcoded to
one candidate or profession.

A future **Resume Layout Analyzer** will provide layout, ATS, and template
intelligence. It will require the original PDF/DOCX plus document layout metadata
to assess fonts, spacing, margins, columns, visual hierarchy, page structure,
template quality, and ATS presentation risks. Those judgments do not belong in
the text-only Candidate Profile parser.

## Deterministic Matching

Match scoring is requirement-centric rather than model-judged. The matching
service converts CandidateProfile data into atomic evidence records and
JobProfile data into atomic requirements. Each requirement receives a status,
confidence, evidence strength, explanation, and source evidence before aggregate
scores are calculated.

A lightweight cross-domain concept taxonomy normalizes related wording across
software, data, finance, marketing, operations, healthcare, education, research,
sales, HR, legal/compliance, and other role families. Concept and transferable
matches still require explicit candidate evidence; the taxonomy cannot supply a
missing skill. Mandatory gaps produce transparent risk penalties.

The optional semantic layer batches requirement and evidence embeddings in
memory to identify paraphrases missed by lexical matching. It does not persist
vectors and falls back to deterministic decisions when unavailable. An optional
structured LLM evidence judge is limited to ambiguous pairs, may only select
candidate evidence already supplied to it, and cannot produce the final score.
All aggregate scores and risk penalties remain deterministic.

## Future Runtime

The initial `docker-compose.yml` provides PostgreSQL with pgvector and Redis.
Background workers, object storage, migrations, observability, and deployment
manifests will be added when ingestion and matching logic are implemented.
