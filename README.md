# City Data Analyzer Monorepo

This repository is organized as a monorepo with a Next.js frontend and a Python API backend.

```
apps/
├── frontend/        # Next.js application skeleton
└── python-backend/  # Existing FastAPI/Typer backend (formerly repository root)
```

## Frontend (Vite/React)
- Location: `apps/frontend`
- Recommended Node version: **20.x** (tested with v20.19.5)
- Quick start:
  ```bash
  npm install
  npm run --workspace frontend dev -- --host --port 3000
  ```
  The dev server responds at http://localhost:3000.

## Backend (Python)
- Location: `apps/python-backend`
- Quick start (REST API):
  ```bash
  cd apps/python-backend
  uv sync
  INTERFACE_TYPE=restapi PYTHONPATH=src uv run python -m clean_interfaces.main
  ```
  The FastAPI server listens on http://localhost:8000 (health check: `/health`).
- The backend codebase was moved intact from the previous repository root. See the
  [backend README](apps/python-backend/README.md) for detailed setup, tooling, and usage instructions.

## Environment
- Copy `.env.example` to `.env` at the repo root for shared local defaults (backend URL, LLM keys, DB URL, dev ports).

## Tooling notes
- CI and pre-commit hooks now target the backend from its new location.
- Node and Python artifacts (e.g., `node_modules`, `.venv`) are ignored in nested app directories for cleaner monorepo workflows.

## Known limitations / TODO
- 対話モードのフロント `datasetOptions` はダミー ID なので、実データを使う場合は `apps/frontend/src/data/dashboardPresets.ts` で `dataset_id`（例: `"1"` や `"2"`）に置き換えてから起動してください。
- `uv run nox -s pip-audit` は証明書検証エラーで失敗します。`pip-audit --skip-editable --path` での回避またはネットワーク設定の見直しが必要です。
- Sphinx ビルドには既存の重複 docstring 警告が残っており、`nox -s docs` が失敗する場合があります。ドキュメント修正時は警告解消を併せて検討してください。
