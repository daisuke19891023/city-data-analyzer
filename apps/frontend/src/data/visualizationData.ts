export type DatasetRecord = {
    datasetId: string;
    date: string; // ISO format (YYYY-MM-DD)
    category: string;
    segment: string;
    metric: string;
    value: number;
    unit: string;
    note?: string;
};

export type DatasetDefinition = {
    id: string;
    label: string;
    helper: string;
    description: string;
    defaultMetric: string;
    availableMetrics: string[];
    categories: string[];
    segments: string[];
    records: DatasetRecord[];
};

const months = [
    '2024-04-01',
    '2024-05-01',
    '2024-06-01',
    '2024-07-01',
    '2024-08-01',
    '2024-09-01',
    '2024-10-01',
    '2024-11-01',
    '2024-12-01',
    '2025-01-01'
];

function buildSeries(
    datasetId: string,
    metric: string,
    category: string,
    segment: string,
    values: number[],
    unit: string
): DatasetRecord[] {
    return values.map((value, index) => ({
        datasetId,
        date: months[index % months.length],
        category,
        segment,
        metric,
        value,
        unit,
        note: 'ダミーデータ'
    }));
}

export const visualizationDatasets: Record<string, DatasetDefinition> = {
    'population-trend': {
        id: 'population-trend',
        label: '人口・世帯動態',
        helper: '年齢階層別の推移や転入出を即時把握',
        description:
            '転入超過や夜間人口の変化を追跡し、子育て施策や住宅需要の手がかりを提供します。',
        defaultMetric: '転入超過指数',
        availableMetrics: ['転入超過指数', '夜間人口指数'],
        categories: ['中心市街地', '西部住宅地', '東部ニュータウン'],
        segments: ['子育て世帯', '単身', '高齢世帯'],
        records: [
            ...buildSeries(
                'population-trend',
                '転入超過指数',
                '中心市街地',
                '子育て世帯',
                [138, 142, 145, 149, 153, 158, 162, 164, 166, 170],
                '指数'
            ),
            ...buildSeries(
                'population-trend',
                '転入超過指数',
                '西部住宅地',
                '子育て世帯',
                [120, 125, 130, 134, 136, 139, 141, 143, 145, 148],
                '指数'
            ),
            ...buildSeries(
                'population-trend',
                '転入超過指数',
                '東部ニュータウン',
                '単身',
                [102, 104, 106, 110, 113, 118, 120, 123, 125, 128],
                '指数'
            ),
            ...buildSeries(
                'population-trend',
                '夜間人口指数',
                '中心市街地',
                '単身',
                [109, 111, 112, 114, 116, 118, 120, 119, 121, 122],
                '指数'
            ),
            ...buildSeries(
                'population-trend',
                '夜間人口指数',
                '西部住宅地',
                '高齢世帯',
                [98, 99, 99, 100, 101, 101, 102, 103, 104, 104],
                '指数'
            )
        ]
    },
    mobility: {
        id: 'mobility',
        label: '交通・モビリティ',
        helper: '時間帯別の渋滞／回遊トレンドを分析',
        description:
            '主要交差点の交通量や回遊距離をモニタリングし、イベント混雑の緩和策を検討します。',
        defaultMetric: '平均遅延率',
        availableMetrics: ['平均遅延率', 'ピーク渋滞指数'],
        categories: ['港湾エリア', '駅前エリア', '産業道路'],
        segments: ['平日', '休日'],
        records: [
            ...buildSeries(
                'mobility',
                '平均遅延率',
                '港湾エリア',
                '平日',
                [6.2, 6.0, 6.1, 6.4, 6.5, 6.8, 6.7, 6.6, 6.4, 6.3],
                '%'
            ),
            ...buildSeries(
                'mobility',
                '平均遅延率',
                '駅前エリア',
                '休日',
                [5.4, 5.5, 5.3, 5.2, 5.1, 5.0, 5.4, 5.6, 5.5, 5.3],
                '%'
            ),
            ...buildSeries(
                'mobility',
                'ピーク渋滞指数',
                '産業道路',
                '平日',
                [1.12, 1.15, 1.18, 1.19, 1.2, 1.25, 1.23, 1.21, 1.2, 1.18],
                'x'
            ),
            ...buildSeries(
                'mobility',
                'ピーク渋滞指数',
                '港湾エリア',
                '休日',
                [1.05, 1.1, 1.12, 1.15, 1.16, 1.17, 1.18, 1.16, 1.14, 1.12],
                'x'
            )
        ]
    },
    energy: {
        id: 'energy',
        label: 'エネルギー・環境',
        helper: 'ピーク需要と再エネ寄与をリアルタイム追跡',
        description:
            'ピーク需要と再エネ比率を合わせて可視化し、節電施策の効果を即時に検証します。',
        defaultMetric: '再エネ比率',
        availableMetrics: ['再エネ比率', '需要ピーク削減量'],
        categories: ['住宅', 'オフィス', '公共施設'],
        segments: ['平日', '休日'],
        records: [
            ...buildSeries(
                'energy',
                '再エネ比率',
                '住宅',
                '平日',
                [28, 29, 29, 30, 31, 31, 32, 33, 32, 33],
                '%'
            ),
            ...buildSeries(
                'energy',
                '再エネ比率',
                'オフィス',
                '平日',
                [24, 25, 25, 26, 27, 27, 28, 28, 29, 29],
                '%'
            ),
            ...buildSeries(
                'energy',
                '需要ピーク削減量',
                '公共施設',
                '休日',
                [3.1, 3.2, 3.0, 3.3, 3.4, 3.5, 3.6, 3.6, 3.7, 3.8],
                'MW'
            ),
            ...buildSeries(
                'energy',
                '需要ピーク削減量',
                '住宅',
                '平日',
                [2.4, 2.5, 2.6, 2.6, 2.7, 2.8, 2.9, 2.9, 3.0, 3.0],
                'MW'
            )
        ]
    }
};

export const visualizationDatasetOptions = Object.values(visualizationDatasets).map(
    ({ id, label, helper, defaultMetric }) => ({
        id,
        label,
        helper,
        defaultMetric
    })
);
