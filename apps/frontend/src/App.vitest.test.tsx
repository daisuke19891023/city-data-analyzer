import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

    it('toggles between light and dark themes', async () => {
        render(<App />);

        await waitFor(() => {
            expect(document.documentElement.dataset.theme).toBeDefined();
        });

        const toggleButton = await screen.findByRole('button', {
            name: /モードに切り替え/
        });

        const initialTheme = document.documentElement.dataset.theme;
        fireEvent.click(toggleButton);

        const nextTheme = document.documentElement.dataset.theme;
        expect(nextTheme).not.toBe(initialTheme);
        expect(toggleButton.getAttribute('aria-label')).toMatch(
            /モードに切り替え/
        );
    });
});
