import {
    visualizationDatasetOptions,
    visualizationDatasets
} from '../data/visualizationData';
import type { DatasetDefinition, DatasetRecord } from '../data/visualizationData';

export type FilterState = {
    timeRange: '6m' | '12m' | '24m' | 'all';
    category: 'all' | string;
    segment: 'all' | string;
    metric: string;
};

export type ChatIntent = {
    updatedFilters?: Partial<FilterState>;
    notes: string[];
};

export type ChartPoint = {
    label: string;
    value: number;
};

export type DatasetSummary = {
    id: string;
    label: string;
    helper: string;
    defaultMetric: string;
};

function getImportMetaEnv(): Record<string, string | undefined> | undefined {
    return (globalThis as { __IMPORT_META_ENV__?: Record<string, string | undefined> })
        .__IMPORT_META_ENV__;
}

function getEnv(key: string): string | undefined {
    const viteEnv = getImportMetaEnv();
    if (viteEnv?.[key] !== undefined) return viteEnv[key];
    if (typeof process !== 'undefined') {
        return process.env[key];
    }
    return undefined;
}

export function resolveDataMode(): 'dummy' | 'api' {
    const mode = (getEnv('VITE_DATA_MODE') || getEnv('DATA_MODE') || 'dummy')
        .toString()
        .toLowerCase();
    return mode === 'api' ? 'api' : 'dummy';
}

export const dataMode = resolveDataMode();

function resolveDataApiBase(): string {
    return (
        getEnv('VITE_DATA_API_BASE') ||
        getEnv('DATA_API_BASE') ||
        getEnv('VITE_PY_BACKEND_URL') ||
        getEnv('PY_BACKEND_URL') ||
        'http://localhost:8000'
    ).replace(/\/$/, '');
}

async function fetchFromApi<T>(path: string): Promise<T | null> {
    if (typeof fetch === 'undefined') return null;
    try {
        const response = await fetch(`${resolveDataApiBase()}${path}`);
        if (!response.ok) return null;
        return (await response.json()) as T;
    } catch (error) {
        console.warn('データAPI呼び出しに失敗しました', error);
        return null;
    }
}

export async function getDatasetSummaries(): Promise<DatasetSummary[]> {
    if (dataMode === 'api') {
        const payload = await fetchFromApi<DatasetSummary[]>('/datasets');
        if (payload && payload.length > 0) return payload;
    }
    return visualizationDatasetOptions;
}

export async function getDatasetData(
    datasetId: string
): Promise<DatasetDefinition | null> {
    if (dataMode === 'api') {
        const payload = await fetchFromApi<DatasetDefinition>(
            `/datasets/${datasetId}/records`
        );
        if (payload && payload.records?.length) return payload;
    }
    return visualizationDatasets[datasetId] ?? null;
}

function isWithinRange(date: Date, timeRange: FilterState['timeRange']): boolean {
    if (timeRange === 'all') return true;
    const now = new Date('2025-01-15');
    const months = { '6m': 6, '12m': 12, '24m': 24 }[timeRange];
    const boundary = new Date(now);
    boundary.setMonth(boundary.getMonth() - months);
    return date >= boundary;
}

export function applyFilters(
    records: DatasetRecord[],
    filters: FilterState
): DatasetRecord[] {
    return records.filter((record) => {
        const recordDate = new Date(record.date);
        const inRange = isWithinRange(recordDate, filters.timeRange);
        const inCategory =
            filters.category === 'all' || record.category === filters.category;
        const inSegment = filters.segment === 'all' || record.segment === filters.segment;
        const inMetric = record.metric === filters.metric;
        return inRange && inCategory && inSegment && inMetric;
    });
}

export function buildMonthlySeries(records: DatasetRecord[]): ChartPoint[] {
    const buckets = new Map<string, number>();
    records.forEach((record) => {
        const month = record.date.slice(0, 7);
        buckets.set(month, (buckets.get(month) ?? 0) + record.value);
    });
    return Array.from(buckets.entries())
        .sort(([a], [b]) => (a < b ? -1 : 1))
        .map(([label, value]) => ({ label, value: Number(value.toFixed(2)) }));
}

