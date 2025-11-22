import type { FormEvent } from 'react';
import { useMemo, useState } from 'react';
import type { UseChatOptions } from 'ai/react';
import { useChat } from 'ai/react';
import '../index.css';
import { ChatMessage } from '../components/chat/ChatMessage';
import { Dashboard } from '../components/dashboard/Dashboard';
import { ChartPlaceholder } from '../components/dashboard/ChartPlaceholder';
import type { DashboardData } from '../data/dashboardPresets';
import { dashboardPresets, datasetOptions } from '../data/dashboardPresets';
import { runInteractiveAnalysis, submitFeedback } from '../lib/backendClient';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from '../components/ui/card';

const providerOptions = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'google', label: 'Google' }
];

const modelCandidates: Record<string, string[]> = {
    openai: ['gpt-4o-mini', 'o3-mini'],
    anthropic: ['claude-3-5-haiku-latest'],
    google: ['gemini-1.5-flash']
};

function buildDashboardFromInsight(
    datasetId: string,
    assistantText: string,
    summary?: string
): DashboardData {
    const base = dashboardPresets[datasetId];
    const enrichedInsight = assistantText || summary;
    return {
        ...base,
        statsCallout: summary || base.statsCallout,
        insights: [
            {
                title: 'AIが生成した最新の観測',
                signal: enrichedInsight || base.headline,
                recommendation: '提案を右側のカードから確認してください'
            },
            ...base.insights
        ].slice(0, 4)
    };
}

