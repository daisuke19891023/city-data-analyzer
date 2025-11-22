# バッチ探索モードの操作フロー

1. **実験の作成**
   - フロントの `/experiments` ページで「やりたいこと」と対象データセットを指定し、作成ボタンを押す。
   - もしくは FastAPI の `POST /experiments` に `{ "goal_description": "...", "dataset_ids": [1,2] }` を送信する。
2. **ジョブ計画の確認**
   - `GET /experiments` または `GET /experiments/{id}` で、PlanExperiments が生成した `experiment_jobs`（job_type/description/status）を確認する。
3. **ワーカーの起動**
   - バックエンド直下で `PYTHONPATH=src uv run python -m clean_interfaces.worker` を起動し、`pending` ジョブを順次処理する。
   - CLI ログには処理済みジョブ数と生成されたインサイト候補が表示される。
4. **インサイト候補のレビュー**
   - `GET /experiments/{id}/insights` またはフロントの `/experiments/{id}` で候補を確認し、「採用/却下/コメント」を登録する。`POST /insights/{candidate_id}/feedback` も利用可能。

## サンプルログ

以下はメモリDBで 1 goal から複数ジョブを生成し、ワーカー実行で2件のインサイト候補が作られた例です。

```
jobs processed: 2
insight#1: metric_summary @ dataset 1 | adopted=False
insight#2: top_values @ dataset 1 | adopted=False
```
【edf939†L1-L11】
