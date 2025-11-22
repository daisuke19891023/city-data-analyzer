# API 設計書（backendClient 連携ルート）

FastAPI で公開している主要エンドポイントと、フロントエンドの `apps/frontend/src/lib/backendClient.ts` が利用するルートの仕様をまとめる。OpenAPI はバックエンド起動後に `GET /api/v1/swagger-ui/schema` でも取得できる（`uv run python -m clean_interfaces.main --interface restapi` などで起動）。ここでは追加のダミーデータやエラーパターンを明示する。

## 共通事項
- ベース URL: `http://localhost:8000`（環境変数 `VITE_PY_BACKEND_URL` または `PY_BACKEND_URL` で上書き可）
- すべて JSON を送受信。`Content-Type: application/json`
- バリデーションエラー: `400 Bad Request`（Pydantic / FastAPI の詳細エラー配列を `detail` に含む）
- リソース未存在: `404 Not Found`
- サーバ内部エラー: `500 Internal Server Error`

## POST /dspy/interactive
- 概要: NL 質問をもとにクエリ生成・集計・インサイト生成を行う。
- リクエストスキーマ:
  ```json
  {
    "dataset_id": 1,
    "question": "2023年の人口推移を教えて",
    "provider": "openai",   // 任意
    "model": "gpt-4o-mini"   // 任意
  }
  ```
  - レスポンススキーマ:
  ```json
  {
    "dataset_id": 1,
    "question": "2023年の人口推移を教えて",
    "query_spec": {
      "filters": [{ "column": "year", "op": "eq", "value": 2023 }],
      "group_by": ["ward"],
      "metrics": [{ "agg": "sum", "column": "population" }],
      "order_by": [{ "column": "population", "direction": "desc" }],
      "limit": 10
    },
    "data": [
      { "ward": "A区", "population": 120000 },
      { "ward": "B区", "population": 98000 }
    ],
    "stats": {
      "totalRecords": 12400,
      "primaryMetric": "人口合計",
      "positiveRate": "72%"
    },
    "insight": "A区が最大の人口を保持し、前年比+2% の増加。",
    "summary": "2023年は全体で微増傾向。",
    "analysis_id": 42,
    "program_version": "interactive-compiled-v1"
  }
  ```
- ステータスコード: 200
- 主なエラー: 無効な dataset_id や存在しないカラム参照で 400。DB/LLM 障害で 500。
- ダミーデータ利用時: フロントのフォールバックは `summary`/`insight` を簡易メッセージに差し替える。

## GET /datasets
- 概要: データセットメタデータ一覧（カラム情報を含む）。
- レスポンススキーマ（配列要素）:
  ```json
  {
    "id": 1,
    "slug": "population-trend",
    "name": "人口推移",
    "description": "年度別人口統計",
    "year": 2023,
    "columns": [
      { "name": "year", "data_type": "integer", "description": "年度", "is_index": true },
      { "name": "ward", "data_type": "text", "description": "行政区", "is_index": false },
      { "name": "population", "data_type": "integer", "description": "人口", "is_index": false }
    ]
  }
  ```
- ステータスコード: 200
- 主なエラー: DB 接続失敗時に 500。
- ダミーデータ例: バックエンド無応答時、フロントは `{id:1,name:"人口推移 (サンプル)"}` など2件のサンプルを表示。

## POST /experiments
- 概要: ゴールと対象データセットを元に実験を登録し、ジョブを生成。
- リクエストスキーマ:
  ```json
  {
    "goal_description": "子育て支援の需要分析",
    "dataset_ids": [1, 2]
  }
  ```
- レスポンススキーマ:
  ```json
  {
    "experiment_id": 101,
    "job_count": 3
  }
  ```
- ステータスコード: 201
- 主なエラー: `dataset_ids` が空/無効で 400。指定データセットが見つからない場合は 404。DB エラーで 500。
- ダミーデータ例: バックエンド不達時はフロントで `null` を返し、作成失敗扱い。

## GET /experiments
- 概要: 実験一覧を取得。
- レスポンススキーマ（配列要素）:
  ```json
  {
    "id": 101,
    "goal_description": "子育て支援の需要分析",
    "dataset_ids": [1, 2],
    "status": "pending",
    "created_at": "2025-01-20T12:00:00Z",
    "updated_at": "2025-01-20T12:00:00Z",
    "jobs": [
      {
        "id": 501,
        "dataset_id": 1,
        "job_type": "aggregation",
        "description": "年齢別人口推移集計",
        "status": "pending",
        "error_message": null,
        "created_at": "2025-01-20T12:00:00Z",
        "updated_at": "2025-01-20T12:00:00Z"
      }
    ]
  }
  ```
- ステータスコード: 200
- 主なエラー: DB 障害で 500。

## GET /experiments/{experiment_id}
- 概要: 実験詳細とジョブ一覧を取得。
- パスパラメータ: `experiment_id` (int)
- レスポンスは `/experiments` の単一要素と同一構造。
- ステータスコード: 200 / 404（存在しない場合）。

## GET /experiments/{experiment_id}/insights
- 概要: 実験で生成されたインサイト候補の一覧を取得。
- パスパラメータ: `experiment_id` (int)
- レスポンススキーマ:
  ```json
  {
    "insights": [
      {
        "id": 9001,
        "experiment_id": 101,
        "job_id": 501,
        "dataset_id": 1,
        "title": "子育て関連施設の不足が顕著",
        "description": "A区で児童館が人口比で最も少ない。",
        "metrics": { "ratio": 0.12 },
        "adopted": false,
        "feedback_comment": null,
        "created_at": "2025-01-20T12:00:00Z"
      }
    ]
  }
  ```
- ステータスコード: 200（実験が存在しない場合でも空配列の可能性を想定）。
- 主なエラー: DB 障害で 500。

## POST /feedback
- 概要: インサイトまたはインタラクティブ分析へのフィードバックを保存。
- リクエストスキーマ:
  ```json
  {
    "insight_id": 9001,       // batch インサイトの場合
    "analysis_id": null,       // interactive の場合はこちらに ID
    "rating": 1,               // +1: 採用 / -1: 却下
    "comment": "有用な示唆でした",
    "target_module": "batch"   // "interactive" | "batch" | "other"
  }
  ```
- レスポンススキーマ:
  ```json
  {
    "feedback_id": 30001,
    "target_module": "batch",
    "rating": 1,
    "analysis_id": null,
    "insight_id": 9001,
    "message": "Feedback recorded"
  }
  ```
- ステータスコード: 201
- 主なエラー: `insight_id` と `analysis_id` の両方欠如、または `rating=0` で 400。存在しない `insight_id` 指定で 404。DB 障害で 500。

---

### 参考: OpenAPI スキーマの取得
`GET /api/v1/swagger-ui/schema` にアクセスすると動的に生成された OpenAPI JSON を取得できる。カスタム UI は `GET /api/v1/swagger-ui` で確認可能。
