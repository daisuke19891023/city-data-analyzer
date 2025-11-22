import { useEffect, useState } from 'react';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import './index.css';
import { ExperimentDetailPage } from './pages/ExperimentDetailPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { InteractivePage } from './pages/InteractivePage';

type Theme = 'dark' | 'light';

function resolveInitialTheme(): Theme {
    if (typeof window === 'undefined') return 'dark';
    const stored = window.localStorage.getItem('theme');
    if (stored === 'dark' || stored === 'light') return stored;
    const prefersLight = Boolean(
        window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: light)').matches
    );
    return prefersLight ? 'light' : 'dark';
}

function App(): JSX.Element {
    const [theme, setTheme] = useState<Theme>(resolveInitialTheme);

    useEffect(() => {
        const root = document.documentElement;
        root.dataset.theme = theme;
        window.localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((current) => (current === 'dark' ? 'light' : 'dark'));
    };

    return (
        <BrowserRouter>
            <div className="app-shell">
                <header className="nav-header">
                    <div className="nav-brand">City Data Analyzer</div>
                    <div className="nav-controls">
                        <button
                            type="button"
                            className="theme-toggle"
                            onClick={toggleTheme}
                            aria-label={`テーマを${
                                theme === 'dark' ? 'ライト' : 'ダーク'
                            }モードに切り替え`}
                        >
                            <span aria-hidden>
                                {theme === 'dark' ? '🌙' : '☀️'}
                            </span>
                            <span className="theme-toggle__label">
                                {theme === 'dark' ? 'ダーク' : 'ライト'}モード
                            </span>
                        </button>
                        <nav className="nav-links">
                            <Link to="/">インタラクティブ</Link>
                            <Link to="/experiments">バッチ探索</Link>
                        </nav>
                    </div>
                </header>
                <Routes>
                    <Route path="/" element={<InteractivePage />} />
                    <Route path="/experiments" element={<ExperimentsPage />} />
                    <Route
                        path="/experiments/:id"
                        element={<ExperimentDetailPage />}
                    />
                </Routes>
            </div>
        </BrowserRouter>
    );
}

export default App;