export function InteractivePage(): JSX.Element {
    const [datasetId, setDatasetId] = useState(datasetOptions[0].id);
    const [provider, setProvider] = useState(providerOptions[0].value);
    const [model, setModel] = useState(modelCandidates[provider][0]);
    const [dashboard, setDashboard] = useState<DashboardData>(
        dashboardPresets[datasetId]
    );
    const [status, setStatus] = useState(
        'Pythonバックエンドと接続してインサイトを取得します。'
    );
    const [lastInsight, setLastInsight] = useState('');
    const [lastAnalysisId, setLastAnalysisId] = useState<number | undefined>();
    const [programVersion, setProgramVersion] = useState<string | undefined>();
    const [feedbackComment, setFeedbackComment] = useState('');
    const [feedbackState, setFeedbackState] = useState('');
    const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
    const [backendSummary, setBackendSummary] = useState('');

    const availableModels = useMemo(
        () => modelCandidates[provider] || [],
        [provider]
    );

    const {
        messages,
        input,
        handleInputChange,
        handleSubmit,
        isLoading,
        setInput
    } = useChat({
        api: '/api/agent/interactive',
        streamMode: 'text',
        body: { provider, model, datasetId },
        initialMessages: [
            {
                id: 'intro',
                role: 'assistant',
                content:
                    'データセットを選択し、聞きたいことを送信してください。必要に応じてPythonの /dspy/interactive を呼び出します。'
            }
        ],
        onFinish: (message) => {
            setStatus('AI応答が届きました。ダッシュボードを更新しました。');
            setLastInsight(message.content as string);
            setDashboard(
                buildDashboardFromInsight(
                    datasetId,
                    message.content as string,
                    backendSummary
                )
            );
        },
        onError: () =>
            setStatus(
                'AI API 呼び出しに失敗しました。サンプルデータを表示しています。'
            )
    } satisfies UseChatOptions);

    function resetDashboard(nextDataset: string): void {
        setDashboard(dashboardPresets[nextDataset]);
        setLastInsight('');
    }

    async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
        event.preventDefault();
        if (!input.trim()) return;

        setStatus('Pythonバックエンドに問い合わせ中...');
        const analysis = await runInteractiveAnalysis({
            question: input,
            datasetId,
            provider,
            model
        });
        setBackendSummary(analysis.summary);
        setDashboard(
            buildDashboardFromInsight(
                datasetId,
                analysis.insight,
                analysis.summary
            )
        );
        setLastInsight(analysis.insight);
        setLastAnalysisId(analysis.analysisId);
        setProgramVersion(analysis.programVersion);
        setFeedbackComment('');
        setFeedbackState('');
        setStatus(
            analysis.fallback
                ? 'バックエンド未接続のためサンプルで更新しました。'
                : 'バックエンド応答を反映しました。AIストリームを待機します。'
        );
        await handleSubmit(event);
        setInput('');
    }

    async function handleFeedback(rating: 1 | -1): Promise<void> {
        if (!lastInsight) return;
        setFeedbackSubmitting(true);
        await submitFeedback({
            analysisId: lastAnalysisId,
            rating,
            comment: feedbackComment,
            targetModule: 'interactive'
        });
        setFeedbackState(
            rating > 0
                ? '👍 高評価を受け付けました'
                : '👎 改善フィードバックを保存しました'
        );
        setFeedbackSubmitting(false);
    }

    return (
        <div className="app-container">
            <section className="hero" aria-labelledby="app-heading">
                <div className="hero__title">
                    <div>
                        <h1 id="app-heading">City Data Analyzer</h1>
                        <p className="hero__subtitle">
                            都市データのダッシュボードとVercel AI
                            SDKを組み合わせて、 Pythonの /dspy/interactive
                            から返るインサイトをストリーミング表示します。
                        </p>
                    </div>
                    <div className="actions-row">
                        <Button variant="ghost">共有リンクをコピー</Button>
                        <Button>AI提案を実行</Button>
                    </div>
                </div>
                <div
                    className="control-row"
                    aria-label="データセットとプロバイダー選択"
                >
                    <div className="control-group">
                        <label htmlFor="dataset-select">データセット</label>
                        <select
                            id="dataset-select"
                            value={datasetId}
                            onChange={(event) => {
                                const nextId = event.target.value;
                                setDatasetId(nextId);
                                resetDashboard(nextId);
                            }}
                        >
                            {datasetOptions.map((option) => (
                                <option key={option.id} value={option.id}>
                                    {option.label} — {option.helper}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="control-group">
                        <label htmlFor="provider-select">LLM Provider</label>
                        <select
                            id="provider-select"
                            value={provider}
                            onChange={(event) => {
                                const nextProvider = event.target.value;
                                setProvider(nextProvider);
                                setModel(modelCandidates[nextProvider][0]);
                            }}
                        >
                            {providerOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="control-group">
                        <label htmlFor="model-select">モデル</label>
                        <select
                            id="model-select"
                            value={model}
                            onChange={(event) => setModel(event.target.value)}
                        >
                            {availableModels.map((candidate) => (
                                <option key={candidate} value={candidate}>
                                    {candidate}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </section>

            <section
                className="two-column"
                aria-label="チャットとダッシュボード"
            >
                <Card className="chat-card">
                    <CardHeader>
                        <CardTitle>インタラクティブチャット</CardTitle>
                        <CardDescription>
                            useChat(
                            {`{ body: { provider: '${provider}', model: '${model}' } }`}
                            ) で Pythonバックエンドをツール呼び出しします。
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="chat-panel">
                        <div className="chat-messages" aria-live="polite">
                            {messages.map((message, index) => (
                                <ChatMessage
                                    key={`${message.id}-${index}`}
                                    role={
                                        message.role === 'assistant'
                                            ? 'assistant'
                                            : 'user'
                                    }
                                    content={message.content}
                                    tone={
                                        message.role === 'assistant'
                                            ? 'action'
                                            : 'neutral'
                                    }
                                />
                            ))}
                        </div>
                        <div className="status-row" aria-live="polite">
                            <Badge variant={isLoading ? 'accent' : 'success'}>
                                {status}
                            </Badge>
                        </div>
                        <form className="chat-input" onSubmit={onSubmit}>
                            <input
                                aria-label="AIへの質問"
                                value={input}
                                onChange={handleInputChange}
                                placeholder="例: 人口推移と移動パターンから夜間ピークを教えて"
                            />
                            <Button type="submit" disabled={isLoading}>
                                {isLoading ? '送信中...' : '送信'}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <Dashboard
                    data={dashboard}
                    lastInsight={lastInsight}
                    onRefresh={() => resetDashboard(datasetId)}
                />
            </section>

            {lastInsight ? (
                <Card className="card">
                    <CardHeader>
                        <CardTitle>インサイトへのフィードバック</CardTitle>
                        <CardDescription>
                            最新のAI応答に対する 👍 / 👎
                            とコメントを送信できます。
                            {programVersion
                                ? ` (program: ${programVersion})`
                                : ''}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="insight-title">{lastInsight}</p>
                        <textarea
                            aria-label="インサイトへのコメント"
                            className="form__textarea"
                            rows={3}
                            placeholder="気付いたことや改善点を記載してください"
                            value={feedbackComment}
                            onChange={(event) =>
                                setFeedbackComment(event.target.value)
                            }
                        />
                        <div
                            className="insight-actions"
                            style={{ gap: '0.5rem' }}
                        >
                            <Button
                                type="button"
                                onClick={() => void handleFeedback(1)}
                                disabled={feedbackSubmitting}
                            >
                                👍 役立った
                            </Button>
                            <Button
                                type="button"
                                variant="ghost"
                                onClick={() => void handleFeedback(-1)}
                                disabled={feedbackSubmitting}
                            >
                                👎 改善してほしい
                            </Button>
                            {feedbackState ? (
                                <Badge variant="success">{feedbackState}</Badge>
                            ) : null}
                        </div>
                    </CardContent>
                </Card>
            ) : null}

            <section aria-label="可視化の雛形" className="two-column">
                <ChartPlaceholder
                    title="実験ジョブの完了率"
                    description="Node APIとPythonの連携結果を表示"
                    callout="フロントエンドのみで雛形を構築し、バックエンドの応答を待ち受けます。"
                />
                <ChartPlaceholder
                    title="モデル別レスポンス時間"
                    description="プロバイダー切替時の参考情報"
                    callout="openai/anthropic/google を同一UIで流用可能な構造"
                />
            </section>

            <p className="footer-note">
                フロントエンド側でチャットとダッシュボードの土台を実装し、
                /dspy/interactive への呼び出しは lib/backendClient.ts
                で共通化しました。
            </p>
        </div>
    );
}
