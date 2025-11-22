import { Badge } from '../ui/badge';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from '../ui/card';

function trendClass(trend: 'up' | 'down' | 'steady'): string {
    if (trend === 'down') return 'metric-card__trend metric-card__trend--down';
    if (trend === 'steady')
        return 'metric-card__trend metric-card__trend--steady';
    return 'metric-card__trend';
}

type MetricCardProps = {
    label: string;
    value: string;
    helper: string;
    trend?: 'up' | 'down' | 'steady';
    emphasis?: string;
};

export function MetricCard({
    label,
    value,
    helper,
    trend = 'up',
    emphasis
}: MetricCardProps): JSX.Element {
    return (
        <Card className="metric-card">
            <CardHeader>
                <CardTitle>{label}</CardTitle>
                <CardDescription>{helper}</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="metric-card__value">{value}</div>
                {emphasis ? <Badge variant="accent">{emphasis}</Badge> : null}
                <div className={trendClass(trend)}>
                    {trend === 'up' && '↗ 成長傾向'}
                    {trend === 'down' && '↘ 要注意'}
                    {trend === 'steady' && '→ 安定'}
                </div>
            </CardContent>
        </Card>
    );
}
