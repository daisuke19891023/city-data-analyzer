import { useEffect, useMemo, useState, type FormEvent } from 'react';
import {
    activateOptimizationArtifact,
    listOptimizationJobs,
    startOptimization,
    type OptimizationJob
} from '../lib/backendClient';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from '../components/ui/card';

type ToastVariant = 'info' | 'success' | 'error';

type ToastState = {
    message: string;
    variant: ToastVariant;
} | null;

const providerOptions = [
    { label: 'OpenAI', value: 'openai' },
    { label: 'Anthropic', value: 'anthropic' },
    { label: 'Google', value: 'google' }
];

const modelOptions: Record<string, string[]> = {
    openai: ['gpt-4o-mini', 'o4-mini'],
    anthropic: ['claude-3.5-sonnet', 'claude-3-opus'],
    google: ['gemini-1.5-pro', 'gemini-1.5-flash']
};

const datasetOptions = [
    { label: '人口推移データ', value: 'population-trend' },
    { label: '交通量データ', value: 'traffic-volume' },
    { label: '子育て支援データ', value: 'childcare-support' }
];

export function OptimizationPage(): JSX.Element {
    const [provider, setProvider] = useState('openai');
    const [model, setModel] = useState(modelOptions.openai[0]);
    const [dataset, setDataset] = useState(datasetOptions[0]?.value || '');
    const [trainset, setTrainset] = useState('train-v1');
    const [jobs, setJobs] = useState<OptimizationJob[]>([]);
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState<ToastState>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        void refreshJobs();
    }, []);

    useEffect(() => {
        setModel((current) => {
            const nextModels = modelOptions[provider];
            return nextModels.includes(current) ? current : nextModels[0];
        });
    }, [provider]);

    const providerLabel = useMemo(
        () =>
            providerOptions.find((option) => option.value === provider)?.label,
        [provider]
    );

    async function refreshJobs(): Promise<void> {
        const data = await listOptimizationJobs();
        setJobs(data);
    }

    function showToast(message: string, variant: ToastVariant): void {
        setToast({ message, variant });
        window.setTimeout(() => setToast(null), 3000);
    }

    async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
        event.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const response = await startOptimization({
                provider,
                model,
                dataset,
                trainset
            });
            if (!response) {
                throw new Error('最適化ジョブの開始に失敗しました');
            }
            showToast(`ジョブ ${response.jobId} を開始しました`, 'success');
            await refreshJobs();
        } catch (err) {
            console.error(err);
            setError(
                '最適化リクエストに失敗しました。しばらくしてから再試行してください。'
            );
            showToast('最適化リクエストに失敗しました', 'error');
        } finally {
            setLoading(false);
        }
    }

    async function onActivate(jobId: string): Promise<void> {
        try {
            const ok = await activateOptimizationArtifact(jobId);
            if (!ok) throw new Error('activate failed');
            showToast('成果物バージョンを有効化しました', 'success');
            await refreshJobs();
        } catch (err) {
            console.error(err);
            setError('成果物の有効化に失敗しました。');
            showToast('成果物の有効化に失敗しました', 'error');
        }
    }

    function renderStatusBadge(status: OptimizationJob['status']): JSX.Element {
        const variant: 'neutral' | 'success' | 'warning' | 'error' =
            status === 'completed'
                ? 'success'
                : status === 'running'
                  ? 'warning'
                  : status === 'failed'
                    ? 'error'
                    : 'neutral';
        return <Badge variant={variant}>{status}</Badge>;
    }

    return (
        <main className="app-container">
            <section className="hero">
                <div className="hero__title">
                    <h1>最適化ジョブ管理</h1>
                    <Badge variant="accent">新しいバックエンドAPI</Badge>
                </div>
                <p className="hero__subtitle">
                    provider / model / dataset / trainset を指定して Node 経由の
                    /api/agent/optimization
                    を呼び出し、進行中のジョブを追跡します。
                </p>
            </section>

            <div className="two-column">
                <Card>
                    <CardHeader>
                        <CardTitle>最適化の実行</CardTitle>
                        <CardDescription>
                            モデルやデータセットを指定して成果物を生成します。
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {error && <div className="error-box">{error}</div>}
                        <form className="control-row" onSubmit={onSubmit}>
                            <div className="control-group">
                                <label htmlFor="provider">Provider</label>
                                <select
                                    id="provider"
                                    value={provider}
                                    onChange={(event) =>
                                        setProvider(event.target.value)
                                    }
                                >
                                    {providerOptions.map((option) => (
                                        <option
                                            key={option.value}
                                            value={option.value}
                                        >
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="control-group">
                                <label htmlFor="model">Model</label>
                                <select
                                    id="model"
                                    value={model}
                                    onChange={(event) =>
                                        setModel(event.target.value)
                                    }
                                >
                                    {modelOptions[provider].map((name) => (
                                        <option key={name} value={name}>
                                            {name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="control-group">
                                <label htmlFor="dataset">Dataset</label>
                                <select
                                    id="dataset"
                                    value={dataset}
                                    onChange={(event) =>
                                        setDataset(event.target.value)
                                    }
                                >
                                    {datasetOptions.map((option) => (
                                        <option
                                            key={option.value}
                                            value={option.value}
                                        >
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="control-group">
                                <label htmlFor="trainset">Trainset</label>
                                <input
                                    id="trainset"
                                    value={trainset}
                                    onChange={(event) =>
                                        setTrainset(event.target.value)
                                    }
                                    placeholder="train-v1"
                                />
                            </div>
                            <div className="actions-row">
                                <Button type="submit" disabled={loading}>
                                    {loading ? '送信中...' : '最適化を開始'}
                                </Button>
                                <Badge variant="neutral">
                                    {providerLabel} / {model}
                                </Badge>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>ジョブ一覧</CardTitle>
                        <CardDescription>
                            進行中/完了したジョブと成果物を確認します。
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="status-grid">
                            {jobs.map((job) => (
                                <div key={job.id} className="status-card">
                                    <div className="status-row">
                                        <div>
                                            <div className="status-title">
                                                {job.model}
                                            </div>
                                            <div className="status-meta">
                                                {job.provider} ・ {job.dataset}{' '}
                                                ・ {job.trainset}
                                            </div>
                                        </div>
                                        {renderStatusBadge(job.status)}
                                    </div>
                                    <div className="status-meta">
                                        {job.createdAt && (
                                            <span>
                                                作成:{' '}
                                                {new Date(
                                                    job.createdAt
                                                ).toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                    <div className="status-actions">
                                        {job.artifactVersion ? (
                                            <span className="artifact-label">
                                                成果物: {job.artifactVersion}
                                            </span>
                                        ) : (
                                            <span className="artifact-label">
                                                成果物: --
                                            </span>
                                        )}
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            disabled={
                                                job.status !== 'completed'
                                            }
                                            onClick={() =>
                                                void onActivate(job.id)
                                            }
                                        >
                                            有効化
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {toast && (
                <div className={`toast toast--${toast.variant}`} role="status">
                    {toast.message}
                </div>
            )}
        </main>
    );
}
