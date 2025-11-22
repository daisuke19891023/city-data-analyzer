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
- オープンデータ: 川崎市オープンデータカタログの CSV を別プロジェクトでダウンロード・前処理済みとし、本プロジェクトは CSV を取り込んで DB 化する。カテゴリは「医療・介護・福祉」「防災・防犯」「観光・イベント」「住まい・生活・引越し」「子育て・教育」「公共施設・都市計画」「人口・世帯」「環境・エネルギー」「情報通信・先端技術」「産業」「地図・地理空間」「その他」の12種を初期値として扱う。
- LLM: DSPy 経由で OpenAI/Anthropic/Gemini を切替可能にし、litellm で統一インターフェイスを確保。

## 機能要求（フェーズ別）
### フェーズ1: 起動確認 & 開発環境整備
- フロント/バックエンドの dev 起動手順を整備し、README と .env.example に集約。

### フェーズ2: Python バックエンドにデータ基盤 + DSPy 最小パイプライン
- DB スキーマ（open_data_categories, datasets, dataset_columns, dataset_records, analysis_queries [+ dataset_files 任意]）とマイグレーション雛形。CSV カラムを JSONB で柔軟に保持し、index 抽出用カラムを設ける。
- CSV 取り込みスクリプト（idempotent）。カテゴリ slug と dataset slug を受け取り、ヘッダから dataset_columns を生成し dataset_records に JSONB で投入。year/ward_code などの index_cols 抽出ルールを備える。
- DSPy NL→QuerySpec モジュールを拡張し、dataset_meta（dataset_columns, index_cols 情報）を LLM に渡す。
- QuerySpec 集計 API (`POST /analysis/query`) を JSONB 抽出ベースで汎用化し、基本統計を返す。
- DSPy インタラクティブ API (`POST /dspy/interactive`) で NL→集計→インサイト文章を一括返却。dataset_id を入力とし、複数データセットに対応。

### フェーズ3: Next.js フロント + Vercel AI SDK 対話モード
- Vercel AI SDK によるチャット UI。
- Node API `/api/agent/interactive` が Python `/dspy/interactive` をツール呼び出し。
- /interactive ページでチャット + ダッシュボード描画。

### フェーズ4: バッチ探索モード
- experiments/experiment_jobs/insight_candidates モデルと API。結合キーの推定には dataset_columns.is_index を活用。
- DSPy PlanExperiments + ワーカーでジョブ処理とインサイト蓄積。query_spec には dataset_id を含める。
- フロントのバッチ探索 UI（実験作成・結果レビュー）。

### フェーズ5: フィードバック蓄積 & DSPy 自動チューニング
- insight_feedback API & UI。
- DSPy Optimizer で NL→DSL をコンパイルし、program_version を管理。analysis_queries には dataset_id と dataset_version を保存。
- フィードバックから trainset を生成し再コンパイルを回す導線。

### フェーズ6: 仕上げ
- ハッピーパスの手動 E2E（データ投入→対話→バッチ探索→フィードバック）。
- 既知の制約/TODO の整理とドキュメント拡充。

## UX 向上プラン（追加要件）
以下の 5 テーマを追加し、既存の対話/バッチ体験に拡張 UX を重ねる。各タスクは AC/DoD を tasks.md に具体化し、API/スキーマは design.md に反映する。

### テーマA: ユーザーに“観点”を提案する UX
- 観点テンプレートスキーマ `analysis_viewpoints` を追加し、`GET/POST /viewpoints` でギャラリーに供給。
- /interactive などに「観点ギャラリー」を配置し、カードクリックで NL プロンプト下書き or 即送信を実行。タグ/検索フィルタ付き。
- データセット別の質問サジェスト API `GET /datasets/{id}/suggested_questions` を追加し、質問チップとして表示。クリックで送信/入力に挿入。
- 会話ショートカットボタンをチャット下部に配置し、定義済みメッセージをワンクリック送信。

### テーマB: 知見の蓄積 & 再利用
- 分析レシピ用テーブル `analysis_recipes` と API `POST/GET /recipes` を追加し、query_spec + chart_config を保存・再利用。
- レシピ適用 UI を用意し、別自治体/期間で同一レシピを実行できる導線を提供。
- インサイトノート `insight_notes`（タグ/検索対応）と `POST/GET /insight-notes`/`/search` を追加。対話結果からノート保存ボタンを提供。
- ノート/インサイトの束ね出力として Markdown/PDF レポート生成 API と選択 UI を用意。
- フィードバック付きインサイトのタイムライン（学びの履歴）ビューを /history に追加し、タグ集計と期間フィルタを提供。

### テーマC: ダッシュボードとのインタラクション強化
- DashboardConfig を JSON として保存する `dashboard_instances` 系 API（GET/PUT /dashboards/{id}`）を追加し、構成の保存/復元を担保。
- DSPy の EditDashboardConfig モジュールと Node の editDashboard ツールを用意し、自然言語でグラフ種別・フィルタ等を変更。
- What-if シミュレーション API `POST /analysis/what-if` と UI を追加し、メトリクス変化の差分グラフを提供。

### テーマD: 信頼感と運用性
- datasets に `last_updated_at/source_description/warning_text` を追加し、各ダッシュボードに更新情報・ディスクレーマーを表示。
- データ更新後の再実行候補を返す `GET /rerun-candidates` を追加し、実験/レシピの再実行リストとボタンを提供。
- 運用者向け軽量ログダッシュボードとして `GET /admin/stats` と /admin/stats UI を追加。利用量/観点別集計を表示し簡易認証を検討。

### テーマE: ちょっと攻めた分析 UX
- 自治体クラスタリング API `POST /analysis/clusters` を追加し、k-means + LLM 要約でクラスタ別ペルソナを返す。/clusters で地図/表表示。
- モデル比較 UI /compare と Node API `/api/agent/compare` を用意し、同一質問を複数プロバイダで実行した結果を並べて提示。

## 成功指標（暫定）
- 起動手順に従い、他メンバーがフロント/バックエンドを立ち上げられる。
- NL 質問から query_spec/集計/インサイトが一貫して返るエンドツーエンド動作。
- バッチ探索で実験作成後、ワーカーがインサイト候補を生成し UI で確認できる。
- フィードバックを元に DSPy プログラムを再コンパイルできる手順が確立。
