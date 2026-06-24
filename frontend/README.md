# CareerGraph AI Frontend

Next.js 16, React 19, and TypeScript frontend for CareerGraph AI.

The UI presents CareerGraph as an AI career advisor workspace: users upload a
resume, run an async analysis, review an evidence profile, compare career
directions, read a full selected-direction Advisor Report, generate advisor
guidance, and revisit saved analyses.

## Current Workflow

1. Upload a PDF or DOCX resume.
2. Confirm the resume is ready for analysis.
3. Click Analyze.
4. Create an async backend analysis job.
5. Poll job status and show step-level progress:
   - Profile Parsing
   - Career Directions
   - Advisor/Suggestions
   - Job Matching, skipped in the default resume-only flow
6. Display results:
   - Evidence Profile
   - Recommended career directions
   - Selected-direction Advisor Report
   - Advisor guidance and next actions
7. Save/reopen local analysis history.
8. Review suggestion items with accept/edit/reject state.

Optional pasted job description matching remains available as a secondary
workflow, not the main product experience.

## UX Structure

- Landing screen with product positioning and primary resume upload CTA.
- Compact post-upload ready state.
- Analysis job progress with staged loading.
- Career direction ranking list.
- Full-width Advisor Report below the ranking/profile workbench.
- Evidence profile and advisor CTA as supporting context.
- Advisor guidance sections for evidence, gaps, resume-ready improvements, and
  next actions.
- Analysis history panel for reopening saved analyses.

## Language Support

The frontend uses a lightweight local English/Simplified Chinese dictionary.
The selected language is sent to backend AI endpoints as `preferred_language`.

Chinese mode localizes UI labels, loading states, helper text, badges, and
advisor chrome. Resume evidence excerpts remain in the original resume
language. Resume-ready rewrites preserve the source resume language when
appropriate.

Generated advisor content is language-specific. If the user switches language
after advisor content was generated in another language, stale advisor content
is hidden and the UI prompts regeneration in the selected language.

## Configuration

```bash
cd frontend
cp .env.example .env.local
```

Default:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WORKSPACE_USER_EMAIL=
```

The API client appends `/api/v1` automatically. A value already ending in
`/api/v1` is also accepted.

`NEXT_PUBLIC_WORKSPACE_USER_EMAIL` is an MVP development header used by the
workspace API. It is not authentication.

## Run Locally

Start the backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

For WSL or LAN testing, set `NEXT_PUBLIC_API_BASE_URL` to the backend host that
the browser can reach.

## Validation

```bash
npm run lint
npm run typecheck
npm run build
```

## MVP Boundaries

The frontend does not include real authentication, billing, payments, resume
export, auto-apply, scraping, browser extensions, or production account
management. Current workspace identity is a development scaffold backed by the
API, not a finished SaaS account system.
