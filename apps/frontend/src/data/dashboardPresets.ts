export type Trend = 'up' | 'down' | 'steady';

export type DashboardMetric = {
    label: string;
    value: string;
    helper: string;
    trend?: Trend;
    emphasis?: string;
};

export type ChartDescriptor = {
    title: string;
    description: string;
    callout: string;
};

export type InsightRow = {
    title: string;
    signal: string;
    recommendation: string;
};

export type DashboardData = {
    datasetId: string;
    datasetLabel: string;
    timeframe: string;
    headline: string;
    statsCallout: string;
    metrics: DashboardMetric[];
    charts: ChartDescriptor[];
    insights: InsightRow[];
    suggestions: string[];
};

export const datasetOptions = [
    {
        id: 'population-trend',
        label: '人口・世帯動態',
        helper: '年齢階層別の推移や転入出を即時把握'
    },
    {
        id: 'mobility',
        label: '交通・モビリティ',
        helper: '時間帯別の渋滞／回遊トレンドを分析'
    },
    {
        id: 'energy',
        label: 'エネルギー・環境',
        helper: 'ピーク需要と再エネ寄与をリアルタイム追跡'
    }
];

export const dashboardPresets: Record<string, DashboardData> = {
    'population-trend': {
        datasetId: 'population-trend',
        datasetLabel: '人口・世帯動態',
        timeframe: '2024年4月〜2025年1月',
        headline:
            '主要区で子育て世帯の転入超過が継続。夜間人口も緩やかに増加。',
        statsCallout:
            '3ヶ月連続で30代前半の転入が増。保育・教育需要の先行指標として注視。',
        metrics: [
            {
                label: '転入超過率',
                value: '+1.8%',
                helper: '前月比 +0.3pt / 主要3区平均',
                trend: 'up',
                emphasis: '住宅支援策が寄与'
            },
            {
                label: '夜間人口推移',
                value: '+0.9%',
                helper: '週次移動平均',
                trend: 'steady',
                emphasis: '徐々に持ち直し'
            },
            {
                label: '出生数速報',
                value: '1,241 件',
                helper: '先月比 +4.1% / 医療機関連携',
                trend: 'up'
            },
            {
                label: '転出先トップ',
                value: '首都圏ベッドタウン',
                helper: '通勤30-50分圏への流出',
                trend: 'down',
                emphasis: '雇用施策の効果検証'
            }
        ],
        charts: [
            {
                title: '年齢階層別の転入出推移',
                description: '20-39歳の流入が増加。学生層は横ばい。',
                callout: '市内西部で子育て世帯の回遊が増え、夜間滞在が1.1倍'
            },
            {
                title: '世帯属性ごとの需給予測',
                description: '保育需要と小学校入学者数の先行指標',
                callout: '来期に向けた保育枠拡充が必要なエリアを提案'
            }
        ],
        insights: [
            {
                title: '子育て世帯の移動',
                signal: '転入が3ヶ月連続で増加。共働き世帯比率も上昇。',
                recommendation: '保育枠の即応確保と学童の開設計画を優先'
            },
            {
                title: '夜間人口',
                signal: '主要駅周辺で夜間滞在が増。飲食関連の需要増に連動。',
                recommendation: '公共交通の増便と安全対策をセットで検討'
            },
            {
                title: '住宅需要',
                signal: '西部の住宅着工件数が前年同期比+6%。',
                recommendation: '住環境改善策と子育て支援のPRを継続'
            }
        ],
        suggestions: [
            '子育て支援施策の効果を可視化',
            '夜間人口の増加要因を特定',
            '教育需要の先行指標を自動生成'
        ]
    },
    mobility: {
        datasetId: 'mobility',
        datasetLabel: '交通・モビリティ',
        timeframe: '直近7日間と週次比較',
        headline: '港湾エリアで18:00-19:00に出庫が集中し渋滞度が1.3倍。',
        statsCallout:
            'イベント退場と物流搬出が重なる時間帯に信号制御と増便で緩和余地あり。',
        metrics: [
            {
                label: '平均遅延率',
                value: '5.8%',
                helper: '主要交差点の平均遅延',
                trend: 'steady',
                emphasis: '許容範囲'
            },
            {
                label: 'ピーク渋滞指数',
                value: '1.3x',
                helper: '先週比 +0.1 / 港湾エリア',
                trend: 'up'
            },
            {
                label: '公共交通利用',
                value: '+6.2%',
                helper: 'イベント開催日の増加率',
                trend: 'up'
            },
            {
                label: '回遊距離中央値',
                value: '2.4km',
                helper: '市内回遊データより',
                trend: 'steady'
            }
        ],
        charts: [
            {
                title: '交通量トレンド',
                description: '主要交差点の7日間推移と混雑予測',
                callout: 'ピーク帯は18:00-19:00。信号制御案を提示。'
            },
            {
                title: '回遊ヒートマップ',
                description: 'イベント時の移動集中エリア',
                callout: '夜間回遊が週次+8%。深夜交通の増便検討。'
            }
        ],
        insights: [
            {
                title: '港湾エリア',
                signal: '夜間人流が週次+8%上昇、物流とイベントが重なる日が多い。',
                recommendation: '深夜交通の増便と誘導案内を推奨'
            },
            {
                title: 'Innovation Park',
                signal: '滞在時間が平均+12分、屋外イベントが継続。',
                recommendation: '無料Wi-Fi整備と回遊ルート表示を追加'
            },
            {
                title: '主要幹線',
                signal: '気象影響でピークが前倒し。',
                recommendation: '信号制御の自動最適化を設定'
            }
        ],
        suggestions: [
            'ピーク時間の増便シナリオを比較',
            '渋滞要因ごとの寄与率を算出',
            'イベント日を考慮した回遊増便案を生成'
        ]
    },
    energy: {
        datasetId: 'energy',
        datasetLabel: 'エネルギー・環境',
        timeframe: '当日と前日比較 / 週次平均',
        headline: '再エネ比率が最大32%。夕方ピークは-1.2%で抑制。',
        statsCallout: '節電キャンペーンと蓄電池シフトによりピーク抑制が継続。',
        metrics: [
            {
                label: '需要ピーク時刻',
                value: '18:30',
                helper: '前日比較 -6分',
                trend: 'down'
            },
            {
                label: '再エネ比率',
                value: '32%',
                helper: '週次平均 +2.4pt',
                trend: 'up',
                emphasis: '太陽光寄与増'
            },
            {
                label: '節電参加率',
                value: '18%',
                helper: 'DRプログラム参加世帯',
                trend: 'up'
            },
            {
                label: 'CO₂削減',
                value: '-4.2%',
                helper: '先週比 / kg-CO₂換算',
                trend: 'up'
            }
        ],
        charts: [
            {
                title: 'エネルギー需要プロファイル',
                description: '再エネ比率とピークカット状況',
                callout: '太陽光寄与が最大32%。需要抑制が効果的。'
            },
            {
                title: '需要抑制の時間帯',
                description: 'DR参加と効果量の推移',
                callout: '夕方の抑制でCO₂換算-4.2%。さらなる参加を促進。'
            }
        ],
        insights: [
            {
                title: 'ピークシフト',
                signal: '夕方ピークが前倒し、気温影響が顕著。',
                recommendation: '蓄電池シフトとDRインセンティブを強化'
            },
            {
                title: '再エネ活用',
                signal: '日中の余剰電力を夜間に活用できる余地あり。',
                recommendation: '蓄電池とEV充電の分散制御を提案'
            },
            {
                title: '節電効果',
                signal: '広報キャンペーン後も参加率が維持。',
                recommendation: 'エリア別の参加率差を可視化し重点周知'
            }
        ],
        suggestions: [
            '需要ピークを自動検知して警告',
            '節電キャンペーンの効果を比較',
            '再エネ比率が高い時間帯を通知'
        ]
    }
};
