import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Vitest)', () => {
    it('renders hero, dashboard sections, and chat entry point', () => {
        render(<App />);

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: /city data analyzer/i
            })
        ).toBeInTheDocument();
        expect(
            screen.getByText(/都市データのダッシュボードとAIアシスタントを統合/)
        ).toBeInTheDocument();
        expect(
            screen.getByRole('heading', { level: 3, name: /aiアシスタント/i })
        ).toBeInTheDocument();
        expect(screen.getByLabelText('AIへの質問')).toHaveValue(
            '最新の交通量ピークとAI提案の概要をまとめて'
        );
    });
});
