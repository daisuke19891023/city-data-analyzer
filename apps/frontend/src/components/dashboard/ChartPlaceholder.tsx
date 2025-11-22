import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from '../ui/card';

export type ChartPlaceholderProps = {
    title: string;
    description: string;
    callout: string;
};

export function ChartPlaceholder({
    title,
    description,
    callout
}: ChartPlaceholderProps): JSX.Element {
    return (
        <Card className="chart-card">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="chart-placeholder">チャートをここに追加</div>
                <div className="chart-legend">{callout}</div>
            </CardContent>
        </Card>
    );
}
