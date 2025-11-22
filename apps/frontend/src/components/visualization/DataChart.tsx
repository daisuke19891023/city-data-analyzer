import type { ChartPoint } from '../../lib/dataSource';

type DataChartProps = {
    title: string;
    metric: string;
    series: ChartPoint[];
    unit?: string;
};

export function DataChart({ title, metric, series, unit }: DataChartProps): JSX.Element {
    const maxValue = Math.max(...series.map((point) => point.value), 1);
    return (
        <div className="data-chart">
            <div className="data-chart__header">
                <div>
                    <p className="data-chart__eyebrow">{metric}</p>
                    <h3 className="data-chart__title">{title}</h3>
                </div>
                <p className="data-chart__helper">
                    時系列に集計したダミーデータを描画しています。
                </p>
            </div>
            <div className="data-chart__bars" role="img" aria-label={`${metric} の推移`}>
                {series.map((point) => (
                    <div key={point.label} className="data-chart__bar">
                        <div
                            className="data-chart__bar-fill"
                            style={{ height: `${Math.max((point.value / maxValue) * 100, 8)}%` }}
                            aria-label={`${point.label} の値 ${point.value}${unit ?? ''}`}
                        />
                        <span className="data-chart__bar-label">{point.label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
