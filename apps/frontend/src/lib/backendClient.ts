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
    analysisId?: number;
    programVersion?: string;
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

function resolveBackendBase(): string {
    return (
        (globalThis as { VITE_PY_BACKEND_URL?: string }).VITE_PY_BACKEND_URL ||
        (globalThis as { __PY_BACKEND_URL__?: string }).__PY_BACKEND_URL__ ||
        (typeof process !== 'undefined'
            ? process.env.VITE_PY_BACKEND_URL || process.env.PY_BACKEND_URL
            : undefined) ||
        'http://localhost:8000'
    ).replace(/\/$/, '');
}

export async function runInteractiveAnalysis(
    payload: InteractiveAnalysisRequest
): Promise<InteractiveAnalysisResponse> {
    try {
        const response = await fetch(
            `${resolveBackendBase()}/dspy/interactive`,
            {
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
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to reach backend: ${response.status}`);
        }

        const json = (await response.json()) as Record<string, unknown>;
        return {
            summary:
                (json.summary as string | undefined) ||
                'バックエンド応答を受信しました。',
            stats:
                (json.stats as InteractiveAnalysisResponse['stats']) ||
                fallbackInsight.stats,
            insight:
                (json.insight as string | undefined) ||
                (json.summary as string | undefined) ||
                fallbackInsight.insight,
            datasetId:
                (json.dataset_id as string | undefined) ||
                (json.datasetId as string | undefined) ||
                payload.datasetId,
            analysisId: json.analysis_id as number | undefined,
            programVersion: json.program_version as string | undefined,
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

async function safeFetch<T>(
    path: string,
    options?: Parameters<typeof fetch>[1]
): Promise<T | null> {
    try {
        const response = await fetch(`${resolveBackendBase()}${path}`, options);
        if (!response.ok) return null;
        return (await response.json()) as T;
    } catch (error) {
        console.warn('Backend fetch failed', path, error);
        return null;
    }
}

async function safeNodeFetch<T>(
    path: string,
    options?: Parameters<typeof fetch>[1]
): Promise<T | null> {
    try {
        const response = await fetch(path, options);
        if (!response.ok) return null;
        return (await response.json()) as T;
    } catch (error) {
        console.warn('Node backend fetch failed', path, error);
        return null;
    }
}

export async function fetchDatasets(): Promise<
    {
        id: number;
        name: string;
        description?: string | null;
        year?: number | null;
    }[]
> {
    const data = await safeFetch<
        {
            id: number;
            name: string;
            description?: string | null;
            year?: number | null;
        }[]
    >('/datasets');
    return (
        data || [
            {
                id: 1,
                name: '人口推移 (サンプル)',
                description: 'Fallback dataset',
                year: 2023
            },
            {
                id: 2,
                name: '子育て支援 (サンプル)',
                description: 'Fallback dataset',
                year: 2022
            }
        ]
    );
}

export async function createExperiment(
    goalDescription: string,
    datasetIds: number[]
): Promise<number | null> {
    const response = await safeFetch<{ experiment_id: number }>(
        '/experiments',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                goal_description: goalDescription,
                dataset_ids: datasetIds
            })
        }
    );
    return response?.experiment_id ?? null;
}

export async function listExperiments(): Promise<
    {
        id: number;
        goal_description: string;
        status: string;
        dataset_ids: number[];
    }[]
> {
    return (
        (await safeFetch<
            {
                id: number;
                goal_description: string;
                status: string;
                dataset_ids: number[];
            }[]
        >('/experiments')) || []
    );
}

export async function fetchExperimentDetail(experimentId: number): Promise<{
    id: number;
    goal_description: string;
    status: string;
    dataset_ids: number[];
    jobs: Array<{
        id: number;
        dataset_id: number;
        job_type: string;
        status: string;
        description?: string | null;
    }>;
} | null> {
    return await safeFetch(`/experiments/${experimentId}`);
}

export type OptimizationJob = {
    id: string;
    provider: string;
    model: string;
    dataset: string;
    trainset: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    artifactVersion?: string | null;
    createdAt?: string;
};

export type OptimizationPayload = {
    provider: string;
    model: string;
    dataset: string;
    trainset: string;
};

type OptimizationArtifactResponse = {
    id: number;
    version: string;
    trainset: Array<Record<string, unknown>>;
    metric: Record<string, unknown> | null;
    path: string;
    active: boolean;
    created_at: string;
};

function describeTrainset(trainset: Array<Record<string, unknown>>): string {
    if (!trainset.length) return 'unknown';
    const first = trainset[0];
    const dataset = first.dataset ?? first.name ?? first.id;
    const split = first.trainset ?? first.split ?? first.version;
    if (dataset && split) return `${dataset}/${split}`;
    if (dataset) return String(dataset);
    if (split) return String(split);
    return JSON.stringify(first);
}

function toOptimizationJob(artifact: OptimizationArtifactResponse): OptimizationJob {
    // Artifacts are created synchronously and flagged as inactive by default, so
    // treat them as completed so the UI allows activation toggling.
    const status: OptimizationJob['status'] = 'completed';

    return {
        id: artifact.id.toString(),
        provider: 'dspy',
        model: artifact.version,
        dataset: describeTrainset(artifact.trainset),
        trainset: describeTrainset(artifact.trainset),
        status,
        artifactVersion: artifact.version,
        createdAt: artifact.created_at
    };
}

const optimizationFallback: OptimizationJob[] = [
    {
        id: 'optim-demo-1',
        provider: 'openai',
        model: 'gpt-4o-mini',
        dataset: 'population-trend',
        trainset: 'train-v1',
        status: 'running',
        artifactVersion: null,
        createdAt: '2024-10-10T05:00:00Z'
    },
    {
        id: 'optim-demo-2',
        provider: 'anthropic',
        model: 'claude-3.5-sonnet',
        dataset: 'childcare-support',
        trainset: 'train-v0',
        status: 'completed',
        artifactVersion: 'v0.3.2',
        createdAt: '2024-10-09T02:00:00Z'
    }
];

export async function startOptimization(
    payload: OptimizationPayload
): Promise<{ jobId: string } | null> {
    const response = await safeFetch<OptimizationArtifactResponse>(
        '/dspy/optimization',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                version: `${payload.provider}:${payload.model}`,
                trainset: [
                    {
                        dataset: payload.dataset,
                        trainset: payload.trainset
                    }
                ],
                metric: {
                    provider: payload.provider,
                    model: payload.model
                }
            })
        }
    );

    const jobId = response?.id;
    return jobId ? { jobId: jobId.toString() } : null;
}

export async function listOptimizationJobs(): Promise<OptimizationJob[]> {
    const artifacts = await safeFetch<OptimizationArtifactResponse[]>(
        '/dspy/optimization/history'
    );
    return artifacts?.map(toOptimizationJob) || optimizationFallback;
}

export async function activateOptimizationArtifact(
    jobId: string
): Promise<boolean> {
    const response = await safeFetch<OptimizationArtifactResponse>(
        `/dspy/optimization/${Number(jobId)}`,
        {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: true })
        }
    );
    return Boolean(response);
}

export async function fetchInsightCandidates(experimentId: number): Promise<{
    insights: Array<{
        id: number;
        title: string;
        description: string;
        adopted: boolean;
    }>;
} | null> {
    return await safeFetch(`/experiments/${experimentId}/insights`);
}

export async function submitInsightFeedback(
    candidateId: number,
    decision: 'adopted' | 'rejected',
    comment?: string
): Promise<void> {
    await submitFeedback({
        insightId: candidateId,
        rating: decision === 'adopted' ? 1 : -1,
        comment,
        targetModule: 'batch'
    });
}

export type FeedbackPayload = {
    insightId?: number;
    analysisId?: number;
    rating: -1 | 1;
    comment?: string;
    targetModule: 'interactive' | 'batch' | 'other';
};

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
    await safeFetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            insight_id: payload.insightId,
            analysis_id: payload.analysisId,
            rating: payload.rating,
            comment: payload.comment,
            target_module: payload.targetModule
        })
    });
}
