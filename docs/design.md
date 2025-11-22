# city-data-analyzer アーキテクチャ設計（初版）

## システム全体像
- **モノレポ構成**: `apps/frontend` (Next.js) と `apps/python-backend` (FastAPI/Typer + DSPy) を npm workspace で管理。
- **データフロー（対話モード）**: ユーザー質問 → Next.js (Vercel AI SDK) → Node API `/api/agent/interactive` → Python `/dspy/interactive` → NL2QuerySpec → 集計関数 → インサイト生成 → Node 経由で UI にストリーミング。
- **データフロー（バッチ探索）**: 実験作成 → DSPy PlanExperiments でジョブ生成 → ワーカーが DB を参照し集計 → insight_candidates 保存 → フロントでレビュー。

## バックエンド設計 (apps/python-backend)
- **DB レイヤ**: SQLAlchemy/Alembic を想定。柔軟なオープンデータ取り込みに対応する汎用スキーマを採用。
  - `open_data_categories`: 川崎市オープンデータの12カテゴリを初期登録。`slug` を英小文字で管理。
  - `datasets`: データセット定義 (category_id, slug, name, description, source_url, dataset_year)。
  - `dataset_columns`: 各 CSV の列定義 (column_name, data_type, column_order, is_index, description)。
  - `dataset_records`: CSV 1行を `row_json` (JSONB) に保持し、抽出したキーを `index_cols` (JSONB) に格納。idempotent なロードを想定。
  - 任意で `dataset_files` を追加し、元 CSV ファイル名やハッシュを保存可能。
  - `analysis_queries`: NL 質問と生成された query_spec、実行統計、program_version、dataset_id/dataset_version を保存。
  - フェーズ4以降で `experiments`, `experiment_jobs`, `insight_candidates`, `insight_feedback` を追加し、結合キーには `dataset_columns.is_index` を活用。
- **DSPy モジュール**:
  - `NL2QuerySpecSig/Module`: question + dataset_meta (dataset_columns, index_cols 説明) → query_spec(JSON)。LM は `configure_lm(provider, model)` で切替し、日本語カラム名にそのまま対応。
  - `InteractiveAnalysisProgram`: NL2QuerySpec → QueryRunner → SummarizeInsight の Module チェーン。query_runner は JSONB 抽出で SQL を動的生成。
  - `PlanExperiments`: goal_description + datasets_meta → jobs (後続でワーカーが処理)。dataset_ids を持つ query_spec を前提にする。
- **API**:
  - `POST /analysis/query`: {dataset_id, query_spec} → {data, summary, schema}。JSONB 抽出 + バインドパラメータで SQL インジェクションを防ぎ、バリデーションで400を返す。
  - `POST /dspy/interactive`: {question, dataset_id, provider, model} → {query_spec, stats, insight_title, insight_description}。dataset_meta をプログラムに渡す。
  - フェーズ4で `/experiments` 系 API を追加。
- **ETL/スクリプト**:
  - `scripts/load_csv.py`: カテゴリ slug・dataset slug・CSV パス・データセット名・説明・年度を受け取り、dataset/dataset_columns/dataset_records を作成。ヘッダからカラムを生成し、year/ward_code など index_cols を抽出。再実行で重複を避ける冪等設計。
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
