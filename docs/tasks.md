# city-data-analyzer タスク & ロードマップ

## フェーズ1: 起動確認 & 開発環境整備
ステータス: 2025-11-22 時点でローカル確認済み（Node v20.19.5、`npm run --workspace frontend dev -- --host --port 3000`、`INTERFACE_TYPE=restapi PYTHONPATH=src uv run python -m clean_interfaces.main` で /health 応答を確認）。
### Task 1-1: フロントエンドの起動確認
- やること: ルートで `npm install`、`npm run --workspace frontend dev` で Next.js 起動、http://localhost:3000 を確認。
- AC: dev サーバが起動しページが表示できる。重大な TypeScript/ビルドエラーで落ちない。
- DoD: README（ルート or apps/frontend）に「フロント起動コマンド」「必要 Node バージョン」を追記。

### Task 1-2: Python バックエンドの起動確認
- やること: `cd apps/python-backend` で uv/pip インストール、`uv run python -m clean_interfaces.main --interface restapi` などで起動。
- AC: `curl http://localhost:8000/health` でヘルスチェック通過、既存サンプルエンドポイントが応答。
- DoD: `apps/python-backend/README.md` に dev 起動コマンドと想定ポート（例: 8000）を明記。

### Task 1-3: 共通 .env と開発フロー整理
- やること: ルートに `.env.example` を作成/更新し `PY_BACKEND_URL`, 各種 LLM API キー, `DATABASE_URL` 等を定義。frontend で `process.env.PY_BACKEND_URL` を参照可能にする。
- AC: フロント/バックエンドの起動手順が README から辿れる。.env.example をコピーすれば最低限の環境が整う。
- DoD: README 手順だけで別メンバーが両サーバを立ち上げられる状態。

## フェーズ2: Python バックエンドにデータ基盤 + DSPy 最小パイプライン
### Task 2-1: スキーマ定義（柔軟なオープンデータ対応）
- やること: `open_data_categories`, `datasets`, `dataset_columns`, `dataset_records`, `analysis_queries`（+ 任意で `dataset_files`）のテーブルを Alembic などで追加。川崎市オープンデータ12カテゴリを初期登録し、JSONB で柔軟な列を保持する。
- AC: マイグレーション実行で上記テーブル作成。open_data_categories に12件が挿入済み。任意の datasets/dataset_columns への INSERT が通る。
- DoD: `apps/python-backend/docs/` に ER 図とテーブル説明（カラム用途、index_cols の意図）を記載。
- [DONE] `SQLAlchemy` モデルを追加し `open_data_categories/datasets/dataset_columns/dataset_records/analysis_queries/dataset_files` を作成。`init_database` で 12 カテゴリをシードし、`docs/data_schema.md` に概要と ER テキスト図を追記。

### Task 2-2: CSV取り込みスクリプト（複数形対応）
- やること: `scripts/load_csv.py` を作成し、カテゴリ slug・dataset slug・CSV パス・データセット名・説明・年度を受け取る。存在しない場合は datasets/dataset_columns を自動登録し、dataset_records に row_json/index_cols を idempotent に投入。year/ward_code などの index 抽出ルールまたはマッピング設定を実装。
- AC: サンプル CSV で datasets/dataset_columns/dataset_records にデータが投入され、行数が一致。index_cols に year や ward_code が格納される。
- DoD: README または docs に使い方・引数説明・サンプル実行例・失敗時のロールバック説明を記載。
- [DONE] `scripts/load_csv.py` を追加し、`--index`/`--year`/`--database-url` 付きで冪等に取り込めるようにした。`docs/csv_import.md` に引数、インデックス抽出ルール、ロールバック方針を記載。

