import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import './index.css';
import { ExperimentDetailPage } from './pages/ExperimentDetailPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { InteractivePage } from './pages/InteractivePage';

function App(): JSX.Element {
    return (
        <BrowserRouter>
            <div className="app-shell">
                <header className="nav-header">
                    <div className="nav-brand">City Data Analyzer</div>
                    <nav className="nav-links">
                        <Link to="/">インタラクティブ</Link>
                        <Link to="/experiments">バッチ探索</Link>
                    </nav>
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
