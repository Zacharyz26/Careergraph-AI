# CareerGraph AI Frontend

Next.js 16, React 19, and TypeScript workspace UI for CareerGraph AI.

The frontend presents CareerGraph AI as an AI career advisor workspace: users
upload a resume, start an async analysis job, watch step-level progress, review
an evidence profile, compare recommended career directions, generate advisor
guidance, and optionally check fit against a pasted job description.

## Current Workflow

1. Upload a PDF or DOCX resume.
2. Confirm the resume is ready for analysis.
3. Click Analyze.
4. Create an async backend analysis job.
5. Poll job status and show step progress:
   - Profile Parsing
   - Career Directions
   - Advisor/Suggestions
   - Job Matching, skipped in the default resume-only workflow.
6. Display partial results as they become available.
7. Retry failed analysis jobs from the UI.
8. Optionally paste a job description and run job-fit scoring.

The analyzed-state workspace emphasizes:

- recommended career directions
- selected direction analysis
- evidence profile
- advisor next action
- optional job match as a secondary section

## Language Support

The UI includes a lightweight local English/Simplified Chinese dictionary. The
selected language is sent to backend AI endpoints as `preferred_language`.

Chinese mode localizes UI labels, loading states, helper text, badges, and
advisor chrome. Resume evidence excerpts remain in the original resume language.
Resume-ready rewrites preserve the source resume language when appropriate.

Generated advisor content is language-specific. If the user switches language
after advisor content is generated, stale advisor content is hidden and the UI
shows the advisor CTA so it can be regenerated in the selected language.

## Configuration

```bash
cd frontend
cp .env.example .env.local
```

Default:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The API client appends `/api/v1` automatically. A value already ending in
`/api/v1` is also accepted.

For local development, the API base URL follows the current browser hostname
when `NEXT_PUBLIC_API_BASE_URL` is not set, so both `localhost:3000` and
`127.0.0.1:3000` can work with the backend CORS defaults.

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

## Validation

```bash
npm run lint
npm run typecheck
npm run build
```

## MVP Boundaries

The frontend does not currently include authentication, browser persistence,
payments, resume export, auto-apply, scraping, or saved job boards. It is a
stateless MVP client backed by the FastAPI API.
