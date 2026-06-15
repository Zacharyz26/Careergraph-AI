# CareerGraph AI Backend

FastAPI service for resume ingestion, candidate profiles, verified facts, job
description parsing, hybrid matching, and human-reviewed improvement
suggestions.

## Setup

```bash
./scripts/setup_backend.sh
cd backend
source .venv/bin/activate
```

Add secrets or local overrides to `backend/.env`, then run:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with development docs at
`http://localhost:8000/docs`.

## Resume text extraction

`POST /api/v1/resumes/upload` accepts one multipart `file` field containing a
PDF or DOCX resume. It extracts text without storing the file or calling an LLM.

```bash
curl -X POST \
  http://localhost:8000/api/v1/resumes/upload \
  -H "accept: application/json" \
  -F "file=@/absolute/path/to/resume.pdf"
```

The response contains the sanitized filename, file type, extracted text,
character count, and PDF page count when applicable.

## Candidate profile parsing

Set the API key and optional model in `backend/.env`:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

`POST /api/v1/resumes/parse-profile` converts previously extracted resume text
into a schema-validated candidate profile. It uses structured output and
instructs the model to return null or empty collections rather than inventing
missing facts. This endpoint performs **content intelligence only**: it analyzes
the words present in the extracted text, including experience, education,
skills, projects, patents, strengths, and content gaps.

It does not evaluate fonts, spacing, templates, columns, visual hierarchy, page
layout, or ATS layout. A future **Resume Layout Analyzer** endpoint will inspect
the original PDF/DOCX file and parser layout metadata for layout, template, and
ATS presentation intelligence.

Target role inference is generic and evidence-based rather than hardcoded for a
particular candidate or industry. It returns 3 to 6 supported roles with role
family, conservative seniority, confidence, rationale, and source evidence.
Vague resumes receive broader, lower-confidence role suggestions.

`role_family` and `seniority_level` use controlled taxonomies. Seniority values
are `Internship`, `Entry-level`, `Junior`, `Mid-level`, `Senior`, `Leadership`,
or `Unknown`. Current students, recent graduates, and internship-heavy resumes
prefer `Internship` or `Entry-level` when the resume supports that classification.

```bash
curl -X POST \
  http://localhost:8000/api/v1/resumes/parse-profile \
  -H "Content-Type: application/json" \
  -d '{
    "extracted_text": "Jordan Lee\nBackend Engineer\nPython, FastAPI, PostgreSQL"
  }'
```

If `OPENAI_API_KEY` is not configured, the endpoint returns HTTP 503 with a
configuration error. Tests inject a structured mock response and never require
an API key or network access.

## Job description parsing

`POST /api/v1/jobs/parse` converts a pasted job description into a structured
`JobProfile`. It separates required and preferred skills, responsibilities and
qualifications, and uses the same controlled role-family and seniority
taxonomies as CandidateProfile parsing.

Company name, salary, visa sponsorship, location, and remote policy are returned
only when explicitly supported by the job description. Missing facts remain
null, empty, or `Unknown`; evidence excerpts accompany extracted requirements.

```bash
curl -X POST \
  http://localhost:8000/api/v1/jobs/parse \
  -H "Content-Type: application/json" \
  -d '{
    "raw_job_description": "Example Company is hiring a full-time Data Analyst in Toronto. Required: SQL and dashboard development. Python is preferred. This is a hybrid role."
  }'
```

## Resume-to-job match scoring

`POST /api/v1/matches/score` compares a structured `CandidateProfile` and
`JobProfile` using a hybrid, requirement-centric scoring engine. The engine,
not an LLM, always computes the final score, and no result is persisted.

The matcher:

1. Builds an evidence index from candidate skills, experience bullets, projects,
   papers, patents, education, certifications, and languages.
2. Builds individual job requirements from required and preferred skills,
   responsibilities, qualifications, education, and experience requirements.
3. Applies deterministic exact, token, and taxonomy matching.
4. When configured, batches requirement and evidence embeddings to recover
   semantic paraphrases missed by keyword matching.
5. Optionally sends only ambiguous requirement/evidence pairs to a structured
   LLM evidence judge. The judge cannot add evidence or assign the final score.
6. Evaluates each requirement as `full_match`, `partial_match`,
   `transferable_match`, or `missing`.
7. Aggregates required coverage, preferred coverage, responsibility alignment,
   education fit, seniority fit, and evidence strength.
8. Applies explicit penalties for unsupported mandatory requirements.

