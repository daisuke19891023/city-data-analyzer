import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Vitest)', () => {
    it('renders dataset controls, chart, and chat entry point', async () => {
        render(<App />);

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: /city data analyzer/i
            })
        ).toBeInTheDocument();
        expect(
            await screen.findByText(/データセットを選び/)
        ).toBeInTheDocument();
        expect(
            await screen.findByRole('heading', {
                level: 3,
                name: /データ質問チャット/i
            })
        ).toBeInTheDocument();
        expect(screen.getByLabelText('データセット')).toBeInTheDocument();
        expect((await screen.findAllByText(/グラフ/)).length).toBeGreaterThan(
            0
        );
        expect(screen.getByLabelText('データに関する質問')).toHaveAttribute(
            'placeholder',
            expect.stringContaining('6ヶ月')
        );
    });
});
