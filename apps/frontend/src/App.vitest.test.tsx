import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Vitest)', () => {
    it('renders hero, dataset controls, and chat entry point', () => {
        render(<App />);

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: /city data analyzer/i
            })
        ).toBeInTheDocument();
        expect(
            screen.getByText(/都市データのダッシュボードとVercel AI SDK/)
        ).toBeInTheDocument();
        expect(
            screen.getByRole('heading', {
                level: 3,
                name: /インタラクティブチャット/i
            })
        ).toBeInTheDocument();
        expect(screen.getByLabelText('データセット')).toBeInTheDocument();
        expect(screen.getByLabelText('AIへの質問')).toHaveAttribute(
            'placeholder',
            expect.stringContaining('夜間ピーク')
        );
    });
});
