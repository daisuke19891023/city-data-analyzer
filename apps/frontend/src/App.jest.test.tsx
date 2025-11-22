import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Jest)', () => {
    it('shows interactive view and key controls', () => {
        render(<App />);

        expect(
            screen.getByText(/Vercel AI SDKを組み合わせて/)
        ).toBeInTheDocument();
        expect(screen.getByText(/データセット/)).toBeInTheDocument();
        expect(
            screen.getByRole('button', { name: /ai提案を実行/i })
        ).toBeInTheDocument();
        expect(
            screen.getByText(/インタラクティブチャット/)
        ).toBeInTheDocument();
    });
});
