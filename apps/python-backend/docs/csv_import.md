# CSV 取り込みスクリプトの使い方

`scripts/load_csv.py` は CSV を読み込み、カテゴリとデータセットを自動作成して `dataset_columns` / `dataset_records` に投入します。行の JSON をソートしてハッシュ化するため、同じ CSV を複数回実行しても重複投入されません。

## 使い方

```bash
cd apps/python-backend
uv run python scripts/load_csv.py population population_by_ward_2023 data/population.csv "人口（区別）2023" "川崎市人口統計" --year 2023 --index ward_code year
```

引数:

- `category_slug`: カテゴリスラグ（例: `population`）
- `dataset_slug`: データセットスラグ（例: `population_by_ward_2023`）
- `csv_path`: CSV ファイルパス
- `dataset_name`: 表示用名称
- `description`: 説明文
- `--year`: 任意。データセットの年度
- `--index`: 任意。インデックス列として扱うカラム名をスペース区切りで指定
- `--database-url`: 任意。`DATABASE_URL` を上書きしたい場合に指定

## インデックス抽出ルール

- `--index` で指定した列を最優先で `is_index=True` に設定
- 指定がない場合でも、カラム名に `year/年度/month/code/コード` を含む列を自動でインデックス化し、`index_cols` として JSON に保存

## 失敗時のロールバック

スクリプトは `session_scope()` を使用しており、挿入時に例外が発生した場合は自動でロールバックされます。重複行はユニーク制約違反として検知され、既存データを壊さずにスキップされます。
