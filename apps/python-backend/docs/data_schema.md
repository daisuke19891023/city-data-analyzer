# データ基盤スキーマ

Python バックエンドでは SQLAlchemy で以下のテーブルを作成します。`DATABASE_URL` を未設定の場合は `./data/city_data.db` (SQLite) が利用されます。

## テーブル概要

- **open_data_categories**: 川崎市オープンデータのカテゴリ。初期化時に12件がシードされます。
- **datasets**: CSV などで取り込んだデータセットのメタ情報（カテゴリ、説明、年度など）。
- **dataset_columns**: データセットのカラム定義。`is_index` でインデックス用途の列をマーキングします。
- **dataset_records**: 1レコードごとの JSON 本文と `index_cols`（年度や区コードなどのインデックス列のみを抽出した JSON）。`dataset_id + row_hash` のユニーク制約で冪等に投入できます。
- **analysis_queries**: インタラクティブ分析 API の問い合わせ履歴（question/query_spec/result_summary/provider/model）。
- **dataset_files**: 取り込み済みファイルのパスとファイル種別。

## 初期カテゴリ (12件)

| slug | name |
| --- | --- |
| population | 人口・世帯 |
| economy | 経済・雇用 |
| welfare | 福祉 |
| health | 健康 |
| environment | 環境 |
| education | 教育 |
| culture | 文化・スポーツ |
| safety | 防犯・消防 |
| infrastructure | 都市基盤 |
| transport | 交通 |
| childcare | 子育て |
| industry | 産業振興 |

## カラム・インデックスの方針

- 数値判定: 全行が数値の場合は `data_type="number"`、それ以外は `text`。
- インデックス列: `--index` で指定された列、またはカラム名に `year/年度/month/code/コード` を含む列を自動で `is_index=True` に設定し、`index_cols` に抽出します。
- レコード重複防止: JSON 本文のソート済みダンプから SHA256 ハッシュを計算し、既存ハッシュと重複する行はスキップします。

## ER 図 (テキスト)

```
open_data_categories 1 -- * datasets 1 -- * dataset_columns
                             |            \
                             |             * dataset_records
                             * analysis_queries
                             * dataset_files
```
