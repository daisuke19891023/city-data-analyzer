# city-data-analyzer アーキテクチャ設計（初版）

## システム全体像
- **モノレポ構成**: `apps/frontend` (Next.js) と `apps/python-backend` (FastAPI/Typer + DSPy) を npm workspace で管理。
- **データフロー（対話モード）**: ユーザー質問 → Next.js (Vercel AI SDK) → Node API `/api/agent/interactive` → Python `/dspy/interactive` → NL2QuerySpec → 集計関数 → インサイト生成 → Node 経由で UI にストリーミング。
- **データフロー（バッチ探索）**: 実験作成 → DSPy PlanExperiments でジョブ生成 → ワーカーが DB を参照し集計 → insight_candidates 保存 → フロントでレビュー。

## バックエンド設計 (apps/python-backend)
- **DB レイヤ**: SQLAlchemy/Alembic を想定。
  - `datasets`: データセットメタ (name, source, schema_meta など)。
  - `dataset_rows`: 汎用 JSONB (`row_json`) で人口統計などを保持。必要に応じてインデックスを追加。
  - `analysis_queries`: NL 質問と生成された query_spec、実行統計、program_version を保存。
  - フェーズ4以降で `experiments`, `experiment_jobs`, `insight_candidates`, `insight_feedback` を追加。
- **DSPy モジュール**:
  - `NL2QuerySpecSig/Module`: question + dataset_meta → query_spec(JSON)。LM は `configure_lm(provider, model)` で切替。
  - `InteractiveAnalysisProgram`: NL2QuerySpec → QueryRunner → SummarizeInsight の Module チェーン。
  - `PlanExperiments`: goal_description + datasets_meta → jobs (後続でワーカーが処理)。
- **API**:
  - `POST /analysis/query`: {dataset_id, query_spec} → {data, summary, schema}。バリデーションで400を返す。
  - `POST /dspy/interactive`: {question, dataset_id, provider, model} → {query_spec, stats, insight_title, insight_description}。
  - フェーズ4で `/experiments` 系 API を追加。
- **ETL/スクリプト**:
  - `scripts/load_population.py`（案）: 人口統計 CSV を datasets/dataset_rows にロード。idempotent を明記。
  - フィードバック→trainset 生成スクリプトをフェーズ5で追加。

## フロントエンド設計 (apps/frontend)
- **依存**: Vercel AI SDK (`ai`, `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/google`) を追加。環境変数 `process.env.PY_BACKEND_URL` を参照。
- **API レイヤ**: `app/api/agent/interactive/route.ts` がツール呼び出しで Python を叩く。HTTP クライアントは `lib/backendClient.ts` などで共通化。
- **UI**:
  - `/interactive`: useChat ベースのチャット + ダッシュボード。ダッシュボードはカード/グラフ/テーブルを描画する再利用可能コンポーネントに分離。
  - `/experiments`, `/experiments/[id]`: 実験作成フォーム、実験一覧、インサイトカード（採用/却下/コメント）。
- **エラーハンドリング**: バックエンドが落ちた場合は Node API 側で検知し、ユーザーに分かりやすいメッセージを返す。

## 環境/設定
- ルートに `.env.example` を置き、バックエンド URL・LLM API キー・DB URL を共有。フロント/バックエンド README から参照できるようにする。
- 既定ポート: Frontend 3000, Backend 8000。起動コマンドを README に明記。

## 品質と運用の指針
- **AC/DoD 満たす粒度**でタスク化し、マイグレーション・スクリプト・API I/O を docs に残す。
- **テスト**: 集計ロジックに最小ユニットテスト、API の 400/200 パス検証。ワーカーは最小の統合テストまたはログ確認を DoD に含める。
- **再現性**: ETL と DSPy コンパイル手順はコマンドつきで記載。trainset には元インサイト ID を含め、改善サイクルをトレース可能にする。
