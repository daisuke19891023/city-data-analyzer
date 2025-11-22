/** @type {import('jest').Config} */
const config = {
    preset: 'ts-jest/presets/default-esm',
    testEnvironment: 'jsdom',
    roots: ['<rootDir>/src'],
    testMatch: ['**/*.jest.test.ts?(x)'],
    setupFilesAfterEnv: ['<rootDir>/setupTests.ts'],
    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': '<rootDir>/test-file-stub',
        '^ai/react$': '<rootDir>/src/test-utils/aiReactMock.ts'
    },
    collectCoverageFrom: ['src/**/*.{ts,tsx}'],
    extensionsToTreatAsEsm: ['.ts', '.tsx'],
    globals: {
        'ts-jest': {
            useESM: true,
            tsconfig: '<rootDir>/tsconfig.jest.json'
        }
    }
};

module.exports = config;
