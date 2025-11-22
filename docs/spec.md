# city-data-analyzer 仕様（初版）

## プロジェクト概要
- 市区町村オープンデータとドメインデータを掛け合わせ、FastAPI + DSPy で分析 API を提供し、Next.js + Vercel AI SDK の UI から対話的に活用するモノレポ。
- 現状: `apps/frontend` に Next.js スケルトン、`apps/python-backend` に clean-python-interfaces ベースの FastAPI/Typer が存在。
- ゴール: NL 質問から DB クエリ・集計・インサイト生成までを一貫提供し、対話モードとバッチ探索モードを備えた分析体験を実現。

## スコープと非スコープ
- スコープ: フロント/バックエンド開発、DSPy 導入、DB スキーマ・マイグレーション、ETL スクリプト、実験ワーカー、フィードバック蓄積と最適化。
- 非スコープ: 本番運用インフラ設計、厳密なセキュリティ/認証基盤、商用 SLA 対応。

## 環境前提
- モノレポ: Node (workspace) + Python。フロントは Next.js、バックエンドは FastAPI/Typer。
- 推奨バージョン: Node は frontend README に追記予定、Python 3.13 以上、パッケージ管理は uv。
- 主要エンドポイントの既定ポート: フロント 3000、バックエンド 8000（DoD に明記）。

## データ/LLM 前提
- 共通環境変数: `PY_BACKEND_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `DATABASE_URL` などを `.env.example` に集約。
- オープンデータ: 市区町村人口統計 CSV 等を datasets/dataset_rows にロードする前提。
- LLM: DSPy 経由で OpenAI/Anthropic/Gemini を切替可能にし、litellm で統一インターフェイスを確保。

## 機能要求（フェーズ別）
### フェーズ1: 起動確認 & 開発環境整備
- フロント/バックエンドの dev 起動手順を整備し、README と .env.example に集約。

### フェーズ2: Python バックエンドにデータ基盤 + DSPy 最小パイプライン
- DB スキーマ（datasets, dataset_rows, analysis_queries）とマイグレーション雛形。
- 人口統計データ ETL スクリプト（idempotent）。
- DSPy NL→QuerySpec モジュール + LM 設定切替。
- QuerySpec 集計 API (`POST /analysis/query`) と基本統計。
- DSPy インタラクティブ API (`POST /dspy/interactive`) で NL→集計→インサイト文章を一括返却。

### フェーズ3: Next.js フロント + Vercel AI SDK 対話モード
- Vercel AI SDK によるチャット UI。
- Node API `/api/agent/interactive` が Python `/dspy/interactive` をツール呼び出し。
- /interactive ページでチャット + ダッシュボード描画。

### フェーズ4: バッチ探索モード
- experiments/experiment_jobs/insight_candidates モデルと API。
- DSPy PlanExperiments + ワーカーでジョブ処理とインサイト蓄積。
- フロントのバッチ探索 UI（実験作成・結果レビュー）。

### フェーズ5: フィードバック蓄積 & DSPy 自動チューニング
- insight_feedback API & UI。
- DSPy Optimizer で NL→DSL をコンパイルし、program_version を管理。
- フィードバックから trainset を生成し再コンパイルを回す導線。

### フェーズ6: 仕上げ
- ハッピーパスの手動 E2E（データ投入→対話→バッチ探索→フィードバック）。
- 既知の制約/TODO の整理とドキュメント拡充。

## 成功指標（暫定）
- 起動手順に従い、他メンバーがフロント/バックエンドを立ち上げられる。
- NL 質問から query_spec/集計/インサイトが一貫して返るエンドツーエンド動作。
- バッチ探索で実験作成後、ワーカーがインサイト候補を生成し UI で確認できる。
- フィードバックを元に DSPy プログラムを再コンパイルできる手順が確立。
