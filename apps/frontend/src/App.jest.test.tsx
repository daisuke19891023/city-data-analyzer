import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Jest)', () => {
    it('shows the helper copy', () => {
        render(<App />);
        expect(
            screen.getByText(
                /frontend scaffold powered by vite, react, and typescript/i
            )
        ).toBeInTheDocument();
    });
});
