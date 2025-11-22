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
### Task 2-1: DB スキーマ設計とマイグレーション雛形
- やること: `datasets`, `dataset_rows`, `analysis_queries` のテーブルを SQLAlchemy モデル or Alembic で追加。
- AC: マイグレーション実行で上記テーブル作成。`datasets` に対する SELECT/INSERT が動作。
- DoD: `apps/python-backend/docs/` か README に ER 図/テーブル説明（カラムと用途）を記載。

### Task 2-2: 人口統計データの取り込みスクリプト
- やること: `scripts/load_population.py` などで CSV を datasets + dataset_rows に投入。`dataset_rows.row_json` で柔軟に保持。idempotent 性を意識。
- AC: スクリプト実行後、datasets に1レコード、dataset_rows に数百〜数千件のデータが入り人口や年/自治体コードが確認できる。
- DoD: 再実行時の挙動を README に明記（重大な重複を避けるか、注意書き）。

### Task 2-3: DSPy NL→QuerySpec モジュール作成
- やること: `pyproject.toml` に `dspy-ai`, `litellm` を追加。`src/clean_interfaces/citydata/dspy_programs/nl2query.py` を作成し、`configure_lm(provider, model)`、`NL2QuerySpecSig`、`NL2QuerySpec` を実装。
- AC: 代表質問（例: 「東京都の2015年以降の高齢者人口の推移を見たい」）で JSON パース可能な `query_spec` が返る。カラム名がスキーマに存在するものだけになっている。
- DoD: 3〜5 パターンの質問と `query_spec` 例をソースまたは docs に残す。LM 設定失敗時に FastAPI が 5xx でなく明示エラー JSON を返す。

### Task 2-4: QuerySpec → 集計実行 → 基本統計 API
- やること: query_spec を受けて SQL を発行し、pandas などで基本統計を計算する関数を実装。FastAPI に `POST /analysis/query` を追加。
- AC: `POST /analysis/query` で期待通りの集計が返る。不正 query_spec で 400 台とわかりやすいメッセージ。
- DoD: 集計ロジックを関数に切出しユニットテストを最低1本追加。引数/戻り値は素直な Python 型で DSPy からも再利用可能にする。

### Task 2-5: DSPy /dspy/interactive プログラム
- やること: `src/clean_interfaces/citydata/dspy_programs/interactive.py` に `InteractiveAnalysisProgram`（NL2QuerySpec → 集計関数 → SummarizeInsight）を Module として実装。FastAPI に `POST /dspy/interactive` を追加。
- AC: エンドポイント呼び出しで「質問に対応した集計」と説明文が一度に返る。同じ質問で意味的に一貫した回答が返る。
- DoD: `/dspy/interactive` の I/O フォーマットを docs に明記。InteractiveAnalysisProgram は DSPy Module クラスで定義。

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
