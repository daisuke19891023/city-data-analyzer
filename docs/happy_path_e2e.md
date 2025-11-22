# ハッピーパス E2E 操作手順（フェーズ6）

以下は「人口統計 + 川崎市の消費者相談データ」を使った手動 E2E 手順です。バックエンド/フロントの両方が落ちずに一連の操作を完了させることを目的にしています。

## 前提
- ルートで `npm install`、`uv sync`（backend）は済ませておく。
- `.env` をルートにコピーし、`PY_BACKEND_URL` を FastAPI のポート（例: http://localhost:8000）に合わせる。
- Python 側の DB はデフォルトで `apps/python-backend/data/city_data.db`（SQLite）。

## ステップ1: オープンデータ投入（人口統計 + 川崎市相談データ）
1. **人口CSVの作成（サンプル）**
   ```bash
   cd apps/python-backend
   mkdir -p data
   uv run python - <<'PY'
   import pandas as pd
   from pathlib import Path

   Path('data').mkdir(exist_ok=True)
   df = pd.DataFrame(
       [
           {"ward_code": "101", "ward": "川崎区", "year": 2023, "population": 237691},
           {"ward_code": "102", "ward": "幸区", "year": 2023, "population": 176918},
           {"ward_code": "103", "ward": "中原区", "year": 2023, "population": 264316},
           {"ward_code": "104", "ward": "高津区", "year": 2023, "population": 233207},
           {"ward_code": "105", "ward": "宮前区", "year": 2023, "population": 235379},
           {"ward_code": "106", "ward": "多摩区", "year": 2023, "population": 212430},
           {"ward_code": "107", "ward": "麻生区", "year": 2023, "population": 181765},
       ]
   )
   df.to_csv('data/population_by_ward_2023.csv', index=False)
   PY
   ```

2. **川崎市相談データのダウンロードと整形**
   ```bash
   cd apps/python-backend
   curl -L -o data/kawasaki_consult.xlsx \
     https://www.city.kawasaki.jp/280/cmsfiles/contents/0000031/31314/R6nenpoudata.xlsx

   # Excel→CSV（1相談件数シートを利用）
   uv run python scripts/convert_excel_to_csv.py \
     data/kawasaki_consult.xlsx data/kawasaki_consult_raw.csv --sheet "1相談件数"

   # 必要部分だけ抽出して tidy 化
   uv run python - <<'PY'
   import pandas as pd

   era_to_year = {
       "H27": 2015,
       "H28": 2016,
       "H29": 2017,
       "H30": 2018,
       "R1": 2019,
       "R2": 2020,
       "R3": 2021,
       "R4": 2022,
       "R5": 2023,
       "R6": 2024,
   }

   raw = pd.read_csv('data/kawasaki_consult_raw.csv')
   cleaned = raw.iloc[:2]  # 全体件数 + 不当請求件数
   melted = cleaned.melt(id_vars=['区分'], var_name='era', value_name='相談件数')
   melted['year'] = melted['era'].map(era_to_year)
   melted = melted.dropna(subset=['year', '相談件数'])
   melted.to_csv('data/kawasaki_consult_cases.csv', index=False)
   PY
   ```

3. **DBへ投入** (`DATABASE_URL` を上書きしたい場合は `--database-url` を指定)
   ```bash
   cd apps/python-backend
   uv run python scripts/load_csv.py \
     population population_by_ward_2023 \
     data/population_by_ward_2023.csv "人口（区別）2023" "川崎市人口統計" \
     --year 2023 --index ward_code year

   uv run python scripts/load_csv.py \
     consumer_affairs kawasaki_consult_cases \
     data/kawasaki_consult_cases.csv "川崎市消費者相談" "相談件数の年度推移" \
     --index year 区分
   ```

4. **dataset_id の確認**（フロント/バッチで利用）
   ```bash
   cd apps/python-backend
   sqlite3 data/city_data.db "select id, slug, name from datasets order by id;"
   ```

## ステップ2: 対話モード（チャット + ダッシュボード + フィードバック）
1. **バックエンド起動**
   ```bash
   cd apps/python-backend
   INTERFACE_TYPE=restapi PYTHONPATH=src uv run python -m clean_interfaces.main
   ```
2. **フロント起動と datasetId の紐付け**
   - `apps/frontend/src/data/dashboardPresets.ts` の `datasetOptions` に、上で確認した `dataset_id` を文字列でセット（例: `id: '1'` を人口、`id: '2'` を相談データに割当）。
   - ルートで `npm run --workspace frontend dev -- --host --port 3000` を起動。
3. **/interactive での動作確認**
   - データセットを選択し、「2023年の区別人口の平均は？」や「消費者相談の件数が最も多い年度は？」などを送信。
   - レスポンスがダッシュボードに反映され、エラーでバックエンドが落ちないことを確認。
4. **フィードバック送信**
   - 応答カードの 👍/👎 ボタンにコメントを添えて送信し、状態メッセージが「高評価を受け付けました」等に変わることを確認。

## ステップ3: バッチ探索（実験作成→ワーカー→レビュー→フィードバック）
1. **実験作成**
   - フロント `/experiments` で「やりたいこと」を入力し、人口・相談データの `dataset_id` を選択して作成。
   - もしくは API: `POST /experiments` に `{ "goal_description": "相談件数の急増パターンを調べたい", "dataset_ids": [<人口ID>, <相談ID>] }` を送信。
2. **ワーカー実行**
   ```bash
   cd apps/python-backend
   PYTHONPATH=src uv run python -m clean_interfaces.worker
   ```
   `pending` ジョブが `completed/failed` に遷移し、`insight_candidates` が生成されるまで待機。
3. **インサイトレビュー + フィードバック**
   - フロント `/experiments/<id>` で候補を確認し、「採用/却下」やコメントを送信。
   - 必要なら `POST /insights/{candidate_id}/feedback` でも確認。

## ステップ4: スクリーンショット（任意）
- 対話ダッシュボードやバッチ詳細画面を開いた状態で OS/ブラウザのキャプチャを取得し、運用ドキュメントに添付すると再現が容易になります。
