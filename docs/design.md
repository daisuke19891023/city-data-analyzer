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

## UX 向上設計（追加）
### テーマA: 観点提案 UX
- **スキーマ/API**: `analysis_viewpoints` を SQLAlchemy モデルで追加し、FastAPI に `GET /viewpoints`, `GET /viewpoints/{id}`, `POST /viewpoints` を実装。`config_json` に推奨データセット ID 等を持たせる。
- **サジェスト API**: `GET /datasets/{id}/suggested_questions` で dataset schema + 観点テンプレートを DSPy/LLM に渡し 3〜5 件を生成。
- **フロント UI**: `/interactive` に再利用可能な `<ViewpointGallery>` を追加し、カードクリックで nl_prompt をチャット欄に下書き or 即送信。タグ/検索フィルタを props で制御。ショートカットボタンはチャット入力下に並べ、定義を JSON/定数で一元管理。

### テーマB: 知見の蓄積 & 再利用
- **レシピ保存**: `analysis_recipes` モデルと `POST/GET /recipes` を追加。`query_spec_json` と `chart_config_json` を保存し、作成者/作成日時を保持。
- **レシピ適用 UI**: `/interactive` または `/recipes` に `<RecipeList>` + 「このレシピを使う」ボタンを設置。dataset_id 不一致時はモーダルで自治体コード/期間を聞き、Python `/analysis/query` へパラメータ上書きで送信。
- **インサイトノート**: `insight_notes` テーブルと `POST/GET /insight-notes`/`/search` を追加し、タグ・検索に対応。対話/実験詳細から「ノート保存」モーダルを開き、/notes で一覧・絞り込みを表示。
- **レポート出力**: 選択したノート/インサイトをまとめるエンドポイントを Python に実装し、Markdown（将来 PDF）を返却。フロントはプレビュー/コピー、余裕があれば PDF ダウンロード。
- **学びの履歴**: `insight_feedback` + `insight_notes` を集約し、/history でタイムライン/タグクラウドを表示。期間フィルタを備え、元ノートへのリンクを表示。

### テーマC: ダッシュボード操作強化
- **状態管理**: DashboardConfig 型を frontend で定義し、バックエンドに `dashboard_instances`（config_json を保存）と `GET/PUT /dashboards/{id}` を追加。再読み込み時に JSON から復元。
- **自然言語編集**: DSPy Module `EditDashboardConfig` を新設し、Node の `/api/agent/interactive` に editDashboard ツールを追加。フロントは「編集モード」入力をツール呼び出しとして扱い、エラー時はバリデーションメッセージを返す。
- **What-if**: Python に `POST /analysis/what-if` を追加し、query_spec + 変化指定からベース/シミュレーション結果を返す。フロントはモーダルで入力を受け、差分グラフを Dashboard コンポーネントで描画。

### テーマD: 信頼性/運用
- **データ更新情報**: datasets に `last_updated_at`, `source_description`, `warning_text` を追加し、ダッシュボード/ノートに更新日とディスクレーマーを表示。バックエンドはシリアライザで値を返却。
- **再実行候補**: `last_run_at` を experiments/analysis_recipes に保持し、`GET /rerun-candidates` で `datasets.last_updated_at` との比較結果を返す。/settings or /maintenance に一覧 + 手動再実行ボタン。
- **運用ダッシュボード**: SQL View か集計テーブルで期間別・観点別の利用状況をまとめ、`GET /admin/stats` を返却。フロント /admin/stats で期間フィルタ + シンプルな棒/折れ線グラフを表示し、簡易認証を検討。

### テーマE: 先進分析 UX
- **クラスタリング + ペルソナ**: Python に `POST /analysis/clusters` を追加し、標準化→k-means→LLM 要約でクラスタ特徴を生成。レスポンスは自治体ごとのクラスタ番号とペルソナ説明を含み、/clusters で地図/テーブル + ペルソナカード表示。
- **モデル比較**: Node に `/api/agent/compare` を実装し、同一 question/datasetId を複数プロバイダに投げて結果を配列で返却。フロント /compare でタブ/カード並列表示し、設定ファイルにモデル一覧を集約。