export function buildCategoryTable(
    records: DatasetRecord[],
    metric: string
): Array<{
    key: string;
    total: number;
    average: number;
    latest?: number;
    unit: string;
}> {
    const groups = new Map<string, DatasetRecord[]>();
    records.forEach((record) => {
        const key = `${record.category} / ${record.segment}`;
        groups.set(key, [...(groups.get(key) ?? []), record]);
    });

    return Array.from(groups.entries()).map(([key, rows]) => {
        const total = rows.reduce((sum, row) => sum + row.value, 0);
        const average = total / rows.length;
        const latestRow = [...rows].sort((a, b) => (a.date < b.date ? 1 : -1))[0];
        return {
            key,
            total: Number(total.toFixed(2)),
            average: Number(average.toFixed(2)),
            latest: latestRow?.value,
            unit: latestRow?.unit ?? metric
        };
    });
}

export function summarizeRecords(
    records: DatasetRecord[],
    metric: string
): { headline: string; detail: string } {
    if (!records.length) {
        return {
            headline: '該当するレコードがありません',
            detail: 'フィルター条件を緩めるとトレンドを確認できます。'
        };
    }
    const values = records.map((record) => record.value);
    const average =
        values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
    const latest = [...records].sort((a, b) => (a.date < b.date ? 1 : -1))[0];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const change = latest.value - values[0];
    const trend = change >= 0 ? '増加傾向' : '減少傾向';
    const headline = `${metric}は${trend}で、直近値は ${latest.value}${latest.unit}`;
    const detail = `平均 ${average.toFixed(1)}${latest.unit}、最小 ${min}${latest.unit}、最大 ${max}${latest.unit}。初期値との差は ${change.toFixed(1)}${latest.unit} です。`;
    return { headline, detail };
}

function detectTimeRange(question: string): FilterState['timeRange'] | undefined {
    const q = question.replace(/\s+/g, '');
    if (/(直近|最近)?6(か|ヶ|ケ)月|半年/.test(q)) return '6m';
    if (/(直近|最近)?1(2|２)(か|ヶ|ケ)月|1年|１年/.test(q)) return '12m';
    if (/(直近|最近)?2(4|４)(か|ヶ|ケ)月|2年|２年/.test(q)) return '24m';
    if (/全期間|全部|すべて|すべての期間|all/i.test(q)) return 'all';
    return undefined;
}

function detectMetric(question: string, dataset: DatasetDefinition): string | undefined {
    return dataset.availableMetrics.find((metric) => question.includes(metric));
}

function detectCategory(
    question: string,
    dataset: DatasetDefinition
): string | undefined {
    return dataset.categories.find((category) => question.includes(category));
}

function detectSegment(question: string, dataset: DatasetDefinition): string | undefined {
    return dataset.segments.find((segment) => question.includes(segment));
}

export function deriveChatIntent(
    question: string,
    dataset: DatasetDefinition,
    current: FilterState
): ChatIntent {
    const updates: Partial<FilterState> = {};
    const notes: string[] = [];

    const timeRange = detectTimeRange(question);
    if (timeRange && timeRange !== current.timeRange) {
        updates.timeRange = timeRange;
        notes.push(`期間を${timeRange}に変更しました。`);
    }

    const metric = detectMetric(question, dataset);
    if (metric && metric !== current.metric) {
        updates.metric = metric;
        notes.push(`指標を「${metric}」に切り替えました。`);
    }

    const category = detectCategory(question, dataset);
    if (category && category !== current.category) {
        updates.category = category;
        notes.push(`カテゴリを「${category}」に絞り込みました。`);
    }

    const segment = detectSegment(question, dataset);
    if (segment && segment !== current.segment) {
        updates.segment = segment;
        notes.push(`セグメントを「${segment}」に絞り込みました。`);
    }

    return { updatedFilters: Object.keys(updates).length ? updates : undefined, notes };
}

export function answerQuestionFromData(
    question: string,
    dataset: DatasetDefinition,
    filtered: DatasetRecord[]
): string {
    if (!filtered.length) {
        return `${dataset.label} では条件に合うデータが見つかりませんでした。フィルターを調整してください。`;
    }
    const { headline, detail } = summarizeRecords(filtered, filtered[0].metric);
    const dominantCategory = [...
        filtered.reduce((map, record) => {
            map.set(record.category, (map.get(record.category) ?? 0) + record.value);
            return map;
        }, new Map<string, number>()).entries()
    ]
        .sort((a, b) => (a[1] > b[1] ? -1 : 1))[0]?.[0];

    const cue = dominantCategory
        ? `${dominantCategory}の寄与が最も大きく、質問「${question}」に対して重点領域として示しています。`
        : '';

    return `${headline}。${detail} ${cue}`.trim();
}
