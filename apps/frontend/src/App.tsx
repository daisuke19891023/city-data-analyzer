import { useState } from 'react';
import './index.css';
import { ChatMessage } from './components/chat/ChatMessage';
import { ChartPlaceholder } from './components/dashboard/ChartPlaceholder';
import { MetricCard } from './components/dashboard/MetricCard';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from './components/ui/card';

type NeighborhoodRow = {
    name: string;
    signal: string;
    impact: string;
};

const metrics = [
    {
        label: '人口増加率',
        value: '+2.1%',
        helper: '前月比 / 居住者移動データ',
        trend: 'up' as const,
        emphasis: '暮らしやすさ上昇'
    },
    {
        label: '公共交通の遅延率',
        value: '5.8%',
        helper: '主要駅 24h モニタリング',
        trend: 'steady' as const,
        emphasis: '許容範囲内'
    },
    {
        label: 'エネルギー需要ピーク',
        value: '18:30',
        helper: '前日比較 -1.2%',
        trend: 'down' as const,
        emphasis: '節電効果あり'
    },
    {
        label: 'AI改善提案 実行率',
        value: '74%',
        helper: '今週の市庁内アクション',
        trend: 'up' as const,
        emphasis: '自動化ワークフロー活用中'
    }
];

const neighborhoods: NeighborhoodRow[] = [
    {
        name: 'Harbor District',
        signal: '夜間人流が週次+8%上昇、店舗売上も連動',
        impact: '深夜交通の増便検討を推奨'
    },
    {
        name: 'Innovation Park',
        signal: '日中滞在時間が平均+12分、イベント効果が継続',
        impact: '無料Wi-Fiの追加整備で回遊促進'
    },
    {
        name: 'Green Valley',
        signal: '電力ピークが夕方前倒し、気温影響が顕著',
        impact: '蓄電池シフトとデマンドレスポンス提案'
    }
];

const chartConfigs = [
    {
        title: '交通量トレンド',
        description: '主要交差点の7日間推移と混雑予測',
        callout: 'ピーク帯は18:00-19:00。AIが信号制御パターンを自動生成。'
    },
    {
        title: 'エネルギー需要プロファイル',
        description: '再エネ比率とピークカット状況',
        callout: '太陽光寄与が最大32%。需要抑制でCO₂換算-4.2%。'
    }
];

const chatHistory = [
    {
        role: 'user' as const,
        content: '主要エリアで渋滞が増える時間帯と原因を教えて'
    },
    {
        role: 'assistant' as const,
        tone: 'action' as const,
        content:
            '18:00-19:00に港湾エリアで出庫が集中し交通量が1.3倍。イベント退場と物流搬出が重なっています。' +
            ' 信号制御案とバス増便シナリオをダッシュボード右上の提案から確認できます。'
    },
    {
        role: 'user' as const,
        content: 'AIの推奨アクションをダッシュボードに保存して'
    },
    {
        role: 'assistant' as const,
        content:
            '「提案キュー」に2件を保存しました。共有リンクを更新しています。'
    }
];

const suggestions = [
    'ピーク時間の増便シナリオを比較',
    'エリア別のCO₂削減インパクトを算出',
    'AI提案をSlack通知に接続'
];

function App(): JSX.Element {
    const [prompt, setPrompt] = useState(
        '最新の交通量ピークとAI提案の概要をまとめて'
    );

    return (
        <div className="app-shell">
            <div className="app-container">
                <section className="hero" aria-labelledby="app-heading">
                    <div className="hero__title">
                        <div>
                            <h1 id="app-heading">City Data Analyzer</h1>
                            <p className="hero__subtitle">
                                都市データのダッシュボードとAIアシスタントを統合した再利用可能なビュー。
                                スマートフォンでも見やすいレスポンシブレイアウトです。
                            </p>
                        </div>
                        <div className="actions-row">
                            <Button variant="ghost">共有リンクをコピー</Button>
                            <Button>AI提案を実行</Button>
                        </div>
                    </div>
                    <div className="badge-row">
                        <Badge variant="accent">データ分析</Badge>
                        <Badge variant="success">リアルタイム指標</Badge>
                        <Badge variant="warning">インシデント監視</Badge>
                    </div>
                </section>

                <section aria-label="主要メトリクス">
                    <div className="metrics-grid">
                        {metrics.map((metric) => (
                            <MetricCard key={metric.label} {...metric} />
                        ))}
                    </div>
                </section>

                <section
                    className="two-column"
                    aria-label="ダッシュボードビジュアル"
                >
                    {chartConfigs.map((config) => (
                        <ChartPlaceholder key={config.title} {...config} />
                    ))}
                </section>

                <section className="two-column" aria-label="詳細インサイト">
                    <Card>
                        <CardHeader>
                            <CardTitle>エリア別インサイト</CardTitle>
                            <CardDescription>
                                AIが抽出したシグナルと推奨アクション
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <table className="list-table">
                                <thead>
                                    <tr>
                                        <th>エリア</th>
                                        <th>シグナル</th>
                                        <th>推奨</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {neighborhoods.map((row) => (
                                        <tr key={row.name}>
                                            <td>{row.name}</td>
                                            <td>{row.signal}</td>
                                            <td>{row.impact}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>AIアシスタント</CardTitle>
                            <CardDescription>
                                ダッシュボード連携のチャット応答
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="chat-panel">
                            <div className="chat-messages" aria-live="polite">
                                {chatHistory.map((message, index) => (
                                    <ChatMessage
                                        key={`${message.role}-${index}`}
                                        role={message.role}
                                        content={message.content}
                                        tone={
                                            'tone' in message
                                                ? message.tone
                                                : 'neutral'
                                        }
                                    />
                                ))}
                            </div>
                            <div
                                className="suggestion-row"
                                aria-label="プロンプト候補"
                            >
                                {suggestions.map((suggestion) => (
                                    <Badge key={suggestion}>{suggestion}</Badge>
                                ))}
                            </div>
                            <form
                                className="chat-input"
                                onSubmit={(event) => event.preventDefault()}
                            >
                                <input
                                    aria-label="AIへの質問"
                                    value={prompt}
                                    onChange={(event) =>
                                        setPrompt(event.target.value)
                                    }
                                />
                                <Button type="submit">送信</Button>
                            </form>
                        </CardContent>
                    </Card>
                </section>

                <p className="footer-note">
                    shadcn
                    UI風のプリミティブを用いて、ダッシュボードとAI応答を組み合わせるための下準備を完了しました。
                </p>
            </div>
        </div>
    );
}

export default App;
