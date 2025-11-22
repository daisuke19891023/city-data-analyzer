import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Jest)', () => {
    it('shows dashboard-ready copy and key metrics', () => {
        render(<App />);

        expect(
            screen.getByText(
                /スマートフォンでも見やすいレスポンシブレイアウトです/
            )
        ).toBeInTheDocument();
        expect(screen.getByText('人口増加率')).toBeInTheDocument();
        expect(screen.getByText('AI改善提案 実行率')).toBeInTheDocument();
        expect(
            screen.getByText(/ダッシュボード連携のチャット応答/)
        ).toBeInTheDocument();
    });
});
