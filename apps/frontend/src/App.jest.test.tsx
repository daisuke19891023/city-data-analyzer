import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Jest)', () => {
    it('shows interactive view with filters and chat', async () => {
        render(<App />);

        expect(
            await screen.findByText(/フィルターをリセット/)
        ).toBeInTheDocument();
        expect(screen.getByLabelText('データセット')).toBeInTheDocument();
        expect((await screen.findAllByText(/グラフ/)).length).toBeGreaterThan(
            0
        );
        expect(
            await screen.findByText(/データ質問チャット/)
        ).toBeInTheDocument();
    });
});
