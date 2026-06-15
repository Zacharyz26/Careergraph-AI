# CareerGraph AI Frontend

Polished Next.js and TypeScript MVP for the CareerGraph AI resume intelligence
workflow.

## Included workflow

The single-page workspace supports:

1. PDF or DOCX resume upload and text extraction.
2. Structured CandidateProfile parsing.
3. Evidence-based career direction recommendations.
4. Career direction selection.
5. Evidence-grounded resume improvement suggestions.
6. Optional job description parsing and resume-to-job match scoring.

The UI keeps raw extracted text and structured JSON in collapsible sections.
Loading, empty, and API error states are handled independently. No
authentication or browser persistence is included in the MVP.

## Configuration

Copy the example environment file:

```bash
cd frontend
cp .env.example .env.local
```

The browser uses:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The API client appends `/api/v1`. A value already ending in `/api/v1` is also
accepted.

## Run locally

Start the backend in one terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Candidate profile parsing, job parsing, and LLM-assisted suggestion generation
require the backend `OPENAI_API_KEY`. Career directions and suggestions retain
their backend deterministic fallbacks where configured.

## Validation

```bash
npm run lint
npm run typecheck
npm run build
```
