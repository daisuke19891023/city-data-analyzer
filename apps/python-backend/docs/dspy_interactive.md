# /dspy/interactive エンドポイント概要

自然言語の質問を QuerySpec に変換し、`dataset_records` の JSON を集計する最小構成の DSPy 風パイプラインを実装しました。

## エンドポイント

- **POST `/dspy/interactive`**
  - リクエスト: `{ "dataset_id": 1, "question": "2023年の区別人口の平均は？", "provider": "openai", "model": "gpt-4.1" }`
  - レスポンス例:
    ```json
    {
      "dataset_id": 1,
      "question": "2023年の区別人口の平均は？",
      "query_spec": {
        "filters": [{"column": "year", "op": "eq", "value": 2023}],
        "group_by": ["ward"],
        "metrics": [{"agg": "avg", "column": "population"}],
        "order_by": [{"column": "population", "direction": "desc"}],
        "limit": 20
      },
      "data": [{"ward": "A区", "avg_population": 1000.0}],
      "stats": {"requested_rows": 3, "returned_rows": 1, "group_by": ["ward"], "metrics": [{"agg": "avg", "column": "population"}], "filters": [{"column": "year", "op": "eq", "value": 2023}]},
      "insight": "質問『2023年の区別人口の平均は？』に対し、avg(population) を計算しました。返却件数: 1件。",
      "analysis_id": 42,
      "program_version": "interactive-compiled-v1"
    }
    ```

## パイプライン構成

1. **RuleBasedQueryGenerator**: `dataset_columns` を参照し、年度・区などのキーワードを元に `group_by` と `filters` を推定。数値カラムがある場合は平均/合計などのメトリクスを選択し、該当しない場合は `count` を返す。
2. **QueryRunner**: `dataset_records.row_json` を DataFrame 化し、フィルタ・グループ化・メトリクス・ソート・limit を適用。無効なカラムは `400` エラーを返す。
3. **InteractiveAnalysisProgram**: 実行結果を要約文に変換し、`analysis_queries` に履歴として保存。`program_version` にロード済みコンパイル済みプログラムのバージョン（例: `interactive-compiled-v1`）を記録する。

### DSPy Optimizer を使ったコンパイル

- サンプルの学習ペアは `dspy/interactive/trainset_samples.json` に 6 件保存済みです。
- `PYTHONPATH=src` を設定した上で、`scripts/compile_interactive.py` を実行すると Heuristic + DSPy Optimizer 風の評価を行い、`dspy/interactive/compiled_program.json` に保存します。

例:

```bash
cd apps/python-backend
PYTHONPATH=src python scripts/compile_interactive.py \
  --trainset dspy/interactive/trainset_samples.json \
  --output dspy/interactive/compiled_program.json \
  --version interactive-compiled-v1
# baseline と compiled のスコアがログ出力されます
```

### 再コンパイル手順とプログラムの利用

- `/dspy/interactive` は `dspy/interactive/compiled_program.json` が存在する場合にロードし、最も近いサンプルから `query_spec` を補完します。ない場合は従来のルールベースにフォールバックします。
- 生成された `program_version` が API レスポンスと `analysis_queries.program_version` に保存され、フィードバックからどのバージョンが使われたかを後から追跡できます。

## サンプル質問

- 「2023年の区別人口の平均は？」
- 「区ごとの施設数を教えて」
- 「2022年以降で最大の人口は？」

いずれも存在しないカラムを参照した場合は `400 Bad Request`、データセットが見つからない場合は `404` を返します。
