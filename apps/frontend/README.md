# City Data Analyzer Frontend

This directory hosts the Next.js UI for the monorepo. It currently contains a minimal placeholder page so you can wire up the Python API backend located in `apps/python-backend`.

## Getting started

1. Install dependencies from the repository root (Node 20.x recommended):
   ```bash
   npm install
   ```
2. Run the development server:
   ```bash
   npm run --workspace frontend dev
   ```

Environment:
- Copy the repository root `.env.example` to `.env` so the frontend can read `PY_BACKEND_URL` (e.g., http://localhost:8000).

Update the placeholder content in `app/page.tsx` as you build out the frontend experience.
