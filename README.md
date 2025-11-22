# City Data Analyzer Monorepo

This repository is organized as a monorepo with a Next.js frontend and a Python API backend.

```
apps/
├── frontend/        # Next.js application skeleton
└── python-backend/  # Existing FastAPI/Typer backend (formerly repository root)
```

## Frontend (Next.js)
- Location: `apps/frontend`
- Quick start:
  ```bash
  npm install
  npm run --workspace frontend dev
  ```

## Backend (Python)
- Location: `apps/python-backend`
- The backend codebase was moved intact from the previous repository root.
- Refer to the [backend README](apps/python-backend/README.md) for detailed setup, tooling, and usage instructions.

## Tooling notes
- CI and pre-commit hooks now target the backend from its new location.
- Node and Python artifacts (e.g., `node_modules`, `.venv`) are ignored in nested app directories for cleaner monorepo workflows.