Semantic matching uses `OPENAI_EMBEDDING_MODEL` when `OPENAI_API_KEY` is
configured. If embeddings fail or no key is available, scoring automatically
falls back to the deterministic engine. `MATCHING_ENABLE_LLM_JUDGE` defaults to
`false`; enabling it only affects ambiguous requirement-level decisions.

Its lightweight concept taxonomy covers software, AI/ML, data, finance,
accounting, marketing, product, design, operations, healthcare, research,
education, sales, HR, and legal/compliance concepts. Taxonomy relationships can
connect supported wording, but never create a match without candidate evidence.
Work, project, paper, and patent evidence is weighted more strongly than a
standalone skill label or education evidence.

```bash
curl -X POST \
  http://localhost:8000/api/v1/matches/score \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_profile": {
      "skills": [{"category": "Programming", "skills": ["Python", "SQL"], "evidence": ["Python, SQL"]}],
      "experience": [{"organization": "Example Labs", "title": "Backend Intern", "bullets": ["Built REST APIs with Python"], "evidence": ["Built REST APIs with Python"]}],
      "projects": [],
      "papers": [],
      "patents": [],
      "education": [{"institution": "Example University", "degree": "BS", "field_of_study": "Computer Science", "evidence": ["BS in Computer Science"]}],
      "inferred_target_roles": [
        {"role": "Backend Engineer", "role_family": "Software Engineering", "seniority_level": "Internship", "confidence": 0.9, "rationale": "API internship evidence.", "is_inferred": true, "evidence": ["Backend Intern"]},
        {"role": "Software Engineer", "role_family": "Software Engineering", "seniority_level": "Entry-level", "confidence": 0.8, "rationale": "Python software evidence.", "is_inferred": true, "evidence": ["Built REST APIs with Python"]},
        {"role": "Data Analyst", "role_family": "Data / Analytics", "seniority_level": "Entry-level", "confidence": 0.6, "rationale": "SQL evidence.", "is_inferred": true, "evidence": ["Python, SQL"]}
      ]
    },
    "job_profile": {
      "job_title": "Backend Engineering Intern",
      "role_family": "Software Engineering",
      "seniority_level": "Internship",
      "employment_type": "Internship",
      "required_skills": [{"value": "Python", "evidence": ["Required: Python"]}],
      "preferred_skills": [{"value": "SQL", "evidence": ["SQL preferred"]}],
      "responsibilities": [{"value": "Build REST APIs", "evidence": ["Build REST APIs"]}],
      "qualifications": [],
      "education_requirements": [{"value": "Computer Science", "evidence": ["Computer Science degree"]}]
    }
  }'
```

The response includes one decision per requirement, attached candidate evidence,
coverage and evidence scores, risk penalties, matched and missing skills,
transferable matches, an explanation, and a recommendation label.

Example requirement decision:

```json
{
  "requirement_type": "required_skill",
  "importance": 1.0,
  "requirement": "Marketing analytics",
  "match_status": "transferable_match",
  "match_strength": 0.28,
  "confidence": 0.58,
  "similarity_score": 0.71,
  "evaluation_method": "semantic",
  "candidate_evidence": [
    {
      "source_type": "skills",
      "text": "Performed data analysis for sales reporting",
      "evidence_strength": 0.7,
      "normalized_concepts": ["data_analysis"]
    }
  ],
  "reason": "Candidate evidence is related and potentially transferable, but does not directly satisfy the requirement."
}
```

## Career direction recommendations

`POST /api/v1/career-directions/recommend` ranks up to five evidence-supported
career directions from a `CandidateProfile`.

The recommender uses an evidence-controlled hybrid pipeline:

1. Build an evidence summary with stable IDs for education, skills, work,
   projects, papers, patents, certifications, leadership, and languages.
2. When configured, ask the LLM for 8 to 12 structured candidate directions.
   Every proposal must cite evidence IDs from that summary.
3. Remove unknown IDs and directions with no valid evidence.
4. Downgrade primary directions supported only by isolated skill tokens.
5. Require strong work, project, paper, or patent evidence for a primary fit.
6. Suppress generic internship suggestions when specialized directions have
   meaningful support.
7. Deterministically rank the validated proposals using evidence strength,
   evidence diversity, directness, role-family consistency, seniority fit, and
   gap severity.

The LLM proposes candidates but does not choose the final Top 5 or assign final
scores. Inferred target roles are supporting signals only. If `OPENAI_API_KEY`
is absent or proposal generation fails, the service uses the deterministic
cross-domain catalog fallback.

