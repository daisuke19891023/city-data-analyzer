# City Data Backend

このバックエンドはモノレポ内の `apps/python-backend/` ディレクトリに配置されています。

## Features

-   **複数インターフェース**: CLI / REST API / MCP を切り替え可能
-   **柔軟な設定**: `.env` で環境別設定を切り替え
-   **構造化ログ**: structlog による JSON/console ログ出力
-   **モダン Python**: Python 3.13+, Typer, FastAPI, SQLAlchemy で構築
-   **品質ツール**: Ruff / Pyright / pytest / nox による検証

## Project Structure (under `apps/python-backend/`)

```
apps/python-backend/
├── src/city_data_backend/        # Application code
│   ├── __init__.py
│   ├── api.py                    # FastAPI routes
│   ├── app.py                    # Application bootstrap
│   ├── base.py                   # Base component definitions
│   ├── constants.py
│   ├── database.py               # SQLAlchemy engine/session helpers
│   ├── db_models.py              # ORM models
│   ├── main.py                   # CLI entry point (--dotenv 対応)
│   ├── types.py
│   ├── worker.py                 # Experiment/optimization workers
│   ├── interfaces/               # CLI/REST/MCP インターフェース
│   ├── models/                   # Pydantic/データモデル
│   ├── services/                 # データ取得・最適化などのサービス層
│   └── utils/                    # 共通ユーティリティ
├── tests/                        # Test suite
├── migrations/                   # SQL migration files
├── docs/                         # Additional documentation
├── constraints/                  # Dependency constraints
├── pyproject.toml                # Project configuration
├── noxfile.py                    # Task automation
├── env.example                   # Example environment configuration
└── README.md                     # This file
```

## Quick Start (monorepo)

### Prerequisites

-   Python 3.13 以上
-   uv (Python package manager)

### Setup

```bash
# モノレポのルートで実行
cd apps/python-backend

# 依存関係をインストール
uv sync

# 環境変数ファイルを準備
cp env.example .env
# 必要に応じて .env を編集
```

### Running the REST API (FastAPI + Uvicorn)

```bash
cd apps/python-backend
INTERFACE_TYPE=restapi PYTHONPATH=src uv run python -m city_data_backend.main
# Health check
curl http://localhost:8000/health
```

### Workers (experiments / optimization)

```bash
cd apps/python-backend
# 例: SQLite マイグレーション適用
sqlite3 data/city_data.db < migrations/202501010000_add_experiments.sql

# ワーカー起動（Experiment/Optimization を同一プロセスでポーリング）
PYTHONPATH=src uv run python -m city_data_backend.worker
```

`POST /experiments` や `optimization_jobs` テーブルに投入された `pending` ジョブを順次処理します。`status`/`error_message` に結果が反映されるため、再実行は状態を `pending` に戻して行ってください。

### CLI interface (default)

```bash
cd apps/python-backend
PYTHONPATH=src uv run python -m city_data_backend.main --help
```

## Configuration

### Environment Variables

Configuration is managed through environment variables. See `.env.example` for all available options:

| Variable         | Description                                  | Default | Options                                         |
| ---------------- | -------------------------------------------- | ------- | ----------------------------------------------- |
| `INTERFACE_TYPE` | Interface to use                             | `cli`   | `cli`, `restapi`                                |
| `LOG_LEVEL`      | Logging level                                | `INFO`  | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT`     | Log output format                            | `json`  | `json`, `console`, `plain`                      |
| `LOG_FILE_PATH`  | Log file path                                | None    | Any valid file path                             |
| `OTEL_*`         | [Deprecated] OpenTelemetry exporter settings | -       | Removed                                         |

### Using Custom Environment Files

You can specify custom environment files using the `--dotenv` option:

```bash
# Development environment
uv run python -m city_data_backend.main --dotenv dev.env

# Production environment
uv run python -m city_data_backend.main --dotenv prod.env

# Testing environment
uv run python -m city_data_backend.main --dotenv test.env
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

### Development Commands

| Command              | Description         |
| -------------------- | ------------------- |
| `nox -s lint`        | Run code linting    |
| `nox -s format_code` | Format code         |
| `nox -s typing`      | Run type checking   |
| `nox -s test`        | Run all tests       |
| `nox -s security`    | Run security checks |
| `nox -s docs`        | Build documentation |
| `nox -s ci`          | Run all CI checks   |

### Testing

```bash
# Run all tests
nox -s test

# Run specific test file
uv run pytest tests/unit/city_data_backend/test_app.py

# Run with coverage
uv run pytest --cov=src --cov-report=html
```
