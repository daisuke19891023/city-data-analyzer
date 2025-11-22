export type InteractiveAnalysisRequest = {
    question: string;
    datasetId: string;
    provider: string;
    model: string;
};

export type InteractiveAnalysisResponse = {
    summary: string;
    stats: {
        totalRecords: number;
        primaryMetric: string;
        positiveRate?: string;
    };
    insight: string;
    datasetId: string;
    fallback: boolean;
};

const fallbackInsight: InteractiveAnalysisResponse = {
    summary:
        'バックエンドの応答が利用できないため、ダッシュボードはサンプルデータで更新しました。',
    stats: {
        totalRecords: 12400,
        primaryMetric: 'サンプルデータで要約'
    },
    insight:
        '人口推移と移動パターンをもとに、夜間ピーク前後のアクションを提案します。',
    datasetId: 'population-trend',
    fallback: true
};

function resolveBackendUrl(): string {
    const base =
        (globalThis as { VITE_PY_BACKEND_URL?: string }).VITE_PY_BACKEND_URL ||
        (globalThis as { __PY_BACKEND_URL__?: string }).__PY_BACKEND_URL__ ||
        (typeof process !== 'undefined'
            ? process.env.VITE_PY_BACKEND_URL || process.env.PY_BACKEND_URL
            : undefined) ||
        'http://localhost:8000';
    return `${base.replace(/\/$/, '')}/dspy/interactive`;
}

export async function runInteractiveAnalysis(
    payload: InteractiveAnalysisRequest
): Promise<InteractiveAnalysisResponse> {
    try {
        const response = await fetch(resolveBackendUrl(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: payload.question,
                dataset_id: payload.datasetId,
                provider: payload.provider,
                model: payload.model
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to reach backend: ${response.status}`);
        }

        const json =
            (await response.json()) as Partial<InteractiveAnalysisResponse>;
        return {
            summary: json.summary || 'バックエンド応答を受信しました。',
            stats: json.stats || fallbackInsight.stats,
            insight: json.insight || json.summary || fallbackInsight.insight,
            datasetId: json.datasetId || payload.datasetId,
            fallback: false
        };
    } catch (error) {
        console.warn('Interactive analysis fallback', error);
        return {
            ...fallbackInsight,
            datasetId: payload.datasetId,
            fallback: true
        };
    }
}