```dotenv
CAREER_DIRECTIONS_ENABLE_LLM=true
```

Standalone skills are intentionally weak evidence. Work experience and
projects/papers/patents carry more weight. Sparse profiles return fewer
recommendations with wider score ranges and lower confidence.

```bash
curl -X POST \
  http://localhost:8000/api/v1/career-directions/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_profile": {
      "skills": [{"category": "Finance", "skills": ["Financial modeling", "Excel", "Budgeting"], "evidence": ["Financial modeling, Excel, budgeting"]}],
      "experience": [{"organization": "Example Finance", "title": "Finance Intern", "bullets": ["Built financial forecasts"], "evidence": ["Built financial forecasts"]}],
      "inferred_target_roles": [
        {"role": "Financial Analyst", "role_family": "Finance / Accounting", "seniority_level": "Entry-level", "confidence": 0.9, "rationale": "Finance evidence.", "is_inferred": true, "evidence": ["Built financial forecasts"]},
        {"role": "Accounting Analyst", "role_family": "Finance / Accounting", "seniority_level": "Entry-level", "confidence": 0.8, "rationale": "Finance evidence.", "is_inferred": true, "evidence": ["Financial modeling"]},
        {"role": "Business Analyst", "role_family": "Business / Operations", "seniority_level": "Entry-level", "confidence": 0.6, "rationale": "Analytical evidence.", "is_inferred": true, "evidence": ["Excel"]}
      ]
    }
  }'
```

Each result includes rank, fit type, score range, confidence, matched evidence,
direction-specific strengths and gaps, positioning advice, and example titles.
Each matched evidence object includes the original `evidence_id`, allowing every
recommendation to be traced back to the submitted CandidateProfile.

## Resume improvement suggestions

`POST /api/v1/suggestions/generate` produces evidence-grounded resume content
suggestions in three modes:

- `general`: improve clarity and emphasis using only the candidate profile.
- `career_direction`: position supported evidence for a target direction or a
  `CareerDirectionRecommendation`.
- `job_specific`: use a `JobProfile` and `MatchResult` to emphasize matched
  evidence while keeping missing requirements out of resume-ready text.

The service builds the same stable candidate evidence summary used by career
direction recommendations. When an API key is configured, structured LLM output
may propose wording and organization changes. The service then validates every
source ID, removes unsupported metrics, links, certifications, concepts, and
job requirements, and raises the risk level for weak evidence. The LLM cannot
add candidate facts. Missing skills and other unsupported gaps are returned in
`missing_but_not_addable`.

If `OPENAI_API_KEY` is absent or generation fails, the endpoint returns a
deterministic fallback that only emphasizes existing evidence verbatim. Every
suggestion requires user review.

General request:

```bash
curl -X POST \
  http://localhost:8000/api/v1/suggestions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_mode": "general",
    "candidate_profile": {
      "skills": [{"category": "Backend", "skills": ["Python", "FastAPI"], "evidence": ["Python and FastAPI"]}],
      "experience": [{"organization": "Example Co", "title": "Software Intern", "bullets": ["Built REST APIs with Python"], "evidence": ["Built REST APIs with Python"]}],
      "inferred_target_roles": []
    }
  }'
```

For job-specific generation, set `suggestion_mode` to `job_specific` and include
the complete `job_profile` and `match_result` returned by the existing parsing
and scoring endpoints. Supplying complete job or career-direction context also
selects the corresponding mode when `suggestion_mode` is omitted.

Example response:

```json
{
  "overall_summary": "Lead with the candidate's supported backend API work.",
  "suggestions": [
    {
      "suggestion_type": "experience_emphasis",
      "target_section": "work",
      "original_text": "Built REST APIs with Python",
      "suggested_text": "Built REST APIs with Python",
      "reason": "Emphasize direct backend evidence.",
      "source_evidence_ids": ["E003"],
      "source_evidence_text": ["Built REST APIs with Python"],
      "related_requirement_or_direction": "Backend Developer",
      "risk_level": "low",
      "requires_user_review": true,
      "should_add_to_resume": true
    }
  ],
  "missing_but_not_addable": ["Kubernetes"],
  "suggested_resume_focus": ["Backend Developer"],
  "warnings": []
}
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Current status

Resume upload, PDF/DOCX text extraction, CandidateProfile parsing, JobProfile
parsing, hybrid match scoring, and career direction recommendations are
implemented. Evidence-grounded resume improvement suggestions are available
with structured LLM generation and a deterministic fallback. Database
persistence, verified fact persistence, and embedding persistence/vector search
remain future work.
