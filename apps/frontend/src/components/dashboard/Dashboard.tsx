import type { DashboardData } from '../../data/dashboardPresets';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { ChartPlaceholder } from './ChartPlaceholder';
import type { MetricCardProps } from './MetricCard';
import { MetricCard } from './MetricCard';

type DashboardProps = {
    data: DashboardData;
    lastInsight?: string;
    onRefresh?: () => void;
};

function InsightRow({
    title,
    signal,
    recommendation
}: DashboardData['insights'][number]): JSX.Element {
    return (
        <tr>
            <td>{title}</td>
            <td>{signal}</td>
            <td>{recommendation}</td>
        </tr>
    );
}

export function Dashboard({ data, lastInsight, onRefresh }: DashboardProps): JSX.Element {
    return (
        <section aria-label="ダッシュボードビュー" className="dashboard-grid">
            <Card className="dashboard__panel dashboard__panel--hero">
                <CardHeader>
                    <CardTitle className="dashboard__headline">
                        {data.headline}
                    </CardTitle>
                    <CardDescription>
                        {data.datasetLabel} / {data.timeframe}
                    </CardDescription>
                </CardHeader>
                <CardContent className="dashboard__summary">
                    <div className="dashboard__callout">{data.statsCallout}</div>
                    <div className="dashboard__summary-actions">
                        <Badge variant="accent">リアルタイム更新</Badge>
                        <Badge variant="success">分析OK</Badge>
                        <Button variant="secondary" size="sm" onClick={onRefresh}>
                            KPIを再計算
                        </Button>
                    </div>
                    {lastInsight ? (
                        <div className="dashboard__note" aria-live="polite">
                            最新のAI応答: {lastInsight}
                        </div>
                    ) : null}
                </CardContent>
            </Card>

            <div className="dashboard__metrics">
                {data.metrics.map((metric: MetricCardProps) => (
                    <MetricCard key={metric.label} {...metric} />
                ))}
            </div>

            <div className="two-column">
                {data.charts.map((chart) => (
                    <ChartPlaceholder key={chart.title} {...chart} />
                ))}
            </div>

            <Card className="dashboard__panel">
                <CardHeader>
                    <CardTitle>インサイトのリスト</CardTitle>
                    <CardDescription>AIが抽出したシグナルと推奨アクション</CardDescription>
                </CardHeader>
                <CardContent>
                    <table className="list-table">
                        <thead>
                            <tr>
                                <th>テーマ</th>
                                <th>シグナル</th>
                                <th>推奨アクション</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.insights.map((row) => (
                                <InsightRow key={row.title} {...row} />
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>

            <Card className="dashboard__panel dashboard__panel--suggestions">
                <CardHeader>
                    <CardTitle>おすすめの後続分析</CardTitle>
                    <CardDescription>チャットに貼り付けてすぐに質問できます</CardDescription>
                </CardHeader>
                <CardContent className="suggestion-row">
                    {data.suggestions.map((suggestion) => (
                        <Badge key={suggestion}>{suggestion}</Badge>
                    ))}
                </CardContent>
            </Card>
        </section>
    );
}