### Task 2-3: DSPy NL→QuerySpec モジュールの拡張
- やること: NL2QuerySpec を dataset_meta（dataset_columns, index_cols 説明を含む JSON）を入力に取るよう拡張。日本語カラム名をそのまま使用し、filters/group_by/metrics/order_by/limit を dataset_columns に基づいて生成。
- AC: 任意の dataset_id に対し日本語質問から有効な query_spec JSON を生成し、存在しないカラムが含まれない。
- DoD: 3〜5件の dataset_id と質問例に対する query_spec 出力サンプルを docs に記載。Task 2-4 でエラーにならないことを確認。
- [DONE] `RuleBasedQueryGenerator` で年度/区などのキーワードと数値カラムを元に `filters/group_by/metrics/order_by/limit` を生成し、存在しないカラムを排除するバリデーションを実装。`docs/dspy_interactive.md` にサンプルクエリを記載。

### Task 2-4: QuerySpec 実行 & 基本統計計算の汎用化
- やること: query_spec と dataset_id を受けて JSONB 抽出 SQL を動的生成し、filters/group_by/metrics/order_by/limit を反映。結果を DataFrame 変換し平均/最大/最小/件数などを返却。バインドパラメータで安全性を確保。
- AC: Task 2-3 の query_spec を入力して data/summary/schema が取得できる。不正カラム/フィルタは 400 を返す。
- DoD: 異なる2種類以上のデータセットで動作確認。SQL インジェクション対策を説明。
- [DONE] `QueryRunner` で DataFrame 集計（フィルタ・group_by・メトリクス・order_by・limit）を実装し、無効カラム時に 400 エラー相当の例外を送出。複数データセットでのフィルタ・グループ集計をユニットテストで確認。

### Task 2-5: DSPy インタラクティブプログラム & /dspy/interactive エンドポイント
- やること: InteractiveAnalysisProgram を NL2QuerySpec → run_query_and_stats → SummarizeInsight で再構成し、dataset_meta を渡す。FastAPI の `/dspy/interactive` に dataset_id/question/provider/model を受ける I/F を追加し、stats/query_spec/insight を返す。
- AC: 複数データセット（人口系・施設系など）への質問で適切なインサイトと集計が返る。タイムアウトせず完了。
- DoD: 3〜5件の質問例と dataset_id を用意し docs にリクエスト/レスポンススキーマを記載。
- [DONE] `/dspy/interactive` を追加し、`InteractiveAnalysisProgram`（クエリ生成→実行→サマリ保存）で stats/query_spec/insight を返却。`docs/dspy_interactive.md` にリクエスト/レスポンス例と質問サンプルを追記。

## フェーズ3: Next.js フロント + Vercel AI SDK 連携
### Task 3-1: フロントに Vercel AI SDK を導入
- やること: `ai`, `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/google` を追加し、useChat を使ったチャットを既存ページに組込む。
- AC: `/` または `/interactive` でチャット送信とストリーミング表示が動作。
- DoD: `useChat({ body: { provider, model } })` で拡張可能な API にする（UI で切替できなくても可）。

### Task 3-2: Node API から Python /dspy/interactive をツール呼び出し
- やること: `apps/frontend/app/api/agent/interactive/route.ts` を作成し、`runAnalysis(question, datasetId)` ツールで `PY_BACKEND_URL/dspy/interactive` を呼ぶ。System prompt で必要時のみツール使用を指示。
- AC: フロント質問に応じて Python にクエリが飛び、DB 値に基づく回答が返る。バックエンド停止時は Node がエラーをハンドルし案内する。
- DoD: Python API 呼び出しを `lib/backendClient.ts` 等に分離し、将来バッチ API でも再利用可能にする。

### Task 3-3: 対話モード UI（チャット＋簡易ダッシュボード）
- やること: `/interactive` ページ新設。左にチャット、右/下にダッシュボード（KPI カード + グラフ + テーブル）。API レスポンスの stats/グラフ用データで描画。ダッシュボードを `<Dashboard>` コンポーネントとして分離。
- AC: 質問→回答→ダッシュボード更新の流れが最低1パターン動く。「人口推移を見たい」で時系列グラフが表示される。
- DoD: ダッシュボードコンポーネントが再利用可能で、テストデータを渡せば単体表示できる構造（Storybook は任意）。

