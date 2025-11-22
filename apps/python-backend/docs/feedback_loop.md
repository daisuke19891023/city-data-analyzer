# フィードバック収集と再コンパイル手順

フェーズ5で追加したフィードバック導線と DSPy Optimizer 風コンパイルの使い方をまとめます。

## フィードバックの保存形式

- `insight_feedback` テーブルに `rating`（👍=1 / 👎=-1）、`comment`、`target_module`（`interactive` or `batch`）、`analysis_id` or `candidate_id` を保存します。
- `analysis_queries.program_version` に `/dspy/interactive` を実行したプログラムのバージョンを記録しています。

### 集計クエリ例（DoD）

```sql
SELECT target_module, COUNT(*) AS feedback_count, AVG(rating) AS avg_rating
FROM insight_feedback
GROUP BY target_module;
```

## 再コンパイル/Optimizer 実行手順（DoD）

1. サンプル学習ペア: `apps/python-backend/dspy/interactive/trainset_samples.json` に 6 件格納済み。
2. コンパイル: `PYTHONPATH=src` を設定して `scripts/compile_interactive.py` を実行。
   ```bash
   cd apps/python-backend
   PYTHONPATH=src python scripts/compile_interactive.py \
     --trainset dspy/interactive/trainset_samples.json \
     --output dspy/interactive/compiled_program.json \
     --version interactive-compiled-v1
   # baseline / compiled のスコアがログに出ます
   ```
3. `/dspy/interactive` はコンパイル済みファイルがあればロードし、`program_version` をレスポンスと `analysis_queries` に保存します。

## フィードバック→trainset 生成スクリプト（DoD）

高評価フィードバックを学習データに落とすには `export_feedback_trainset.py` を利用します。

```bash
cd apps/python-backend
PYTHONPATH=src DATABASE_URL=sqlite:///./data/city_data.db \
  python scripts/export_feedback_trainset.py --min-rating 1 \
  --output dspy/interactive/trainset_from_feedback.json
```

- `feedback_id`, `analysis_id`/`insight_id` を含めているため、どのフィードバックが学習に使われたかを後から追跡できます。
- 生成された trainset を `compile_interactive.py --trainset dspy/interactive/trainset_from_feedback.json ...` でそのまま Optimizer に再投入できます。

## 改善サイクル

1. `/feedback` で集まった評価を上記クエリで集計し、対象データセット/モジュールを把握。
2. `export_feedback_trainset.py` で高評価サンプルから trainset を生成。
3. `compile_interactive.py` で再コンパイルし、`program_version` を更新。
4. `/dspy/interactive` のレスポンスから新しい `program_version` を確認し、次のフィードバック収集に回す。
