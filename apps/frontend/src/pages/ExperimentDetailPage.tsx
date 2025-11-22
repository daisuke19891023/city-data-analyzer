import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
    fetchExperimentDetail,
    fetchInsightCandidates,
    submitInsightFeedback
} from '../lib/backendClient';
import type { ExperimentDetail, InsightCandidate } from '../types/experiments';

export function ExperimentDetailPage(): JSX.Element {
    const params = useParams();
    const experimentId = Number(params.id);
    const [detail, setDetail] = useState<ExperimentDetail | null>(null);
    const [insights, setInsights] = useState<InsightCandidate[]>([]);
    const [comments, setComments] = useState<Record<number, string>>({});

    useEffect(() => {
        void (async () => {
            const info = await fetchExperimentDetail(experimentId);
            if (info) setDetail(info as ExperimentDetail);
            const insightResponse = await fetchInsightCandidates(experimentId);
            if (insightResponse?.insights) {
                setInsights(insightResponse.insights as InsightCandidate[]);
            }
        })();
    }, [experimentId]);

    async function handleDecision(
        candidateId: number,
        decision: 'adopted' | 'rejected'
    ): Promise<void> {
        const comment = comments[candidateId];
        await submitInsightFeedback(candidateId, decision, comment);
        const refreshed = await fetchInsightCandidates(experimentId);
        if (refreshed?.insights) {
            setInsights(refreshed.insights as InsightCandidate[]);
        }
    }

    return (
        <main className="page experiment-detail">
            <div className="breadcrumb">
                <Link to="/experiments">← 実験一覧に戻る</Link>
            </div>
            <section className="card">
                <h2>実験 #{experimentId}</h2>
                <p>ゴール: {detail?.goal_description}</p>
                <p>ステータス: {detail?.status}</p>
                <div className="job-list">
                    {detail?.jobs.map((job) => (
                        <div key={job.id} className="job-item">
                            <div>
                                <div className="job-title">{job.job_type}</div>
                                <div className="job-desc">
                                    {job.description}
                                </div>
                            </div>
                            <div className={`badge badge--${job.status}`}>
                                {job.status}
                            </div>
                        </div>
                    ))}
                </div>
            </section>
            <section className="card">
                <h3>インサイト候補</h3>
                {insights.length === 0 && (
                    <p>まだインサイトが生成されていません。</p>
                )}
                <div className="insight-grid">
                    {insights.map((insight) => (
                        <div key={insight.id} className="insight-card">
                            <div className="insight-card__header">
                                <div>
                                    <div className="insight-title">
                                        {insight.title}
                                    </div>
                                    <div className="insight-meta">
                                        dataset #{insight.dataset_id}
                                    </div>
                                </div>
                                <span
                                    className={`badge badge--${insight.adopted ? 'adopted' : 'pending'}`}
                                >
                                    {insight.adopted ? '採用済み' : '未評価'}
                                </span>
                            </div>
                            <p>{insight.description}</p>
                            <textarea
                                placeholder="コメントを入力"
                                value={
                                    comments[insight.id] ||
                                    insight.feedback_comment ||
                                    ''
                                }
                                onChange={(event) =>
                                    setComments({
                                        ...comments,
                                        [insight.id]: event.target.value
                                    })
                                }
                                className="form__textarea"
                                rows={2}
                            />
                            <div className="insight-actions">
                                <button
                                    className="button button--ghost"
                                    type="button"
                                    onClick={() =>
                                        void handleDecision(
                                            insight.id,
                                            'rejected'
                                        )
                                    }
                                >
                                    👎 改善
                                </button>
                                <button
                                    className="button"
                                    type="button"
                                    onClick={() =>
                                        void handleDecision(
                                            insight.id,
                                            'adopted'
                                        )
                                    }
                                >
                                    👍 採用
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
}
