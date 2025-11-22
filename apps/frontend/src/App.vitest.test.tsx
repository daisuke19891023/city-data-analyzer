import { render, screen } from '@testing-library/react';
import App from './App';

describe('App component (Vitest)', () => {
    it('renders the app title', () => {
        render(<App />);
        expect(
            screen.getByRole('heading', { name: /city data analyzer/i })
        ).toBeInTheDocument();
    });
});