## フェーズ4: バッチ探索モード
### Task 4-1: Experiments / Jobs / InsightCandidates モデルと API
- やること: `experiments`, `experiment_jobs`, `insight_candidates` テーブルを追加。FastAPI に `POST /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/insights` を実装。
- AC: `POST /experiments` で experiment_id が返る。`GET /experiments/{id}/insights` で JSON 配列が返る（空でも可）。
- DoD: I/O スキーマを Pydantic モデルで型定義。マイグレーションにテーブル定義を追加。

### Task 4-2: DSPy PlanExperiments とワーカー
- やること: `PlanExperimentsSig/PlanExperiments` を実装し、`POST /experiments` で jobs を生成し保存。`worker.py` が pending jobs を処理し、job_type に応じて集計・insight_candidates 保存・失敗時ステータス更新。
- AC: 1実験作成→ワーカー稼働で insight_candidates にレコードが生成。失敗 job は status='failed' とエラー原因を保存。
- DoD: ワーカー起動コマンドを README に明記。1 goal で複数 job→複数 insight が生成されたログかスクリーンショットを残す。

### Task 4-3: フロントのバッチ探索 UI
- やること: `/experiments` ページで goal 入力・dataset 選択・実験作成・一覧表示。`/experiments/[id]` で概要・insight_cards 表示と採用/却下/コメント UI。
- AC: 実験作成→待機→開き直しでインサイト候補がリストアップ。採用/却下/コメントが DB に反映。
- DoD: バッチ探索フロー（作成→待つ→レビュー）を docs に図または文章で整理。

## フェーズ5: フィードバック蓄積 & DSPy 自動チューニング
### Task 5-1: フィードバック API & UI
- やること: DB に `insight_feedback` を追加し、`POST /feedback`（Python or Node のどちらかに統一）。対話/バッチのインサイトカードに 👍/👎 + コメント UI を追加。
- AC: 任意のインサイトカードからフィードバック送信でレコードが追加。必須欠如時は 400。
- DoD: `insight_feedback` に対する簡易集計（rating 平均など）を docs に記載。

### Task 5-2: DSPy Optimizer を用いた NL→DSL 初回コンパイル
- やること: question→query_spec 正解ペアを 5〜10 件用意。`optimizer.compile()` を InteractiveAnalysisProgram に適用し、コンパイル済みプログラムを保存。`/dspy/interactive` で読み込むよう変更。`analysis_queries` に program_version を保存。
- AC: コンパイル前後で query_spec の正解度が向上。コンパイル時に metric がログ出力。
- DoD: 再コンパイル手順（コマンド/必要ファイル）を docs に記載。program_version 管理を実装。

### Task 5-3: フィードバック→trainset 生成スクリプト
- やること: 高評価フィードバックから question/dataset_meta/query_spec/insight_description を含む trainset を生成するスクリプトを作成。生成 trainset で Optimizer を再実行し新しい program_version を登録。
- AC: スクリプト実行で trainset (JSON/dict) が出力され、その trainset で Optimizer を再度回せる。
- DoD: trainset に元の insight_id などを含め、学習に使ったフィードバックを追跡可能にする。改善サイクル（集計→学習→再コンパイル）の概要を docs に記載。

## フェーズ6: 仕上げ（簡易 E2E / ドキュメント / UX 改善）
### Task 6-1: ハッピーパス E2E チェック（手動）
- やること: (1) オープンデータ投入（人口統計 + 1ドメインデータ）→ (2) 対話モードで質問・ダッシュボード表示・フィードバック → (3) バッチ探索で実験作成・ワーカー実行・インサイトレビュー・フィードバック。必要ならスクリーンショット取得。
- AC: 上記 1〜3 がエラーなく完了。想定外の例外でサーバが落ちない。
- DoD: ハッピーパス手順を docs にステップで残す（スクショ付きが望ましい）。既知の制約や TODO を README or ISSUE に整理。

## MVP のすすめ方
- まずフェーズ2の Task 2-3〜2-5（DSPy を用いた最小インタラクティブ分析）を優先すると、対話モードの骨格が早期に確認できる。
- 併せてフェーズ3の Node API 設計をコードレベルまで固めると、フロント接続がスムーズ。
