import type { buildCategoryTable } from '../../lib/dataSource';

type SummaryRow = ReturnType<typeof buildCategoryTable>[number];

type DataSummaryTableProps = {
    rows: SummaryRow[];
    metric: string;
};

export function DataSummaryTable({
    rows,
    metric
}: DataSummaryTableProps): JSX.Element {
    if (!rows.length) {
        return (
            <p className="data-table__empty">条件に合うデータがありません。</p>
        );
    }

    return (
        <table className="data-table" aria-label={`${metric} の集計テーブル`}>
            <thead>
                <tr>
                    <th scope="col">カテゴリ / セグメント</th>
                    <th scope="col">合計</th>
                    <th scope="col">平均</th>
                    <th scope="col">直近値</th>
                </tr>
            </thead>
            <tbody>
                {rows.map((row) => (
                    <tr key={row.key}>
                        <td>{row.key}</td>
                        <td>
                            {row.total} {row.unit}
                        </td>
                        <td>
                            {row.average} {row.unit}
                        </td>
                        <td>
                            {row.latest ?? '―'} {row.unit}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
