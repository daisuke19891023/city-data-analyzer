import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const envFromVite =
    typeof import.meta !== 'undefined'
        ? ((import.meta as { env?: Record<string, string | undefined> }).env ??
          undefined)
        : undefined;

if (typeof globalThis !== 'undefined') {
    (
        globalThis as {
            __IMPORT_META_ENV__?: Record<string, string | undefined>;
        }
    ).__IMPORT_META_ENV__ = envFromVite;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
