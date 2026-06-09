# CareerGraph AI

CareerGraph AI is an evidence-grounded, human-in-the-loop resume intelligence
platform for students and early-career candidates. The MVP turns resumes and job
descriptions into structured profiles, explainable matches, and fact-linked
improvement suggestions.

It is not an auto-apply bot. Automatic application submission, platform
automation, and fabricated candidate claims are explicitly outside the MVP.

## Repository

- `backend/`: FastAPI, Pydantic v2, SQLAlchemy 2, services, agents, and tests.
- `frontend/`: Next.js and TypeScript workflow shell.
- `docs/`: architecture, API, data model, roadmap, and project plan.
- `scripts/`: local setup helpers.

## Quick Start

```bash
docker compose up -d
./scripts/setup_backend.sh
./scripts/setup_frontend.sh
```

Run the API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Run the web app in another terminal:

```bash
cd frontend
npm run dev
```

The API health endpoint is `http://localhost:8000/health`; the web app defaults
to `http://localhost:3000`.

## Status

This is an initial production-style scaffold. Business logic, authentication,
database migrations, background workers, real document parsing, embeddings, and
LLM calls remain intentionally unimplemented.
