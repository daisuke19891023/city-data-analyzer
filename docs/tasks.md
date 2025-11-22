# city-data-analyzer タスク & ロードマップ

## 最新対応
- [DONE] frontend ダーク/ライト切替の Prettier フォーマット崩れを修正（App.tsx, App.vitest.test.tsx, index.css を整形）（2025-11-23）。
- [DONE] [Issue #19] VITE_DATA_MODE を import.meta.env から直接読んでモード判定するよう修正し、データモードのユニットテストを追加（2025-11-23）。
- [DONE] frontend フォーマットエラーの修正（`src/lib/dataSource.ts` を Prettier 準拠に整形）（2025-11-23）。
- [DONE] backendClient が利用するルートの API 設計書を `docs/api-spec.md` に追加し、メソッド/スキーマ/エラーパターンを整理（2025-11-23）。

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
  - [DONE] Vite フロントに Vercel AI SDK を導入し、プロバイダー/モデルを body に含めた useChat 構成にした。チャット UI を /interactive 相当のセクションに追加。

### Task 3-2: Node API から Python /dspy/interactive をツール呼び出し
- やること: `apps/frontend/app/api/agent/interactive/route.ts` を作成し、`runAnalysis(question, datasetId)` ツールで `PY_BACKEND_URL/dspy/interactive` を呼ぶ。System prompt で必要時のみツール使用を指示。
- AC: フロント質問に応じて Python にクエリが飛び、DB 値に基づく回答が返る。バックエンド停止時は Node がエラーをハンドルし案内する。
- DoD: Python API 呼び出しを `lib/backendClient.ts` 等に分離し、将来バッチ API でも再利用可能にする。
  - [DONE] lib/backendClient.ts で /dspy/interactive 呼び出しを共通化し、バックエンド停止時はサンプル応答でダッシュボードを更新するフロント実装を追加。

### Task 3-3: 対話モード UI（チャット＋簡易ダッシュボード）
- やること: `/interactive` ページ新設。左にチャット、右/下にダッシュボード（KPI カード + グラフ + テーブル）。API レスポンスの stats/グラフ用データで描画。ダッシュボードを `<Dashboard>` コンポーネントとして分離。
- AC: 質問→回答→ダッシュボード更新の流れが最低1パターン動く。「人口推移を見たい」で時系列グラフが表示される。
- DoD: ダッシュボードコンポーネントが再利用可能で、テストデータを渡せば単体表示できる構造（Storybook は任意）。
  - [DONE] チャットとダッシュボードの2カラム UI を追加し、`<Dashboard>` コンポーネント化。ダミー応答でも KPI/グラフ/インサイトが更新される仕組みを構成。

## フェーズ4: バッチ探索モード
### Task 4-1: Experiments / Jobs / InsightCandidates モデルと API
- やること: `experiments`, `experiment_jobs`, `insight_candidates` テーブルを追加。FastAPI に `POST /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/insights` を実装。
- AC: `POST /experiments` で experiment_id が返る。`GET /experiments/{id}/insights` で JSON 配列が返る（空でも可）。
- DoD: I/O スキーマを Pydantic モデルで型定義。マイグレーションにテーブル定義を追加。
  - [DONE] SQLAlchemy モデル/マイグレーションを追加し、Experiment API（作成・取得・インサイト取得・フィードバック）を実装。

### Task 4-2: DSPy PlanExperiments とワーカー
- やること: `PlanExperimentsSig/PlanExperiments` を実装し、`POST /experiments` で jobs を生成し保存。`worker.py` が pending jobs を処理し、job_type に応じて集計・insight_candidates 保存・失敗時ステータス更新。
- AC: 1実験作成→ワーカー稼働で insight_candidates にレコードが生成。失敗 job は status='failed' とエラー原因を保存。
- DoD: ワーカー起動コマンドを README に明記。1 goal で複数 job→複数 insight が生成されたログかスクリーンショットを残す。
  - [DONE] PlanExperiments と ExperimentWorker を追加し、ジョブ作成・処理・インサイト生成のログを docs に記載。README にワーカー起動手順を追記。

### Task 4-3: フロントのバッチ探索 UI
- やること: `/experiments` ページで goal 入力・dataset 選択・実験作成・一覧表示。`/experiments/[id]` で概要・insight_cards 表示と採用/却下/コメント UI。
- AC: 実験作成→待機→開き直しでインサイト候補がリストアップ。採用/却下/コメントが DB に反映。
- DoD: バッチ探索フロー（作成→待つ→レビュー）を docs に図または文章で整理。
  - [DONE] React Router を導入し、/experiments と /experiments/:id で実験作成・一覧・フィードバック UI を追加。フローを docs/batch_experiments_flow.md にまとめた。

## フェーズ5: フィードバック蓄積 & DSPy 自動チューニング
### Task 5-1: フィードバック API & UI
- やること: DB に `insight_feedback` を追加し、`POST /feedback`（Python or Node のどちらかに統一）。対話/バッチのインサイトカードに 👍/👎 + コメント UI を追加。
- AC: 任意のインサイトカードからフィードバック送信でレコードが追加。必須欠如時は 400。
- DoD: `insight_feedback` に対する簡易集計（rating 平均など）を docs に記載。
  - [DONE] `/feedback` エンドポイントを追加し、対話/バッチのカードから 👍/👎 とコメントを送信すると `insight_feedback` に保存されるようにした。必須欠落時は 400 を返し、docs/feedback_loop.md に集計 SQL を掲載。

### Task 5-2: DSPy Optimizer を用いた NL→DSL 初回コンパイル
- やること: question→query_spec 正解ペアを 5〜10 件用意。`optimizer.compile()` を InteractiveAnalysisProgram に適用し、コンパイル済みプログラムを保存。`/dspy/interactive` で読み込むよう変更。`analysis_queries` に program_version を保存。
- AC: コンパイル前後で query_spec の正解度が向上。コンパイル時に metric がログ出力。
- DoD: 再コンパイル手順（コマンド/必要ファイル）を docs に記載。program_version 管理を実装。
  - [DONE] サンプル trainset を用意し、`scripts/compile_interactive.py` で baseline/compiled スコアを出力・保存する導線を追加。`program_version` を `/dspy/interactive` レスポンスと `analysis_queries` に保存し、コンパイル済みファイルを優先ロードするよう変更。

### Task 5-3: フィードバック→trainset 生成スクリプト
- やること: 高評価フィードバックから question/dataset_meta/query_spec/insight_description を含む trainset を生成するスクリプトを作成。生成 trainset で Optimizer を再実行し新しい program_version を登録。
- AC: スクリプト実行で trainset (JSON/dict) が出力され、その trainset で Optimizer を再度回せる。
- DoD: trainset に元の insight_id などを含め、学習に使ったフィードバックを追跡可能にする。改善サイクル（集計→学習→再コンパイル）の概要を docs に記載。
  - [DONE] `scripts/export_feedback_trainset.py` で高評価フィードバックから trainset JSON を生成し、`feedback_id`/`analysis_id`/`insight_id` を保持。docs/feedback_loop.md に集計→学習→再コンパイルの流れを追加。

## フェーズ6: 仕上げ（簡易 E2E / ドキュメント / UX 改善）
### Task 6-1: ハッピーパス E2E チェック（手動）
- やること: (1) オープンデータ投入（人口統計 + 1ドメインデータ）→ (2) 対話モードで質問・ダッシュボード表示・フィードバック → (3) バッチ探索で実験作成・ワーカー実行・インサイトレビュー・フィードバック。必要ならスクリーンショット取得。
- AC: 上記 1〜3 がエラーなく完了。想定外の例外でサーバが落ちない。
- DoD: ハッピーパス手順を docs にステップで残す（スクショ付きが望ましい）。既知の制約や TODO を README or ISSUE に整理。
- [DONE] 川崎市相談データと人口CSVの投入手順を `docs/happy_path_e2e.md` に追加し、対話モード/バッチ探索/フィードバックのハッピーパス操作を整理。Excel→CSV 変換用スクリプトと `openpyxl` 依存を追加し、README に制約を明記。
  - `convert_excel_to_csv.py` の単体テストを追加し、ruff/pytest/pyright を通過させた。

## MVP のすすめ方
- まずフェーズ2の Task 2-3〜2-5（DSPy を用いた最小インタラクティブ分析）を優先すると、対話モードの骨格が早期に確認できる。
- 併せてフェーズ3の Node API 設計をコードレベルまで固めると、フロント接続がスムーズ。

## メンテナンス・QA
- [DONE] バックエンド nox 実行とフロントのバッチ探索テスト追加
  - uv run nox で lint/typing/pytest/pip-audit など品質チェックを実行
  - backendClient/ExperimentsPage/ExperimentDetailPage に単体テストを追加し、Vitest/Jest を通過
  - npm run --workspace apps/frontend test -- --runInBand で動作確認
- [DONE] CI lint/format 修正
  - ruff の TC/E501 系指摘を修正して `uv run --with nox nox -s lint` を通過
  - フロントエンドの Prettier チェックを `npm run format --workspace frontend -- --write` で解消
  - CI の frontend format ステップ（`npm run format --workspace frontend`）が通過するよう再整形を実施
- [DONE] uv run nox & フロント lint/format 再実行 (2025-11-22)
  - ruff/pyright の指摘を解消し、nox の lint/typing/test セッションを成功させた
  - pip-audit は証明書検証エラー、Sphinx ビルドは既存の重複 docstring 警告で失敗することを確認
  - `npm run --workspace apps/frontend lint` と `npm run --workspace apps/frontend format -- --write` を完了

## フェーズ7: UX 向上プラン統合
### テーマA: 観点提案 UX
#### Task A-1: 観点テンプレートのスキーマ & API 追加
- ステータス: TODO
- やること: `analysis_viewpoints` テーブルと `GET/POST /viewpoints`, `GET /viewpoints/{id}` を追加し、config_json に推奨データセット ID などを保持。
- AC: 3〜5件のテンプレートを登録し一覧/詳細取得できる。
- DoD: テーブル定義と API I/O を docs に記載し、curl で3件以上登録→取得済み。

#### Task A-2: 観点テンプレートギャラリーUI
- ステータス: TODO
- やること: `/interactive` などにギャラリーコンポーネントを配置し、カードクリックで nl_prompt を下書き or 即送信。タグ/検索フィルタとモバイル対応。
- AC: 3枚以上のカード表示とクリック時の自動入力/送信が動作し、観点に沿った回答が得られる。
- DoD: ギャラリーコンポーネントが独立し、別ページに埋め込める。スマホ幅でもカードが崩れない。

#### Task A-3: データセットに応じた質問サジェスト
- ステータス: TODO
- やること: `GET /datasets/{id}/suggested_questions` を追加し、LLM に dataset schema + 観点テンプレートを渡して質問候補を生成。フロントでチップ表示しクリック送信。
- AC: データセット変更で候補が変わり、候補から送信すると分析が実行される。
- DoD: レスポンス例を docs に記載し、代表的な 2〜3 dataset_id でサジェスト内容を確認。

#### Task A-4: 会話ショートカットボタン
- ステータス: TODO
- やること: よく使う指示をチップ化しチャット下に配置。クリックで messages に定義済み system/user メッセージを追加して送信。
- AC: 3種類以上のショートカットから即応答が返る。
- DoD: 定義が一箇所に集約され拡張しやすく、UX 的に邪魔にならない位置に配置。

### テーマB: 知見の蓄積 & 再利用
#### Task B-1: 分析レシピのスキーマ & API
- ステータス: TODO
- やること: `analysis_recipes` テーブルと `POST/GET /recipes`, `GET /recipes/{id}` を追加。query_spec_json/chart_config_json を保存。
- AC: 対話モードで生成した query_spec と chart_config を保存し、一覧取得できる。
- DoD: レシピ 2〜3 件を手動保存し DB 内容を確認。JSON 構造を docs に記載。

#### Task B-2: レシピの適用 UI
- ステータス: TODO
- やること: `/interactive` or `/recipes` に一覧と「このレシピを使う」ボタンを配置。必要なら自治体コード/期間をモーダル入力し、/analysis/query をパラメータ上書きで実行。
- AC: レシピから別自治体で同じ分析を実行し、ダッシュボード表示まで 1クリック + 1〜2入力で完了。
- DoD: 実行結果と元レシピ説明を紐付けて表示し、「レシピ利用」ラベルを付与。

#### Task B-3: インサイトノート & タグ・検索
- ステータス: TODO
- やること: `insight_notes` テーブルと `POST/GET /insight-notes`/`/search` を実装。対話/実験詳細からノート保存、/notes でタグ/キーワード絞り込み UI を提供。
- AC: ノート保存→タグ絞り込み・検索が機能し、ヒットしたノートが表示される。
- DoD: 3〜5件のノートで保存〜検索のデモを確認。

#### Task B-4: 簡易レポート出力（Markdown/PDF）
- ステータス: TODO
- やること: ノート/インサイトの複数選択 UI を追加し、Python で Markdown（将来 PDF）レポートを生成。元データ情報を明記し、エラー時に簡易メッセージを返す。
- AC: 2〜3件のノート/インサイトからレポートビューを生成できる。
- DoD: サンプルレポートを docs に保存し、重大エラー時のハンドリングを実装。

#### Task B-5: 学びの履歴ビュー
- ステータス: TODO
- やること: insight_feedback + insight_notes を集約し、/history でタイムライン + タグクラウドを表示。期間フィルタと元ノートリンクを提供。
- AC: 重要インサイトが日付順で閲覧でき、期間絞り込みが可能。
- DoD: ダミーデータ含むタイムラインを確認し、カードから元ノート/インサイト詳細へ遷移可能。

### テーマC: ダッシュボード操作強化
#### Task C-1: ダッシュボード構成の状態管理と API 化
- ステータス: TODO
- やること: DashboardConfig 型を定義し、`dashboard_instances` に config_json を保存する `GET/PUT /dashboards/{id}` を実装。再読み込みで構成を復元。
- AC: 現在のダッシュボード構成が JSON で保存/復元される。
- DoD: DashboardConfig スキーマを docs に明記し、1ケースで保存→再読み込み→復元を確認。

#### Task C-2: 「ダッシュボード編集」DSPy/ツール定義
- ステータス: TODO
- やること: DSPy EditDashboardConfig モジュールを作成し、Node `/api/agent/interactive` に editDashboard ツールを追加。代表的な編集指示の Before/After サンプルを残す。
- AC: 棒→折れ線、上位N件、地域色分けなどの指示が config に反映され、不正カラムはエラーになる。
- DoD: 3〜5 個の編集指示サンプルとプロンプト制約をコード/コメントに残す。

#### Task C-3: What-if シミュレーション API + UI
- ステータス: TODO
- やること: `POST /analysis/what-if` を実装し、query_spec + 変化指標/率からベース vs シミュレーション結果を返却。フロントでモーダル入力と差分グラフを表示。
- AC: 「Aを+10%したらBがどうなるか」をグラフ比較でき、異常入力時に警告/エラーが出る。
- DoD: What-if 結果のサンプルを docs に残し、比例/回帰などの仮定を明記。

### テーマD: 信頼感と運用性
#### Task D-1: データセット更新情報 & ディスクレーマー表示
- ステータス: TODO
- やること: datasets に `last_updated_at/source_description/warning_text` を追加し、ダッシュボードやノートに更新日・注意文を表示。
- AC: ダッシュボードに更新日とディスクレーマーが表示される。
- DoD: warning_text を設定した dataset で UI 表示を確認し、仕様を docs に記載。

#### Task D-2: データ更新に伴う再実行候補一覧
- ステータス: TODO
- やること: experiments/analysis_recipes に last_run_at を保持し、`GET /rerun-candidates` で datasets.last_updated_at を超えるものを抽出。/settings or /maintenance で一覧 + 再実行ボタンを提供。
- AC: データ更新後に再実行候補がリスト化され、1件以上を再実行できる。
- DoD: 更新→候補抽出→再実行→完了までを手動確認し、実行時データ時点が UI で確認できる。

#### Task D-3: 軽量ログダッシュボード（運用者向け）
- ステータス: TODO
- やること: 集計ビュー or テーブルで期間別/観点別利用状況をまとめ、`GET /admin/stats` と /admin/stats UI を追加。期間フィルタと棒/折れ線グラフ表示、簡易認証を検討。
- AC: 直近7日/30日の利用状況と観点テンプレートの使用回数ランキングを確認できる。
- DoD: ダッシュボードサンプルスクショを docs に残し、最低限の認証で一般ユーザーから隠蔽。

### テーマE: 先進分析 UX
#### Task E-1: 自治体クラスタリング & ペルソナ生成
- ステータス: TODO
- やること: `POST /analysis/clusters` を追加し、標準化→k-means→クラスタ統計→LLM 要約を行う。/clusters で地図/テーブル表示とペルソナカードを提供。
- AC: k=3 以上で異なる特徴説明が返り、同クラスタ自治体を UI でハイライトできる。
- DoD: クラスタ JSON とペルソナ例を docs に残し、欠損/極端値の扱いをコード/コメントに明記。

#### Task E-2: モデル比較（マルチモデル A/B UI）
- ステータス: TODO
- やること: Node `/api/agent/compare` を実装し、同じ question/datasetId を複数プロバイダで実行。/compare で回答を横並び表示し、モデル一覧を設定ファイルに集約。
- AC: 2モデル以上の回答を並べて表示し、実際にバックエンド分析にアクセスしている。
- DoD: 代表質問の差分例を docs に残し、モデル選択肢を定数/設定にまとめる。
