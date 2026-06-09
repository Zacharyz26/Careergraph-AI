# CareerGraph AI Frontend

Next.js and TypeScript shell for resume upload, candidate profile review, job
matching, suggestion approval, and career roadmap workflows.

## Local development

```bash
./scripts/setup_frontend.sh
cd frontend
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in `.env.local` when the API is not running at the
default `http://localhost:8000/api/v1`.

The current UI is intentionally placeholder-only. API integration, state
management, authentication, accessibility review, and visual design are future
implementation phases.
