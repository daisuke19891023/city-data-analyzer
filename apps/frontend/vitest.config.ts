import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            'ai/react': '/src/test-utils/aiReactMock.ts'
        }
    },
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: './setupTests.ts',
        coverage: {
            provider: 'v8',
            reporter: ['text', 'lcov']
        }
    }
});
