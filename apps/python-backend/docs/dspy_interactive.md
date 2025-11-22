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
      "insight": "質問『2023年の区別人口の平均は？』に対し、avg(population) を計算しました。返却件数: 1件。"
    }
    ```

## パイプライン構成

1. **RuleBasedQueryGenerator**: `dataset_columns` を参照し、年度・区などのキーワードを元に `group_by` と `filters` を推定。数値カラムがある場合は平均/合計などのメトリクスを選択し、該当しない場合は `count` を返す。
2. **QueryRunner**: `dataset_records.row_json` を DataFrame 化し、フィルタ・グループ化・メトリクス・ソート・limit を適用。無効なカラムは `400` エラーを返す。
3. **InteractiveAnalysisProgram**: 実行結果を要約文に変換し、`analysis_queries` に履歴として保存。

## サンプル質問

- 「2023年の区別人口の平均は？」
- 「区ごとの施設数を教えて」
- 「2022年以降で最大の人口は？」

いずれも存在しないカラムを参照した場合は `400 Bad Request`、データセットが見つからない場合は `404` を返します。
