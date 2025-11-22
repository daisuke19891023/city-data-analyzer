import { useEffect, useMemo, useState, type FormEvent } from 'react';
import '../index.css';
import { ChatMessage } from '../components/chat/ChatMessage';
import { DataChart } from '../components/visualization/DataChart';
import { DataSummaryTable } from '../components/visualization/DataSummaryTable';
import type {
    DatasetDefinition,
    DatasetRecord
} from '../data/visualizationData';
import { visualizationDatasetOptions } from '../data/visualizationData';
import {
    answerQuestionFromData,
    applyFilters,
    buildCategoryTable,
    buildMonthlySeries,
    dataMode,
    deriveChatIntent,
    getDatasetData,
    getDatasetSummaries,
    summarizeRecords,
    type FilterState,
    type DatasetSummary
} from '../lib/dataSource';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from '../components/ui/card';

type ChatEntry = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
};

const timeRangeOptions: FilterState['timeRange'][] = [
    '6m',
    '12m',
    '24m',
    'all'
];

function makeId(): string {
    if (
        typeof globalThis.crypto !== 'undefined' &&
        globalThis.crypto.randomUUID
    ) {
        return globalThis.crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2);
}

function initialChatMessage(mode: 'dummy' | 'api'): ChatEntry {
    const label = mode === 'api' ? 'APIモード' : 'ダミーデータモード';
    return {
        id: 'intro',
        role: 'assistant',
        content: `${label}でデータを読み込みました。データセットを選び、気になるポイントを質問してください。`
    };
}

