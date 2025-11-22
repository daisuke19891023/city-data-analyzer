import type { FormEvent } from 'react';
import { useEffect, useState } from 'react';
import {
    createExperiment,
    fetchDatasets,
    listExperiments
} from '../lib/backendClient';
import type { DatasetSummary, ExperimentSummary } from '../types/experiments';
import { Link } from 'react-router-dom';

export function ExperimentsPage(): JSX.Element {
    const [goal, setGoal] = useState('街の人口推移からトレンドを知りたい');
    const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
    const [selected, setSelected] = useState<number[]>([]);
    const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
    const [message, setMessage] = useState('データセットを選択して実験を作成してください');

    useEffect(() => {
        void (async () => {
            const ds = await fetchDatasets();
            setDatasets(ds);
            setSelected(ds.slice(0, 1).map((d) => d.id));
            setExperiments(await listExperiments());
        })();
    }, []);

    async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
        event.preventDefault();
        if (!goal.trim() || selected.length === 0) return;
        setMessage('実験を作成しています...');
        const id = await createExperiment(goal, selected);
        if (id) {
            setMessage(`実験 #${id} を作成しました。しばらくお待ちください。`);
            setExperiments(await listExperiments());
        } else {
            setMessage('バックエンドに接続できないため、作成に失敗しました。');
        }
    }

    return (
        <main className="page experiments-page">
            <section className="card">
                <h2>バッチ探索モード</h2>
                <p>{message}</p>
                <form className="form" onSubmit={onSubmit}>
                    <label className="form__label" htmlFor="goal-input">
                        やりたいこと
                    </label>
                    <textarea
                        id="goal-input"
                        value={goal}
                        onChange={(event) => setGoal(event.target.value)}
                        rows={3}
                        className="form__textarea"
                    />
                    <div className="form__group">
                        <p>データセット選択</p>
                        <div className="checkbox-grid">
                            {datasets.map((dataset) => (
                                <label key={dataset.id} className="checkbox">
                                    <input
                                        type="checkbox"
                                        checked={selected.includes(dataset.id)}
                                        onChange={(event) => {
                                            if (event.target.checked) {
                                                setSelected([...selected, dataset.id]);
                                            } else {
                                                setSelected(selected.filter((id) => id !== dataset.id));
                                            }
                                        }}
                                    />
                                    {dataset.name}
                                </label>
                            ))}
                        </div>
                    </div>
                    <button type="submit" className="button">
                        実験を作成
                    </button>
                </form>
            </section>
            <section className="card">
                <h3>実験一覧</h3>
                <div className="experiment-list">
                    {experiments.map((experiment) => (
                        <div key={experiment.id} className="experiment-item">
                            <div>
                                <div className="experiment-title">{experiment.goal_description}</div>
                                <div className="experiment-meta">対象: {experiment.dataset_ids.join(', ')}</div>
                            </div>
                            <div className="experiment-actions">
                                <span className={`badge badge--${experiment.status}`}>
                                    {experiment.status}
                                </span>
                                <Link to={`/experiments/${experiment.id}`} className="link">
                                    詳細を見る
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
}