export function InteractivePage(): JSX.Element {
    const [datasetSummaries, setDatasetSummaries] = useState<DatasetSummary[]>(
        visualizationDatasetOptions
    );
    const [datasetId, setDatasetId] = useState<string>(
        visualizationDatasetOptions[0].id
    );
    const [dataset, setDataset] = useState<DatasetDefinition | null>(null);
    const [records, setRecords] = useState<DatasetRecord[]>([]);
    const [filters, setFilters] = useState<FilterState>({
        timeRange: '12m',
        category: 'all',
        segment: 'all',
        metric: visualizationDatasetOptions[0].defaultMetric
    });
    const [status, setStatus] = useState(
        'ダッシュボードのデータを準備しています...'
    );
    const [chatMessages, setChatMessages] = useState<ChatEntry[]>([
        initialChatMessage(dataMode)
    ]);
    const [chatInput, setChatInput] = useState('');
    const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);

    useEffect(() => {
        void (async () => {
            const summaries = await getDatasetSummaries();
            setDatasetSummaries(summaries);
            setDatasetId(
                (current) => current || summaries[0]?.id || 'population-trend'
            );
        })();
    }, []);

    useEffect(() => {
        void (async () => {
            setStatus('データセットを読み込んでいます...');
            const data = await getDatasetData(datasetId);
            if (!data) {
                setStatus('データセットを読み込めませんでした');
                return;
            }
            setDataset(data);
            setRecords(data.records);
            setFilters((current) => ({
                ...current,
                metric: data.availableMetrics.includes(current.metric)
                    ? current.metric
                    : data.defaultMetric,
                category: 'all',
                segment: 'all'
            }));
            setStatus(`「${data.label}」を表示中`);
        })();
    }, [datasetId]);

    const filteredRecords = useMemo(
        () => applyFilters(records, filters),
        [records, filters]
    );
    const monthlySeries = useMemo(
        () => buildMonthlySeries(filteredRecords),
        [filteredRecords]
    );
    const tableRows = useMemo(
        () => buildCategoryTable(filteredRecords, filters.metric),
        [filteredRecords, filters.metric]
    );
    const summary = useMemo(
        () => summarizeRecords(filteredRecords, filters.metric),
        [filteredRecords, filters.metric]
    );

    function handleAsk(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();
        if (!chatInput.trim() || !dataset) return;
        const userMessage: ChatEntry = {
            id: makeId(),
            role: 'user',
            content: chatInput
        };
        const { updatedFilters, notes } = deriveChatIntent(
            chatInput,
            dataset,
            filters
        );
        const nextFilters = updatedFilters
            ? { ...filters, ...updatedFilters }
            : filters;
        if (updatedFilters) {
            setFilters(nextFilters);
        }
        const scopedRecords = applyFilters(dataset.records, nextFilters);
        const answer = answerQuestionFromData(
            chatInput,
            dataset,
            scopedRecords
        );
        const assistantMessage: ChatEntry = {
            id: makeId(),
            role: 'assistant',
            content: [notes.join(' '), answer].filter(Boolean).join('\n')
        };
        setChatMessages((prev) => [...prev, userMessage, assistantMessage]);
        setChatInput('');
    }

    const activeSummary = datasetSummaries.find(
        (summary) => summary.id === datasetId
    );

    const renderFilterControls = (className = '') => (
        <div
            className={`control-row ${className}`.trim()}
            aria-label="データ選択とフィルター"
        >
            <div className="control-group">
                <label htmlFor="dataset-select">データセット</label>
                <select
                    id="dataset-select"
                    value={datasetId}
                    onChange={(event) => setDatasetId(event.target.value)}
                >
                    {datasetSummaries.map((option) => (
                        <option key={option.id} value={option.id}>
                            {option.label} — {option.helper}
                        </option>
                    ))}
                </select>
            </div>
            <div className="control-group">
                <label htmlFor="metric-select">指標</label>
                <select
                    id="metric-select"
                    value={filters.metric}
                    onChange={(event) =>
                        setFilters((current) => ({
                            ...current,
                            metric: event.target.value
                        }))
                    }
                >
                    {dataset?.availableMetrics?.map((metric) => (
                        <option key={metric} value={metric}>
                            {metric}
                        </option>
                    ))}
                </select>
            </div>
            <div className="control-group">
                <label htmlFor="category-select">カテゴリ</label>
                <select
                    id="category-select"
                    value={filters.category}
                    onChange={(event) =>
                        setFilters((current) => ({
                            ...current,
                            category: event.target.value
                        }))
                    }
                >
                    <option value="all">すべて</option>
                    {dataset?.categories?.map((category) => (
                        <option key={category} value={category}>
                            {category}
                        </option>
                    ))}
                </select>
            </div>
            <div className="control-group">
                <label htmlFor="segment-select">セグメント</label>
                <select
                    id="segment-select"
                    value={filters.segment}
                    onChange={(event) =>
                        setFilters((current) => ({
                            ...current,
                            segment: event.target.value
                        }))
                    }
                >
                    <option value="all">すべて</option>
                    {dataset?.segments?.map((segment) => (
                        <option key={segment} value={segment}>
                            {segment}
                        </option>
                    ))}
                </select>
            </div>
            <div className="control-group">
                <label htmlFor="timerange-select">期間</label>
                <select
                    id="timerange-select"
                    value={filters.timeRange}
                    onChange={(event) =>
                        setFilters((current) => ({
                            ...current,
                            timeRange: event.target
                                .value as FilterState['timeRange']
                        }))
                    }
                >
                    {timeRangeOptions.map((option) => (
                        <option key={option} value={option}>
                            {option === 'all' ? 'すべて' : option}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );

    return (
        <div className="app-container">
            <section className="hero" aria-labelledby="app-heading">
                <div className="hero__title">
                    <div>
                        <h1 id="app-heading">City Data Analyzer</h1>
                        <p className="hero__subtitle">
                            データセットの選択とフィルタリングでグラフとテーブルを即座に更新し、
                            下部のチャットで自然言語による質問に答える可視化ビューです。
                        </p>
                        <div className="badge-row">
                            <Badge
                                variant={
                                    dataMode === 'api' ? 'accent' : 'warning'
                                }
                            >
                                データモード:{' '}
                                {dataMode === 'api'
                                    ? 'API経由'
                                    : 'ダミーデータ'}
                            </Badge>
                            <Badge variant="success">{status}</Badge>
                        </div>
                    </div>
                    <div className="actions-row">
                        <Button
                            className="filter-modal-trigger"
                            variant="ghost"
                            onClick={() => setIsFilterModalOpen(true)}
                        >
                            フィルターを開く
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={() =>
                                setFilters((current) => ({
                                    ...current,
                                    category: 'all',
                                    segment: 'all',
                                    timeRange: '12m',
                                    metric:
                                        activeSummary?.defaultMetric ||
                                        visualizationDatasetOptions[0]
                                            .defaultMetric
                                }))
                            }
                        >
                            フィルターをリセット
                        </Button>
                        <Button
                            onClick={() =>
                                window.scrollTo({
                                    top: document.body.scrollHeight,
                                    behavior: 'smooth'
                                })
                            }
                        >
                            チャットで聞く
                        </Button>
                    </div>
                </div>
                {renderFilterControls('control-row--inline')}
            </section>

            {isFilterModalOpen && (
                <div className="filter-modal" role="dialog" aria-modal="true">
                    <button
                        type="button"
                        className="filter-modal__backdrop"
                        aria-label="フィルターを閉じる"
                        onClick={() => setIsFilterModalOpen(false)}
                    />
                    <div className="filter-modal__body">
                        <header className="filter-modal__header">
                            <h2>フィルターを調整</h2>
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setIsFilterModalOpen(false)}
                            >
                                閉じる
                            </Button>
                        </header>
                        {renderFilterControls('control-row--modal')}
                    </div>
                </div>
            )}

            <section className="two-column" aria-label="データ可視化">
                <Card className="card">
                    <CardHeader>
                        <CardTitle>グラフ</CardTitle>
                        <CardDescription>
                            フィルター結果を月次で集計し、棒グラフで可視化しています。
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <DataChart
                            title={dataset?.label ?? 'データセット'}
                            metric={filters.metric}
                            series={monthlySeries}
                            unit={filteredRecords[0]?.unit}
                        />
                    </CardContent>
                </Card>

                <Card className="card">
                    <CardHeader>
                        <CardTitle>サマリー</CardTitle>
                        <CardDescription>
                            指標の傾向とダミーデータのハイライトを表示します。
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="summary-panel">
                        <p className="summary-panel__headline">
                            {summary.headline}
                        </p>
                        <p className="summary-panel__detail">
                            {summary.detail}
                        </p>
                        <ul className="summary-panel__list">
                            <li>
                                データセット: {dataset?.label}
                                {dataset?.description
                                    ? ` — ${dataset.description}`
                                    : ''}
                            </li>
                            <li>
                                適用フィルター: {filters.category} /{' '}
                                {filters.segment}
                            </li>
                            <li>期間: {filters.timeRange}</li>
                        </ul>
                    </CardContent>
                </Card>
            </section>

            <Card className="card">
                <CardHeader>
                    <CardTitle>テーブル</CardTitle>
                    <CardDescription>
                        カテゴリとセグメント別の集計結果を表形式で確認できます。
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <DataSummaryTable
                        rows={tableRows}
                        metric={filters.metric}
                    />
                </CardContent>
            </Card>

            <Card className="chat-card">
                <CardHeader>
                    <CardTitle>データ質問チャット</CardTitle>
                    <CardDescription>
                        質問を送信すると、現在のフィルターとデータに基づいた回答を生成します。
                    </CardDescription>
                </CardHeader>
                <CardContent className="chat-panel">
                    <div className="chat-messages" aria-live="polite">
                        {chatMessages.map((message, index) => (
                            <ChatMessage
                                key={`${message.id}-${index}`}
                                role={message.role}
                                content={message.content}
                                tone={
                                    message.role === 'assistant'
                                        ? 'action'
                                        : 'neutral'
                                }
                            />
                        ))}
                    </div>
                    <form className="chat-input" onSubmit={handleAsk}>
                        <input
                            aria-label="データに関する質問"
                            value={chatInput}
                            onChange={(event) =>
                                setChatInput(event.target.value)
                            }
                            placeholder="例: 最近6ヶ月で増えているエリアは？"
                        />
                        <Button type="submit">送信</Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
